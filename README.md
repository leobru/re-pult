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
The resident-page variants on 2148/2248 and their listings are indexed in
[doc/pult-residents.md](doc/pult-residents.md).
The known and unidentified parts of РЕЗРВ1/РЕЗРВ3, including JINN's МОСТ
and the ВЫЗОВЛ LISP launcher, are listed in [doc/pult-reserves.md](doc/pult-reserves.md).
The remaining programs and partial analyses are indexed in
[doc/pult-remaining.md](doc/pult-remaining.md).
The recovered [BD dispatcher](re-bd.asm) and [BANDIT engine](re-bandit.asm)
reproduce all words of 2148/2248:01026–01027 (`make checkbanditasm`).
[doc/bandit.md](doc/bandit.md) describes the engine, record allocation,
linked fragments, metadata and suspicious MODIFY paths.
`make checkbandit` verifies private database operations and reproduces the
MOD failure; its multiblock scenario explicitly moves the private buffer.
`make bdprivate` builds private BD/BANDIT with a working reverse-copy MOD;
`make checkbdmod` verifies replacement, chained records and error paths
described in [doc/bandit.md](doc/bandit.md).
The March 2025 pasauto-re sources, including ЛЕС/PRETTY, ЛЕНТЯЙ, РРR,
НОВРЕД, КПЕЧ and КБИЛИС, are described in
[doc/pasauto-imports.md](doc/pasauto-imports.md).
`make checknewedt` recompiles the sources and compares original/rebuilt
editor output and saved archive contents.

The UPD database library in 2148:01013–01025 is described in
[doc/upd.md](doc/upd.md). `make upd` extracts eight BEMSH object modules,
their entry tables and 803 surviving source/macro-expansion records.

The recovered [ВЫЗОВЛ Pascal source](pascal/vyzovl.pas) loads Lisp from
unit 66. `make checkvyzovl` compares its code and diagnostic behavior;
[doc/vyzovl.md](doc/vyzovl.md) records two compiler-generated ADSIS differences.
The retained АВТПАК module, its four-zone ITM assembler driver and ПАКЕТ
command-chain interpreter are described in [doc/avtpak.md](doc/avtpak.md).
The ПУЛЬТ launcher generator, its passport templates and generated loader
are described in [doc/pult.md](doc/pult.md). The retained ПУЛЬТФ image
and its unrelated code fragments are examined in [doc/pultf.md](doc/pultf.md).
The АЦПУК output-file viewer, part addressing, character conversion and
formatter compatibility are described in [doc/acpuk.md](doc/acpuk.md).
The БАВТ dispatcher, every command handler, Pascal launch frames and
translator return paths are described in [doc/bavt.md](doc/bavt.md).
The СПИС text reader/editor, commands С/Р, encodings and context search are
described in [doc/spis.md](doc/spis.md).
The ОТЛ debugger, memory commands, symbolic addresses, native execution and
instruction interpreter are described in [doc/otl.md](doc/otl.md).
The ДЖИП/ДЖИН ARFA loader and its Pascal reconstruction with an identical
194-word program image are described in [doc/dzhin.md](doc/dzhin.md).
The ALGOL `_БИБ` lookup and all 182 standard-library names, addresses and
dependencies are described in [doc/algol-library.md](doc/algol-library.md).
The extracted УППBULLM20 card-package converter and its damaged prefix are
analysed in [doc/upp-bullm20.md](doc/upp-bullm20.md).
The ALGOL NEW/НОВ interfaces to БАНДИТ, their name conversion and error
handlers are described in [doc/algol-new.md](doc/algol-new.md).

## Requirements

