#!/usr/bin/env python3
"""Recompile annotated СЕРВИС and compare all 3072 words with 2148 and 2068.

Use the May 1988 Pascal compiler from 2248 in a temporary volume 2068.
Only localtime() is overridden to reproduce the compilation date 21.11.88.
Generated words are never patched or masked out of the comparison.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import shutil
import struct
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from gost import G
from make2068 import MASK, ZONE, control_words, payload


def digest(data):
    return hashlib.sha256(data).hexdigest()


def raw_zones(image, first, count):
    return b''.join((word & MASK).to_bytes(6, 'big')
                    for zone in range(first, first + count)
                    for word in struct.unpack('<1024Q', payload(image, zone)))


def encode_source(source, helper):
    # Comments use Unicode prose; compiler option comments remain in the input.
    # Match strings and CODE's backtick annotations before Pascal comments.
    tokens = re.compile(r"'(?:''|[^'])*'|`[^`]*`|\(\*.*?\*\)", re.S)

    def comment(match):
        text = match[0]
        if text.startswith('(*') and not text.startswith('(*='):
            return ' ' + '\n' * text.count('\n')
        return text

    source = tokens.sub(comment, source)
    # dispak/encoding.c's ASCII aliases for GOST 0136 and 0115.
    return helper['gost_source'](source.replace('?', '°').replace('^', '‾'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dispak', default='dispak')
    parser.add_argument('--volumes', type=Path, default=ROOT / 'build/volumes')
    parser.add_argument('--source', type=Path, default=ROOT / 'pascal/servic.pas')
    args = parser.parse_args()
    app = shutil.which(args.dispak)
    if app is None:
        parser.error('dispak executable not found')
    helper = runpy.run_path(str(ROOT / 'tests/pascal-segments.py'))
    sources = {v: (args.volumes / v).read_bytes() for v in ('2148', '2248', '2068')}
    original = raw_zones(sources['2148'], 0o1031, 3)
    assert original == raw_zones(sources['2068'], 0o31, 3), '2068 has another СЕРВИС'
    end = int.from_bytes(original[30:36], 'big')
    assert end == 0o5620
    out = ROOT / 'build/servic-rebuild'
    out.mkdir(parents=True, exist_ok=True)
    library = out / 'compile-date.so'
    subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-shared', '-fPIC',
                    '-o', str(library), str(ROOT / 'tests/servic/compile-date.c')], check=True)
    env = dict(os.environ, DISPAK=app, LD_PRELOAD=str(library))
    env.pop('BESM6_PATH', None)
    env.pop('BESM6_SMALL_DISKS', None)
    with tempfile.TemporaryDirectory(prefix='pult-servic-') as directory:
        private = Path(directory)
        (private / '2248').write_bytes(sources['2248'])
        image = bytearray(sources['2068'])
        # Whole historical compiler images, including the May version banner.
        for zone in range(0o101, 0o115):
            data = payload(sources['2248'], zone + 0o1000)
            start = (zone + 4) * ZONE
            image[start:start + ZONE] = control_words(zone, data) + data
        (private / '2068').write_bytes(image)
        archive = private / '2345'
        archive.write_bytes(bytes((0o400 + 4) * ZONE))
        gost = lambda s: int.from_bytes(bytes(G.index(c) for c in s.ljust(6)), 'big')
        catalog = [0] * 1024
        catalog[0] = gost('ВАСЯ')
        catalog[1] = gost('СЕРВИС')
        catalog[2] = (1 << 24) | 0o30
        catalog[0o377] = 3
        helper['write_words'](archive, 0o100, catalog)
        helper['write_words'](archive, 0o101, encode_source(args.source.read_text(), helper))
        job = private / 'job.b6'
        job.write_text((ROOT / 'pult2068.b6').read_text().replace(
            'лент 30(1С)^', 'лент 30(1С)^\nлент 50(2345-зп)^'))
        commands = 'арх вася,50,100\nпас сервис - па зонгп 500300 3\nконец\n'
        (out / 'compile.input').write_text(commands)
        result = subprocess.run(
            [str(ROOT / 'tools/run-dispak.sh'), '--725',
             '--path=' + directory + ':/usr/local/share/besm6',
             '--arfa-dir=' + str(private / 'arfa'), '-p', '-t', str(job)],
            input=commands, text=True, capture_output=True, cwd=private, env=env, timeout=60)
        (out / 'compile.out').write_text(result.stdout)
        (out / 'compile.trace').write_text(result.stderr)
        assert result.returncode == 0, result.stderr
        assert 'АВОСТ' not in result.stdout and 'БЫЛИ ОШИБКИ' not in result.stdout, result.stdout
        assert 'ПАСКАЛЬ-АВТОКОД 9.(17.05.88)' in result.stdout, result.stdout
        assert 'МАХАDR=05620' in result.stdout and 'ВСЕ СДЕЛАНО.' in result.stdout, result.stdout
        generated = raw_zones(archive.read_bytes(), 0o300, 3)
    (out / 'original.bin').write_bytes(original)
    (out / 'generated.bin').write_bytes(generated)
    differences = [f'{i:05o}' for i in range(3072)
                   if original[i*6:(i+1)*6] != generated[i*6:(i+1)*6]]
    report = dict(source_sha256=digest(args.source.read_bytes()),
                  source_volume=2148, source_zones_octal=['1031', '1032', '1033'],
                  compiler='Pascal-autocode 9 (17.05.88), from 2248:1101-1114',
                  compiler_sha256=digest(raw_zones(sources['2248'], 0o1101, 12)),
                  compilation_date='1988-11-21', program_end_octal=f'{end:05o}',
                  program_words=end, residual_words=3072-end, compared_words=3072,
                  original_sha256=digest(original), generated_sha256=digest(generated),
                  differing_words=differences)
    (out / 'comparison.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    assert all((args.volumes / v).read_bytes() == data for v, data in sources.items())
    assert not differences, 'СЕРВИС differs at: ' + ' '.join(differences)
    print('PASS: all 3072 words match СЕРВИС on 2148 and 2068, including date and zone tail')
    print('Source volumes unchanged; artifacts: ' + str(out))


if __name__ == '__main__':
    main()
