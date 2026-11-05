#!/usr/bin/env python3
"""Extract BEMSH UPD objects and surviving source records from 2148:1013–1025.

Container layout follows re-bemsh/tools/findmod.py and disbesm6::Module;
character decoding follows dispak-tools/arfa/arap8.py. Instruction fields
are obtained exclusively from disbesm6, via the existing listing parser.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import runpy
import subprocess

ROOT = Path(__file__).resolve().parents[1]
START, COUNT = 0o1013, 11
ZONES = (0o1013, 0o1014, 0o1015, 0o1016, 0o1020, 0o1022, 0o1023, 0o1024)
KOI7 = {c: chr(c) for c in range(0o40, 0o140)}
KOI7.update(zip(range(0o140, 0o177), 'ЮАБЦДЕФГХИЙКЛМНОПЯРСТУЖВЬЫЗШЭЩЧ'))


def char(byte):
    if 0o100 <= byte <= 0o137:
        return KOI7[byte - 0o40]
    if 0o240 <= byte <= 0o336:
        return KOI7[byte - 0o140]
    return f'<{byte:o}>'


def name(word):
    value = ''.join('\0' if b == 0 else char(b)
                    for b in word.to_bytes(6, 'big')).rstrip(' \0')
    return value.translate(str.maketrans('ABEKMHOPCTYX', 'АВЕКМНОРСТУХ'))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--disassembler', type=Path,
                        default=ROOT.parent/'dispak-tools/disbesm6')
    args = parser.parse_args()
    out = ROOT/'build/upd'
    out.mkdir(parents=True, exist_ok=True)
    disks = {v: Path('/usr/local/share/besm6')/v for v in ('2148', '2248')}
    hashes = {v: sha(p.read_bytes()) for v, p in disks.items()}
    raw = {}
    for volume in disks:
        target = out/(volume+'.bin')
        target.unlink(missing_ok=True)
        subprocess.run(['besmtool', 'dump', volume, '--start=01013', '--length=11',
                        '--to-file='+str(target)], check=True, stdout=subprocess.DEVNULL,
                       cwd='/usr/local/share/besm6')
        raw[volume] = target.read_bytes()
        assert len(raw[volume]) == COUNT*6144
    data = raw['2148']
    words = [int.from_bytes(data[i:i+6], 'big') for i in range(0, len(data), 6)]
    occupied = set()
    modules = []
    parse = runpy.run_path(str(ROOT/'tests/echolot-layout.py'))['parse_instructions']
    for zone in ZONES:
        start = (zone-START)*1024

        def chunk(index):
            pos = start + index//85*1024 + index%85*12
            return words[pos:pos+12]

        header = chunk(0)
        assert header[0] == 1 and header[2] == 0o10000
        assert all((header[i] >> 24) == ((header[i] & 0xffffff)+5)//6
                   for i in (7, 8, 9))
        count = 1 + header[5] + sum(header[i] >> 24 for i in (7, 8, 9))
        length = count*12 + count//85*4
        binary = out/f'{zone:04o}.obj'
        binary.write_bytes(data[start*6:(start+length)*6])
        occupied.update(range(start, start+length))
        addresses = [((chunk(k)[10] & 0o177) << 8) | (chunk(k)[11] & 0o377)
                     for k in range(1, header[5]+1)]
        assert addresses == sorted(addresses) and addresses[0] == header[2]
        entries = []
        for i in range(header[7] & 0xffffff):
            c = chunk(1+header[5]+i//6)
            entries.append(dict(name=name(c[i%6*2]), address=f'{c[i%6*2+1]:05o}'))
        externs = []
        for i in range(header[8] & 0xffffff):
            c = chunk(1+header[5]+(header[7] >> 24)+i//6)
            externs.append(dict(module=name(c[i%6*2]), name=name(c[i%6*2+1])))
        lo, hi = header[2], header[2]+header[6]
        sym = out/f'{zone:04o}.sym'
        sym.write_text(f'{lo:05o}-{hi-1:05o} C -\n')
        command = [str(args.disassembler), '-r', '-e10000', '-n', str(sym), str(binary)]

        def disassemble():
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            assert not result.stderr, result.stderr
            return result.stdout

        # Mechanical code view supplies fields even in indirectly reached bodies.
        probe = disassemble()
        (out/f'{zone:04o}-all.lst').write_text(probe)
        instructions = parse(probe)
        entrypoints = sorted({int(e['address'], 8) for e in entries
                              if lo <= int(e['address'], 8) < hi
                              and e['name'] not in ('КОНСТ', 'СЛЕ006', 'ОШБ001')})
        bases = {}
        for (address, half), (reg, op, value, long) in instructions.items():
            if reg == 0o14 and op == 0o24 and long and value == address:
                bases[address] = value
            # These procedures receive their entry address in M15.
            if reg == 0o15 and op == 0o44 and not long and value == 0o14:
                bases[address] = max(e for e in entrypoints if e <= address)
        # Also enter bodies/epilogues directly: the generic analyzer cannot
        # infer the caller-supplied M15 across each indirect method call.
        seeds = set(entrypoints)
        for address, base in bases.items():
            for current in range(address, address+3):
                jumps = [(half, fields) for (a, half), fields in instructions.items()
                         if a == current and fields[0:2] == (0o14, 0o30) and fields[3]]
                if jumps:
                    target = base+jumps[0][1][2]
                    if lo <= target < hi:
                        seeds.update((target, current+1))
                    break
        sym.write_text(''.join(f'{a:05o} 524 {v:05o}\n' for a, v in sorted(bases.items()))
                       + ''.join(f'{a:05o} B -\n' for a in sorted(seeds)))
        listing = disassemble()
        (out/f'{zone:04o}.lst').write_text(listing)
        assert re.search(r'Module: (.+)', listing)[1] == name(header[1])
        modules.append(dict(zone=f'{zone:04o}', name=name(header[1]),
                            stored_words=length, last=f'{START+(start+length-1)//1024:04o}:'
                            f'{(start+length-1)%1024:04o}',
                            start=f'{lo:05o}', length=f'{header[6]:05o}',
                            relocation_range=[f'{header[i]:05o}' for i in (3, 4)],
                            chunks=header[5], entries=entries, externs=externs,
                            sha256=sha(binary.read_bytes()),
                            bases={f'{a:05o}': f'{v:05o}' for a, v in sorted(bases.items())}))

    # The remaining bytes contain editor/expansion records. Four header words
    # precede 8-bit BEMSH text; byte 5 gives the total record length in words.
    records = []
    for pos in range(len(words)):
        if pos in occupied:
            continue
        h = data[pos*6:pos*6+6]
        length = h[5]
        if h[4] != 0o124 or not 5 <= length <= 60 or pos+length > len(words):
            continue
        if any(i in occupied for i in range(pos, pos+length)):
            continue
        payload = data[(pos+4)*6:(pos+length)*6]
        if b'\0' not in payload:
            continue
        payload = payload.split(b'\0')[0]
        text = ''.join(' '*c if c < 0o100 else char(c) for c in payload).rstrip()
        if '<' in text or len(text.strip()) < 2:
            continue
        records.append(dict(location=f'{START+pos//1024:04o}:{pos%1024:04o}',
                            line=int.from_bytes(h[1:3], 'big') & 0x7fff,
                            header=[f'{w:016o}' for w in words[pos:pos+4]],
                            words=length, text=text))
    source = '\n'.join(f'{r["location"]} {r["line"]:5d} {r["text"]}' for r in records)+'\n'
    (out/'tail-source.txt').write_text(source)
    (out/'tail-source.json').write_text(json.dumps(records, ensure_ascii=False, indent=2)+'\n')
    old_entries = []
    start = (0o1025-START)*1024+0o14
    for i in range(8):
        old_entries.append(dict(name=name(words[start+i*2]),
                                address=f'{words[start+i*2+1]:05o}'))
    assert [e['name'] for e in old_entries] == [e['name'] for e in modules[-1]['entries']]
    differences = {f'{START+i:04o}': sum(a != b for a, b in zip(
        [data[n:n+6] for n in range(i*6144, (i+1)*6144, 6)],
        [raw['2248'][n:n+6] for n in range(i*6144, (i+1)*6144, 6)])) for i in range(COUNT)}
    assert all(differences[f'{z:04o}'] == 0 for z in range(0o1014, 0o1026))
    assert len(modules) == 8 and len(records) == 803
    for volume, path in disks.items():
        assert sha(path.read_bytes()) == hashes[volume], volume
    report = dict(modules=modules, source_records=len(records),
                  source_records_by_zone=dict(Counter(r['location'][:4] for r in records)),
                  earlier_kp_entries=old_entries, differing_words_2248=differences,
                  source_disks_sha256=hashes, source_disks_unchanged=True)
    (out/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print('UPD: eight complete BEMSH objects; 803 surviving source/expansion records')
    for m in modules:
        print(f'{m["zone"]}:0000–{m["last"]}  {m["name"]:6} '
              f'length {m["length"]}; externs {len(m["externs"])}')
    print('1014–1025 identical on 2148/2248; source disks unchanged')


if __name__ == '__main__':
    main()
