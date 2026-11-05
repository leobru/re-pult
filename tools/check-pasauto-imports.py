#!/usr/bin/env python3
"""Compile the March 2025 pasauto-re reconstructions on private PULT disks."""
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
from make2068 import ZONE, payload, control_words, build

PROGRAMS = dict(ppr=(0o1001, 1), lazy=(0o1034, 1), pretty=(0o1055, 3),
                newedt=(0o1075, 3), print=(0o1115, 1), bilist=(0o1116, 1), test=(None, 1))


def normalize(source):
    # Preserve strings while removing %-style comments used by these imports.
    source = re.sub(r"'(?:''|[^'])*'|%[^\n]*",
                    lambda m: '' if m[0].startswith('%') else m[0], source)
    # Original togost.c aliases: backslash and { mean the numeric escape.
    return source.expandtabs(8).translate(str.maketrans(
        {'\\': '≡', '{': '≡', '&': '∧', '|': '∨', '#': '≠', '$': '◇', '~': '¬',
         '≤': '⩽', '≥': '⩾'}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dispak', default=os.environ.get('DISPAK', 'dispak'))
    parser.add_argument('--program', action='append', choices=PROGRAMS)
    parser.add_argument('--compiler', choices=['may', 'december'], default='may')
    parser.add_argument('--source', type=Path, help='working edition; requires one --program')
    args = parser.parse_args()
    if args.source:
        assert args.program and len(args.program) == 1, '--source requires one --program'
    app = shutil.which(args.dispak)
    assert app, args.dispak
    helpers = runpy.run_path(str(ROOT / 'tests/pascal-segments.py'))
    common = runpy.run_path(str(ROOT / 'tests/rebuild-analyzers.py'))
    encode = runpy.run_path(str(ROOT / 'tests/servic.py'))['encode_source']
    raw = common['raw_zones']
    disks = {v: (ROOT / 'build/volumes' / v).read_bytes() for v in ('2068', '2148', '2248')}
    image = bytearray(disks['2068'])
    if args.compiler == 'may':
        for z in range(0o101, 0o115):
            data = payload(disks['2248'], z + 0o1000)
            offset = (z + 4) * ZONE
            image[offset:offset + ZONE] = control_words(z, data) + data
    else:
        image, _ = build(ROOT / 'build/volumes/2148', ROOT / 'build/volumes/2248',
                         json.loads((ROOT / 'tools/volume2068.json').read_text()))
    reports = {}
    for name in args.program or PROGRAMS:
        zone, count = PROGRAMS[name]
        out = ROOT / 'build/pasauto-imports' / args.compiler / (name + ('-working' if args.source else ''))
        out.mkdir(parents=True, exist_ok=True)
        source = args.source or ROOT / 'pascal/pasauto-2025' / (name + '.pas')
        source = source.resolve()
        text = normalize(source.read_text())
        (out / 'compiler-input.pas').write_text(text)
        report = dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                      source=str(source.relative_to(ROOT)), compiler=args.compiler,
                      original_zone=f'{zone:04o}' if zone else None, zones=count)
        with tempfile.TemporaryDirectory(prefix='pult-import-', dir=out) as temporary:
            folder = Path(temporary)
            (folder / '2068').write_bytes(image)
            (folder / '2248').write_bytes(disks['2248'])
            archive = folder / '2345'
            archive.write_bytes(bytes((0o400 + 4) * ZONE))
            word = lambda s: int.from_bytes(bytes(G.index(c) for c in s.ljust(6)), 'big')
            catalog = [0] * 1024
            catalog[:3] = [word('ВАСЯ'), word('ПРОБА'), (1 << 24) | 0o30]
            catalog[0o377] = 3
            helpers['write_words'](archive, 0o100, catalog)
            helpers['write_words'](archive, 0o101, encode(text, helpers))
            job = folder / 'job.b6'
            job.write_text((ROOT / 'pult2068.b6').read_text().replace(
                'лент 30(1С)^', 'лент 30(1С)^\nлент 50(2345-зп)^'))
            home = folder / 'home'
            home.mkdir()
            env = dict(os.environ, HOME=str(home))
            env.pop('BESM6_PATH', None)
            env.pop('BESM6_SMALL_DISKS', None)
            commands = 'арх вася,50,100\nпас проба - па зонгп 500300 10\nконец\n'
            (out / 'compile.input').write_text(commands)
            result = subprocess.run([app, '--725', '--path=' + str(folder) +
                                     ':/usr/local/share/besm6', '-p', '-t', str(job)],
                                    input=commands, text=True, capture_output=True,
                                    cwd=folder, env=env, timeout=60)
            (out / 'compile.out').write_text(result.stdout)
            (out / 'compile.trace').write_text(result.stderr)
            saved = 'ЗАПИСЬ' in result.stdout and 'ЗОН С 500300' in result.stdout
            report['returned_to_driver'] = 'ВСЕ СДЕЛАНО.' in result.stdout
            report['compiled'] = (result.returncode == 0 and saved
                                  and all(s not in result.stdout for s in ('БЫЛИ ОШИБКИ', '***ОШ.', 'АВОСТ')))
            if report['compiled']:
                old = raw(disks['2248'], zone, count) if zone else bytes(count * 6144)
                new = raw(archive.read_bytes(), 0o300, count)
                (out / 'original.bin').write_bytes(old)
                (out / 'generated.bin').write_bytes(new)
                end = int.from_bytes(old[30:36], 'big')
                newend = int.from_bytes(new[30:36], 'big')
                assert 0 < newend <= count * 1024, (name, newend)
                differences = [f'{a:05o}' for a in range(max(end, newend))
                               if old[a * 6:a * 6 + 6] != new[a * 6:a * 6 + 6]]
                report.update(original_end=f'{end:05o}' if zone else None, generated_end=f'{newend:05o}',
                              different_words=len(differences), differences=differences,
                              different_words_after_header=sum(int(a, 8) >= 0o11 for a in differences),
                              original_sha256=hashlib.sha256(old).hexdigest(),
                              generated_sha256=hashlib.sha256(new).hexdigest())
                if zone is None:
                    for key in ('differences', 'different_words', 'different_words_after_header',
                                'original_sha256'):
                        report.pop(key)
                disassembler = ROOT.parent / 'dispak-tools/disbesm6'
                for label in ('original', 'generated') if zone else ('generated',):
                    with (out / (label + '.lst')).open('w') as listing:
                        subprocess.run([str(disassembler), '-b', '-a0', '-e7',
                                        str(out / (label + '.bin'))], stdout=listing, check=True)
        (out / 'comparison.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        reports[name] = report
        print(name, 'compiled' if report['compiled'] else 'FAILED',
              report.get('original_end', ''), report.get('generated_end', ''),
              report.get('different_words', ''), flush=True)
    assert all((ROOT / 'build/volumes' / v).read_bytes() == b for v, b in disks.items())
    target = ROOT / 'build/pasauto-imports' / args.compiler / 'report.json'
    target.write_text(json.dumps(reports, ensure_ascii=False, indent=2) + '\n')
    assert all(r['compiled'] for r in reports.values()), 'See compile.out for failed sources'


if __name__ == '__main__':
    main()
