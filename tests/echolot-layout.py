#!/usr/bin/env python3
"""Track original ЭХОЛОТ frames and the recovered procedure prefix.

Instruction fields come from disbesm6. Static seeds do not imply execution.
All recovered procedures must retain their original starts and sizes. Raw command differences remain in the report.
"""
from pathlib import Path
import re
import subprocess

ENTRIES = tuple(int(v, 8) for v in '''
540 552 560 577 676 1030 1057 1136 1177 1256 1302 1314 1332 1401
1427 1445 1470 2015 2027 2066 2102 2131 2156 2206 2233 2260 2276
2463 3316 3327 3346 3520 3671 3735 4354 5245 5454 5465 5725 5743
6114 6137
'''.split())
RECOVERED = ('BindInput', 'SkipPromptSpaces', 'SetCodeFile',
             'ReadArrayAddress', 'ReadRequest', 'FindReturn',
             'IsPrologue', 'ReadCodeBounds', 'PrintField',
             'TrimName', 'AddAddress', 'SkipThrough', 'Diagnostic',
             'NewIdentifier', 'NewConstant', 'NewBuiltin', 'InitHistorical',
             'AddExponent', 'PutLiteral', 'Digraph', 'ScanError',
             'OctalEscape', 'ReadIdentifier', 'SkipComment', 'ReadBound',
             'ReadSwitch', 'OptionComment', 'ScanToken', 'PoolWord',
             'Chain', 'TypeCheck', 'ScalarConstant',
             'BitWidth', 'Fields', 'ParseType', 'FormalParams',
             'SkipParameters', 'ProgramHeader', 'RememberCall', 'ScanBody', 'PruneHash', 'analyze')


def parse_instructions(listing):
    instructions = {}
    address = None
    for line in listing.splitlines():
        word = re.match(r'^([ 0-7]{5})[: ](.*)$', line)
        if word and word[1].strip():
            address, half, tail = int(word[1], 8), 0, word[2]
        elif line.startswith('      ') and address is not None:
            half, tail = 1, line[6:]
        else:
            continue
        fields = re.match(r'\s*([0-7]{2}) ([0-7]{2,3}) ([0-7]{4,5})\s', tail)
        if fields:
            # Opcode width distinguishes the short and long formats.
            instructions[address, half] = (*[int(v, 8) for v in fields.groups()],
                                           len(fields[2]) == 2)
    return instructions


def inspect(path, disassembler, directory):
    path = Path(path)
    end = int.from_bytes(path.read_bytes()[30:36], 'big')
    seeds = directory / (path.stem + '-layout.entries')
    seeds.write_text(''.join(f'{i:05o}:\n' for i in range(0o11, end)))
    listing = subprocess.run([disassembler, '-b', '-a0', '-e7',
                              '--trace=' + str(seeds), str(path)],
                             text=True, capture_output=True, check=True).stdout
    (directory / (path.stem + '-layout.lst')).write_text(listing)
    instructions = parse_instructions(listing)
    main = instructions[0o10, 1][2]
    helpers = {a for (a, h), op in instructions.items()
               if a > main and h == 0 and op == (0, 0o37, 3, False)
               and instructions.get((a, 1)) == (0, 0o42, 0o13, False)
               and instructions.get((a + 1, 0)) == (0o17, 0o44, 0o13, False)}
    # The main program calls the file initializer with M14. Its address is the
    # code boundary; literal words can otherwise mimic an inline prologue.
    code = min(op[2] for (a, h), op in instructions.items()
               if main <= a < min(helpers) and op[:2] == (0o14, 0o31)
               and op[3] and op[2] < main)
    entries = set()
    for (a, h), op in instructions.items():
        if not code <= a < main:
            continue
        if op[:2] == (0o14, 0o31) and op[3] and op[2] in helpers:
            entries.add(a)
        if (h == 0 and op == (0, 0o43, 0o13, False)
                and instructions.get((a + 1, 0)) == (0, 0o37, 3, False)):
            entries.add(a)
    return sorted(entries), main, end, instructions


