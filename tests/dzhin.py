#!/usr/bin/env python3
"""Recompile ДЖИН, compare its complete program image, and replay the ARFA error path.

Only compilation date is controlled, through localtime() in compile-date.c.
No generated words are patched. Disk copies and the ARFA catalogs are disposable.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import struct
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from gost import G
from make2068 import ZONE, MASK, payload, control_words

END = 0o302


def digest(data):
    return hashlib.sha256(data).hexdigest()


def raw_zone(image, zone):
    return b''.join((word & MASK).to_bytes(6, 'big')
                    for word in struct.unpack('<1024Q', payload(image, zone)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dispak', default='dispak')
    parser.add_argument('--current-date', action='store_true',
                        help='use the current date; allow only header word 00002 to differ')
    args = parser.parse_args()
    app = shutil.which(args.dispak)
    if app is None:
        parser.error('dispak executable not found')
    helper = runpy.run_path(str(ROOT / 'tests/pascal-segments.py'))
    volumes = ROOT / 'build/volumes'
    out = ROOT / 'build/dzhin-rebuild'
    if args.current_date:
        out /= 'current-date'
    out.mkdir(parents=True, exist_ok=True)
    sources = {v: (volumes / v).read_bytes() for v in ('2148', '2248', '2068')}
    original = raw_zone(sources['2248'], 0o1070)
    assert original == raw_zone(sources['2148'], 0o1070)
    assert original == raw_zone(sources['2068'], 0o70)
    assert int.from_bytes(original[5*6:6*6], 'big') == END
    env = dict(os.environ, DISPAK=app)
    env.pop('BESM6_PATH', None)
    env.pop('BESM6_SMALL_DISKS', None)
    if not args.current_date:
        library = out / 'compile-date.so'
        subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-shared', '-fPIC',
                        '-o', str(library), str(ROOT / 'tests/dzhin/compile-date.c')], check=True)
        env['LD_PRELOAD'] = str(library)
    with tempfile.TemporaryDirectory(prefix='pult-dzhin-') as directory:
        private = Path(directory)
        for v in ('2248', '2068'):
            (private / v).write_bytes(sources[v])
        archive = private / '2345'
        archive.write_bytes(bytes((0o400 + 4) * ZONE))
        gost = lambda s: int.from_bytes(bytes(G.index(c) for c in s.ljust(6)), 'big')
        catalog = [0] * 1024
        catalog[0] = gost('ВАСЯ')
        catalog[1] = gost('ДЖИН')
        catalog[2] = (1 << 24) | 0o30
        catalog[0o377] = 3
        helper['write_words'](archive, 0o100, catalog)
        helper['write_words'](archive, 0o101,
                              helper['gost_source']((ROOT / 'pascal/dzhin.pas').read_text()))
        job = private / 'job.b6'
        job.write_text((ROOT / 'pult2068.b6').read_text().replace(
            'лент 30(1С)^', 'лент 30(1С)^\nлент 50(2345-зп)^'))

        def session(name, commands, compile_job=False):
            (out / (name + '.input')).write_text(commands)
            flags = ['-p', '-t'] if compile_job else ['-q', '-t', '-t']
            result = subprocess.run(
                [str(ROOT / 'tools/run-dispak.sh'), '--725',
                 '--path=' + directory + ':/usr/local/share/besm6',
                 '--arfa-dir=' + str(private / ('arfa-' + name)), *flags, str(job)],
                input=commands, text=True, capture_output=True, cwd=private, env=env, timeout=30)
            (out / (name + '.out')).write_text(result.stdout)
            (out / (name + '.trace')).write_text(result.stderr)
            assert result.returncode == 0 and 'АВОСТ' not in result.stdout, (name, result.stdout)
            assert 'ВРЕМЯ РЕШ:' in result.stdout, (name, result.stdout)
            return result

        compiled = session('compile', 'арх вася,50,100\nпас джин - па зонгп 500300 1\nконец\n', True)
        assert 'ВСЕ СДЕЛАНО.' in compiled.stdout and 'БЫЛИ ОШИБКИ' not in compiled.stdout
        generated = raw_zone(archive.read_bytes(), 0o300)
        (out / 'generated.bin').write_bytes(generated)
        (out / 'original-program.bin').write_bytes(original[:END*6])
        (out / 'generated-program.bin').write_bytes(generated[:END*6])
        differences = [i for i in range(END) if original[i*6:(i+1)*6] != generated[i*6:(i+1)*6]]
        allowed = {2} if args.current_date else set()
        assert set(differences) <= allowed, 'program words differ: ' + ' '.join(f'{i:05o}' for i in differences)
        baseline = session('original', 'джин\nконец\n')
        image = bytearray((private / '2068').read_bytes())
        header = (0o70 + 4) * ZONE
        for i in range(1024):
            offset = header + 64 + i*8
            old, = struct.unpack_from('<Q', image, offset)
            value = int.from_bytes(generated[i*6:(i+1)*6], 'big')
            struct.pack_into('<Q', image, offset, (old & ~MASK) | value)
        image[header:header+64] = control_words(0o70, image[header+64:header+ZONE])
        (private / '2068').write_bytes(image)
        rebuilt = session('rebuilt', 'джин\nконец\n')
        for result in (baseline, rebuilt):
            assert '*** ОШИБКА АРХ. = ТАКОГО ИМЕНИ НЕТ' in result.stdout
            assert '00156: *63 (7)' in result.stderr
        assert baseline.stdout == rebuilt.stdout, 'original/rebuilt terminal output differs'
    report = dict(program_end_octal=f'{END:05o}', program_words=END,
                  compilation_date='current' if args.current_date else '1987-12-07',
                  source_sha256=digest((ROOT / 'pascal/dzhin.pas').read_bytes()),
                  original_program_sha256=digest(original[:END*6]),
                  generated_program_sha256=digest(generated[:END*6]),
                  differing_program_words=[f'{i:05o}' for i in differences],
                  residual_zone_words=1024-END,
                  differing_residual_words=sum(original[i*6:(i+1)*6] != generated[i*6:(i+1)*6]
                                               for i in range(END, 1024)),
                  original_missing_archive='passed', rebuilt_missing_archive='passed')
    (out / 'comparison.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    assert all(digest((volumes / v).read_bytes()) == digest(data) for v, data in sources.items())
    print(f'PASS: {END} program words compared; differences: {report["differing_program_words"]}')
    print('Original/rebuilt ARFA error paths match; source volumes unchanged')
    print('Artifacts: ' + str(out))


if __name__ == '__main__':
    main()
