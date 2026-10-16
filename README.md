# re-pult

Disassembly of ПУЛЬТ, the interactive programming system of the BESM-6, as
found in the catalog at zone 01000 of the system volumes 2248 and 2148.

## Requirements

- `dispak` and `besmtool` (<https://github.com/besm6/dispak>), with volumes
  2248 and 2148 where the tools find them
- `disbesm6` from `~/git/leobru/dispak-tools` (set `DIS=` to override)
- Python 3

## Usage

```sh
make            # extract images, trace sessions/*.txt, write build/*.lst
make diff       # catalog entries that differ between 2148 and 2248
tools/catalog.py 2248              # print the ПУЛЬТ catalog
tools/loads.sh < sessions/лес.txt  # exchanges (Э70) of a session
tools/findpage.py 2148 2248        # zones resembling page 37
```

`images/<vol>/<NAME>.bin` holds each catalog entry (and `<NAME>+<k>.bin`
for each zone of a multi-zone entry). `build/<NAME>.lst` is its listing at
the address where it runs, seeded with the addresses it executed in the
sessions. See AGENTS.md for what is known so far.