def compare_layout(original, generated, disassembler, directory):
    directory = Path(directory)
    old, main, end, oi = inspect(original, disassembler, directory)
    new, new_main, new_end, ni = inspect(generated, disassembler, directory)
    assert tuple(old) == ENTRIES, 'original ЭХОЛОТ prologues were not recognized'
    assert len(new) == len(RECOVERED)
    rows = []
    old_binary, new_binary = Path(original).read_bytes(), Path(generated).read_bytes()
    for i, name in enumerate(RECOVERED):
        a, b = old[i], new[i]
        size = (old + [main])[i + 1] - a
        new_size = (new + [new_main])[i + 1] - b
        differences = []
        for offset in range(min(size, new_size)):
            for half in (0, 1):
                before, after = oi.get((a + offset, half)), ni.get((b + offset, half))
                if before != after:
                    differences.append(dict(original=f'{a+offset:05o}:{half}',
                                            generated=f'{b+offset:05o}:{half}',
                                            before=before, after=after))
        # Frame slots and VTM M12 (allocation lengths / string widths) do not
        # relocate. A changed NEW length could otherwise pass a shape check.
        fixed_differences = []
        global_differences = []
        global_references = 0
        literal_differences = []
        literal_addresses = []
        code_target_differences = []
        for offset in range(min(size, new_size)):
            for half in (0, 1):
                before, after = oi.get((a + offset, half)), ni.get((b + offset, half))
                if before is None or after is None:
                    continue
                reg, opcode, target, long = before
                previous = oi.get((a + offset, 0)) if half else oi.get((a + offset - 1, 1))
                modified = previous is not None and previous[3] and previous[1] in (0o20, 0o23)
                # M1 is the global frame. Include UTC/WTC and array biases:
                # these are physical offsets, even after an address modifier.
                if reg == 1:
                    global_references += 1
                    if before != after:
                        global_differences.append(f'{a+offset:05o}:{half}')
                fixed = (reg in (2, 3, 4, 5) and not long
                         and opcode in (0, *range(0o4, 0o20)))
                # A zero-register read after UTC/WTC uses C: its operand is
                # a record offset, not an address in the literal pool.
                fixed |= modified and reg == 0 and not long and opcode in (0, *range(0o4, 0o20))
                fixed |= reg == 0o12 and long and opcode == 0o24
                if fixed and before != after:
                    fixed_differences.append(f'{a+offset:05o}:{half}')
                # Direct reads from the literal pool must retain the word value.
                if (not modified and reg in (0, 0o10) and not long and opcode in range(0o4, 0o20)
                        and 0o11 <= target < 0o531):
                    new_target = after[2]
                    if new_target != target:
                        literal_addresses.append(f'{a+offset:05o}:{half}')
                    if not (0o11 <= new_target < new[0] and
                            old_binary[target*6:target*6+6] ==
                            new_binary[new_target*6:new_target*6+6]):
                        literal_differences.append(f'{a+offset:05o}:{half}')
                # WRITE/BIND also pass literal addresses through index registers.
                if long and opcode == 0o24 and reg in (0o11, 0o13, 0o15) and 0o11 <= target < 0o531:
                    if after[2] != target:
                        literal_addresses.append(f'{a+offset:05o}:{half}')
                # Recovered code is contiguous and preserves halfword layout.
                # Check local branches, jump-table entries and recovered calls.
                code_reference = long and opcode in (0o26, 0o27, 0o30, 0o31,
                                                     0o34, 0o35, 0o37)
                code_reference |= long and opcode == 0o24 and reg in (0o15, 0o16)
                if code_reference and old[0] <= target < main:
                    if after[2] != new[0] + target - old[0]:
                        code_target_differences.append(f'{a+offset:05o}:{half}')
        rows.append(dict(name=name, original_start=f'{a:05o}',
                         generated_start=f'{b:05o}', original_words=f'{size:04o}',
                         generated_words=f'{new_size:04o}', size_match=size == new_size,
                         instruction_shapes_match=size == new_size and all(
                             d['before'] is not None and d['after'] is not None
                             and d['before'][:2] == d['after'][:2]
                             and d['before'][3] == d['after'][3] for d in differences),
                         global_operands_match=not global_differences,
                         global_operand_differences=global_differences,
                         global_reference_count=global_references,
                         fixed_operands_match=not fixed_differences,
                         fixed_operand_differences=fixed_differences,
                         literal_values_match=not literal_differences,
                         literal_value_differences=literal_differences,
                         literal_addresses_match=not literal_addresses,
                         literal_address_differences=literal_addresses,
                         code_targets_match=not code_target_differences,
                         code_target_differences=code_target_differences,
                         raw_instruction_differences=differences))
    # Independently check the mode capture, block state and LABEL entry.
    # Keep the M10 -> M0 literal-base difference visible and narrowly bounded.
    entry_words = 0o6232 - 0o6137
    entry_differences = []
    for offset in range(entry_words):
        for half in (0, 1):
            before = oi.get((old[-1] + offset, half))
            after = ni.get((new[-1] + offset, half))
            expected = before
            if before and before[3] and before[0] == 0 and before[1] in (0o26, 0o27, 0o30):
                if old[-1] <= before[2] <= old[-1] + entry_words:
                    expected = (*before[:2], new[-1] + before[2] - old[-1], before[3])
            if after != expected:
                entry_differences.append(dict(original=f'{old[-1]+offset:05o}:{half}',
                                              generated=f'{new[-1]+offset:05o}:{half}',
                                              before=before, after=after))
    entry = dict(original_start=f'{old[-1]:05o}', generated_start=f'{new[-1]:05o}',
                 words=f'{entry_words:04o}', exact_after_relocation=not entry_differences,
                 differences=entry_differences,
                 matches_except_literal_base=not entry_differences or entry_differences == [dict(
                     original='06145:1', generated=f'{new[-1]+6:05o}:1',
                     before=(0o10, 0o11, 0o13, False), after=(0, 0o11, 0o13, False))])
    def main_end(table, start):
        return min(a for (a, half), op in table.items()
                   if a > start and half == 0 and op == (0o13, 0o44, 3, False)
                   and table.get((a, 1)) == (3, 0o10, 2, False))
    old_tail, new_tail = main_end(oi, main), main_end(ni, new_main)
    main_layout = dict(original_start=f'{main:05o}', generated_start=f'{new_main:05o}',
                       original_words=f'{old_tail-main:04o}', generated_words=f'{new_tail-new_main:04o}',
                       start_match=main == new_main, size_match=old_tail-main == new_tail-new_main,
                       helper_words_match=end-old_tail == new_end-new_tail,
                       original_helpers=f'{old_tail:05o}', generated_helpers=f'{new_tail:05o}')
    return dict(analyze_entry=entry, main_layout=main_layout, recovered=rows, recovered_sizes_match=all(r['size_match'] for r in rows),
                recovered_instruction_shapes_match=all(r['instruction_shapes_match'] for r in rows),
                recovered_starts_match=all(r['original_start'] == r['generated_start'] for r in rows),
                recovered_literal_addresses_match=all(r['literal_addresses_match'] for r in rows),
                recovered_global_operands_match=all(r['global_operands_match'] for r in rows),
                recovered_global_reference_count=sum(r['global_reference_count'] for r in rows),
                recovered_fixed_operands_match=all(r['fixed_operands_match'] for r in rows),
                recovered_literal_values_match=all(r['literal_values_match'] for r in rows),
                recovered_code_targets_match=all(r['code_targets_match'] for r in rows),
                original_procedures=[dict(start=f'{a:05o}', words=f'{b-a:04o}')
                                     for a, b in zip(old, old[1:] + [main])],
                generated_procedure_count=len(new), original_procedure_count=len(old),
                original_main=f'{main:05o}', generated_main=f'{new_main:05o}',
                original_end=f'{end:05o}', generated_end=f'{new_end:05o}')


