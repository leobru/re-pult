#!/usr/bin/env python3
"""Compile, load, unload and relocate a Pascal segment with a temporary ЗАГР.

The stock PULT resident has no compatible dynamic loader at 077040.
This test temporarily installs the checked loader from archive zone 0117;
no system volume or installed image is patched.
"""
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
from make2068 import MASK, ZONE, payload

# Checked adaptations from pasauto-re/mkloader2.py: monitor save/restore,
# saved registers, temporary words, and return to PULT's restart entry.
PATCHES = (
    (0o77447, 0o0113613600430017, 0o0113612500430017),
    (0o77462, 0o7317610400000000, 0o7317606600000000),
    (0o77470, 0o0113613601007570, 0o0113612501007570),
    (0o77473, 0o0110617501126172, 0o0110616301126160),
    (0o77475, 0o0100617500000000, 0o0100616300000000),
    (0o77502, 0o7317611200000000, 0o7317607400000000),
    (0o77606, 0o0277607436400000, 0o0277600236400000),
    (0o77657, 0o0112613602677674, 0o0112612502677674),
    (0o77660, 0o2410000201126135, 0o2410000201126124),
)


def raw_words(image, zone):
    return [w & MASK for w in struct.unpack('<1024Q', payload(image, zone))]


def compatible_loader(image):
    source = raw_words(image, 0o117)
    raw = b''.join(w.to_bytes(6, 'big') for w in source)
    assert hashlib.sha256(raw).hexdigest() == 'c1ed2fc74afae5244235810fa4c44f2873c3d6ebc86be8fd2b565cded7d4cf2c'
    adapted = list(source)
    for address, old, new in PATCHES:
        index = address - 0o76000
        assert adapted[index] == old, f'loader patch mismatch at {address:05o}'
        adapted[index] = new
    current = raw_words(image, 0o35)
    current[0o1040:0o1700] = adapted[0o1040:0o1700]
    return current


def gost_source(source):
    letters = {c: i for i, c in enumerate(G)}
    letters.update(zip('ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                       (0o40, 0o42, 0o61, 0o77, 0o45, 0o100, 0o101, 0o55,
                        0o102, 0o103, 0o52, 0o104, 0o54, 0o105, 0o56, 0o60,
                        0o106, 0o107, 0o110, 0o62, 0o111, 0o112, 0o113, 0o65, 0o63, 0o114)))
    letters.update({'@': 0o21, '[': 0o27, ']': 0o30, "'": 0o33,
                    '`': 0o32, '\n': 0o175})
    encoded = bytes(letters[c] for c in source.upper()) + bytes([0o172])
    if len(encoded) > 6144 * 0o30:
        raise ValueError('source exceeds its allocated archive entry')
    encoded = encoded.ljust((len(encoded) + 5) // 6 * 6, b'\0')
    return [int.from_bytes(encoded[i:i + 6], 'big') for i in range(0, len(encoded), 6)]


def write_words(path, zone, words):
    with path.open('r+b') as stream:
        for i, word in enumerate(words):
            z, offset = divmod(i, 1024)
            stream.seek((zone + z + 4) * ZONE + 64 + offset * 8)
            stream.write(struct.pack('<Q', word | (2 << 48)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dispak', default='dispak')
    parser.add_argument('--volumes', type=Path, default=ROOT / 'build/volumes')
    parser.add_argument('--output', type=Path, default=ROOT / 'build/pascal-segments')
    args = parser.parse_args()
    app = Path(shutil.which(args.dispak) or args.dispak).resolve()
    directory, output = args.volumes.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    hashes = {v: hashlib.sha256((directory / v).read_bytes()).digest()
              for v in ('2148', '2248', '2068')}
    image = (directory / '2068').read_bytes()
    with tempfile.TemporaryDirectory(prefix='pult-segments-') as temporary:
        temporary = Path(temporary)
        for v in hashes:
            shutil.copyfile(directory / v, temporary / v)
        archive = temporary / '2345'
        archive.write_bytes(bytes((0o1000 + 4) * ZONE))
        deck = (ROOT / 'pult2068.b6').read_text().replace(
            'лент 30(1С)^', 'лент 30(1С)^\nлент 50(2345-зп)^')
        job = temporary / 'job.b6'
        job.write_text(deck)
        env = dict(os.environ, HOME=str(temporary))
        env.pop('BESM6_PATH', None)
        env.pop('BESM6_SMALL_DISKS', None)

        def session(name, commands, expected):
            (output / (name + '.txt')).write_text(commands)
            result = subprocess.run([str(app), '--725', '--path=' + str(temporary) +
                                     ':/usr/local/share/besm6', '-q', '-t', str(job)],
                                    input=commands, text=True, capture_output=True,
                                    cwd=temporary, env=env, timeout=30)
            (output / (name + '.out')).write_text(result.stdout)
            (output / (name + '.trace')).write_text(result.stderr)
            assert result.returncode == 0, (name, result.stdout, result.stderr[-2000:])
            assert 'АВОСТ' not in result.stdout, (name, result.stdout)
            for text in expected:
                assert text in result.stdout, (name, text, result.stdout)
            print(name + ' passed', flush=True)
            return result

        session('archive', 'дай новарх,50,100,вася\nарх вася,50,100,100\n'
                'з сегм(30)\nз тест(30)\nконец\n',
                ['МСВ   СЕГМ', 'МСВ   ТЕСТ'])
        fixtures = ROOT / 'tests/pascal-segments'
        write_words(archive, 0o101, gost_source((fixtures / 'segment.pas').read_text()))
        write_words(archive, 0o131, gost_source((fixtures / 'main.pas').read_text()))
        write_words(archive, 0o400, compatible_loader(image))
        session('compile-segment', 'арх вася,50,100\nпас сегм - зонгп 500300 1\nконец\n',
                ['ПАСКАЛЬ-АВТОКОД 9.(09.12.88)',
                 'НА БОБ 2345 ЗАПИСЬ 0001 ЗОН С 500300', 'ВСЕ СДЕЛАНО.'])
        assert any(raw_words(archive.read_bytes(), 0o300)), 'segment image not saved'
        result = session('run', 'арх вася,50,100\nпас тест\nконец\n',
                         ['ЗАГРУЗКА 7', 'СЕГМЕНТ ВХОД', 'СЕГМЕНТ ВОЗВРАТ',
                          'ВЫГРУЗКА 7', 'ЗАГРУЗКА 8', 'СЕГМЕНТАЦИЯ ПРОШЛА', 'ВСЕ СДЕЛАНО.'])
        assert result.stdout.count('СЕГМЕНТ ВХОД') == 2, result.stdout
        assert result.stdout.count('СЕГМЕНТ ВОЗВРАТ') == 2, result.stdout
        assert re.findall(r'ВЫЗОВ\s+(\d+)', result.stdout) == ['1', '2'], result.stdout
        assert 'ОШИБКА СЕГМЕНТАЦИИ' not in result.stdout
        # ЗАГР reads into work page 035, then relocates/copies to the LAD
        # destination. Both loads must reach the saved segment on unit 50.
        assert result.stderr.count('(=0010350000500300)') == 2, result.stderr[-2000:]
        print('LOAD/UNLOAD, relocation after erasing the first page, and callbacks passed')
    for v, digest in hashes.items():
        assert hashlib.sha256((directory / v).read_bytes()).digest() == digest
    print('Source disks unchanged; temporary loader restored by the Pascal program')


if __name__ == '__main__':
    main()
