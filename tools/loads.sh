#!/bin/sh
# Run a ПУЛЬТ session (stdin) under dispak -t and list the exchanges (Э70)
# as "pc: read|write page PP unit UU zone ZZZZ" lines.
# usage: tools/loads.sh [job.b6] < session.txt
rm -rf ~/.besm6/input_queue
timeout ${TIMEOUT:-60} dispak -t -q "${1:-pult.b6}" 2>&1 |
awk '/\*70 / { d = substr($4, 3, 16);
       rw = substr(d, 3, 1) == "1" ? "read " : "write";
       printf "%s %s page %s unit %s zone %s\n", $1, rw, substr(d, 5, 2), substr(d, 11, 2), substr(d, 13, 4) }'
