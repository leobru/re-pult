#!/usr/bin/env python3
"""Check the С/Р text editor on private PULT volumes, one session at a time."""
import argparse
import hashlib
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
from make2068 import ZONE

SOURCE = 'ААА\nБББ\nААА ВВВ\nГГГ\n'
CASES = (
    ('list', 'с 1:4', ('1. ААА', '2. БББ', '3. ААА ВВВ', '4. ГГГ')),
    ('replace', "р 2='НОВАЯ'\nс 1:4", ('2. НОВАЯ', '3. ААА ВВВ')),
    ('delete', 'р 2\nс 1:3', ('2. ААА ВВВ', '3. ГГГ')),
    ('copy', 'р 2=(4)\nс 1:4', ('2. ГГГ', '3. ААА ВВВ', '4. ГГГ')),
    ('insert', "р 0,'НОВАЯ_175'\nс 1:4", ('1. НОВАЯ', '2. ААА', '3. БББ')),
    ('partial', "р 3 'ААА'='Х'\nс 1:4", ('2. БББ', '3. Х ВВВ')),
    ('global', "р 1:4 'ААА'='ХХ'Ц\nс 1:4", ('1. ХХ', '2. БББ', '3. ХХ ВВВ')),
    ('terminal', "р 2=т\n'НОВАЯ'\nс 1:4", ('2. НОВАЯ', '3. ААА ВВВ')),
    ('quote', "р 2='Э050''105'\nс 1:4", ('2. Э050’105',)),
    ('missing', "р 20='Х'\nс 1:4", ('НЕТ СТРОКИ N =    20', '2. БББ')),
    # Context includes the two words preceding the match, even before 010000.
    ('find', "с 1 'ААА'", ('1. 000000000000ААА', 'ААА ВВВ')),
    ('not-found', "с 1 'ДДД'", ('НЕ НАЙДЕН ОБРАЗЕЦ', 'ДДД')),
    ('empty-pattern', "с 1 ''", ('НЕПРАВИЛЬНО ЗАДАН ОБРАЗЕЦ',)),
    ('archive', 'арх вася,50,100\nс тест\nс 1:4', ('ЕСТЬ', '2. БББ', '4. ГГГ')),
    ('decimal', 'с 10:12', ('10. СТРОКА 10', '11. СТРОКА 11', '12. СТРОКА 12')),
    ('printer', 'с 1:4 а', ()),
    ('punch', 'с 1:4 п', ()),
    ('buffer', 'с буф', ()),
)


def encode(text):
    """СИС КОД: GOST bytes, 0175 line end, 0172/0175 text end."""
    data = bytes(0o175 if c == '\n' else G.index(c) for c in text)
    data += bytes((0o172, 0o175))
    data = data.ljust((len(data) + 5) // 6 * 6, b'\0')
    return [int.from_bytes(data[i:i + 6], 'big') for i in range(0, len(data), 6)]


def write_zone(path, zone, words):
    with path.open('r+b') as stream:
        stream.seek((zone + 4) * ZONE + 64)
        stream.write(b''.join(struct.pack('<Q', w | (2 << 48)) for w in words))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dispak', default='dispak')
    parser.add_argument('--case', action='append', choices=[c[0] for c in CASES])
    parser.add_argument('--volumes', type=Path, default=ROOT / 'build/volumes')
    parser.add_argument('--output', type=Path, default=ROOT / 'build/spis-check')
    args = parser.parse_args()
    app = str(Path(shutil.which(args.dispak) or args.dispak).resolve())
    volumes, output = args.volumes.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    originals = {v: hashlib.sha256((volumes / v).read_bytes()).digest()
                 for v in ('2248', '2068')}
    selected = [c for c in CASES if not args.case or c[0] in args.case]
    for name, commands, expected in selected:
        with tempfile.TemporaryDirectory(prefix='pult-spis-') as temporary:
            temporary = Path(temporary)
            for v in originals:
                shutil.copyfile(volumes / v, temporary / v)
            text = SOURCE if name != 'decimal' else ''.join(
                f'СТРОКА {i}\n' for i in range(1, 13))
            words = encode(text)
            deck = (ROOT / 'pult2068.b6').read_text().replace(
                'еконец', 'в 10000\n' + ''.join(f'с {w:016o}\n' for w in words) + 'еконец')
            if name == 'archive':
                archive = temporary / '2345'
                archive.write_bytes(bytes((0o200 + 4) * ZONE))
                catalog = [0] * 1024
                catalog[0] = int.from_bytes(bytes(G.index(c) for c in 'ВАСЯ  '), 'big')
                catalog[1] = int.from_bytes(bytes(G.index(c) for c in 'ТЕСТ  '), 'big')
                catalog[2], catalog[0o377] = (1 << 24) | 1, 3
                write_zone(archive, 0o100, catalog)
                write_zone(archive, 0o101, words)
                deck = deck.replace('лент 30(1С)^', 'лент 30(1С)^\nлент 50(2345-зп)^')
            job = temporary / 'job.b6'
            job.write_text(deck)
            env = dict(os.environ, HOME=str(temporary))
            for key in ('BESM6_PATH', 'BESM6_SMALL_DISKS'):
                env.pop(key, None)
            commands += '\nконец\n'
            (output / f'{name}.input').write_text(commands)
            with (output / f'{name}.out').open('w') as stdout, \
                    (output / f'{name}.trace').open('w') as stderr:
                result = subprocess.run(
                    [app, '--725', '--path=' + str(temporary) + ':/usr/local/share/besm6',
                     '-q', '-t', '-t', str(job)], input=commands, text=True,
                    stdout=stdout, stderr=stderr, env=env, cwd=temporary, timeout=15)
            terminal = (output / f'{name}.out').read_text()
            trace = (output / f'{name}.trace').read_text()
            assert result.returncode == 0, (name, result.returncode)
            assert 'АВОСТ' not in terminal, (name, terminal)
            for fragment in expected:
                assert fragment in terminal, (name, fragment, terminal)
            assert re.search(r'^02010: \*70', trace, re.M) if name in (
                'replace', 'delete', 'copy', 'insert', 'partial', 'global',
                'terminal', 'quote', 'missing') else re.search(r'^00023:', trace, re.M)
            if name == 'printer':
                assert len(re.findall(r'^00411: \*64', trace, re.M)) == 4
            if name == 'punch':
                assert re.search(r'^00302: \*71 600', trace, re.M)
            if name == 'buffer':
                assert len(re.findall(r'^01214: \*70', trace, re.M)) == 4
            if name == 'archive':
                assert re.search(r'^01256: \*70.*0010040000500101', trace, re.M)
            print(name + ': OK', flush=True)
    assert all(hashlib.sha256((volumes / v).read_bytes()).digest() == digest
               for v, digest in originals.items()), 'source volume changed'
    print(f'{len(selected)} checks passed; source volumes unchanged')


if __name__ == '__main__':
    main()
