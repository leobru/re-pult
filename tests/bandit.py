#!/usr/bin/env python3
"""Exercise the disk-identical BD/BANDIT using private writable volumes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from gost import G
from make2068 import MASK, ZONE, payload, control_words
import struct


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dispak', default=os.environ.get('DISPAK', 'dispak'))
    parser.add_argument('--safe-buffer', action='store_true',
                        help='patch private BD default buffer 33 -> 32 for multiblock records')
    args = parser.parse_args()
    out = ROOT / ('build/bandit-runtime-safe' if args.safe_buffer else 'build/bandit-runtime')
    out.mkdir(parents=True, exist_ok=True)
    volumes = ROOT / 'build/volumes'
    hashes = {v: hashlib.sha256((volumes / v).read_bytes()).hexdigest()
              for v in ('2068', '2148', '2248')}
    length = 0o2100
    pattern = [0o1234567000000000 + i for i in range(length)]
    bandit = int.from_bytes(bytes(G.index(c) for c in 'БАНДИТ'), 'big')
    commands = """арх сисбиб,40,0
bd open ктлBD
bd инф ктлбд
bd инф бд7154
bd delete восьмр
bd new 300200 4
bd open восьмр
bd ктл
bd put alpha 74001 длв 1
bd get alpha 20000
bd put beta 20000 длв 1
bd put alpha 74002 длв 1
bd get alpha 20100
bd delete alpha
bd get alpha 20100
bd put gamma 10200 длв 2100
bd get gamma 20200
bd инф gamma
bd delete gamma
bd ктл
конец
"""
    if not args.safe_buffer:
        commands = commands.replace('bd put gamma 10200 длв 2100\nbd get gamma 20200\n'
                                    'bd инф gamma\nbd delete gamma\n', '')
        commands = commands.replace('конец\n', 'bd mod beta 10000\nконец\n')
    (out / 'session.txt').write_text(commands)
    with tempfile.TemporaryDirectory(prefix='pult-bandit-', dir=out) as temporary:
        folder = Path(temporary)
        for v in hashes:
            shutil.copyfile(volumes / v, folder / v)
        if args.safe_buffer:
            image = bytearray((folder / '2068').read_bytes())
            data = bytearray(payload(image, 0o26))
            old, = struct.unpack_from('<Q', data, 0o546 * 8)
            assert old & MASK == 0o33
            struct.pack_into('<Q', data, 0o546 * 8, (old & ~MASK) | 0o32)
            offset = (0o26 + 4) * ZONE
            image[offset:offset + ZONE] = control_words(0o26, data) + data
            (folder / '2068').write_bytes(image)
        (folder / '1234').write_bytes(b'')
        home = folder / 'home'
        home.mkdir()
        source = (ROOT / 'pult2068.b6').read_text()
        source = source.replace('40(2068)', '40(2068-ЗП)').replace('30(1С)', '30(1234-ЗП)')
        source = source.replace('в 3000\n', 'в 10200\n' +
                                ''.join(f'с {w:016o}\n' for w in pattern) + 'в 3000\n')
        job = folder / 'job.b6'
        job.write_text(source)
        (out / 'job.b6').write_text(source)
        env = dict(os.environ, HOME=str(home))
        env.pop('BESM6_PATH', None)
        env.pop('BESM6_SMALL_DISKS', None)
        with (out / 'trace.txt').open('w') as stream:
            run = subprocess.run([args.dispak, '--725', '--path=' + str(folder) +
                                  ':/usr/local/share/besm6', '-q', '-t', '-t', str(job)],
                                 input=commands, text=True, stdout=subprocess.PIPE,
                                 stderr=stream, cwd=folder, env=env, timeout=45)
        (out / 'output.txt').write_text(run.stdout)
        trace = (out / 'trace.txt').read_text()
        assert run.returncode == 0, run.stdout
        if args.safe_buffer:
            assert 'АВОСТ' not in run.stdout, run.stdout
        else:
            assert 'АВОСТ 000022' in run.stdout, run.stdout
            assert 'vjm 74022(4)' in trace and 'r[4]=66471' in trace
        assert 'КТЛБД       00001  0353 06096' in run.stdout
        assert 'БД7154      00001  0353 08096' in run.stdout
        for message in ('В КТЛ НЕТ ЗАПИСЕЙ', 'ЭТО ИМЯ УЖЕ ЕСТЬ', 'ТАКОЙ ЗАПИСИ НЕТ'):
            assert message in run.stdout, message
        stores = {}
        for match in re.finditer(r'^ +([0-7]{5}): store ([0-7]{16})', trace, re.M):
            stores.setdefault(int(match[1], 8), []).append(int(match[2], 8))
        assert bandit in stores.get(0o20000, []), 'GET did not copy ALPHA'
        assert bandit in stores.get(0o20100, []), 'duplicate PUT changed ALPHA'
        if args.safe_buffer:
            for i, word in enumerate(pattern):
                assert word in stores.get(0o20200 + i, []), f'long GET word {i:o}'
        disk = (folder / '1234').read_bytes()
        blocks = [[w & MASK for w in struct.unpack('<1024Q', payload(disk, 0o200 + i))]
                  for i in range(4)]
        first = blocks[0]
        directory = first[3] & 0o1777
        count = first[-5]  # N=4: free table at 01774; used count at 01773.
        beta = int.from_bytes(bytes(G.index(c) for c in 'ВЕТА  '), 'big')
        assert count == 2 and first[directory] == beta, 'unexpected surviving directory'
        ref = first[directory + 1]
        descriptor = blocks[ref & 0o1777][ref >> 10 & 0o1777]
        body = descriptor & 0o1777
        assert blocks[ref & 0o1777][body + 1] == bandit, 'BETA lost GET data'
    assert hashes == {v: hashlib.sha256((volumes / v).read_bytes()).hexdigest() for v in hashes}
    report = dict(fixed_record_round_trip=True, duplicate_preserved_original=True,
                  deleted_record_not_found=True,
                  private_buffer_patch='026:0546 33 -> 32' if args.safe_buffer else None,
                  expected_mod_abort=not args.safe_buffer,
                  long_record_words=length if args.safe_buffer else 0,
                  long_record_round_trip=args.safe_buffer, surviving_record='BETA',
                  source_volumes_unchanged=True)
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print('BD/BANDIT: NEW, OPEN, PUT, GET, duplicate rollback, DELETE, metadata; '
          + (f'linked record {length} words, private buffer 32'
             if args.safe_buffer else 'original MOD abort reproduced')
          + '; private disks only')


if __name__ == '__main__':
    main()
