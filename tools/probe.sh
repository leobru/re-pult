#!/bin/sh
# Run each command line given as an argument in its own ПУЛЬТ session
# ("<line>" then "конец") and show what it did: the Э70 exchanges after boot
# and before the final reload of ПУСК by `конец`, and the terminal output.
# usage: tools/probe.sh 'арх вася,50,100' 'сис код' ...
# Env: PULT (job, default pult.b6), TIMEOUT (seconds per session, default 30).
for cmd; do
    echo "=== $cmd"
    rm -rf ~/.besm6/input_queue
    printf '%s\nконец\n' "$cmd" |
    timeout ${TIMEOUT:-30} dispak -t -q "${PULT:-pult.b6}" 2>&1 |
    awk '{ line = $0; ex = ""
           if (match(line, /[0-7][0-7][0-7][0-7][0-7]: \*[0-7]+ .*/)) {
               ex = substr(line, RSTART); line = substr(line, 1, RSTART - 1) }
           sub(/^-/, "", line)
           if (line ~ /[^ ]/) out[m++] = "  | " line
           split(ex, f, " ")
           if (f[2] != "*70") next
           d = substr(f[4], 3, 16)
           rw = substr(d, 3, 1) == "1" ? "read " : "write"
           l = sprintf("  %s %s page %s unit %s zone %s", f[1], rw,
                       substr(d, 5, 2), substr(d, 11, 2), substr(d, 13, 4))
           if (booted) loads[n++] = l
           if (f[1] == "00661:") booted = 1 }
         END { # drop the reload of ПУСК by `конец` (НАБЛ 56334)
               if (n && loads[n-1] ~ /^  56334: /) n--
               for (i = 0; i < n; i++) print loads[i]
               for (i = 0; i < m; i++) print out[i] }'
done
