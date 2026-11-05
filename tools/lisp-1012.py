#!/usr/bin/env python3
"""Disassemble the displaced Lisp fragment in 2148:01012 and map its cells."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import runpy
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def dump(volume, target, *options):
    target.unlink(missing_ok=True)
    subprocess.run(['besmtool', 'dump', volume, *options, '--to-file=' + str(target)],
                   cwd='/usr/local/share/besm6', check=True, stdout=subprocess.DEVNULL)
    return target.read_bytes()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--disassembler', type=Path,
                        default=ROOT.parent / 'dispak-tools/disbesm6')
    parser.add_argument('--search-copies', action='store_true',
                        help='search six exact eight-word windows across both volumes')
    args = parser.parse_args()
    out = ROOT / 'build/lisp-1012'
    out.mkdir(parents=True, exist_ok=True)
    disks = {v: Path('/usr/local/share/besm6') / v for v in ('2148', '2248')}
    hashes = {v: sha(p.read_bytes()) for v, p in disks.items()}
    raw = dump('2148', out / 'zone.bin', '--start=01012', '--length=1')
    assert len(raw) == 6144
    words = [int.from_bytes(raw[i:i+6], 'big') for i in range(0, len(raw), 6)]
    assert all(words[:0o154]) and not any(words[0o154:0o400])
    assert all(words[0o400:])
    for name, command in (
        ('zone.dump', ['besmtool', 'dump', '2148', '--start=01012', '--length=1']),
        ('zone.itm', ['besmtool', 'view', '2148', '--start=01012', '--length=1', '--encoding=i']),
    ):
        result = subprocess.run(command, check=True, capture_output=True, text=True,
                                cwd='/usr/local/share/besm6')
        (out / name).write_text(result.stdout)

    # The mutable 24-bit pair is addressed explicitly as 06143 by this code.
    pair_offset = 0o640
    assert words[pair_offset] == (2 << 24) | 1
    displacement = 0o6143 - pair_offset
    assert displacement + 0o475 == 0o6000
    assert displacement + 0o777 == 0o6302
    binary = out / 'code.bin'
    binary.write_bytes(raw[0o475*6:0o1000*6])
    result = subprocess.run([str(args.disassembler), '-b', '-a6000', '-e6000', '-n',
                             str(ROOT / 'syms/ЛИСП-1012.sym'), str(binary)],
                            capture_output=True, text=True, check=True)
    assert not result.stderr, result.stderr
    parse = runpy.run_path(str(ROOT / 'tests/echolot-layout.py'))['parse_instructions']
    instructions = parse(result.stdout)
    # Validate the actual references that fix the original address, using
    # instruction fields supplied by disbesm6 rather than another decoder.
    for location, fields in {
        (0o6017, 0): (0, 0o003, 0o6027, False),
        (0o6020, 0): (0, 0o010, 0o6030, False),
        (0o6136, 0): (0, 0o003, 0o6143, False),
        (0o6141, 0): (0, 0o001, 0o6143, False),
        (0o6152, 0): (0, 0o010, 0o6143, False),
        (0o6155, 0): (0, 0o000, 0o6143, False),
        (0o6156, 0): (0, 0o23, 0o410, True),
        (0o6156, 1): (0, 0o30, 0o6156, True),
        (0o6160, 0): (0, 0o30, 0o6144, True),
    }.items():
        assert instructions[location] == fields, (location, instructions.get(location))
    (out / 'code.lst').write_text(result.stdout.replace(
        'Code: 1170 (0303) words', 'Code: 195 (0303) words; 1170 bytes'))

    links = {}
    cells = ['offset\taddress\tcar24\tcdr24\tcar15\tcdr15']
    for offset in range(0o1000, 0o2000):
        word = words[offset]
        car, cdr = word >> 24, word & 0xffffff
        address = offset + 0o10000
        cells.append(f'{offset:04o}\t{address:05o}\t{car:08o}\t{cdr:08o}'
                     f'\t{car & 0o77777:05o}\t{cdr & 0o77777:05o}')
    for name, shift in (('car', 24), ('cdr', 0)):
        counts = Counter((word >> shift & 0o77777) - index - 1
                         for index, word in enumerate(words[0o1000:])
                         if word >> shift & 0o77777)
        assert counts.most_common(1)[0][0] == 0o11000
        links[name] = {f'{base:05o}': count for base, count in counts.most_common(5)}
    assert links['cdr']['11000'] == 132 and links['car']['11000'] == 37
    (out / 'cells.tsv').write_text('\n'.join(cells) + '\n')

    copies = None
    if args.search_copies:
        copies = {}
        for volume in disks:
            flat = dump(volume, out / (volume + '.bin'))
            copies[volume] = {}
            for offset in (0o475, 0o501, 0o600, 0o740, 0o1000, 0o1700):
                needle = raw[offset*6:(offset+8)*6]
                hits = []
                pos = flat.find(needle)
                while pos >= 0:
                    if pos % 6 == 0:
                        word = pos // 6
                        hits.append(f'{word // 1024:05o}:{word % 1024:04o}')
                    pos = flat.find(needle, pos+1)
                expected = [f'01012:{offset:04o}'] if volume == '2148' else []
                assert hits == expected, (volume, offset, hits)
                copies[volume][f'{offset:04o}'] = hits
    for volume, path in disks.items():
        assert sha(path.read_bytes()) == hashes[volume], volume
    report = dict(zone_sha256=sha(raw), code_sha256=sha(binary.read_bytes()),
                  code_disk_offsets=['0475', '0777'], code_addresses=['06000', '06302'],
                  code_displacement=f'{displacement:05o}', pair_disk_offset='0640',
                  pair_address='06143', cells_addresses=['11000', '11777'],
                  sequential_link_bases=links, exact_eight_word_copies=copies,
                  source_disks_sha256=hashes, source_disks_unchanged=True)
    (out / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print('2148:01012: code 0475–0777 → 06000–06302; cells 1000–1777 → 11000–11777')
    print('Pair 06143 matched; next-cell links: CDR 132, CAR 37; source disks unchanged')


if __name__ == '__main__':
    main()
