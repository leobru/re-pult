#!/usr/bin/env python3
"""Exercise recovered type helpers in a separate Pascal driver on private disks."""
from pathlib import Path
import re
import runpy
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def probe(source, private, archive, job, env, helper, encode, output, install, raw, disassembler):
    # Keep the recovered declarations/functions, replacing the outer analyzer
    # body with the test driver and a dedicated scratch pointer.
    prefix = source.split('(* 06137: source block analyzer body. *)')[0]
    prefix = re.sub(r'(_proced analyze[^\n]*\n)_label[^\n]*\n', r'\1', prefix)
    prefix = prefix.replace('s00142:integer;', 's00142:integer; probeType:idptr;')
    main = source[source.rindex('_(\n errors:=0; setup(heap);'):]
    driver = prefix + (ROOT / 'tests/echolot/type-driver.pas').read_text().replace('s00141', 'probeType') + '\n' + main
    (output / 'types-driver.pas').write_text(driver)
    helper['write_words'](archive, 0o101, encode(driver, helper))

    def run(label, commands, compile=False):
        result = subprocess.run(
            [str(ROOT / 'tools/run-dispak.sh'), '--725',
             '--path=' + str(private) + ':/usr/local/share/besm6',
             *(['-p', '-t'] if compile else ['-q', '-t', '-t']), str(job)],
            input=commands, text=True, capture_output=True, cwd=private, env=env, timeout=60)
        for suffix, text in (('input', commands), ('out', result.stdout), ('trace', result.stderr)):
            (output / (label + '.' + suffix)).write_text(text)
        assert result.returncode == 0, (label, result.stdout, result.stderr[-2000:])
        assert 'АВОСТ' not in result.stdout and 'ОШ.АДСИС' not in result.stdout, result.stdout
        return result

    compiled = run('types-compile', 'арх вася,50,100\nпас проба - па зонгп 500300 10\nконец\n', True)
    assert 'ВСЕ СДЕЛАНО.' in compiled.stdout and '***ОШ.' not in compiled.stdout, compiled.stdout
    binary = raw(archive.read_bytes(), 0o300, 4)
    (output / 'types-driver.bin').write_bytes(binary)
    install(private / '2068', 0o64, 4, binary)
    fixture = (ROOT / 'tests/echolot/types.pas').read_text()
    helper['write_words'](archive, 0o200, helper['gost_source'](fixture))
    result = run('types', 'эхолот\n500200 1\n\nконец\n')
    # dispak renders visually identical Latin letters as Cyrillic GOST letters.
    canon = lambda text: text.translate(str.maketrans('ABCEHKMOPTXY', 'АВСЕНКМОРТХУ'))
    markers = ('ARRAY', 'RECORD', 'VARIANT', 'PACKING', 'RANGE', 'WIDE', 'POINTER', 'SET', 'FORWARD',
               'SIGNED', 'CHAR', 'NIL', 'NAMED', 'REAL', 'CYCLE', 'TYPES', 'BOUNDS',
               'VALUES', 'REFERENCE', 'FUNCTION', 'PROCEDURE', 'HASH')
    for marker in markers:
        assert canon(marker + ' OK') in canon(result.stdout), result.stdout
    assert 'ЕRRОR' not in result.stdout, result.stdout
    layout = runpy.run_path(str(ROOT / 'tests/echolot-layout.py'))
    entries, _, _, _ = layout['inspect'](output / 'types-driver.bin', disassembler, output)
    executed = ('BitWidth', 'Fields', 'ParseType', 'ScalarConstant', 'TypeCheck', 'Chain', 'FormalParams', 'PoolWord', 'PruneHash')
    for name in executed:
        entry = entries[layout['RECOVERED'].index(name)]
        assert re.search(f'^{entry:05o}:', result.stderr, re.M), name + ' did not execute'
    rejected = {
        'value-array': (fixture.replace('_var C:', 'C:'), 4),
        'function-array': (fixture.replace('_function FN:real',
                                         '_function FN:_array[1..2] _of integer'), 4),
        'duplicate-parameter': (fixture.replace('A,B:integer', 'A,A:integer'), 2),
    }
    for name, (text, error) in rejected.items():
        helper['write_words'](archive, 0o200, helper['gost_source'](text))
        failed = run('types-' + name, 'эхолот\n500200 1\n\nконец\n')
        assert canon('BOUNDS OK') in canon(failed.stdout), failed.stdout
        assert re.search(canon(r'ERROR =\s+' + str(error) + r'\s'),
                         canon(failed.stdout)), failed.stdout
        assert canon('PROCEDURE OK') not in canon(failed.stdout), failed.stdout
    print(f'ЭХОЛОТ: type helper driver passed {len(markers)} checks and '
          f'{len(rejected)} rejection probes', flush=True)
    return dict(checks=list(markers), executed_helpers=list(executed),
                rejected_parameters=list(rejected), status='passed')
