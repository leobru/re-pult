#!/usr/bin/env python3
"""Probe ЧИСТКА's Pascal analysis on temporary disks; preserve all source volumes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
# name: (fixture, terminal parameters)
CASES = {name: (name, '500101 1') for name in (
    'clean', 'declarations', 'global-loop', 'comment', 'bad-comment',
    'bad-header', 'shadow', 'unused-types', 'unused-func', 'recursive',
    'assembly', 'arg-omitted', 'enum', 'local-type')}
CASES.update({'cold-default': ('cold', '500101 1'),
              'cold': ('cold', '500101 1 Х'),
              'cold-one': ('cold', '500101 1 Х1'),
              'exit': (None, ''), 'bad-address': (None, '1 1'),
              'too-long': (None, '500101 100')})


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canon(text):
    # GOST renders the shared Latin letters using Cyrillic glyphs.
    return text.translate(str.maketrans('ABCEHKMOPTXY', 'АВСЕНКМОРТХУ'))


def check(name, output, trace, rebuilt=False):
    assert 'АВОСТ' not in output and 'ВРЕМЯ РЕШ:' in output, output
    assert 'ВЫХОД В ПУЛЬТ' in output, output
    if not rebuilt:
        assert re.search(r'^05122:', trace, re.M), 'main entry was not executed'
    output = canon(output)
    if CASES[name][0]:
        assert '(=0010340000500101)' in trace, 'fixture was not read'
    if name in ('clean', 'comment', 'local-type'):
        if name == 'local-type':
            assert 'НЕИСПОЛЬЗУЕМЫЕ' not in output

        assert 'ПРОГРАММА НАПИСАНА ЧИСТО !' in output and 'ОШИБКА=' not in output
    if name == 'declarations':
        for pattern in (r'МЕТКИ\s+10,20', r'КОНСТАНТЫ\s+DEAD',
                        r'ИДЕНТИФИКАТОРЫ\s+IDLE', r'НЕИСПОЛЬЗУЕМАЯ ПРОЦЕДУРА\s+NEVER'):
            assert re.search(canon(pattern), output), output
        assert 'ТИПЫ' not in output, 'IDLETY is referenced by IDLE in a type declaration'
    if name.startswith('cold'):
        assert re.search(canon(r'НЕИСПОЛЬЗУЕМЫЕ ИДЕНТИФИКАТОРЫ\s+NONE'), output), output
        if name == 'cold-default':
            assert 'ХОЛОСТЫЕ' not in output
        else:
            assert re.search(canon(r'ХОЛОСТЫЕ ИДЕНТИФИКАТОРЫ\s+ONCE\(3\)'), output), output
    if name == 'global-loop':
        # This warning does not clear ЧИСТКА's final "clean" flag.
        assert 'ПЕРЕМЕННАЯ ЦИКЛА ГЛОБАЛЬНАЯ !!' in output
        assert 'ПРОГРАММА НАПИСАНА ЧИСТО !' in output
    if name == 'bad-comment':
        assert 'НЕЗАКРЫТЫЙ КОМ. СТР.= 2' in output
        assert 'ПРОГРАММА НАПИСАНА ЧИСТО' not in output
    if name == 'bad-header':
        assert 'ОШИБКА=2' in output
        if not rebuilt:
            assert re.search(r'^00675:', trace, re.M)
    if name == 'shadow':
        assert re.search(r'В СТРОКЕ\s+2 ОПИСАНЫ НЕИСПОЛЬЗУЕМЫЕ ИДЕНТИФИКАТОРЫ Х', output)
        assert len(re.findall('НЕИСПОЛЬЗУЕМЫЕ ИДЕНТИФИКАТОРЫ', output)) == 1
    if name == 'unused-types':
        assert re.search(r'НЕИСПОЛЬЗУЕМЫЕ\s+ТИПЫ\s+Т2', output)
    if name in ('unused-func', 'recursive'):
        kind = 'ФУНКЦИЯ' if name == 'unused-func' else 'ПРОЦЕДУРА'
        assert re.search(canon(r'НЕИСПОЛЬЗУЕМАЯ\s+' + kind + r'\s+DEAD'), output), output
    if name == 'assembly':
        assert re.search(canon(r'ИДЕНТИФИКАТОРЫ\s+ASMVAR,IDLE'), output), output
        if not rebuilt:
            assert re.search(r'^02310:', trace, re.M), 'CODE parser was not entered'
    if name == 'enum':
        assert re.search(canon(r'В ТИПАХ НЕ ИСПОЛЬЗУЮТСЯ ИДЕНТИФИКАТОРЫ\s+GREEN,BLUE'), output), output
    if name == 'arg-omitted':
        assert re.search(r'ИДЕНТИФИКАТОРЫ\s+А', output), output
    if name == 'bad-address':
        assert 'НЕ БУДУ.' in output and '(=0010340000500101)' not in trace
    if name == 'too-long':
        assert 'ВЕЛИК МАССИВ' in output and '(=0010340000500101)' not in trace


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dispak', default='dispak')
    parser.add_argument('--image', type=Path, help='test a rebuilt Pascal image on private 2068')
    parser.add_argument('--case', action='append', choices=sorted(CASES))
    args = parser.parse_args()
    app = shutil.which(args.dispak)
    if not app:
        parser.error('dispak executable not found')
    volumes = ROOT / 'build/volumes'
    hashes = {v: sha(volumes / v) for v in ('2148', '2248', '2068')}
    helper = runpy.run_path(str(ROOT / 'tests/pascal-segments.py'))
    out = ROOT / ('build/chistka-rebuilt-check' if args.image else 'build/chistka-check')
    out.mkdir(parents=True, exist_ok=True)
    reports, outputs = {}, {}
    for name, (fixture, params) in CASES.items():
        if args.case and name not in args.case:
            continue
        with tempfile.TemporaryDirectory(prefix='pult-chistka-') as directory:
            private = Path(directory)
            for v in ('2248', '2068'):
                shutil.copyfile(volumes / v, private / v)
            if args.image:
                runpy.run_path(str(ROOT / 'tests/rebuild-analyzers.py'))['install_image'](
                    private / '2068', 0o60, 3, args.image.read_bytes())
            archive = private / '2345'
            archive.write_bytes(bytes((0o120 + 4) * 8256))
            if fixture:
                source = (ROOT / 'tests/chistka' / (fixture + '.pas')).read_text()
                helper['write_words'](archive, 0o101, helper['gost_source'](source))
            archive_hash = sha(archive)
            job = private / 'job.b6'
            job.write_text((ROOT / 'pult2068.b6').read_text().replace(
                'лент 30(1С)^', 'лент 30(1С)^\nлент 50(2345-зп)^'))
            commands = 'чистка\n' + params + '\n' + ('\n' if params else '') + 'конец\n'
            (out / (name + '.input')).write_text(commands)
            env = dict(os.environ, DISPAK=app)
            env.pop('BESM6_PATH', None)
            env.pop('BESM6_SMALL_DISKS', None)
            result = subprocess.run(
                [str(ROOT / 'tools/run-dispak.sh'), '--725',
                 '--path=' + directory + ':/usr/local/share/besm6',
                 '-q', '-t', '-t', str(job)], input=commands, text=True,
                capture_output=True, cwd=private, env=env, timeout=15)
            (out / (name + '.out')).write_text(result.stdout)
            (out / (name + '.trace')).write_text(result.stderr)
            assert result.returncode == 0, (name, result.returncode, result.stdout)
            check(name, result.stdout, result.stderr, bool(args.image))
            assert sha(archive) == archive_hash, 'ЧИСТКА wrote to its input volume'
            outputs[name] = result.stdout
            reports[name] = dict(status='passed', source_unchanged=True)
            print(name + ': OK', flush=True)
    if 'cold' in outputs and 'cold-one' in outputs:
        # DISPAK's elapsed-time footer varies between otherwise identical runs.
        without_time = lambda text: re.sub(r'(?m)^.*ВРЕМЯ РЕШ:.*$', '', text)
        assert without_time(outputs['cold']) == without_time(outputs['cold-one']), 'Х and Х1 output differs'
    assert all(sha(volumes / v) == h for v, h in hashes.items()), 'source volume changed'
    (out / 'results.json').write_text(json.dumps(reports, ensure_ascii=False, indent=2) + '\n')
    print('Source volumes unchanged; logs: ' + str(out))


if __name__ == '__main__':
    main()
