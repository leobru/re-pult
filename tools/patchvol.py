#!/usr/bin/env python3
# Build a patched copy of a system volume for running ПУЛЬТ under dispak.
#
# usage: tools/patchvol.py PATCHES SRC DST
#   PATCHES  lines "zone word old new  comment": zone and word in octal, old
#            and new as 12 hex digits (one 48-bit word, as besmtool dump
#            prints it); '#' starts a comment line
#   SRC      source volume number (read from /usr/local/share/besm6)
#   DST      output volume file, e.g. ~/.besm6/2250
# Every old value is checked before anything is written.
import os, shutil, subprocess, sys, tempfile

patches, src, dst = sys.argv[1:4]
todo = []
for line in open(patches):
    f = line.split()
    if not f or f[0].startswith('#'):
        continue
    todo.append((int(f[0], 8), int(f[1], 8), bytes.fromhex(f[2]), bytes.fromhex(f[3])))

# besmtool finds a volume by its number, so patch DST in place and remove
# it if a check fails.
shutil.copyfile(os.path.join('/usr/local/share/besm6', src), dst)
os.chmod(dst, 0o644)
vol = os.path.basename(dst)
with tempfile.TemporaryDirectory() as d:
    for z in sorted({t[0] for t in todo}):
        f = os.path.join(d, 'z')
        run = dict(cwd=os.path.dirname(dst), check=True, stdout=subprocess.DEVNULL)
        subprocess.run(['besmtool', 'dump', vol, '--start=0%o' % z, '--length=1',
                        '--to-file=' + f], **run)
        b = bytearray(open(f, 'rb').read())
        for zz, w, old, new in todo:
            if zz != z:
                continue
            if b[w*6:w*6+6] != old:
                os.remove(dst)
                sys.exit('zone %o word %o: %s, expected %s' % (z, w, b[w*6:w*6+6].hex(), old.hex()))
            b[w*6:w*6+6] = new
        open(f, 'wb').write(b)
        subprocess.run(['besmtool', 'write', vol, '--start=0%o' % z, '--from-file=' + f], **run)
