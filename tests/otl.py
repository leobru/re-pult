#!/usr/bin/env python3
"""Exercise ОТЛ on isolated disks and check executed code and memory writes."""
import argparse
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PROGRAM = 'в 600в 123,0,456,0\nв 10000к 100600=601,100602=603\n'
CASES = {
    'memory': "о\nвв 10000в 1,2,3,0,17\nвыв 10000:10004в\n"
              "в 10100с 'ПРИВЕТ'\nп 10100с\nп 10000:10001к\nвых",
    'relocated': 'о 40000\nв 10000в 123\nп 10000в\nвых',
    'symbols': "о\nв 600в 123,0,456,0\nимя а=600:603\nадр\n"
               "п а'в\nп а(2)'в\nвых",
    'execute': 'о\n' + PROGRAM + "исп 10000:10002\nп 601в\nп 603в\nп см'в\nвых",
    'interpret': 'о\n' + PROGRAM + "инт 10000:10002\nп 601в\nп 603в\nвых",
    'watch-write': 'о\n' + PROGRAM + "инт 10000'з 601\nп 601в\nп 603в\nвых",
    'commands': "о\nв 600в 123,0\nком 100600=601\nп 601в\nкс",
    'transitions': 'о\nв 600в 123,0\n'
                   'в 10000к 3010002=2200000,100600=601,100600=601\n'
                   "ш 10000:10003'т\nп 601в\nвых",
    # Preserve the actual behavior of this image: +1 finishes a whole word.
    'count-one': 'о\n' + PROGRAM + "инт 10000 +1\nп 601в\nп 603в\nвых",
    'name-mismatch': 'отл\nо\nвых',
}


def check(name, output, trace):
    output = output.replace('\x1b[D', '\n')
    assert 'АВОСТ' not in output and 'ВРЕМЯ РЕШ:' in output, (name, output)
    if name == 'memory':
        assert 'ПРИВЕТ' in output and '00 000 0000 00 000 0001' in output
        values = re.findall(r'^\s+([0-7]+)\s*$', output, re.M)
        assert values[:5] == ['1', '2', '3', '0', '17'], values
    if name == 'relocated':
        assert re.search(r'^40010:', trace, re.M)
        assert '(=0010200000400052)' in trace
        assert '(=0010210000400053)' in trace
        assert '(=0010220000400054)' in trace
    if name == 'symbols':
        assert re.search(r'А\s+=\s+600\s+:\s+603', output)
        assert re.search(r'^\s+123\s*$', output, re.M)
        assert re.search(r'^\s+456\s*$', output, re.M)
    if name in ('execute', 'interpret', 'watch-write', 'commands', 'transitions', 'count-one'):
        assert '00601: store 0000000000000123' in trace, name
    if name in ('execute', 'interpret'):
        assert '00603: store 0000000000000456' in trace, name
    if name in ('watch-write', 'count-one'):
        assert '00603: store 0000000000000456' not in trace, name
    if name == 'execute':
        assert re.search(r'^54372: \*67 6', trace, re.M)
        assert re.search(r'^10000: xta 600', trace, re.M)
    if name in ('interpret', 'watch-write', 'count-one', 'transitions'):
        assert re.search(r'^54547: xta 600', trace, re.M)
        assert not re.search(r'^10000:', trace, re.M)
    if name == 'commands':
        assert re.search(r'^00001: xta 600', trace, re.M)
    if name == 'transitions':
        assert re.search(r'10000\s+10002\s+1', output)
    if name == 'name-mismatch':
        assert 'СТОИТ' in output and re.search(r'^50010:', trace, re.M)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dispak', default='dispak')
    parser.add_argument('--case', action='append', choices=sorted(CASES))
    args = parser.parse_args()
    app = shutil.which(args.dispak)
    if not app:
        parser.error('dispak executable not found')
    volumes = ROOT / 'build/volumes'
    hashes = {v: hashlib.sha256((volumes / v).read_bytes()).digest()
              for v in ('2248', '2068')}
    out = ROOT / 'build/otl-check'
    out.mkdir(parents=True, exist_ok=True)
    for name, commands in CASES.items():
        if args.case and name not in args.case:
            continue
        with tempfile.TemporaryDirectory(prefix='pult-otl-') as directory:
            private = Path(directory)
            for volume in hashes:
                shutil.copyfile(volumes / volume, private / volume)
            job = private / 'job.b6'
            job.write_text((ROOT / 'pult2068.b6').read_text())
            commands += '\nконец\n'
            (out / f'{name}.input').write_text(commands)
            env = dict(os.environ, HOME=directory)
            env['DISPAK'] = app
            env.pop('BESM6_PATH', None)
            env.pop('BESM6_SMALL_DISKS', None)
            with (out / f'{name}.out').open('w') as stdout, (out / f'{name}.trace').open('w') as stderr:
                result = subprocess.run(
                    [str(ROOT / 'tools/run-dispak.sh'), '--725', '--path=' + directory + ':/usr/local/share/besm6',
                     '-q', '-t', '-t', str(job)], input=commands, text=True,
                    stdout=stdout, stderr=stderr, cwd=private, env=env, timeout=15)
            output = (out / f'{name}.out').read_text()
            trace = (out / f'{name}.trace').read_text()
            assert result.returncode == 0, (name, result.returncode, output)
            check(name, output, trace)
            print(name + ': OK', flush=True)
    assert all(hashlib.sha256((volumes / v).read_bytes()).digest() == h
               for v, h in hashes.items()), 'source volumes changed'
    print('Source volumes unchanged; logs: ' + str(out))


if __name__ == '__main__':
    main()
