#!/usr/bin/env python3
"""Compile a СИС БЕМ archive through БАВТ on disposable, adapted disks."""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from make2068 import ZONE, MASK, control_words, payload

# БАВТ addresses relative to 066000; checked against the original image.
# These adaptations are specific to pult2068.b6 and БЕМШ 06/78.
PATCHES = (
    (0o1304, 0o3040003077000000, 0o3057003077000000),  # inverse swap
    (0o1310, 0o300000, 0o300371),                    # system offset
    (0o1106, 0o0220000000751274, 0o0220000002200000),  # preserve BEMSH 01274
    (0o1412, 0o1154, 0o1161),                       # skip foreign status fields
    (0o1421, 0o4111242477, 0o1172),                  # translation message
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dispak', default=os.environ.get('DISPAK', 'dispak'))
    args = parser.parse_args()
    emulator = shutil.which(args.dispak)
    if emulator is None:
        parser.error('dispak executable not found')
    out = ROOT / 'build' / 'bemsh-check'
    out.mkdir(parents=True, exist_ok=True)
    volumes = [ROOT / 'build' / 'volumes' / v for v in ('2248', '2068')]
    original = [digest(p) for p in volumes]
    commands = (ROOT / 'tests' / 'bemsh.txt').read_text()
    with tempfile.TemporaryDirectory(prefix='pult-bemsh-') as directory:
        private = Path(directory)
        for source in volumes:
            shutil.copyfile(source, private / source.name)
        disk = private / '2068'
        image = bytearray(disk.read_bytes())
        header = (0o51 + 4) * ZONE
        start = header + 64
        for address, old, new in PATCHES:
            offset = start + address * 8
            word = struct.unpack_from('<Q', image, offset)[0]
            if word & MASK != old:
                raise RuntimeError(f'БАВТ {0o66000 + address:05o}: unexpected word')
            struct.pack_into('<Q', image, offset, (word & ~MASK) | new)
        image[header:start] = control_words(0o51, image[start:start + 8192])
        disk.write_bytes(image)
        (private / '2345').write_bytes(bytes((0o200 + 4) * ZONE))
        (private / '2222').write_bytes(bytes(4 * ZONE))
        deck = (ROOT / 'pult2068.b6').read_text().replace(
            'лент 30(1С)^',
            'лент 30(1С)^\nлент 50(2345-зп)^\nлент 43(2222-зп)^')
        job = private / 'job.b6'
        job.write_text(deck)
        env = dict(os.environ, HOME=str(private))
        env.pop('BESM6_PATH', None)
        env.pop('BESM6_SMALL_DISKS', None)
        with (out / 'session.out').open('w') as stdout, (out / 'session.trace').open('w') as stderr:
            result = subprocess.run(
                [emulator, '--725', '--path=' + str(private) + ':/usr/local/share/besm6',
                 '-p', '-t', str(job)], input=commands, text=True,
                stdout=stdout, stderr=stderr, env=env, cwd=private, timeout=20)
        for number in ('2222', '2345'):
            shutil.copyfile(private / number, out / number)
        listing = (out / 'session.out').read_text()
        for expected in ('ЧИСЛО ОШИБОК=0000. МАКС СЕРЬЕЗН=0.',
                         'КОНЕЦ ТРАНСЛЯЦИИ', 'ВРЕМЯ РЕШ:', 'КОНЕЦ ЗАДАЧИ'):
            if expected not in listing:
                raise RuntimeError(f'missing output: {expected}')
        if result.returncode or 'АВОСТ' in listing or listing.count('ЗАПИСАН  В  ЗОНЫ') != 1:
            raise RuntimeError('abnormal termination or repeated compilation')
        module = [w & MASK for w in struct.unpack('<1024Q', payload((private / '2222').read_bytes(), 0))]
        if module[2] != 0o1000 or module[6] != 3 or module[0o14:0o17] != [0o0010100100001002, 0o123, 0]:
            raise RuntimeError('unexpected compiled module')
    if [digest(p) for p in volumes] != original:
        raise RuntimeError('source volumes changed')
    print('PASS: СИС БЕМ → БАВТ БТЕСТ → module ТЕСТ, zero errors, return to ПУЛЬТ')
    print(f'Listing and private output volumes: {out}')


if __name__ == '__main__':
    main()
