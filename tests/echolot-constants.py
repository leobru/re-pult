#!/usr/bin/env python3
"""Check the recovered CONST block and its values independently of the full block parser."""
from pathlib import Path
import json
import re
import runpy
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def probe(source, private, archive, job, env, helper, encode, output, install, raw, disassembler, december=False):
    # Retain the original frame and the declarations which fix the literal pool.
    prefix = source.split('(* 06137: source block analyzer body. *)')[0]
    prefix = re.sub(r'(_proced analyze[^\n]*\n)_label[^\n]*', r'\1_label 6411;', prefix)
    fragment = source[source.index(' (* 06232..06417:'):source.index(' (* 06420:')]
    main = source[source.rindex('_(\n errors:=0; setup(heap);'):]
    driver = prefix + '''_(
 InitHistorical; longStrings:=false; ScanToken;
''' + fragment + '''
 _for loopIndex:=0 _to 127 _do _(
  t:=namehash[loopIndex];
  _while t<>_nil _do _(
   _if (t@.kind=CONST) _and (t@.level=1) _then _(
    _if t@.consttype=intType _then leftValue:=1
    _else _if t@.consttype=realType _then leftValue:=2
    _else _if t@.consttype=boolType _then leftValue:=3
    _else _if t@.consttype=charType _then leftValue:=4
    _else _if t@.consttype=alfaType _then leftValue:=5 _else leftValue:=6;
    PrintField(t@.name); write(Space,leftValue:0,Space);
    _if t@.consttype=intType _then write(PoolWord(t@.constvalue):0);
    writeln
   _);
   t:=t@.next
  _)
 _)
_);
''' + main
    (output / 'constants-driver.pas').write_text(driver)
    helper['write_words'](archive, 0o101, encode(driver, helper))

    def run(label, commands, compile=False):
        result = subprocess.run(
            [str(ROOT / 'tools/run-dispak.sh'), '--725',
             '--path=' + str(private) + ':/usr/local/share/besm6',
             *(['-p', '-t'] if compile else ['-q', '-t', '-t']), str(job)],
            input=commands, text=True, capture_output=True, cwd=private, env=env, timeout=60)
        for suffix, text in (('input', commands), ('out', result.stdout), ('trace', result.stderr)):
            (output / (label + '.' + suffix)).write_text(text)
        assert result.returncode == 0 and 'АВОСТ' not in result.stdout, result.stdout
        return result

    compiled = run('constants-compile', 'арх вася,50,100\nпас проба - па зонгп 500300 10\nконец\n', True)
    assert 'ВСЕ СДЕЛАНО.' in compiled.stdout and '***ОШ.' not in compiled.stdout, compiled.stdout
    binary = raw(archive.read_bytes(), 0o300, 4)
    (output / 'constants-driver.bin').write_bytes(binary)
    install(private / '2068', 0o64, 4, binary)
    original = (output / 'original.bin').read_bytes()
    assert binary[0o11*6:0o510*6] == original[0o11*6:0o510*6], 'CONST driver changed literal pool'
    layout = runpy.run_path(str(ROOT / 'tests/echolot-layout.py'))
    new_entries, _, _, instructions = layout['inspect'](output / 'constants-driver.bin', disassembler, output)
    old_entries, _, _, old = layout['inspect'](output / 'original.bin', disassembler, output)
    starts = [a for (a, half), op in instructions.items() if half == 0
              and op == (1, 0o10, 0o46, False)
              and instructions.get((a, 1)) == (0, 0o12, 0o27, False)]
    assert len(starts) == 1, starts
    start = starts[0]
    differences = []
    case_bases = []
    for offset in range(0o6420-0o6232):
        for half in (0, 1):
            before = old[0o6232+offset, half]
            after = instructions.get((start+offset, half))
            expected = before
            if before[3] and before[1] in (0o26, 0o27, 0o30) and 0o6232 <= before[2] <= 0o6420:
                expected = (*before[:2], start + before[2] - 0o6232, before[3])
            if (before[3] and before[1] == 0o31
                    and old_entries[0] <= before[2] < old_entries[-1]):
                expected = (*before[:2], before[2] + new_entries[0] - old_entries[0], before[3])
            if (december and 0o6376 <= 0o6232+offset <= 0o6402
                    and half == 0 and expected[0:2] == (0, 0o30)
                    and after == (0o10, *expected[1:])):
                case_bases.append(f'{0o6232+offset:05o}:{half}')
            elif after != expected:
                differences.append(dict(original=f'{0o6232+offset:05o}:{half}',
                                        generated=f'{start+offset:05o}:{half}',
                                        before=before, after=after))
    report = dict(start=f'{start:05o}', words=f'{0o6420-0o6232:04o}', differences=differences,
                  case_base_differences=case_bases)
    (output / 'constants-layout.json').write_text(json.dumps(report, indent=2)+'\n')
    assert not differences, 'CONST block differs; see constants-layout.json'

    canon = lambda text: text.translate(str.maketrans('ABCEHKMOPTXY', 'АВСЕНКМОРТХУ'))
    fixture = (ROOT / 'tests/echolot/constants.pas').read_text()
    helper['write_words'](archive, 0o200, helper['gost_source'](fixture))
    result = run('constants', 'эхолот\n500200 1\n\n\nконец\n')
    assert canon('ERROR') not in canon(result.stdout), result.stdout
    parsed = canon(result.stdout).replace('ИДТИ?', '').replace('==>', '')
    assert 'ВЫХОД В ПУЛЬТ' in result.stdout and 'ВРЕМЯ РЕШ:' in result.stdout, result.stdout
    expected = dict(A=17, B=20, C=15, D=30, E=7, NEG=-19, SUB=-23,
                    PROD=-57, QUOT=-5, PLUS=8, ZERO=0, BASED=63, REF=17)
    for name, value in expected.items():
        assert re.search(canon(r'^\s*'+name+r'\s+1\s+'+str(value)+r'\s*$'),
                         parsed, re.M), (name, result.stdout)
    for name, flags in dict(RVAL='2', BOOL='3', CHR='4', TXT='5', NILVAL='6').items():
        assert re.search(canon(r'^\s*'+name+r'\s+'+flags+r'\s*$'),
                         parsed, re.M), (name, result.stdout)
    rejected = {
        'name': ('_const 3=1;', 2),
        'duplicate': ('_const A=1; A=2;', 2),
        'equals': ('_const A:1;', 3),
        'value': ('_const A=UNKNOWN;', 4),
        'separator': ('_const A=1 _var X:integer;', 5),
        'zero': ('_const A=1/0;', 6),
        'real-operation': ('_const A=1.5+2.5;', 6),
        'mixed-operation': ('_const A=1+2.5;', 6),
        'signed-right': ('_const A=1+-2;', 6),
        'third-operand': ('_const A=1+2+3;', 5),
    }
    for name, (text, error) in rejected.items():
        helper['write_words'](archive, 0o200, helper['gost_source'](text))
        failed = run('constants-'+name, 'эхолот\n500200 1\n\n\nконец\n')
        assert re.search(canon(r'ERROR =\s+'+str(error)+r'\s'), canon(failed.stdout)), failed.stdout
    report.update(status='passed', integer_values=expected, scalar_types=5,
                  rejected=list(rejected))
    print(f'ЭХОЛОТ: CONST driver passed {len(expected)} integer values, 5 scalar types and '
          f'{len(rejected)} rejection probes', flush=True)
    return report
