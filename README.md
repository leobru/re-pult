# re-pult

Disassembly of ПУЛЬТ, the interactive programming system of the BESM-6, as
found in the catalog at zone 01000 of the system volumes 2248 and 2148.

## Manuals

Proofread transcriptions of both scanned manuals are kept in Markdown:

- [Structure and maintenance](doc/PULT.md), from `PULT.pdf`.
- [User guide](doc/PULT-User.md), from `PULT-User.pdf`.

Each has a PDF-page index, separate left/right sides for book spreads, and
links back to the scans. Transcription notes mark ambiguous source text.
Use `rg` on these files before rendering the PDF again. Edit the Markdown
files directly. The original OCR tool, `python3 tools/pdfmanual.py` (Poppler,
Tesseract with `rus+eng`, and Pillow), writes raw OCR to `build/manuals/ocr/`.

The address-level analysis of ПУСК is in [doc/pusk.md](doc/pusk.md).
The command loop, parsers and terminal formatter in НАБЛ are described in
[doc/nabl.md](doc/nabl.md).
The resident services and scanner in СБОЙ are described in
[doc/sboy.md](doc/sboy.md).
The ДАЙ service monitor, its 15 subcommands and ФОРТ extracode handler are
described in [doc/dai.md](doc/dai.md).
The Pascal runtime АДСИС, its entry vector, files and memory are described in
[doc/adsis.md](doc/adsis.md).
The ALGOL `_БИБ` lookup and all 182 standard-library names, addresses and
dependencies are described in [doc/algol-library.md](doc/algol-library.md).
The extracted УППBULLM20 card-package converter and its damaged prefix are
analysed in [doc/upp-bullm20.md](doc/upp-bullm20.md).
The ALGOL NEW/НОВ interfaces to БАНДИТ, their name conversion and error
handlers are described in [doc/algol-new.md](doc/algol-new.md).

## Requirements

- `dispak` and `besmtool` (<https://github.com/besm6/dispak>), with volumes
  2248 and 2148 where the tools find them
- `disbesm6` from `~/git/leobru/dispak-tools` (set `DIS=` to override)
- Python 3

## Usage

```sh
make            # extract images, trace sessions/*.txt, write build/*.lst
make diff       # catalog entries that differ between 2148 and 2248
make pusk       # static ПУСК listing and full zone dump, without dispak
make nabl       # static НАБЛ listing at 056000 and full source zone dump
make sboy       # static СБОЙ listing at 076000 and full source zone dump
make dai        # static ДАЙ listing, including batch-job and ФОРТ code
make adsis      # static АДСИС listing at 074000 and full source zone dump
make checkadsis # Pascal runtime, file-boundary and error-path checks on private disks
tools/catalog.py 2248              # print the ПУЛЬТ catalog
tools/loads.sh < sessions/лес.txt  # exchanges (Э70) of a session
tools/findpage.py 2148 2248        # zones resembling page 37
```

`images/<vol>/<NAME>.bin` holds each catalog entry (and `<NAME>+<k>.bin`
for each zone of a multi-zone entry). `build/<NAME>.lst` is its listing at
the address where it runs, seeded with the addresses it executed in the
sessions. See AGENTS.md for what is known so far.
`make pusk`, `make nabl`, `make sboy`, `make dai` and `make adsis`
instead use explicit static entries and data
boundaries from their symbol files.

## Volume 2068

The relocated ПУЛЬТ and Pascal archives are built here, independently of the
emulator build. See [the zone comparison and repair report](doc/volume2068.md).

```sh
make 2068                         # build/volumes/2068 and 2068.json
make check2068                    # isolated integration tests
make checksegments                # Pascal LOAD/UNLOAD and relocation
make pult2068                     # interactive session with writable private copies
make pult2068 SYSTEM_VOLUME=2148  # use 2148 for the system volume instead
make install2068                  # install image/provenance in ~/.besm6 if absent
```

Set `DISPAK=/path/to/dispak` to use a local emulator build and
`SOURCE_DISKS=/path/to/disks` to select source images (default
`/usr/local/share/besm6`). The emulator needs the small-disk wrapping and
Э72 scratch-unit switching fixes from `~/git/dispak`. `pult2068.b6` mounts
2068 without an offset on unit 40, and system volume 2248 on unit 57 at
offset 0371. `SYSTEM_VOLUME=2148` selects 2148 with the same offset.
ПАСК retains its original unit-57 assembler descriptor: zones 007–013
resolve to system-volume zones 0400–0404.
Set `INSTALL_DISKS` to override the installation directory.
The original `pult.b6` and 2250 workflow remain available.

The [Pascal segmentation test](doc/pascal-segments.md) uses a temporary
compatibility loader, exercises external calls in both directions, unloads
and reloads at a different address, and restores the original resident.
