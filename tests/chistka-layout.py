#!/usr/bin/env python3
"""Check every Pascal procedure boundary in ЧИСТКА against the disk image."""
from pathlib import Path
import re
import subprocess

# Physical entry order includes the nested routines L1034 and L1053.
ENTRIES = tuple(int(v, 8) for v in '''
547 641 657 675 721 730 761 1000 1014 1034 1053 1071 1442 1512 1563
1604 1644 1665 1714 1762 1773 2017 2057 2151 2172 2223 2310 2576
2701 2733 3160 3224 3350 3472 3644 3723 3761 4213 4431 4516 4744
4756 4764
'''.split())


def inspect(path, disassembler, directory):
    """Recognize compiler prologues from instructions decoded by disbesm6."""
    binary = path.read_bytes()
    end = int.from_bytes(binary[30:36], 'big')
    seeds = directory / (path.stem + '-layout.entries')
    # Static decoding only: these seeds are not execution-coverage claims.
    seeds.write_text(''.join(f'{i:05o}:\n' for i in range(0o547, end)))
    result = subprocess.run([disassembler, '-b', '-a0', '-e7',
                             '--trace=' + str(seeds), str(path)],
                            text=True, capture_output=True, check=True)
    (directory / (path.stem + '-layout.lst')).write_text(result.stdout)
    instructions = {}
    address = None
    for line in result.stdout.splitlines():
        word = re.match(r'^([ 0-7]{5})[: ](.*)$', line)
        if word and word[1].strip():
            address, half, tail = int(word[1], 8), 0, word[2]
        elif line.startswith('      ') and address is not None:
            half, tail = 1, line[6:]
        else:
            continue
        decoded = re.match(r'\s*([0-7]{2}) ([0-7]{2,3}) ([0-7]{4,5})\s', tail)
        if decoded:
            instructions[address, half] = tuple(int(v, 8) for v in decoded.groups())
    main = instructions[0o10, 1][2]
    entries = set()
    for (address, half), (reg, opcode, target) in instructions.items():
        # Shared level-2/3 prologues live in the compiler's short final tail.
        if reg == 0o14 and opcode == 0o31 and end - 0o30 <= target < end:
            entries.add(address)
        # Procedures with nonlocal control flow have an inline frame prologue.
        if (half == 0 and (reg, opcode, target) == (0, 0o43, 0o13)
                and instructions.get((address + 1, 0)) == (0, 0o37, 3)):
            entries.add(address)
    entries.discard(main)
    helpers = min(target for reg, opcode, target in instructions.values()
                  if opcode == 0o31 and main < target < end)
    return sorted(entries), main, helpers, end


def compare_layout(original, generated, disassembler, directory):
    directory = Path(directory)
    old, old_main, old_helpers, old_end = inspect(original, disassembler, directory)
    new, new_main, new_helpers, new_end = inspect(generated, disassembler, directory)
    assert tuple(old) == ENTRIES, 'original Pascal prologues were not recognized'
    assert len(new) == len(old), 'rebuilt procedure count differs'
    rows = []
    for i, (before, after) in enumerate(zip(old, new)):
        old_stop = old[i + 1] if i + 1 < len(old) else old_main
        new_stop = new[i + 1] if i + 1 < len(new) else new_main
        rows.append(dict(name=f'L{before:04o}', original_start=f'{before:05o}',
                         generated_start=f'{after:05o}',
                         original_words=f'{old_stop - before:04o}',
                         generated_words=f'{new_stop - after:04o}',
                         size_match=old_stop - before == new_stop - after))
    main = dict(original_start=f'{old_main:05o}', generated_start=f'{new_main:05o}',
                original_words=f'{old_helpers - old_main:04o}',
                generated_words=f'{new_helpers - new_main:04o}',
                size_match=old_helpers - old_main == new_helpers - new_main)
    return dict(procedures=rows, main=main,
                helper_words_match=old_end - old_helpers == new_end - new_helpers,
                all_sizes_match=all(r['size_match'] for r in rows) and main['size_match'],
                all_starts_match=old == new and old_main == new_main,
                original_end=f'{old_end:05o}', generated_end=f'{new_end:05o}')
