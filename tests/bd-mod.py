#!/usr/bin/env python3
"""Check private BANDIT reverse-copy MOD on disposable database copies."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from gost import G
from make2068 import MASK, ZONE, payload
from bdcatalog import decode


def word(text):
    return int.from_bytes(bytes(G.index(c) for c in text.ljust(6)), 'big')


def records(image):
    blocks = [struct.unpack('<1024Q', payload(image, 0o200 + i)) for i in range(4)]
    first = blocks[0]
    start, count = first[3] & 0o1777, first[-5] & MASK
    result = {}
    for i in range(start, start + count, 2):
        name, reference = first[i] & MASK, first[i + 1] & MASK
        block, slot = reference & 0o1777, reference >> 10 & 0o1777
        body = []
        while True:
            descriptor = blocks[block][slot] & MASK
            offset, length = descriptor & 0o1777, descriptor >> 10 & 0o1777
            body.extend(w & MASK for w in blocks[block][offset:offset + length])
            following = descriptor >> 20 & 0o3777777
            if not following:
                break
            block, slot = following & 0o1777, following >> 10 & 0o1777
        result[name] = body
    return result


def catalog(image):
    return decode(b''.join((w & MASK).to_bytes(6, 'big')
                          for w in struct.unpack('<1024Q', payload(image, 0o30))))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dispak', default=os.environ.get('DISPAK', 'dispak'))
    args = parser.parse_args()
    app = shutil.which(args.dispak)
    assert app, args.dispak
    out = ROOT / 'build/bd-mod'
    out.mkdir(parents=True, exist_ok=True)
    sources = [ROOT / 'build/volumes' / v for v in ('2148', '2248', '2068')]
    sources.append(ROOT / 'build/bd-private/2068')
    hashes = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    setup = ('арх сисбиб,40,0\nbd open ктлBD\nbd delete восьмр\n'
             'bd new 300200 4\nbd open восьмр\nbd put beta 10000 длв 1\n'
             'bd put alpha 10001 длв 1\nконец\n')
    commands = ('арх сисбиб,40,0\nbd open восьмр\nbd mod beta 10010\n'
                'bd get beta 20010\nконец\n')
    reports = {}
    with tempfile.TemporaryDirectory(prefix='runtime-', dir=out) as temporary:
        folder = Path(temporary)
        for v in ('2148', '2248', '2068'):
            shutil.copyfile(ROOT / ('build/bd-private/2068' if v == '2068' else 'build/volumes/' + v), folder / v)
        (folder / '1234').write_bytes(b'')
        job = folder / 'job.b6'
        source = (ROOT / 'pult2068.b6').read_text().replace(
            '40(2068)', '40(2068-ЗП)').replace('30(1С)', '30(1234-ЗП)')
        # Independent old, adjacent and candidate words; candidate has the
        # ordinary two-character text terminator on the following word.
        data = (f'в 10000\nс {word("СТАРОЕ"):016o}\nс {word("СОСЕД"):016o}\n'
                f'в 10010\nс {word("НОВОЕ"):016o}\nс {((0o172 << 40) | (0o175 << 32)):016o}\n')
        job.write_text(source.replace('в 3000\n', data + 'в 3000\n'))

        def session(label, commands, instructions=False):
            home = folder / ('home-' + label)
            home.mkdir()
            env = dict(os.environ, HOME=str(home))
            env.pop('BESM6_PATH', None)
            env.pop('BESM6_SMALL_DISKS', None)
            (out / (label + '.input')).write_text(commands)
            with (out / (label + '.trace')).open('w') as trace:
                run = subprocess.run([app, '--725', '--path=' + str(folder) +
                                      ':/usr/local/share/besm6', '-q', '-t',
                                      *(['-t'] if instructions else []), str(job)],
                                     input=commands, text=True, stdout=subprocess.PIPE,
                                     stderr=trace, cwd=folder, env=env, timeout=20)
            (out / (label + '.out')).write_text(run.stdout)
            assert run.returncode == 0, run.stdout
            return run.stdout, (out / (label + '.trace')).read_text()

        stdout, _ = session('setup', setup)
        assert 'АВОСТ' not in stdout and 'КОНТРОЛЬ КОМАНДЫ' not in stdout
        seed = (folder / '2068').read_bytes()
        database = (folder / '1234').read_bytes()
        before = records(database)
        assert before[word('ВЕТА')][1:] == [word('СТАРОЕ')]
        assert before[word('АLРНА')][1:] == [word('СОСЕД')]
        before_catalog = catalog(seed)
        stdout, trace = session('fixed', commands, instructions=True)
        assert 'КОНТРОЛЬ КОМАНДЫ' not in stdout and 'АВОСТ' not in stdout, stdout
        after = records((folder / '1234').read_bytes())
        assert after[word('ВЕТА')][0] == before[word('ВЕТА')][0]
        assert after[word('ВЕТА')][1:] == [word('НОВОЕ')]
        assert after[word('АLРНА')] == before[word('АLРНА')]
        assert catalog((folder / '2068').read_bytes()) == before_catalog
        assert 'vjm 74022(16)' in trace
        assert not re.search(r'^74664:', trace, re.M), 'MOD entered NEW'
        assert re.search(r'^ +20010: store ' + f'{word("НОВОЕ"):016o}', trace, re.M)
        # Reopening must expose the new data, and a missing key must not write.
        frozen = (folder / '1234').read_bytes()
        stdout, trace = session('reopen', 'арх сисбиб,40,0\nbd open восьмр\nbd get beta 20010\nbd mod missing 10010\nконец\n', True)
        assert 'ТАКОЙ ЗАПИСИ НЕТ' in stdout and 'АВОСТ' not in stdout, stdout
        assert re.search(r'^ +20010: store ' + f'{word("НОВОЕ"):016o}', trace, re.M)
        assert (folder / '1234').read_bytes() == frozen
        # Longer-than-block record exercises both MOD fragment writes.
        n = 0o2100
        old = [0o1230000000000000 + i for i in range(n)]
        new = [0o4560000000000000 + i for i in range(n)]
        init = 'в 10200\n' + ''.join(f'с {w:016o}\n' for w in old)
        init += 'в 13200\n' + ''.join(f'с {w:016o}\n' for w in new)
        job.write_text(source.replace('в 3000\n', init + 'в 3000\n'))
        session('long-put', 'арх сисбиб,40,0\nbd open восьмр\nbd put gamma 10200 длв 2100\nконец\n')
        long_before = records((folder / '1234').read_bytes())
        assert long_before[word('GАММА')][1:] == old
        before_raw = (folder / '1234').read_bytes()
        stdout, trace = session('long-mod', 'арх сисбиб,40,0\nbd open восьмр\nbd mod gamma 13200\nbd get gamma 20200\nконец\n', True)
        assert 'АВОСТ' not in stdout and 'КОНТРОЛЬ КОМАНДЫ' not in stdout, stdout
        long_after = records((folder / '1234').read_bytes())
        assert long_after[word('GАММА')][0] == long_before[word('GАММА')][0]
        assert long_after[word('GАММА')][1:] == new
        assert long_after[word('ВЕТА')] == after[word('ВЕТА')]
        assert long_after[word('АLРНА')] == before[word('АLРНА')]
        # Only payload data may differ: slots, links, free counts and metadata stay.
        after_raw = (folder / '1234').read_bytes()
        for z in range(4):
            x, y = (struct.unpack('<1024Q', payload(raw, 0o200+z)) for raw in (before_raw, after_raw))
            last_slot = x[1] & 0o1777
            assert x[:last_slot+1] == y[:last_slot+1]
            if z == 0:
                directory = x[3] & 0o1777
                assert x[directory:] == y[directory:]
        stores = {(int(a, 8), int(w, 8)) for a, w in re.findall(r'^ +([0-7]{5}): store ([0-7]{16})', trace, re.M)}
        assert all((0o20200+i, w) in stores for i, w in enumerate(new))
        def direct(label, key, limit, pointer=0o74005):
            # Native deck: load BANDIT, open root by entry 31, GET by name,
            # then MOD through key=0 and adescr pointing at curdsc.
            first = struct.unpack('<1024Q', payload((folder / '1234').read_bytes(), 0o200))
            free_slot = next(i for i in range(4, first[3] & 0o1777) if first[i] & MASK == 0)
            constants = [0o0010360000400027,
                         (4 << 18) | (0o30 << 12) | 0o200,
                         0o70000, 0o64000, 0o74000, 0o2200,
                         word(key), 0o20000, 0, pointer, 0o13200, limit, free_slot << 10]
            code = ['00 070 3000', '04 24 74000 00 010 3001',
                    '04 000 0026 00 010 3002', '04 000 0014 00 010 3003',
                    '04 000 0006 00 010 3004', '04 000 0024 00 010 3005',
                    '04 000 0011 16 31 74031',
                    '00 010 3006 04 000 0010', '00 010 3007 04 000 0013',
                    '00 010 3010 04 000 0015', '16 31 74020',
                    '00 010 3011 04 000 0012', '00 010 3012 04 000 0013',
                    '00 010 3013 04 000 0015', '00 010 0000 04 000 0010',
                    '16 31 74022', '00 062 0000']
            deck = ('шифр 412020^\nозу 32^\nвре 20^\nспец^\n'
                    'лент 40(2068)^\nлент 30(1234-ЗП)^\nвхо 2000^\nе\nв 2000\n')
            deck += ''.join('к ' + x + '\n' for x in code)
            deck += 'в 2200\nк 00 062 0000\nв 3000\n'
            deck += ''.join(f'с {w:016o}\n' for w in constants)
            deck += init + 'еконец\n'
            job.write_text(deck)
            snapshot = (folder / '1234').read_bytes()
            stdout, trace = session(label, '', True)
            assert 'АВОСТ' not in stdout and 'КОНТРОЛЬ КОМАНДЫ' not in stdout, stdout
            copied = {(int(a, 8), int(w, 8)) for a, w in re.findall(r'^ +([0-7]{5}): store ([0-7]{16})', trace, re.M)}
            previous_data = records(snapshot)[word(key)][1:]
            assert all((0o20000+i, w) in copied for i, w in enumerate(previous_data))
            if limit or not pointer or pointer == 0o3014:
                error = 12 if limit else (1 if not pointer else 3)
                assert re.search(r'^02200:.*acc=' + f'{error:016o}', trace, re.M)
                assert re.search(r'^02200: \*62', trace, re.M), 'error continuation not called'
                assert (folder / '1234').read_bytes() == snapshot
            else:
                assert not re.search(r'^02200:', trace, re.M)
                result = records((folder / '1234').read_bytes())
                assert result[word('ВЕТА')][1:] == [new[0]]
                assert result[word('GАММА')] == long_after[word('GАММА')]
                assert result[word('АLРНА')] == before[word('АLРНА')]
        direct('address-mod', 'ВЕТА', 0)
        direct('short-buffer', 'GАММА', 1)
        direct('null-descriptor', 'ВЕТА', 0, 0)
        direct('empty-slot', 'ВЕТА', 0, 0o3014)
        reports.update(mod_functional=True, single_word_record=True, linked_words=n,
                       metadata_unchanged=True, structure_unchanged=True,
                       neighbor_unchanged=True, missing_key_no_writes=True, address_mode=True,
                       short_buffer_no_writes=True, null_descriptor_no_writes=True, empty_slot_no_writes=True)

    assert all(hashlib.sha256(p.read_bytes()).hexdigest() == old for p, old in hashes.items())
    reports['source_volumes_unchanged'] = True
    (out / 'report.json').write_text(json.dumps(reports, indent=2) + '\n')
    print('Private MOD: replacement and GET verified, including 1088-word chain; metadata, structure and neighbors unchanged')


if __name__ == '__main__':
    main()
