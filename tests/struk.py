#!/usr/bin/env python3
"""Rebuild PULT СТРУК on private volumes and compare its words and behavior.

Usage: python3 tests/struk.py [--compiler may|december] [--compile-only]
Artifacts are in build/struk-rebuild[-december]. Source disks are never written.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from gost import G, text as gost_text
from make2068 import ZONE, payload, control_words, build as make_volume


CASES = {name: (name, '500101 1 Т') for name in (
    'blocks', 'comments', 'forward', 'nested', 'empty', 'names',
    'bad-header', 'bad-comment', 'bad-token', 'missing-dot', 'premature-end')}
CASES.update({
    'source-order': ('nested', '500101 1'),
    'suffix': ('nested', '500101В 1 Т'),
    'prefix': ('nested', '++> 500101 1 Т'),
    'saved-report': ('nested', '500101 1 /500103 1 Т'),
    'modes': ('empty', 'ПА\nПП\nППН\n500101 1'),
    'exit': (None, ''),
    'bad-number': (None, '?'),
    'bad-address': (None, '1 1'),
    'zero-length': (None, '500101 0'),
})


def digest(b):
    return hashlib.sha256(b).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dispak', default='dispak')
    parser.add_argument('--compiler', choices=['may', 'december'], default='may')
    parser.add_argument('--compile-only', action='store_true')
    parser.add_argument('--case', action='append', choices=sorted(CASES))
    parser.add_argument('--trace', action='store_true')
    args = parser.parse_args()
    app = shutil.which(args.dispak)
    if not app:
        parser.error('dispak executable not found')
    helper = runpy.run_path(str(ROOT / 'tests/pascal-segments.py'))
    common = runpy.run_path(str(ROOT / 'tests/rebuild-analyzers.py'))
    encode = runpy.run_path(str(ROOT / 'tests/servic.py'))['encode_source']
    raw, install = common['raw_zones'], common['install_image']
    volumes = ROOT / 'build/volumes'
    disks = {v: (volumes / v).read_bytes() for v in ['2148', '2248', '2068']}
    original = raw(disks['2248'], 0o1073, 1)
    assert original == raw(disks['2148'], 0o1073, 1)
    source = ROOT / 'pascal/struk.pas'
    out = ROOT / ('build/struk-rebuild' + ('-december' if args.compiler == 'december' else ''))
    out.mkdir(parents=True, exist_ok=True)
    (out / 'original.bin').write_bytes(original)
    date_library = out / 'compile-date.so'
    subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-shared', '-fPIC',
                    '-o', str(date_library), str(ROOT / 'tests/struk/compile-date.c')], check=True)
    compiler = disks['2248']
    if args.compiler == 'december':
        compiler, _ = make_volume(volumes / '2148', volumes / '2248',
                                 json.loads((ROOT / 'tools/volume2068.json').read_text()))
    with tempfile.TemporaryDirectory(prefix='pult-struk-') as directory:
        private = Path(directory)
        image = bytearray(disks['2068'])
        for z in range(0o101, 0o115):
            data = payload(compiler, z if args.compiler == 'december' else z + 0o1000)
            start = (z + 4) * ZONE
            image[start:start+ZONE] = control_words(z, data) + data
        (private / '2068').write_bytes(image)
        (private / '2248').write_bytes(disks['2248'])
        archive = private / '2345'
        archive.write_bytes(bytes((0o400+4)*ZONE))
        catalog = [0]*1024
        gost = lambda s: int.from_bytes(bytes(G.index(c) for c in s.ljust(6)), 'big')
        catalog[:3] = [gost('ВАСЯ'), gost('ПРОБА'), (1 << 24) | 0o30]
        catalog[0o377] = 3
        helper['write_words'](archive, 0o100, catalog)
        helper['write_words'](archive, 0o101, encode(source.read_text(), helper))
        job = private / 'job.b6'
        job.write_text((ROOT / 'pult2068.b6').read_text().replace(
            'лент 30(1С)^', 'лент 30(1С)^\nлент 50(2345-зп)^'))
        env = dict(os.environ, DISPAK=app, LD_PRELOAD=str(date_library))
        env.pop('BESM6_PATH', None)
        env.pop('BESM6_SMALL_DISKS', None)

        def session(label, commands):
            (out / (label+'.input')).write_text(commands)
            r = subprocess.run([str(ROOT / 'tools/run-dispak.sh'), '--725',
                '--path='+directory+':/usr/local/share/besm6', '-p', '-t',
                *(['-t'] if args.trace else []), str(job)],
                input=commands, text=True, capture_output=True, env=env, cwd=private, timeout=60)
            (out / (label+'.out')).write_text(r.stdout)
            (out / (label+'.trace')).write_text(r.stderr)
            assert r.returncode == 0, r.stderr[-3000:]
            assert 'АВОСТ' not in r.stdout, r.stdout
            return r.stdout

        result = session('compile', 'арх вася,50,100\nпас проба - па зонгп 500300 10\nконец\n')
        compiler_date = '09.12.88' if args.compiler == 'december' else '17.05.88'
        assert 'ПАСКАЛЬ-АВТОКОД 9.('+compiler_date+')' in result, result
        assert 'ВСЕ СДЕЛАНО.' in result and 'БЫЛИ ОШИБКИ' not in result and '***ОШ.' not in result, result
        generated = raw(archive.read_bytes(), 0o300, 1)
        (out / 'generated.bin').write_bytes(generated)
        end = int.from_bytes(generated[30:36], 'big')
        report = dict(source_sha256=digest(source.read_bytes()), compiler=args.compiler,
                      compilation_date='11.11.86', compared_words=1024,
                      exact_match=generated==original,
                      compiler_sha256=digest(raw(compiler,0o101 if args.compiler=='december' else 0o1101,0o14)),
                      source_volume_sha256={v:digest(data) for v,data in disks.items()},
                      original_sha256=digest(original), generated_sha256=digest(generated),
                      original_end=f'{int.from_bytes(original[30:36], "big"):05o}',
                      generated_end=f'{end:05o}',
                      differing_addresses=[f'{a:05o}' for a in range(1024)
                          if original[a*6:a*6+6] != generated[a*6:a*6+6]])
        dis = str(ROOT.parent / 'dispak-tools/disbesm6')
        for label, binary in [('original', original), ('generated', generated)]:
            entries = out / (label+'.entries')
            stop = min(1024, int.from_bytes(binary[30:36], 'big'))
            entries.write_text(''.join(f'{i:05o}:\n' for i in range(0o166, stop)))
            r = subprocess.run([dis, '-b', '-a0', '-e7', '--trace='+str(entries),
                                str(out / (label+'.bin'))],capture_output=True,text=True,check=True)
            (out / (label+'.lst')).write_text(r.stdout)
            (out / (label+'-literals.txt')).write_text(''.join(
                f'{a:05o} {binary[a*6:a*6+6].hex().upper()} {gost_text(binary[a*6:a*6+6])}\n'
                for a in range(0o11, 0o166)))
        report['literal_pool'] = dict(start='00011',end='00165',words=109,exact_match=original[0o11*6:0o166*6]==generated[0o11*6:0o166*6])
        (out / 'comparison.json').write_text(json.dumps(report, indent=2)+'\n')
        report['procedures'] = runpy.run_path(str(ROOT / 'tests/struk-layout.py'))['compare'](out)
        assert all(row['size_match'] and row['original']==row['generated'] for row in report['procedures'])
        (out / 'comparison.json').write_text(json.dumps(report, indent=2)+'\n')
        print('СТРУК: original end', report['original_end'], 'generated end',report['generated_end'],
              'differing words',len(report['differing_addresses']),flush=True)
        assert generated == original, 'recompilation changed СТРУК words; see comparison.json'
        if not args.compile_only:
            assert end <= 1024, 'rebuild no longer fits catalog zone'
            checks = []
            for name, (fixture, params) in CASES.items():
                if args.case and name not in args.case:
                    continue
                if fixture:
                    text = (ROOT / 'tests/struk' / (fixture+'.pas')).read_text()
                    helper['write_words'](archive, 0o101, encode(text, helper))
                archive_before = archive.read_bytes()
                # One extra empty response acknowledges the report pager when it appears.
                commands='струк\n'+params+'\n\n\nконец\n'
                (private / '2068').write_bytes(image)
                first=session(name+'-original',commands)
                first_archive = archive.read_bytes()
                archive.write_bytes(archive_before)
                install(private / '2068', 0o73, 1, generated)
                second=session(name+'-rebuilt',commands)
                second_archive = archive.read_bytes()
                def clean(s):
                    return s.split('-=* СТРУКТУРА ПРОГРАММЫ *=-',1)[1].split('ВРЕМЯ РЕШ:',1)[0]
                assert clean(first)==clean(second),name
                assert first_archive == second_archive, name+' disk effects differ'
                if name != 'saved-report':
                    assert first_archive == archive_before, name+' unexpectedly wrote source disk'
                assert '<*> ВОЗВРАТ <*>' in first and 'КОНЕЦ ЗАДАЧИ' in first, first
                expected_errors={'bad-header':0,'bad-token':2,'bad-comment':3,
                                 'missing-dot':4,'premature-end':1}
                if name in expected_errors:
                    assert 'ОШИБКА '+str(expected_errors[name])+' СТР.=' in first, first
                elif name in ('bad-number','bad-address','zero-length'):
                    assert 'ОШИБКА В ЧИСЛЕ' in first, first
                elif fixture:
                    assert 'ОШИБКА' not in first and 'ОШ.АДСИС' not in first, first
                if name == 'nested':
                    assert 'СТР=0007-0008-0008' in first and '(Ф)' in first, first
                    assert 'СТР=0004-0005-0005' in first and 'INNЕR' in first, first
                if name == 'forward':
                    assert 'СТР=0002     +' in first, first
                if name == 'saved-report':
                    data=raw(first_archive,0o103,1)
                    (out / 'saved-report.bin').write_bytes(data)
                    (out / 'saved-report.txt').write_text(gost_text(data.split(bytes([0o172]),1)[0]))
                    assert bytes([0o172,0o175]) in data, 'missing saved report terminator'
                    assert first_archive != archive_before, 'report was not written'
                checks.append(name)
                print('СТРУК:',name,'output and disk effects match',flush=True)
            report['functional_cases']=checks
            (out / 'comparison.json').write_text(json.dumps(report, indent=2)+'\n')
    assert all((volumes / v).read_bytes()==data for v,data in disks.items())
    report['source_volumes_unchanged'] = True
    (out / 'comparison.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
