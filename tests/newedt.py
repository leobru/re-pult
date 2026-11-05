#!/usr/bin/env python3
"""Compare original and rebuilt НОВРЕД while editing a private archive file."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dispak', default=os.environ.get('DISPAK', 'dispak'))
    args = parser.parse_args()
    helper = runpy.run_path(str(ROOT / 'tests/pascal-segments.py'))
    common = runpy.run_path(str(ROOT / 'tests/rebuild-analyzers.py'))
    images = ROOT / 'build/pasauto-imports/may/newedt-working'
    out = ROOT / 'build/newedt-runtime'
    out.mkdir(parents=True, exist_ok=True)
    volumes = {v: (ROOT / 'build/volumes' / v).read_bytes() for v in ('2068', '2248')}
    commands = (ROOT / 'tests/newedt/edit.txt').read_text()
    word = lambda s: int.from_bytes(bytes(common['G'].index(c) for c in s.ljust(6)), 'big')
    outputs, results = [], []
    with tempfile.TemporaryDirectory(prefix='pult-newedt-', dir=out) as temporary:
        folder = Path(temporary)
        for label in ('original', 'generated'):
            for v, data in volumes.items():
                (folder / v).write_bytes(data)
            common['install_image'](folder / '2068', 0o75, 3,
                                    (images / (label + '.bin')).read_bytes())
            archive = folder / '2345'
            archive.write_bytes(bytes((0o400 + 4) * common['ZONE']))
            catalog = [0] * 1024
            catalog[:3] = [word('ВАСЯ'), word('ТЕКСТ'), (1 << 24) | 1]
            catalog[0o377] = 3
            helper['write_words'](archive, 0o100, catalog)
            helper['write_words'](archive, 0o101,
                                  helper['gost_source']('ПЕРВАЯ СТРОКА\nВТОРАЯ СТРОКА\n'))
            job = folder / 'job.b6'
            job.write_text((ROOT / 'pult2068.b6').read_text().replace(
                'лент 30(1С)^', 'лент 30(1С)^\nлент 50(2345-ЗП)^'))
            home = folder / label
            home.mkdir()
            env = dict(os.environ, HOME=str(home))
            env.pop('BESM6_PATH', None)
            env.pop('BESM6_SMALL_DISKS', None)
            run = subprocess.run([args.dispak, '--725', '--path=' + str(folder) +
                                  ':/usr/local/share/besm6', '-q', str(job)],
                                 input=commands, text=True, capture_output=True,
                                 cwd=folder, env=env, timeout=20)
            (out / (label + '.out')).write_text(run.stdout)
            (out / (label + '.stderr')).write_text(run.stderr)
            assert run.returncode == 0 and 'АВОСТ' not in run.stdout, run.stdout
            for text in ('0001 ПЕРВАЯ СТРОКА', '0002 ВТОРАЯ СТРОКА',
                         '0001 ВТОРАЯ СТРОКА', 'ДЛИНА ТЕКСТА:',
                         'В ФАЙЛ ТЕКСТ  ЗАПИСАНО ЗОН: 1'):
                assert text in run.stdout, text
            result = common['raw_zones'](archive.read_bytes(), 0o101, 1)
            expected = helper['gost_source']('ВТОРАЯ СТРОКА\n')
            expected = b''.join(w.to_bytes(6, 'big') for w in expected)
            assert result.startswith(expected.rstrip(b'\0')), 'wrong saved text'
            (out / (label + '.archive.bin')).write_bytes(result)
            outputs.append(run.stdout.split('ВРЕМЯ РЕШ:', 1)[0])
            results.append(result)
    assert outputs[0] == outputs[1] and results[0] == results[1]
    assert all((ROOT / 'build/volumes' / v).read_bytes() == b for v, b in volumes.items())
    report = dict(terminal_output_equal=True, saved_zone_equal=True,
                  saved_zone_sha256=hashlib.sha256(results[0]).hexdigest(),
                  cases=['read', 'display', 'delete-first-line', 'length', 'save', 'exit'],
                  source_volumes_unchanged=True)
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print('НОВРЕД: original/rebuilt output and saved zone match; six operations; private volumes')


if __name__ == '__main__':
    main()
