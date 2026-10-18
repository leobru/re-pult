#!/usr/bin/env python3
"""Exercise the unmodified АДСИС library through compiled Pascal programs.

All emulator sessions are serial and use private volumes and HOME. The source
encoder and physical-volume writer are shared with the segmentation test.
"""
import argparse
import hashlib
import importlib.util
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dispak', default='dispak')
    parser.add_argument('--volumes', type=Path, default=ROOT / 'build/volumes')
    parser.add_argument('--output', type=Path, default=ROOT / 'build/adsis-probes')
    args = parser.parse_args()
    app = Path(shutil.which(args.dispak) or args.dispak).resolve()
    directory, output = args.volumes.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    spec = importlib.util.spec_from_file_location('segments', ROOT / 'tests/pascal-segments.py')
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    hashes = {v: hashlib.sha256((directory / v).read_bytes()).digest()
              for v in ('2148', '2248', '2068')}

    with tempfile.TemporaryDirectory(prefix='pult-adsis-') as temporary:
        temporary = Path(temporary)
        for v in hashes:
            shutil.copyfile(directory / v, temporary / v)
        archive = temporary / '2345'
        archive.write_bytes(bytes((0o600 + 4) * helper.ZONE))
        deck = (ROOT / 'pult2068.b6').read_text().replace(
            'лент 30(1С)^', 'лент 30(1С)^\nлент 50(2345-зп)^')
        job = temporary / 'job.b6'
        job.write_text(deck)
        (output / 'job.b6').write_text(deck)
        env = dict(os.environ, HOME=str(temporary))
        env.pop('BESM6_PATH', None)
        env.pop('BESM6_SMALL_DISKS', None)

        def session(name, commands, expected):
            (output / (name + '.input')).write_text(commands)
            result = subprocess.run(
                [str(app), '--725', '--path=' + str(temporary) +
                 ':/usr/local/share/besm6', '-q', '-t', '-t', str(job)],
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

        session('archive', 'дай новарх 50 100 вася\nарх вася,50,100,400\n'
                'з тест(30)\nконец\n', ['МСВ   ТЕСТ'])
        cases = {
            'runtime': ['АРИФМЕТИКА 7 2', 'ПЕРЕКОДИРОВКА 012345 152',
                        'МНОЖЕСТВА 4 3', 'ФАЙЛ 530965', 'ТЕКСТ 123 45',
                        'АДСИС ПРОШЛА', 'ВСЕ СДЕЛАНО.'],
            'bounds': ['ГР ИНД.СТР= 00005'],
            'file-error': ['ОШ.АДСИС=03'],
        }
        for name, expected in cases.items():
            source = (ROOT / 'tests/adsis' / (name + '.pas')).read_text()
            helper.write_words(archive, 0o101, helper.gost_source(source))
            result = session(name, 'арх вася,50,100\nпас тест\nконец\n', expected)
            assert 'ПРОПУЩЕН КОНТРОЛЬ' not in result.stdout, result.stdout
            assert 'ОШИБКА АДСИС' not in result.stdout, result.stdout
            # An opcode record is execution; an indented "store" record is not.
            executed = {int(m[1], 8) for m in re.finditer(
                r'^([0-7]{5}): (?!store )', result.stderr, re.MULTILINE)}
            required = {
                'runtime': (0o74206, 0o74337, 0o74362, 0o74554,
                            0o74715, 0o74760, 0o75104, 0o75115,
                            0o75361, 0o75363, 0o75442, 0o75474,
                            0o75730, 0o75737),
                'bounds': (0o75241,),
                'file-error': (0o74323, 0o74757),
            }
            assert set(required[name]) <= executed, (name, set(required[name]) - executed)
            if name != 'runtime':
                assert 'ВСЕ СДЕЛАНО.' not in result.stdout, result.stdout

        result = session('statis', 'статис\nконец\n', ['QU'])
        assert '67217: vtm 67221' in result.stderr, 'QU must come from БАВТ'
        assert not re.search(r'^7[45][0-7]{3}:', result.stderr, re.MULTILINE), \
            'no АДСИС instruction should execute for СТАТИС without an argument'

    for v, digest in hashes.items():
        assert hashlib.sha256((directory / v).read_bytes()).digest() == digest
    print('Source volumes unchanged; АДСИС payload unmodified')


if __name__ == '__main__':
    main()
