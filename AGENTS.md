# re-pult working notes

This project disassembles and documents ПУЛЬТ, the interactive (terminal)
programming system of the BESM-6. The source material is the ПУЛЬТ catalog
at zone 01000 of the system volumes 2248 and 2148.

The BESM-6 instruction set and the opcode notation are described in
<https://raw.githubusercontent.com/besm6/c-compiler/refs/heads/main/docs/Besm6_Instruction_Set.md>.
Extracode 070 (`*70`, Э70) is disk/drum exchange, 071 (`*71`, Э71) is
terminal I/O, and 064 is printing.

## Tools

- Disassembler: `~/git/leobru/dispak-tools/disbesm6`, built from
  `disbesm6.cc`. It is newer than `/usr/local/bin/disbesm6`. Ignore the old
  `~/git/besm6/dispak/disbesm6/disbesm6.c`.
  - Options: `-b -aLOAD -eENTRY` (`-e` may be repeated), `--trace=FILE`
    (each `<octal>:` line seeds a code entry), `-n SYMFILE`.
  - Symbol lines are `<addr|lo-hi> <type> <name|-> [entry ...]`. Types:
    D data, C code, B code entry, A code never executed, J jump table (seeds
    entries, printed as конк), K конк without seeding, G GOST text, T text,
    I ISO, M/N ITM, H hex, L literal, R real, U unset.
- To read code in a zone quickly, use `besmtool dump VOL --start=Z --length=N`
  without `--to-file`. It prints octal, hex and both instructions decoded.
  Don't write ad-hoc decoders.
- `dispak --coverage` only maps addresses ≥ 01000. Use `dispak -t -t`, whose
  `AAAAA:` / `AAAAA;` lines include page 0. `tools/phasetrace.py` turns such a
  trace into per-image traces.
- Text in the catalog and in ПУЛЬТ messages is GOST 10859 (`tools/gost.py`).
  The Pascal side keeps its own strings in ITM code.
- dispak `Э50 7700` is "set alarm": with an ordinary A it **sleeps**
  (A & 077777) × 80 ms. Garbage in A looks like a hang. Wrap runs in `timeout`.
- dispak runs share `~/.besm6/input_queue`; remove it before each session
  and never run two sessions at once.

## Build

`make` extracts the images, runs every `sessions/*.txt` under `dispak -t -t`,
splits the trace per catalog image and disassembles each image that
executed, at the address it runs at, into `build/<NAME>.lst`. `syms/<NAME>.sym`
is used when it exists. Add sessions to widen coverage. Add symbols and
notes as routines are understood. `build/` is reproducible, so don't edit it.

## Volumes and the job

- Images are in `/usr/local/share/besm6` (2148, 2248). Private or modified
  copies go in `~/.besm6` (e.g. 2249, below).
