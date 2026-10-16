#!/usr/bin/env python3
# Split a full dispak instruction trace (dispak -t -t) of a ПУЛЬТ session into
# per-image traces.
#
# Every Э70 exchange in the trace is followed to know which catalog image
# occupies each page: a read of unit 40 zone Z puts that catalog entry
# (images-<vol>.txt) in the page; a write of a page to another unit (the
# drum, unit 27) remembers the owner there, and reading it back restores it.
# Each executed address ("AAAAA:" or "AAAAA;" lines) is credited to the owner
# of its page, translated to the image's own load address.
#
# usage: dispak -t -t -q pult.b6 < s.txt 2>&1 | tools/phasetrace.py OUTDIR [images-2248.txt]
# An entry whose zones run in unrelated pages (e.g. РЕЗРВ1, a pool of
# overlays) is split into pieces <NAME>+<k>, one per zone index k.
# Writes OUTDIR/<NAME>.trace ("AAAAA: coverage" lines, for disbesm6 --trace)
# and OUTDIR/<NAME>.load (the address it runs at: the page where its lowest
# executed zone ran most); prints a summary.
import os, re, sys

out = sys.argv[1]
cat = sys.argv[2] if len(sys.argv) > 2 else 'images-2248.txt'
zones = {}                                # unit-40 zone -> (name, index)
for line in open(cat):
    name, z, n = line.split()
    z, n = int(z, 8) - 0o1000, int(n, 8)
    for k in range(n):
        zones[z + k] = (name, k)

page = {}                                 # page -> (name, index)
store = {}                                # (unit, zone) -> (name, index)
seen = {}                                 # name -> {page: set(offsets)}
first = {}                                # name -> {index: page}
rx70 = re.compile(r'^\s*([0-7]{5}): \*70 \S+\s+\(=([0-7]{16})\)')
# Executed instructions. `dispak -t -t` also prints indented
# "      AAAAA: store ..." lines for memory writes; they must not count.
rxpc = re.compile(r'^\s*([0-7]{5})[:;] (?!store )')
for line in sys.stdin:
    m = rx70.match(line)
    if m:
        d = m.group(2)
        read, p = d[2] == '1', int(d[4:6], 8)
        unit, z = int(d[10:12], 8), int(d[12:16], 8)
        if read:
            if unit == 0o40 and z in zones:
                page[p] = zones[z]
                first.setdefault(zones[z][0], {})[zones[z][1]] = p
            else:
                page[p] = store.get((unit, z))
        else:
            store[(unit, z)] = page.get(p)
        continue
    m = rxpc.match(line)
    if m:
        a = int(m.group(1), 8)
        o = page.get(a >> 10)
        if o:
            seen.setdefault(o[0], {}).setdefault(o[1], {}).setdefault(a >> 10, set()).add(a & 0o1777)

def emit(name, base, addrs):
    with open('%s/%s.trace' % (out, name), 'w') as f:
        for a in sorted(addrs):
            f.write('%05o: coverage\n' % a)
    open('%s/%s.load' % (out, name), 'w').write('%o\n' % base)
    print('%-9s load %05o  %5d addresses' % (name, base, len(addrs)))

os.makedirs(out, exist_ok=True)
for name, parts in sorted(seen.items()):
    # each zone index runs mostly in one page; the image runs at
    # (that page - index) if this is the same for all its executed zones
    main = {k: max(pages, key=lambda p: len(pages[p])) for k, pages in parts.items()}
    moved = {k: ' '.join('%02o' % p for p in sorted(pages))
             for k, pages in parts.items() if len(pages) > 1}
    if moved:
        print('  %s: zone index ran in several pages %s' % (name, moved))
    bases = {main[k] - k for k in main}
    if len(bases) == 1 and min(bases) >= 0:
        base = min(bases) * 0o2000
        emit(name, base, {base + k * 0o2000 + off for k, pages in parts.items()
                          for offs in pages.values() for off in offs})
    else:
        # independent overlays inside one catalog entry: one piece per zone,
        # images/<vol>/<NAME>+<k>.bin (tools/extract.py)
        for k, pages in parts.items():
            base = main[k] * 0o2000
            emit('%s+%o' % (name, k), base,
                 {base + off for offs in pages.values() for off in offs})