- `dispak` and `besmtool` (<https://github.com/besm6/dispak>), with volumes
  2248 and 2148 where the tools find them
- `disbesm6` from `dispak-tools` (set `DIS=` to override)
- Python 3

## Usage

```sh
make            # extract images, trace sessions/*.txt, write build/*.lst
make diff       # catalog entries that differ between 2148 and 2248
make checktraces # ALG compilation, timeout/error propagation, private archive checks
make pusk       # static ПУСК listing and full zone dump, without dispak
make nabl       # static НАБЛ listing at 056000 and full source zone dump
make sboy       # static СБОЙ listing at 076000 and full source zone dump
make dai        # static ДАЙ listing, including batch-job and ФОРТ code
make adsis      # АДСИС listing at 074000, source-zone dump and code/data map
make checkadsisasm # assemble adsis.be; compare the complete ЗОНГП zone with disk
make pultresidents # find resident variants on 2148/2248 and disassemble distinct images
make pultreserves  # inventory РЕЗРВ1/РЕЗРВ3 and disassemble ВЫЗОВЛ
make avtpak     # old АВТ driver at 052000 and ПАКЕТ reader at 004000
make launchers  # ПУЛЬТ generator and the retained ПУЛЬТФ image
make acpuk      # АЦПУ output-file viewer at 074000
make spis       # С/Р text editor, both pages at 00000–03777
make bavt       # third command dispatcher and launchers at 066000
make otl        # internal debugger at 050000
make dzhin      # Pascal ДЖИП/ДЖИН loader at 00000
make chistka    # Pascal declaration/reference analyzer at 00000
make checkchistka # isolated analysis probes with Pascal source fixtures
make echolot    # Pascal storage-depth analyzer at 00000
make checkecholot # source analysis and matching against freshly compiled code
make struk       # Pascal structure scanner, static listing
make checkstruk  # exact rebuild with both compilers and isolated behavior probes
make checkanalyzers # compile the recovered Pascal sources and run both probe suites
make checkservic # recompile СЕРВИС; compare all three zones with the disk image
make checkadsis # runtime, packed/multiword files, heap, terminal and REAL comparisons
tools/catalog.py 2248              # print the ПУЛЬТ catalog
tools/loads.sh < sessions/лес.txt  # exchanges (Э70) of a session
tools/findpage.py 2148 2248        # zones resembling page 37
```

`images/<vol>/<NAME>.bin` holds each catalog entry (and `<NAME>+<k>.bin`
for each zone of a multi-zone entry). `build/<NAME>.lst` is its listing at
the address where it runs, seeded with the addresses it executed in the
sessions. See AGENTS.md for what is known so far.

Coverage sessions use `build/volumes/2250`, a private HOME and a private
copy of the unit-50 archive. Each run saves `session.log` (instructions)
and `terminal.txt` under `build/t-<session>/`. `TRACE_TIMEOUT` defaults
to 30 seconds; a timeout or emulator/splitter failure stops Make without
creating `.done`. The ALG session creates a file in `сис алг` mode and
compiles it, printing 123. Bare `алг` reads an empty buffer indefinitely.
`make pusk`, `make nabl`, `make sboy`, `make dai`, `make adsis`, `make avtpak`
`make launchers` and `make acpuk`
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
Э72 scratch-unit switching fixes from `dispak`. `pult2068.b6` mounts
2068 without an offset on unit 40, and system volume 2248 on unit 57 at
offset 0371. `SYSTEM_VOLUME=2148` selects 2148 with the same offset.
ПАСК retains its original unit-57 assembler descriptor: zones 007–013
resolve to system-volume zones 0400–0404.
Set `INSTALL_DISKS` to override the installation directory.
The original `pult.b6` and 2250 workflow remain available.

The [Pascal segmentation test](doc/pascal-segments.md) uses a temporary
compatibility loader, exercises external calls in both directions, unloads
and reloads at a different address, and restores the original resident.

The [annotated СЕРВИС source](pascal/servic.pas) reproduces all 3072 words
of the 21.11.88 image on volumes 2148 and 2068. See [the analysis and build
verification](doc/servic.md).

The [ЧИСТКА analysis](doc/chistka.md) describes its Pascal parser, symbol
records, use of routine references and diagnostics, with reproducible probes.

The [ЭХОЛОТ analysis](doc/echolot.md) explains storage estimates for Pascal
call chains, recursion and NEW, plus matching source routines to compiled code.

Readable Pascal sources are in [pascal/chistka.pas](pascal/chistka.pas) and
[pascal/echolot.pas](pascal/echolot.pas). They use the dialect of
`pasauto-re/pretty.pas`. See [the reconstruction status](doc/analyzers-source.md)
for binary differences and the scope of behavioral verification.

The [СТРУК analysis](doc/struk.md) describes the Pascal procedure tree,
source-line ranges, alphabetical listing and disk reports. Its
[restored source](pascal/struk.pas) rebuilds to all 1024 original words
with both historical Pascal compilers.
