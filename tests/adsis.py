#!/usr/bin/env python3
"""Exercise the unmodified АДСИС library through compiled Pascal programs.

All emulator sessions are serial and use private volumes and HOME. The source
encoder and physical-volume writer are shared with the segmentation test.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import runpy
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dispak', default='dispak')
    parser.add_argument('--volumes', type=Path, default=ROOT / 'build/volumes')
    parser.add_argument('--output', type=Path, default=ROOT / 'build/adsis-probes')
    parser.add_argument('--case', action='append', choices=('runtime','bounds','file-error','heap-error','files','terminal','real-compare','integer-print','real-print'))
    args = parser.parse_args()
    app = Path(shutil.which(args.dispak) or args.dispak).resolve()
    directory, output = args.volumes.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    spec = importlib.util.spec_from_file_location('segments', ROOT / 'tests/pascal-segments.py')
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    hashes = {v: hashlib.sha256((directory / v).read_bytes()).digest()
              for v in ('2148', '2248', '2068')}
    adsis = (ROOT / 'images/2248/АДСИС.bin').read_bytes()
    for volume, zone in (('2148',0o1006),('2248',0o1006),('2068',0o6)):
        data = b''.join(w.to_bytes(6,'big') for w in helper.raw_words((directory / volume).read_bytes(),zone))
        assert data == adsis, 'probe runtime differs from the disassembled АДСИС'

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
                 ':/usr/local/share/besm6', '-p' if name in ('integer-print','real-print') else '-q',
                 '-t', '-t', str(job)],
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
            'heap-error': ['БОЛЬШОЙ NIL', 'ПОСЛЕ NIL', 'ВОССТАНОВЛЕНО 42', 'ВСЕ СДЕЛАНО.'],
            'files': ['ЗАПИСИ 562600', 'УПАКОВКА 3605', 'ФАЙЛЫ ПРОШЛИ', 'ВСЕ СДЕЛАНО.'],
            'terminal': ['ВВОД>', 'ОТВЕТ А', 'ВСЕ СДЕЛАНО.'],
            'real-compare': ['СРАВНЕНИЯ ПРОШЛИ', 'ВСЕ СДЕЛАНО.'],
            'integer-print': ['ЦЕЛЫЕ ПРОВЕРЕНЫ', 'ВСЕ СДЕЛАНО.'],
            'real-print': ['ВЕЩЕСТВЕННЫЕ ПРОВЕРЕНЫ', 'ВСЕ СДЕЛАНО.'],
        }
        for name, expected in cases.items():
            if args.case and name not in args.case:
                continue
            source = (ROOT / 'tests/adsis' / (name + '.pas')).read_text()
            helper.write_words(archive, 0o101, helper.gost_source(source))
            command = 'пас тест - па' if name in ('integer-print','real-print') else 'пас тест'
            result = session(name, 'арх вася,50,100\n'+command+'\n'+('А\n' if name=='terminal' else '')+'конец\n', expected)
            assert 'ПРОПУЩЕН КОНТРОЛЬ' not in result.stdout, result.stdout
            assert 'ОШИБКА АДСИС' not in result.stdout, result.stdout
            if name in ('heap-error', 'files', 'real-compare'):
                assert 'ОШИБКА' not in result.stdout, result.stdout
            # An opcode record is execution; an indented "store" record is not.
            executed = {int(m[1], 8) for m in re.finditer(
                r'^([0-7]{5})[:;] (?!store )', result.stderr, re.MULTILINE)}
            required = {
                'runtime': (0o74206, 0o74337, 0o74362, 0o74554,
                            0o74715, 0o74760, 0o75104, 0o75115,
                            0o75361, 0o75363, 0o75442, 0o75474,
                            0o75730, 0o75737),
                'bounds': (0o75241,),
                'file-error': (0o74323, 0o74757),
                'heap-error': (0o74206, 0o74213, 0o75075),
                'files': (0o74441, 0o74445, 0o74525, 0o74715, 0o74760, 0o75045, 0o75060),
                'terminal': (0o75675, 0o75711, 0o74242),
                'real-compare': (0o75650,0o75654,0o75664,0o75670),
                'integer-print': (0o74075,0o74104,0o75425,0o75442,0o75453),
                'real-print': (0o74076,0o74105,0o75474,0o75541,0o75545,0o75604),
            }
            assert set(required[name]) <= executed, (name, set(required[name]) - executed)
            if name == 'real-print':
                report = runpy.run_path(str(ROOT / 'tests/adsis-real-output.py'))['audit'](output)
                print(f"REAL: {report['conversions']} conversions; OUTPUT/TEXT identical; "
                      f"known defects: {report['lost_nonzero_conversions']} conversions lost nonzero inputs, "
                      f"zero exponent +17, {report['padding_mismatches']} oversized fields", flush=True)
            if name == 'integer-print':
                numbers = [0]
                for power in range(13):
                    for offset in (-1, 0, 1):
                        n = 10 ** power + offset
                        numbers.extend((n, -n))
                for power in range(1, 40):
                    n = 2 ** power
                    numbers.extend((n-1, -n, -n+1, n, n+1))
                numbers.extend((2**40-1, -2**40, -2**40+1))
                rows = ['[' + ']['.join(str(n).rjust(w) for w in (0,5,16,10)) + ']'
                        for n in numbers]
                # The second copy was written to TEXT, reset, and read back
                # character by character. Ignore printer page headers only.
                actual = [line for line in result.stdout.splitlines() if line.startswith('[')]
                assert len(actual) == 2 * len(rows), (len(actual), 2 * len(rows))
                mismatches = []
                for index, (got, wanted) in enumerate(zip(actual, rows + rows)):
                    n = numbers[index % len(numbers)]
                    if got != wanted:
                        mismatches.append(dict(channel='OUTPUT' if index < len(rows) else 'TEXT',
                                               value=n, expected=wanted, actual=got))
                        # Preserve the observed historical lower-bound defect;
                        # every other row must match the independent oracle.
                        known = '[' + ']['.join(str(-1099511627773).rjust(w)
                                               for w in (0,5,16,10)) + ']'
                        assert n == -2**40 and got == known, (index, n, got, wanted)
                assert len(mismatches) == 2, mismatches
                (output / 'integer-print.json').write_text(json.dumps(dict(
                    values=len(rows), widths=[0,5,16,10],
                    conversions=len(rows)*8, mismatches=mismatches),
                    ensure_ascii=False,indent=2)+'\n')
                print(f'INTEGER: {len(rows)} values × 4 widths × OUTPUT/TEXT; '
                      'known defect: -1099511627776 prints as -1099511627773', flush=True)
            if name in ('bounds', 'file-error'):
                assert 'ВСЕ СДЕЛАНО.' not in result.stdout, result.stdout

        result = session('statis', 'статис\nконец\n', ['QU'])
        assert '67217: vtm 67221' in result.stderr, 'QU must come from БАВТ'
        assert not re.search(r'^7[45][0-7]{3}:', result.stderr, re.MULTILINE), \
            'no АДСИС instruction should execute for СТАТИС without an argument'

    for v, digest in hashes.items():
        assert hashlib.sha256((directory / v).read_bytes()).digest() == digest
    report = runpy.run_path(str(ROOT / 'tests/adsis-layout.py'))['audit'](output)
    report['source_volumes_sha256'] = {v:d.hex() for v,d in hashes.items()}
    report['source_volumes_unchanged'] = True
    report['current_cases'] = args.case or list(cases)
    (output / 'coverage.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Source volumes unchanged; АДСИС payload unmodified')


if __name__ == '__main__':
    main()