def compare_code(original, generated, disassembler, directory, december=False):
    directory = Path(directory)
    old, _, end, before = inspect(original, disassembler, directory)
    _, _, new_end, after = inspect(generated, disassembler, directory)
    seeds = directory / 'adsis.entries'
    seeds.write_text(''.join(f'{a:05o}:\n' for a in range(0o74000, 0o74100)))
    image = Path(__file__).resolve().parents[1] / 'images/2248/АДСИС.bin'
    listing = subprocess.run([disassembler, '-b', '-a74000', '--trace='+str(seeds), str(image)],
                             text=True, capture_output=True, check=True).stdout
    (directory / 'adsis-vectors.lst').write_text(listing)
    vectors = {a: op[2] for (a, half), op in parse_instructions(listing).items()
               if half == 0 and 0o74000 <= a < 0o74100 and op[:2] == (0, 0o30) and op[3]}
    differences, runtime, literals, cases = [], [], [], []
    for address in range(0o531, end):
        for half in (0, 1):
            x, y = before.get((address, half)), after.get((address, half))
            if x == y:
                continue
            item = dict(address=f'{address:05o}:{half}', original=x, generated=y)
            if (x and y and x[:2] == y[:2] and x[3] == y[3] and x[3]
                    and x[1] in (0o26, 0o27, 0o30, 0o31, 0o34, 0o35)
                    and vectors.get(x[2]) == y[2]):
                runtime.append(item)
            elif (item['address'] in ('06145:1', '07445:0', '07445:1', '07446:0')
                  and x[0] == 0o10 and y[0] == 0 and x[1:] == y[1:]):
                literals.append(item)
            elif (december and x[0] == 0 and y[0] == 0o10 and x[1] == 0o30
                  and x[1:] == y[1:]):
                cases.append(item)
            else:
                differences.append(item)
    return dict(start='00531', end=f'{end:05o}', sizes_match=end == new_end,
                runtime_vector_aliases=runtime, literal_base_differences=literals,
                case_base_differences=cases, unexpected_differences=differences)


def compare_compilers(may, december, disassembler, directory):
    """Compare equal-source compiler outputs using disbesm6 instruction fields."""
    _, _, _, mi = inspect(may, disassembler, directory)
    _, _, _, di = inspect(december, disassembler, directory)
    first, second = Path(may).read_bytes(), Path(december).read_bytes()
    assert len(first) == len(second)
    differences = []
    only_case_bases = True
    for address in range(len(first) // 6):
        if first[address*6:address*6+6] == second[address*6:address*6+6]:
            continue
        instructions = []
        for half in (0, 1):
            before, after = mi.get((address, half)), di.get((address, half))
            if before != after:
                instructions.append(dict(half=half, may=before, december=after))
                only_case_bases &= bool(before and after and before[0] == 0
                                        and after[0] == 0o10 and before[1] == 0o30
                                        and before[1:] == after[1:])
        only_case_bases &= bool(instructions)
        differences.append(dict(address=f'{address:05o}', instructions=instructions))
    return dict(differing_words=len(differences), only_case_bases=only_case_bases,
                differences=differences)