- `pult.b6` (from pasauto-re's `pult2.b6`) maps `лент 40(2248-1000)` and
  `лент 57(2248-1000)`, so unit 40 zone N = 2248 zone 01000+N. It reads unit
  40 zone 040 into page 0 and jumps to 040. Sessions are fed on stdin, e.g.
  `арх вася,50,100`, `пас нов`, `конец`.
- Zone 01000 on both volumes holds the same catalog. Every code entry is
  identical between 2148 and 2248. Entries that differ (`make diff`): СБОЙ
  (3 run-state words: 76012, 76312-3), КТЛБИБ (12), ПАСК (3), АВТПАК (1),
  and heavily РЕЗРВ1 (first 5 zones), СЕРВИС, РЕЗРВ2.

## Catalog (zone 01000)

Word 0 is the header `СИСБИБ`. Then come pairs of (6-char GOST name) and
(start zone << 24 | length), with zones relative to 01000. The list ends
with a zero word. `tools/catalog.py` prints it.

| name | zone | len | known role / load page (from traces) |
|---|---|---|---|
| РРR | 001 | 1 | |
| ПУЛЬТ | 002 | 1 | |
| АЦПУК | 003 | 1 | |
| ПУЛЬТФ | 004 | 1 | |
| ДАЙ | 005 | 1 | `дай` command, page 0 |
| АДСИС | 006 | 1 | Pascal runtime library, page 36 (074000); the compiler's ИА=74000 table |
| РЕЗРВ1 | 007 | 22 | pool of overlays (zone 015 runs in page 0 for `алг`); per-zone pieces `РЕЗРВ1+k` |
| СЕРВИС | 031 | 3 | `сервис`, Pascal program, pages 0-2 (+АДСИС) |
| ПАСЛ | 034 | 1 | saved state ("ЛЕНТЯЙ…РАSСАL…" text) |
| СБОЙ | 035 | 1 | **page 37 (076000)**, resident ПУЛЬТ services |
| ЗГЛВК | 036 | 1 | read into page 1 at boot, apparently never executed |
| КТЛБИБ | 037 | 1 | library catalog (data) |
| ПУСК | 040 | 1 | **page 0**, boot and resident kernel |
| НАБЛ | 041 | 1 | read into page 1, copied via drum 27 track 37 to **page 27 (056000)**: command loop (terminal Э71 at 56514/56550/56053) |
| АЛГ | 042 | 2 | `алг`: zone 042 → page 1, 043 → page 33 |
| СЛУЖ | 044 | 1 | |
| СПИС | 045 | 2 | |
| АВТПАК | 047 | 1 | |
| ПАСК | 050 | 1 | ПАСКАЛ (Pascal-autocode driver), page 33 (066000) |
| БАВТ | 051 | 1 | page 33. Runs first for `пас` and for any name ПУЛЬТ itself doesn't know (then reads unit 40 zone 0240 into page 34) |
| ОТЛ | 052 | 3 | |
| ЛЕС | 055 | 3 | `лес`, Pascal program, pages 0-2 |
| ЧИСТКА | 060 | 3 | `чистка`, Pascal program, pages 0-2 |
| СТАТИС | 063 | 1 | `статис`, page 0 |
| ЭХОЛОТ | 064 | 4 | `эхолот`, Pascal program, pages 0-3 |
| ДЖИП | 070 | 1 | |
| РЕЗРВ2 | 071 | 2 | |
| СТРУК | 073 | 1 | `струк`, Pascal program, pages 0-1 |
| РЕЗРВ3 | 074 | 1 | |
| НОВРЕД | 075 | 3 | |

The commands `спис`, `отл`, `джип`, `новред`, `служ`, `пуск` and `автпак`
are not recognized under those names; they fall through to БАВТ and the
zone-0240 library. The command names that load these entries are still
unknown.

## Boot (trace of `конец`)

```
02000 Э70 read  page 00 ← u40 z040 (ПУСК)      job loader, then пб 40
00324 Э70 read  page 37 ← u40 z035 (СБОЙ)
00062 Э70 read  page 01 ← u40 z036 (ЗГЛВК)
00477 Э70 read  page 01 ← u40 z041 (НАБЛ)
00503 Э70 write page 01 → u27 z037             drum 27 track 37
00561/00606 read/write page 01 ↔ u27 z037
00607 Э70 write page 37 → u27 z031             saves page 37 on the drum
00661 Э70 read  page 27 ← u27 z037             НАБЛ now runs at 056000
56334 Э70 read  page 00 ← u40 z040             reload ПУСК at the end
```

The exchange descriptor is `0 0 1|0 0 PP 0 0 | 0 0 UU ZZZZ` in octal
digits: digit 2 = 1 means read, digits 4-5 are the page, digits 10-11 the
unit and 12-15 the zone (see `tools/loads.sh`).

## Page 37 (СБОЙ) services

These are used by ПАСКАЛ, compiled Pascal programs and the loader:

- 76000 пб 76127 (restart), 76001, 76002 exit to ПУЛЬТ, 76003 пб 76066,
  76004 пб 76074, 76005 print, 76006 read zones (parameter block
  77770-77774), 76007 пб 76104, 76010 пб 76100.
- 76015 argv (ржа 0; пб 77031), 76016 command-line parse (ржа 0;
  пб 77043; the parse body is 77043-77073 and calls 77162, 77313).
- 76066 save registers, 76074 restore registers. Cells: 76123 temp,
  76124 = 2, 76125 = 1. Register save area 76144-76163.
- 76312 is the `INР GF` hook the compiler emits in modeDe (`ПВ 76312`).
- Pascal error texts at 76324-76363 (`РАSСАL`, «ИНФ О СТЕКЕ…»).
- 77040-77106 is ПУЛЬТ code and data. The Pascal compiler (ver. 9) expects
  the dynamic loader ЗАГР there (`ЗАГР=77040, LOAD, UNLOAD, СН`,
  `DS=СН(3), Z1Z…Z7, ПА, ВИ, …`), so based (X+) programs cannot run under
  this ПУЛЬТ.

## Other page-37 images

Found with `tools/findpage.py 2148 2248`, which compares zones with the
reference words at the same and shifted offsets.

- 2248/2148 zone 01035: the ПУЛЬТ above.
- 2248/2148 zone 01117 (unit 40 zone 0117), identical on both volumes: page 37
  of another (autonomous) monitor, which contains ЗАГР at 077040-077677.
  Its routines map onto the current ПУЛЬТ:

  | 01117 | current ПУЛЬТ |
  |---|---|
  | 76104 save regs | 76066 |
  | 76112 restore regs | 76074 |
  | 76134 temp | 76123 |
  | 76135 (2) | 76124 |
  | 76136 (1) | 76125 |
  | 76156-76175 save area | 76144-76163 |
  | 76074 restart | 76002 |

  76002, 76005, `РАSСАL` 76324 and the texts 76331-76363 are at the same
  addresses; only 76342-76345 differ. In pasauto-re, `mkloader2.py` builds
  a spliced loader and `segtest2.pas` runs the manual's §8.2 segmentation
  example with it.
- 2148 zone 0064 (outside the catalog): a different page-37 build, about 470
  words different. It has a Z1Z…Z7 based-mode stub table at 77047-77055
  (`пб` to 4-word stubs `ржа 3; счи 13; уии 13(17); уии k(17); счим 16;
  счим 6; зп 2(13); пб (14)`), Pascal runtime helpers that call page 36 at
  76324-76364 (number output), at 77400-77440 (terminal input) and at
  77600-77607, and a different 76006 (an overlay loader: it reads М7 zones,
  then calls 74042/74012). It has no LOAD/UNLOAD/СН and no Pascal error
  texts. Its 77043 parse prologue is stale and runs into the stub table and
  an orphaned `Э50 7700` at 77062. Under dispak (volume `~/.besm6/2249` =
  2248 with 01035 ← 2148:0064, pasauto-re `pult64.b6`) it boots and handles
  `арх`, but `пас` hangs at 77062. With the parse body restored, ПАСКАЛ's
  76006 call read unit 12 zones 0360-0417 over all of memory. It belongs to
  a different ПАСКАЛ/runtime generation, possibly a run-time snapshot.
- 2148/2248 zones 01041, 2148 01145-01150, 2248 01167: shifted copies of
  76367-77377. 01006/01176: a piece of 77600-77767. 2148 0543: part of a
  monitor (КАДРЫ, КАТАЛОГ texts from 0540) that shares about 60 words with the
  loader.

## ПАСКАЛ (ПАСК, zone 050) and the autocode translator

The disassembly with comments is `~/git/besm6/pasauto-re/paskal.b6`.

- It runs in page 33 (066000) and calls parse 76016 and argv 76015. An
  older ПАСКАЛ is at 2248 zone 01173 (2048-install build).
- It loads its own copy of the ITM autocode translator AITM from unit 57
  zones 7-13 (= 2248 01007-01013 = 2148 0400-0404). That is not the
  0406-0414 copy that ~/git/re-aitm documents.
- It checks magic1 at 04751 and then patches:
  - 011347: `зп 31(М2)` → `Э75 31(М2)` in the launch-stub copy loop;
  - 011356: `Э70 7` → `ПБ 66005`;
  - 04751: → `сч; пб 4013`, which skips phase 1 when the drum-23 text starts
    with ITM 0223 'В'.
- It writes the patched image to unit 010 zones 6-12. Э72 KEYE72 makes the
  translator's Э74 return to 66005. The compiler ends its output with
  `Н;66005,`, so М3 = 66005 means success; otherwise ПАСКАЛ prints «БЫЛИ
  ОШИБКИ В АВТОКОД ПРОГРАММЕ». Afterwards ПАСКАЛ does Э70 7 itself, re-tags
  the program as instructions with Э75, and then runs it or saves it
  (ЗОНГП).
- If magic1 doesn't match, the fallback is a physical-drum AITM build on
  2248 0746-0752 (drum 010 tracks 6-12; magic2 `уи 2 / э70 6772` at 06770).
  It can't run in dispak without ФИЗО.
- СПЕЦ: with СПЕЦ in the passport, ordinary stores write instructions.
  `Э75 0` turns СПЕЦ on, `Э75 1` restores the passport's setting (dispak
  cu.c case 075). The ПУЛЬТ job has no СПЕЦ.

## Related repositories

- `~/git/besm6/pasauto-re`: the Pascal-autocode compiler (`pasauto.pas`),
  `paskal.b6`, `run.sh` / `pas.sh` (compile and run a Pascal file under
  ПУЛЬТ), `mkloader*.py`, `segtest2.pas`.
- `~/git/re-aitm`: the ITM autocode translator.
- `~/git/leobru/re-dimip`, `re-poplan`: earlier projects with the same
  method (coverage-seeded disbesm6 listings, `.sym` and notes files).
