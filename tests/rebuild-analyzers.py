#!/usr/bin/env python3
"""Compile ЧИСТКА/ЭХОЛОТ on private disks, compare images and run their probes.

The reconstructed sources are not bit-exact. --exact makes any differing word
a failure; the ordinary run verifies compilation and historical behavior probes.
The report includes every differing address, including headers and zone tails.
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
from gost import G, text as gost_text
from make2068 import MASK, ZONE, control_words, payload, build as build_volume2068

PROGRAMS = {'chistka': ('ЧИСТКА', 0o60, 3), 'echolot': ('ЭХОЛОТ', 0o64, 4)}


def raw_zones(image, start, count):
    return b''.join((w & MASK).to_bytes(6, 'big')
                    for z in range(start, start + count)
                    for w in struct.unpack('<1024Q', payload(image, z)))


def install_image(volume, zone, count, binary):
    """Use instruction tags for an executable overlay; keep input disks private."""
    end = int.from_bytes(binary[30:36], 'big')
    assert 0 < end <= count * 1024, 'rebuilt program exceeds its overlay allocation'
    assert len(binary) >= end * 6
    binary = binary[:count * 6144].ljust(count * 6144, b'\0')
    with volume.open('r+b') as stream:
        for z in range(count):
            data = struct.pack('<1024Q', *(
                int.from_bytes(binary[(z*1024+i)*6:(z*1024+i+1)*6], 'big') | (1 << 48)
                for i in range(1024)))
            stream.seek((zone + z + 4) * ZONE)
            stream.write(control_words(zone + z, data) + data)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dispak', default='dispak')
    parser.add_argument('--program', action='append', choices=PROGRAMS)
    parser.add_argument('--exact', action='store_true')
    parser.add_argument('--compiler', choices=('may', 'december'), default='may',
                        help='Pascal 9: May 2248, or checked December 2148 compiler')
    parser.add_argument('--compile-only', action='store_true',
                        help='compile and compare without running behavior probes')
    parser.add_argument('--disassembler', default=str(ROOT.parent / 'dispak-tools/disbesm6'))
    args = parser.parse_args()
    app = shutil.which(args.dispak)
    if not app:
        parser.error('dispak executable not found')
    helper = runpy.run_path(str(ROOT / 'tests/pascal-segments.py'))
    encode = runpy.run_path(str(ROOT / 'tests/servic.py'))['encode_source']
    volumes = ROOT / 'build/volumes'
    disks = {v: (volumes / v).read_bytes() for v in ('2148', '2248', '2068')}
    if args.compiler == 'december':
        compiler_image, _ = build_volume2068(
            volumes / '2148', volumes / '2248',
            json.loads((ROOT / 'tools/volume2068.json').read_text()))
        compiler_date = '09.12.88'
        compiler_description = 'Pascal 9, 09.12.88, 2148:1101-1114; checked volume2068.json patches'
    else:
        compiler_image = disks['2248']
        compiler_date = '17.05.88'
        compiler_description = 'Pascal 9, 17.05.88, 2248:1101-1114'
    reports = {}
    for key in args.program or PROGRAMS:
        name, zone, length = PROGRAMS[key]
        out = ROOT / 'build' / (key + '-rebuild' + ('-december' if args.compiler == 'december' else ''))
        out.mkdir(parents=True, exist_ok=True)
        source = ROOT / 'pascal' / (key + '.pas')
        original = raw_zones(disks['2248'], 0o1000 + zone, length)
        assert original == raw_zones(disks['2148'], 0o1000 + zone, length)
        with tempfile.TemporaryDirectory(prefix='pult-rebuild-' + key + '-') as directory:
            private = Path(directory)
            (private / '2248').write_bytes(disks['2248'])
            image = bytearray(disks['2068'])
            for z in range(0o101, 0o115):
                data = payload(compiler_image, z if args.compiler == 'december' else 0o1000 + z)
                start = (z + 4) * ZONE
                image[start:start + ZONE] = control_words(z, data) + data
            compiler_sha256 = digest(raw_zones(image, 0o101, 0o14))
            (private / '2068').write_bytes(image)
            archive = private / '2345'
            archive.write_bytes(bytes((0o400 + 4) * ZONE))
            gost = lambda s: int.from_bytes(bytes(G.index(c) for c in s.ljust(6)), 'big')
            catalog = [0] * 1024
            catalog[:3] = [gost('ВАСЯ'), gost('ПРОБА'), (1 << 24) | 0o30]
            catalog[0o377] = 3
            helper['write_words'](archive, 0o100, catalog)
            helper['write_words'](archive, 0o101, encode(source.read_text(), helper))
            job = private / 'job.b6'
            job.write_text((ROOT / 'pult2068.b6').read_text().replace(
                'лент 30(1С)^', 'лент 30(1С)^\nлент 50(2345-зп)^'))
            env = dict(os.environ, DISPAK=app)
            env.pop('BESM6_PATH', None)
            env.pop('BESM6_SMALL_DISKS', None)
            commands = 'арх вася,50,100\nпас проба - па зонгп 500300 10\nконец\n'
            result = subprocess.run(
                [str(ROOT / 'tools/run-dispak.sh'), '--725',
                 '--path=' + directory + ':/usr/local/share/besm6', '-p', '-t', str(job)],
                input=commands, text=True, capture_output=True, cwd=private, env=env, timeout=60)
            for ext, text in (('input', commands), ('out', result.stdout), ('trace', result.stderr)):
                (out / ('compile.' + ext)).write_text(text)
            assert result.returncode == 0, result.stderr
            assert 'ПАСКАЛЬ-АВТОКОД 9.(' + compiler_date + ')' in result.stdout, result.stdout
            assert 'ВСЕ СДЕЛАНО.' in result.stdout and '***ОШ.' not in result.stdout, result.stdout
            assert 'БЫЛИ ОШИБКИ' not in result.stdout and 'АВОСТ' not in result.stdout
            generated = raw_zones(archive.read_bytes(), 0o300, length)
            (out / 'generated.bin').write_bytes(generated)
            assert int.from_bytes(generated[30:36], 'big') <= length * 1024, \
                f"rebuilt image ends at {int.from_bytes(generated[30:36], 'big'):05o}, beyond overlay allocation"
            if key == 'echolot' and not args.compile_only:
                (out / 'original.bin').write_bytes(original)
                constants_probe = runpy.run_path(str(ROOT / 'tests/echolot-constants.py'))['probe'](
                    source.read_text(), private, archive, job, env, helper, encode, out,
                    install_image, raw_zones, args.disassembler, args.compiler == 'december')
                type_probe = runpy.run_path(str(ROOT / 'tests/echolot-types.py'))['probe'](
                    source.read_text(), private, archive, job, env, helper, encode, out,
                    install_image, raw_zones, args.disassembler)
        (out / 'original.bin').write_bytes(original)
        binary = out / 'generated.bin'
        binary.write_bytes(generated)
        differences = [f'{i:05o}' for i in range(length * 1024)
                       if original[i*6:(i+1)*6] != generated[i*6:(i+1)*6]]
        report = dict(source_sha256=digest(source.read_bytes()),
                      compiler=compiler_description, compiler_sha256=compiler_sha256,
                      compared_words=length*1024,
                      original_end_octal=f'{int.from_bytes(original[30:36], "big"):05o}',
                      generated_end_octal=f'{int.from_bytes(generated[30:36], "big"):05o}',
                      original_sha256=digest(original), generated_sha256=digest(generated),
                      exact_match=not differences, differing_addresses=differences)
        if key == 'chistka':
            literal_differences = [f'{i:05o}' for i in range(0o11, 0o547)
                                   if original[i*6:(i+1)*6] != generated[i*6:(i+1)*6]]
            layout = runpy.run_path(str(ROOT / 'tests/chistka-layout.py'))['compare_layout'](
                out / 'original.bin', binary, args.disassembler, out)
            report['routine_layout'] = layout
            report['literal_pool'] = dict(start_octal='00011', end_octal='00546',
                                          exact_match=not literal_differences,
                                          differing_addresses=literal_differences)
            assert not literal_differences, 'ЧИСТКА literal pool differs: ' + ', '.join(literal_differences)
        if key == 'echolot':
            literal_differences = [f'{i:05o}' for i in range(0o11, 0o531)
                                   if original[i*6:i*6+6] != generated[i*6:(i+1)*6]]
            report['literal_pool'] = dict(start_octal='00011', end_octal='00530',
                                          exact_match=not literal_differences,
                                          differing_addresses=literal_differences)
            for label, data in (('original', original), ('generated', generated)):
                (out / (label + '-literals.txt')).write_text(''.join(
                    f'{i:05o}  {data[i*6:i*6+6].hex().upper()}  {gost_text(data[i*6:i*6+6])}\n'
                    for i in range(0o11, 0o531)))
            if not args.compile_only:
                report['type_helper_probe'] = type_probe
                report['constants_probe'] = constants_probe
            layout = runpy.run_path(str(ROOT / 'tests/echolot-layout.py'))['compare_layout'](
                out / 'original.bin', binary, args.disassembler, out)
            report['routine_layout'] = layout
        if key == 'echolot' and args.compiler == 'december':
            may_directory = ROOT / 'build/echolot-rebuild'
            may_report = may_directory / 'comparison.json'
            may_binary = may_directory / 'generated.bin'
            if may_report.exists() and may_binary.exists():
                reference = json.loads(may_report.read_text())
                if (reference['source_sha256'] == report['source_sha256']
                        and reference['generated_sha256'] == digest(may_binary.read_bytes())):
                    cross = runpy.run_path(str(ROOT / 'tests/echolot-layout.py'))['compare_compilers'](
                        may_binary, binary, args.disassembler, out)
                    cross['may_image_sha256'] = reference['generated_sha256']
                    report['may_comparison'] = cross
        (out / 'comparison.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        if key == 'chistka':
            assert layout['all_sizes_match'], 'ЧИСТКА procedure/main sizes differ; see comparison.json'
            assert layout['all_starts_match'], 'ЧИСТКА procedure/main entry addresses differ'
            assert layout['helper_words_match'], 'ЧИСТКА compiler helper sizes differ'
            print('ЧИСТКА: all 43 procedure sizes and main size match the original', flush=True)
        if key == 'echolot':
            assert report['literal_pool']['exact_match'], 'ЭХОЛОТ literal pool differs; see comparison.json'
            assert layout['analyze_entry']['matches_except_literal_base'], 'ЭХОЛОТ analyze entry block differs'
            assert layout['recovered_starts_match'], 'ЭХОЛОТ recovered entry addresses differ'
            assert layout['recovered_literal_addresses_match'], 'ЭХОЛОТ recovered literal addresses differ'
            assert layout['recovered_sizes_match'], 'ЭХОЛОТ recovered procedure sizes differ'
            assert all(layout['main_layout'][key] for key in
                       ('start_match', 'size_match', 'helper_words_match')), 'ЭХОЛОТ main/helper layout differs'
            shape_changes = [d for row in layout['recovered']
                             for d in row['raw_instruction_differences']
                             if d['before'][:2] != d['after'][:2]
                             or d['before'][3] != d['after'][3]]
            literal_bases, case_bases = [], []
            for d in shape_changes:
                before, after = d['before'], d['after']
                if (d['original'] in ('06145:1', '07445:0', '07445:1', '07446:0')
                        and before[0] == 0o10 and after[0] == 0
                        and before[1:] == after[1:]):
                    literal_bases.append(d)
                elif (args.compiler == 'december' and before[0] == 0
                      and after[0] == 0o10 and before[1] == 0o30
                      and before[1:] == after[1:]):
                    case_bases.append(d)
                else:
                    raise AssertionError('recovered opcode/register changed: ' + str(d))
            report['compiler_literal_base_differences'] = literal_bases
            report['compiler_case_base_differences'] = case_bases
            assert layout['recovered_global_operands_match'], 'ЭХОЛОТ global frame offsets differ'
            assert layout['recovered_fixed_operands_match'], 'ЭХОЛОТ frame slots or immediate lengths differ'
            assert layout['recovered_literal_values_match'], 'ЭХОЛОТ recovered literal operands differ'
            assert layout['recovered_code_targets_match'], 'ЭХОЛОТ recovered branches/calls differ'
            code = runpy.run_path(str(ROOT / 'tests/echolot-layout.py'))['compare_code'](
                out / 'original.bin', binary, args.disassembler, out, args.compiler == 'december')
            report['code_comparison'] = code
            (out / 'code-comparison.json').write_text(json.dumps(code, indent=2) + '\n')
            assert code['sizes_match'] and not code['unexpected_differences'], 'ЭХОЛОТ unexpected code differences'
            print("ЭХОЛОТ: literal pool 00011..00530 matches exactly; recovered entry and literal addresses match", flush=True)
            print(f"ЭХОЛОТ: {len(layout['recovered'])} recovered procedures match starts, sizes, "
                  f"global/fixed operands, literal addresses and branch targets; "
                  f"{len(literal_bases)} literal-base and {len(case_bases)} CASE register differences", flush=True)
        print(f'{name}: compiled; exact match: {not differences}; {len(differences)} differing words', flush=True)
        if args.compile_only:
            (out / 'comparison.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
            reports[key] = report
            continue
        subprocess.run([sys.executable, str(ROOT / 'tests' / (key + '.py')),
                        '--dispak', app, '--image', str(binary)], check=True, cwd=ROOT)
        if key == 'echolot':
            trace = (ROOT / 'build/echolot-rebuilt-check/nested.trace').read_text()
            initialized = ('InitHistorical', 'NewIdentifier', 'NewConstant', 'NewBuiltin')
            for routine in initialized:
                row = next(row for row in layout['recovered'] if row['name'] == routine)
                assert re.search('^' + row['generated_start'] + ':', trace, re.M), \
                    'recovered initialization did not execute: ' + routine
            scanner_trace = (ROOT / 'build/echolot-rebuilt-check/scanner.trace').read_text()
            options_trace = (ROOT / 'build/echolot-rebuilt-check/scanner-lines.trace').read_text()
            scanned = ('ScanToken', 'ReadIdentifier', 'Digraph', 'OctalEscape',
                       'OptionComment', 'SkipComment', 'ReadBound', 'ReadSwitch',
                       'PutLiteral')
            for routine in scanned:
                row = next(row for row in layout['recovered'] if row['name'] == routine)
                assert re.search('^' + row['generated_start'] + ':', scanner_trace + options_trace, re.M), \
                    'recovered scanner routine did not execute: ' + routine
            error_trace = (ROOT / 'build/echolot-rebuilt-check/scanner-error.trace').read_text()
            for routine in ('ScanError', 'Diagnostic'):
                row = next(row for row in layout['recovered'] if row['name'] == routine)
                assert re.search('^' + row['generated_start'] + ':', error_trace, re.M), \
                    'recovered scanner diagnostic did not execute: ' + routine
            header_trace = (ROOT / 'build/echolot-rebuilt-check/header.trace').read_text()
            row = next(row for row in layout['recovered'] if row['name'] == 'SkipParameters')
            assert re.search('^' + row['generated_start'] + ':', header_trace, re.M), \
                'recovered PROGRAM file-list scanner did not execute'
            row = next(row for row in layout['recovered'] if row['name'] == 'ProgramHeader')
            assert re.search('^' + row['generated_start'] + ':', header_trace, re.M), \
                'recovered PROGRAM header did not execute'
            mode_trace = (ROOT / 'build/echolot-rebuilt-check/header-mode.trace').read_text()
            fill = int(row['generated_start'], 8) + 0o5473 - 0o5465
            assert re.search(f'^{fill:05o}:', mode_trace, re.M), \
                'PROGRAM header did not initialize the C- literal pool'
            call_trace = (ROOT / 'build/echolot-rebuilt-check/calls-slices.trace').read_text()
            row = next(row for row in layout['recovered'] if row['name'] == 'RememberCall')
            assert re.search('^' + row['generated_start'] + ':', call_trace, re.M), \
                'recovered callee-list insertion did not execute'
            body_trace = (ROOT / 'build/echolot-rebuilt-check/body.trace').read_text()
            entry_start = int(layout['analyze_entry']['generated_start'], 8)
            modes = re.findall(f'^{entry_start+5:05o}: xta 76013 +\\(=([0-7]{{16}})\\)',
                               body_trace, re.M)
            flags = re.findall(f'^{entry_start+10:05o}: atx 32\\(2\\).*acc=([0-7]{{16}})',
                               body_trace, re.M)
            assert modes and len(modes) == len(flags), 'analyze entry mode capture did not execute'
            assert [int(mode, 8) & 1 for mode in modes] == [int(flag, 8) for flag in flags], \
                'analyze entry captured the wrong terminal-output flag'
            report['analyze_entry_probe'] = dict(modes=modes, flags=flags, status='passed')
            bad_block_trace = (ROOT / 'build/echolot-rebuilt-check/block-token.trace').read_text()
            guard = entry_start + 0o6172 - 0o6137
            assert re.search(f'^{guard:05o}: vjm 1332\\(16\\)', bad_block_trace, re.M), \
                'recovered block-entry token guard did not execute'
            report['analyze_entry_probe']['token_guard'] = 'passed'
            label_trace = (ROOT / 'build/echolot-rebuilt-check/labels.trace').read_text()
            report['label_probe'] = runpy.run_path(str(ROOT / 'tests/echolot.py'))['check_labels'](
                label_trace, entry_start)
            row = next(row for row in layout['recovered'] if row['name'] == 'ScanBody')
            assert len(re.findall('^' + row['generated_start'] + ':', body_trace, re.M)) >= 4, \
                'recovered body scanner did not recurse into BEGIN/CASE'
            assert re.search('^06105:', body_trace, re.M), 'CODE skip branch did not execute'
            row = next(row for row in layout['recovered'] if row['name'] == 'PruneHash')
            assert re.search('^' + row['generated_start'] + ':', call_trace, re.M), \
                'recovered hash-chain cleanup did not execute'
            report['executed_call_routines'] = ['RememberCall', 'ScanBody', 'PruneHash']
            report['executed_header_routines'] = ['SkipParameters', 'ProgramHeader']
            report['executed_scanner_routines'] = list(scanned) + ['ScanError', 'Diagnostic']
            report['executed_initializers'] = list(initialized)
            (out / 'comparison.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        reports[key] = report
    assert all((volumes / v).read_bytes() == data for v, data in disks.items())
    if args.exact:
        assert all(r['exact_match'] for r in reports.values()), 'recompilation is not bit-exact'
    print('Compilation passed; source volumes unchanged.' if args.compile_only else
          'Compilation and behavior probes passed; source volumes unchanged.')


if __name__ == '__main__':
    main()
