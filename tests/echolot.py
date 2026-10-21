#!/usr/bin/env python3
"""Exercise ЭХОЛОТ's storage estimates, options and compiled-code matching."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from gost import G
from make2068 import ZONE, payload, control_words

CASES = {
    'nested': ('nested', ''), 'summary': ('nested', 'И'),
    'table': ('nested', 'Т'), 'names': ('nested', 'С'),
    'all': ('nested', 'Т С'), 'siblings': ('siblings', 'Т С'),
    'recursive': ('recursive', 'Т С'), 'new': ('new', ''),
    'new-proc': ('new-proc', ''), 'new-k2': ('new-k2', ''),
    'packed': ('packed', ''), 'help': (None, 'И'),
    'bad-address': (None, '1 1'), 'too-long': (None, '500101 100'),
    'exit': (None, ''), 'code': ('nested', 'Т С'),
    'wrong-code': ('nested', ''),
    'code-frames': ('frames', 'Т С'),
    'calls-slices': ('calls-slices', 'Т С'),
    'body': ('body', 'Т С'),
    'groups': ('groups', 'Т С'),
    'const-block': ('const-block', ''),
    'forward': ('forward', 'Т С'),
    'type-forward': ('type-forward', ''),
    'scopes': ('scopes', 'Т С'),
    'labels': ('labels', ''),
    'label-number': ('label-number', ''),
    'label-delimiter': ('label-delimiter', ''),
    'label-comma': ('label-comma', ''),
    'label-token': ('label-token', ''),
    'block-token': ('block-token', ''),
    'header': ('header', 'Т С'),
    'header-mode': ('header-mode', 'Т С'),
    'scanner': ('scanner', 'Т С'),
    'scanner-lines': ('scanner-lines', 'Т С'),
    'scanner-error': ('scanner-error', ''),
    'request-options': ('nested', 'Т,С'),
    'missing-length': (None, '500101'),
    'retry-limit': (None, '1 1'),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canon(text):
    return text.translate(str.maketrans('ABCEHKMOPTXY', 'АВСЕНКМОРТХУ'))


def check_labels(trace, start=0o6137):
    """Validate all six fields and the reverse link order at the recovered sites."""
    def site(original):
        return f'{start + original - 0o6137:05o}'

    assert len(re.findall('^' + site(0o6203) + r': vtm 6\(12\)', trace, re.M)) == 2
    assert len(re.findall('^' + site(0o6203) + r': vjm 74025\(16\)', trace, re.M)) == 2
    fields = {}
    for offset, address in ((0, 0o6205), (2, 0o6206), (3, 0o6210),
                            (1, 0o6211), (5, 0o6213), (4, 0o6214)):
        rows = re.findall('^' + site(address) + r': atx ([0-7]+) +.*acc=([0-7]{16})',
                          trace, re.M)
        assert len(rows) == 2, (offset, rows)
        fields[offset] = [(int(a, 8), int(v, 8)) for a, v in rows]
    bases = [a for a, _ in fields[0]]
    for index, base in enumerate(bases):
        expected = [10 if index == 0 else 20, 0, 1, 0,
                    0o64000 if index == 0 else bases[0], 0]
        for offset, value in enumerate(expected):
            assert fields[offset][index] == (base + offset, value), fields
    return dict(status='passed', nodes=2, words_per_node=6,
                values=[10, 20], level=1, reverse_links=True)


def check(name, output, trace, rebuilt=False):
    assert 'АВОСТ' not in output and 'ВРЕМЯ РЕШ:' in output, output
    if not rebuilt:
        assert re.search(r'^07542:', trace, re.M), 'main entry was not executed'
        for line in re.findall(r'^06145: aax 13\(10\).*$', trace, re.M):
            assert 'r[10]=00000' in line, 'original analyze entry uses a nonzero literal base'
    output = canon(output)

    def has(pattern):
        assert re.search(canon(pattern), output), output

    if CASES[name][0]:
        assert '(=0010340000500101)' in trace, 'fixture was not read'
    if name in ('nested', 'summary', 'table', 'names', 'all', 'code', 'request-options', 'header', 'header-mode'):
        has(r'ГЛОБ.ПЕРЕМ=\s+24\s+ПРОЦЕДУРЫ=\s+15')
        has(r'СУММА=\s+41')
        if name == 'summary':
            assert 'ЛОК=' not in output
        else:
            has(r'LEAF\s+ЛОК=\s+11\s+ВХОД=\s+0\s+СУМ=\s+11')
            has(r'TOP\s+ЛОК=\s+4\s+ВХОД=\s+11\s+СУМ=\s+15')
        if name in ('table', 'all', 'code', 'request-options', 'header', 'header-mode'):
            has(r'ПРОЦЕДУРА\s+TOP\s+МАХ=\s+15')
        else:
            assert 'МАХ=' not in output
        if name in ('names', 'all', 'code', 'request-options', 'header', 'header-mode'):
            has(r'TOP[^\n]*СУМ=\s+15[^\n]*LEAF')
    if name == 'calls-slices':
        has(r'ГЛОБ.ПЕРЕМ=\s+12\s+ПРОЦЕДУРЫ=\s+11')
        has(r'СУММА=\s+23')
        has(r'LEFT[^\n]*СУМ=\s+6\s+LEAF\s*\n')
        has(r'RIGHT[^\n]*СУМ=\s+11\s+LEAF\s+LEFT\s*\n')
        assert len(re.findall(canon(r'ПРОЦЕДУРА\s+LEFT\s+МАХ=\s+6'), output)) == 2, output
        assert len(re.findall(canon(r'ПРОЦЕДУРА\s+RIGHT\s+МАХ=\s+11'), output)) == 1, output
    if name == 'body':
        has(r'WALK[^\n]*ЛОК=\s+3\s+ВХОД=\s+3\s+СУМ=\s+6\s+LEAF\s*\n')
        has(r'ГЛОБ.ПЕРЕМ=\s+12\s+ПРОЦЕДУРЫ=\s+6')
        has(r'СУММА=\s+20')
    if name == 'groups':
        has(r'P[^\n]*ЛОК=\s+14\s+ВХОД=\s+0\s+СУМ=\s+14')
        has(r'ГЛОБ.ПЕРЕМ=\s+17\s+ПРОЦЕДУРЫ=\s+14')
        has(r'СУММА=\s+33')
    if name == 'const-block':
        has(r'ГЛОБ.ПЕРЕМ=\s+36\s+ПРОЦЕДУРЫ=\s+0')
        has(r'СУММА=\s+36')
    if name == 'forward':
        has(r'ПРОЦ.\s+P\s+ИМЕЕТ ТОЛЬКО FORWARD')
        has(r'Q[^\n]*ЛОК=\s+3[^\n]*СУМ=\s+3\s+P')
        has(r'P[^\n]*ЛОК=\s+4[^\n]*СУМ=\s+4')
        has(r'СУММА=\s+15')
    if name == 'type-forward':
        has(r'ГЛОБ.ПЕРЕМ=\s+13\s+ПРОЦЕДУРЫ=\s+0')
        has(r'СУММА=\s+13')
    if name == 'scopes':
        has(r'LEAF[^\n]*ЛОК=\s+10[^\n]*СУМ=\s+10')
        has(r'FIRST[^\n]*ЛОК=\s+3[^\n]*СУМ=\s+13')
        has(r'SECOND[^\n]*ЛОК=\s+5[^\n]*СУМ=\s+5')
        has(r'ГЛОБ.ПЕРЕМ=\s+12\s+ПРОЦЕДУРЫ=\s+13')
        has(r'СУММА=\s+25')
    if name == 'labels':
        if not rebuilt:
            check_labels(trace)
        has(r'ГЛОБ.ПЕРЕМ=\s+13\s+ПРОЦЕДУРЫ=\s+0')
        has(r'СУММА=\s+13')
    if name in ('label-number', 'label-delimiter', 'label-comma', 'label-token'):
        error = {'label-number': 24, 'label-delimiter': 25,
                 'label-comma': 24, 'label-token': 1}[name]
        line = 3 if name == 'label-token' else 2
        has(r'ЕRRОR =\s+' + str(error) + r'\s+NL=\s+' + str(line))
        assert 'СУММА=' not in output
    if name == 'block-token':
        has(r'ЕRRОR =\s+1\s+NL=\s+2')
        assert 'СУММА=' not in output
    if name == 'siblings':
        has(r'DEAD\s+ЛОК=\s+147')
        has(r'ГЛОБ.ПЕРЕМ=\s+12\s+ПРОЦЕДУРЫ=\s+27')
        has(r'СУММА=\s+41')
        assert not re.search(canon(r'ПРОЦЕДУРА\s+DEAD'), output)
    if name == 'recursive':
        has(r'РЕКУРСИЯ -\s+AGAIN\s+СТР\.\s*=\s*4')
        has(r'ЛОК=\s+11\s+ВХОД=\s+11\s+СУМ=\s+22\s+AGAIN')
        has(r'СУММА=\s+34')
    if name == 'new':
        has(r'ГЛОБ.ПЕРЕМ=\s+13\s+ПРОЦЕДУРЫ=\s+0')
        has(r'СУММА=\s+13')
        assert canon('NEW=') not in output
    if name in ('new-proc', 'new-k2'):
        has(r'ПРОЦЕДУРЫ=\s+3')
        has(r'NEW=\s*' + ('10000' if name == 'new-proc' else '4000'))
        has(r'СУММА=\s*' + ('10016' if name == 'new-proc' else '4016'))
    if name == 'packed':
        has(r'ГЛОБ.ПЕРЕМ=\s+37')
        has(r'СУММА=\s+37')
    if name in ('scanner', 'scanner-lines'):
        has(r'P\s+ЛОК=\s+3\s+ВХОД=\s+0\s+СУМ=\s+3')
        has(r'ГЛОБ.ПЕРЕМ=\s+' + ('24' if name == 'scanner' else '13') + r'\s+ПРОЦЕДУРЫ=\s+3')
        has(r'СУММА=\s+' + ('27' if name == 'scanner' else '16'))
        assert 'ЕRRОR' not in output and 'ОШ.АДСИС' not in output, output
    if name == 'scanner-error':
        has(r'ЕRRОR =\s+2\s+NL=\s+2')
        has(r'NАМЕ=WRIТЕL\s+СLАSS=\s+РRОС\s+С=\(\s+VSСТ=\s+АL\s+ЯП=WRIТЕL')
        assert 'СУММА=' not in output
    if name == 'help':
        for text in ('ФОРМА ОБРАЩЕНИЯ:', 'ТОЛЬКО ИТОГОВЫЕ ДАННЫЕ',
                     'ТАБЛИЦА ПРОЦЕДУР ТЕЛА ПРОГРАММЫ'):
            assert text in output
    if name == 'bad-address':
        assert 'НЕ БУДУ.' in output
    if name == 'missing-length':
        assert 'ПОВТОРИТЕ' in output
    if name == 'retry-limit':
        assert output.count('НЕ БУДУ.') == 7, output
        assert output.count('ДЛЯ ВЫХОДА СДЕЛАЙТЕ') == 1, output
    if name == 'too-long':
        assert 'ВЕЛИК МАССИВ' in output
    if name == 'code':
        has(r'LEAF[^\n]*КОД=00047:0015')
        has(r'TOP[^\n]*КОД=00064:0007')
        has(r'ПРОЦЕДУРЫ=\s+15\s+КОД=\s*112')
        has(r'СУММА=\s+41\s+153')
    if name == 'code-frames':
        has(r'INNER[^\n]*ЛОК=\s+6[^\n]*КОД=00053:0014')
        has(r'OUTER[^\n]*ЛОК=\s+7[^\n]*ВХОД=\s+6[^\n]*КОД=00067:0014')
        has(r'ГЛОБ.ПЕРЕМ=\s+13\s+ПРОЦЕДУРЫ=\s+15\s+КОД=\s+131')
        has(r'СУММА=\s+30\s+161')
        if not rebuilt:
            assert re.search(r'^01132:', trace, re.M), 'inline prologue was not recognized'
    if name == 'wrong-code':
        has('НЕ ТЕ КОДЫ !')
        assert 'СУММА=' not in output
    assert 'ВЫХОД В ПУЛЬТ' in output


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
    out = ROOT / ('build/echolot-rebuilt-check' if args.image else 'build/echolot-check')
    out.mkdir(parents=True, exist_ok=True)
    reports = {}
    for name, (fixture, flags) in CASES.items():
        if args.case and name not in args.case:
            continue
        with tempfile.TemporaryDirectory(prefix='pult-echolot-') as directory:
            private = Path(directory)
            for v in ('2248', '2068'):
                shutil.copyfile(volumes / v, private / v)
            if args.image:
                runpy.run_path(str(ROOT / 'tests/rebuild-analyzers.py'))['install_image'](
                    private / '2068', 0o64, 4, args.image.read_bytes())
            archive = private / '2345'
            archive.write_bytes(bytes((0o400 + 4) * ZONE))
            if fixture:
                source = (ROOT / 'tests/echolot' / (fixture + '.pas')).read_text()
                helper['write_words'](archive, 0o101, helper['gost_source'](source))
            job = private / 'job.b6'
            job.write_text((ROOT / 'pult2068.b6').read_text().replace(
                'лент 30(1С)^', 'лент 30(1С)^\nлент 50(2345-зп)^'))
            env = dict(os.environ, DISPAK=app)
            env.pop('BESM6_PATH', None)
            env.pop('BESM6_SMALL_DISKS', None)

            def run(label, commands, compile=False):
                result = subprocess.run(
                    [str(ROOT / 'tools/run-dispak.sh'), '--725',
                     '--path=' + directory + ':/usr/local/share/besm6',
                     *(['-p', '-t'] if compile else ['-q', '-t', '-t']), str(job)],
                    input=commands, text=True, capture_output=True, cwd=private,
                    env=env, timeout=15)
                for suffix, text in (('input', commands), ('out', result.stdout),
                                     ('trace', result.stderr)):
                    (out / (label + '.' + suffix)).write_text(text)
                assert result.returncode == 0, (label, result.stdout)
                return result

            if name in ('code', 'wrong-code', 'code-frames'):
                # Compile with the intact May Pascal 9 image on private 2068.
                image = bytearray((private / '2068').read_bytes())
                system = (private / '2248').read_bytes()
                for z in range(0o101, 0o115):
                    data = payload(system, z + 0o1000)
                    pos = (z + 4) * ZONE
                    image[pos:pos + ZONE] = control_words(z, data) + data
                (private / '2068').write_bytes(image)
                gost = lambda s: int.from_bytes(bytes(G.index(c) for c in s.ljust(6)), 'big')
                catalog = [0] * 1024
                catalog[0:3] = [gost('ВАСЯ'), gost('ПРОБА'), (1 << 24) | 0o30]
                catalog[0o377] = 3
                helper['write_words'](archive, 0o100, catalog)
                result = run(name + '-compile',
                             'арх вася,50,100\nпас проба - па зонгп 500300 1\nконец\n', True)
                assert 'БЫЛИ ОШИБКИ' not in result.stdout
                assert 'ПАСКАЛЬ-АВТОКОД 9.' in result.stdout
                if name == 'wrong-code':
                    source = source.replace('CHECK', 'OTHER')
                    helper['write_words'](archive, 0o101, helper['gost_source'](source))
                params = '500101 1 /500300 1 ' + flags
            else:
                params = '500101 1 ' + flags if fixture else flags
            if name == 'request-options':
                params = '===500101 1 Т,С'
            if name == 'retry-limit':
                params = '\n'.join(['1 1'] * 7)
            archive_hash = sha(archive)
            result = run(name, 'эхолот\n' + params + '\n' + ('\n' if params else '') + 'конец\n')
            check(name, result.stdout, result.stderr, bool(args.image))
            assert sha(archive) == archive_hash, 'ЭХОЛОТ wrote to its input volume'
            reports[name] = dict(status='passed', source_unchanged=True)
            print(name + ': OK', flush=True)
    assert all(sha(volumes / v) == h for v, h in hashes.items()), 'source volume changed'
    (out / 'results.json').write_text(json.dumps(reports, ensure_ascii=False, indent=2) + '\n')
    print('Source volumes unchanged; logs: ' + str(out))


if __name__ == '__main__':
    main()
