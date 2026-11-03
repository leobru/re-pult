#!/usr/bin/env python3
"""Compare АДСИС REAL output with exact values captured at entry 75474."""
from decimal import Decimal, ROUND_HALF_UP, localcontext
import json
from pathlib import Path
import re


def real_value(word):
    mantissa = word & ((1 << 41) - 1)
    if mantissa & (1 << 40):
        mantissa -= 1 << 41
    return Decimal(mantissa) * Decimal(2) ** ((word >> 41) - 104)


def scientific(value, digits):
    """One leading digit, half-up rounding of the exact binary input."""
    sign = '-' if value < 0 else ''
    value = abs(value)
    exponent = value.adjusted() if value else 0
    mantissa = value.scaleb(-exponent).quantize(
        Decimal(1).scaleb(-digits), rounding=ROUND_HALF_UP)
    if mantissa == 10:
        exponent += 1
        mantissa /= 10
    return sign + f'{mantissa:.{digits}f}Е{exponent:+03d}'


def audit(directory):
    directory = Path(directory)
    rows = [re.findall(r'\[([^]]*)\]', line)
            for line in (directory / 'real-print.out').read_text().splitlines()
            if line.startswith('[')]
    assert len(rows) == 38 * 9 * 2, len(rows)
    assert rows[:len(rows)//2] == rows[len(rows)//2:], 'OUTPUT and TEXT differ'
    words = []
    for line in (directory / 'real-print.trace').open():
        m = re.match(r'^75474: ntr .* acc=([0-7]{16})', line)
        if m:
            words.append(int(m[1], 8))
    assert len(words) == 38 * 20, len(words)
    for i in range(38):
        assert len(set(words[20*i:20*i+20])) == 1, (i, 'input changed between formats')
    formats = [(0,0),(1,1),(10,3),(20,6),(26,10),(26,11),(20,-1),(0,10)]
    # Observed defects of the unchanged image, kept separate from the oracle.
    lost_words = {'0056603622476666','0061174155301112',
                  '0210000000000000','0160000000000000',
                  '0050000000000000','0010000000000000'}
    results = []
    with localcontext() as context:
        context.prec = 100
        half = len(rows)//2
        for channel, part in zip(('OUTPUT','TEXT'), (rows[:half], rows[half:])):
            for row_index, fields in enumerate(part):
                index, form = divmod(row_index, 9)
                assert int(fields[0]) == index + 1
                word = words[index * 20]
                value = real_value(word)
                if form < 8:
                    width, requested = formats[form]
                    assert fields[1:3] == [str(width),str(requested)]
                    fields_and_formats = [(fields[3], width, requested)]
                else:
                    fields_and_formats = [(fields[1],14,4),(fields[2],20,4)]
                for actual, width, requested in fields_and_formats:
                    digits = min(10,max(1,requested))
                    number = scientific(value,digits)
                    # The explicit positive sign position takes one space.
                    expected = number.rjust(max(8,width,digits+7))
                    results.append(dict(channel=channel,case=index+1,
                        word=f'{word:016o}',value=str(value),width=width,
                        precision=requested,expected=expected,actual=actual,
                        digits_match=actual.strip()==number,
                        field_match=actual==expected))
                    observed = number
                    if f'{word:016o}' in lost_words or value == 0:
                        observed = ('-' if value < 0 else '') + \
                            f'{Decimal(0):.{digits}f}Е+17'
                    assert actual.strip() == observed, results[-1]
                    # The padding loop emits an extra space when the
                    # requested field can hold the sign, digits and exponent.
                    observed_width = max(max(8,width)+1,digits+7)
                    assert actual == observed.rjust(observed_width), results[-1]
    report = dict(values=38,conversions=len(results),
        numeric_mismatches=sum(not r['digits_match'] for r in results),
        lost_nonzero_conversions=sum(Decimal(r['value']) != 0 and not r['digits_match'] for r in results),
        padding_mismatches=sum(len(r['actual']) != len(r['expected']) for r in results),
        field_mismatches=sum(not r['field_match'] for r in results),results=results)
    assert report['numeric_mismatches'] == 140, report['numeric_mismatches']
    assert report['lost_nonzero_conversions'] == 120, report['lost_nonzero_conversions']
    assert report['padding_mismatches'] == 684, report['padding_mismatches']
    (directory / 'real-print.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report


if __name__ == '__main__':
    report = audit(Path(__file__).resolve().parents[1] / 'build/adsis-probes')
    print({k:v for k,v in report.items() if k!='results'})
