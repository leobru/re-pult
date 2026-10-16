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
- `tools/probe.sh 'cmd args' ...` runs each line in its own session (then
  `конец`) and prints the Э70 exchanges after boot plus the terminal output.
  That is the quick test of whether a command loads an overlay.
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
| РРR | 001 | 1 | `ррr` (Latin R) via БАВТ: page 0, +АДСИС |
| ПУЛЬТ | 002 | 1 | `пульт` via БАВТ: page 0, then ЗГЛВК → page 1; prints «ШИФР  ЛЕНТ» |
| АЦПУК | 003 | 1 | `ацпу` via БАВТ: page 36, then drum 27 zone 0137 → page 36 |
| ПУЛЬТФ | 004 | 1 | |
| ДАЙ | 005 | 1 | `дай SUB args`, page 0; assembly, no АДСИС; see «ДАЙ» below |
| АДСИС | 006 | 1 | Pascal runtime library, page 36 (074000); the compiler's ИА=74000 table |
| РЕЗРВ1 | 007 | 22 | pool of overlays (zone 015 runs in page 0 for `алг`); per-zone pieces `РЕЗРВ1+k` |
| СЕРВИС | 031 | 3 | `сервис`, `сер`, Pascal program, pages 0-2 (+АДСИС) |
| ПАСЛ | 034 | 1 | saved state ("ЛЕНТЯЙ…РАSСАL…" text) |
| СБОЙ | 035 | 1 | **page 37 (076000)**, resident ПУЛЬТ services |
| ЗГЛВК | 036 | 1 | read into page 1 at boot; `я` reads it into page 1 again and prints from it (Э64 01451) |
| КТЛБИБ | 037 | 1 | library catalog (data) |
| ПУСК | 040 | 1 | **page 0**, boot and resident kernel |
| НАБЛ | 041 | 1 | read into page 1, copied via drum 27 track 37 to **page 27 (056000)**: command loop (terminal Э71 at 56514/56550/56053) |
| АЛГ | 042 | 2 | `алг`: zone 042 → page 1, 043 → page 33 |
| СЛУЖ | 044 | 1 | archive-catalog commands `з`/`зап`, `ктл`, `упор`, `искл`; page 0, assembly; see «СЛУЖ» below |
| СПИС | 045 | 2 | `с`: zone 045 → page 0, entry 10; `р`: zone 046 → page 1, entry 2010 |
| АВТПАК | 047 | 1 | |
| ПАСК | 050 | 1 | ПАСКАЛ (Pascal-autocode driver), page 33 (066000) |
| БАВТ | 051 | 1 | page 33. Runs first for `пас` and for any name ПУЛЬТ itself doesn't know; such names are looked up in the archive catalog (see «Name lookup in the archive catalog») |
| ОТЛ | 052 | 3 | `о`: zones 052-054 → pages 24-26 (НАБЛ 56342 adds an offset to the zone) |
| ЛЕС | 055 | 3 | `лес`, Pascal program, pages 0-2 |
| ЧИСТКА | 060 | 3 | `чистка`, Pascal program, pages 0-2 |
| СТАТИС | 063 | 1 | Pascal program, page 0, +АДСИС; six modes, see «СТАТИС» below |
| ЭХОЛОТ | 064 | 4 | `эхолот`, Pascal program, pages 0-3 |
| ДЖИП | 070 | 1 | `джин` (with АДСИС in page 36) → page 0; `диалог` → page 12 (after ЭХОЛОТ's zones 064-067 → pages 0-3) |
| РЕЗРВ2 | 071 | 2 | |
| СТРУК | 073 | 1 | `струк`, Pascal program, pages 0-1 |
| РЕЗРВ3 | 074 | 1 | |
| НОВРЕД | 075 | 3 | `ред NAME` (or `м NAME`) via БАВТ: zones 075-077 → pages 0-2, plus АДСИС → page 36 (Pascal program). `ред пам` gives a `+` prompt; `ред буф` needs `арх` first («НЕТ НАСТРОЙКИ НА АРХИВ»), then looks the name up in the archive («В АРХИВЕ ВАСЯ НЕТ ИМЕНИ БУФ») |

Catalog names are not command names: `спис`, `отл`, `джип` etc. fall
through to БАВТ. The commands that load СЛУЖ, СПИС, ОТЛ, ДЖИП and ЗГЛВК are
in the next section. The БАВТ section below covers ПУЛЬТ, АЦПУК, РРR and НОВРЕД. Nothing
found so far loads ПУЛЬТФ or АВТПАК (НАБЛ has descriptors for zones 047-051 into page 25 at
56362-56364, not reached from the command tables).

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

## Command dispatch (НАБЛ and ПУСК)

Verified with `tools/probe.sh` on 2248, one command per session.

НАБЛ (page 27; position-independent, М10 = 056000) reads a line with Э71
(56540-56551, then 56053), and 56155 parses the first word into 56222. The
word is GOST, right-justified, padded on the left with 0377 bytes, at most 6
letters (Cyrillic and the Latin letters up to Z, codes 040-0114). If the line
does not start with a letter, the word stays all ones. 56021 scans the
(name, jump) pairs at 56027-56075. The match must be exact: `кон`,
`конецабв` and `сисалг` are unknown names. The sentinel 56075 (`0…0377`)
leads to 56076, the default. Words 56053-56064 inside the table are code,
not entries. Table, with what the probe saw:

| word | target | action | overlay |
|---|---|---|---|
| (no word: empty line, digits, `*`, `+` …) | 56077 | calls 56400, back to 56010; no exchange. Probably the text-entry part of НАБЛ (not analysed) | — |
| `з` | 56302 | zone 044 (СЛУЖ) → page 0, пб 10 | СЛУЖ |
| `с` | 56312 | zone 045 (СПИС) → page 0, пб 10 | СПИС |
| `р` | 56314 | zone 046 (СПИС+1) → page 1, пб 2010 | СПИС |
| `о` | 56342 | zones 052+k (ОТЛ) → pages 24-26, пб 10(М7) | ОТЛ |
| `зап` | 56302 | same as `з` | СЛУЖ |
| `ктл` | 56304 | СЛУЖ, пб 11; then reads drum 27 z036 and u40 z0240 into page 3 | СЛУЖ |
| `упор` | 56306 | СЛУЖ, пб 12 (then as `ктл`) | СЛУЖ |
| `искл` | 56310 | СЛУЖ, пб 13 (then as `ктл`) | СЛУЖ |
| Latin `F` (0100) | 56052 | `Э62` with address 0: dispak ends the job at once | — |
| `сис` | 57722 | internal, see below | — |
| `арх` | 56340 | reloads ПУСК (zone 040 → page 0), пб 15 | — |
| `алг` | 56300 | zone 042 (АЛГ) → page 1, пб 2012 | АЛГ |
| `конец` | 56334 | reloads ПУСК, пб 13 (ПУСК 0705) | — |
| anything else | 56336 | reloads ПУСК, пб 14 (ПУСК 01453) | — |

`сис NAME` (57722) parses a second word and stores it in 57767, the
current system (initially `КОД`). `лис` is stored as `АВТ`, with 57757 = 073.
If NAME is one of АЛГ, АВТ, ЛИСП, КОД, ИСО, БЕМ (table 57734-57741), НАБЛ
writes itself back to drum 27 zone 037 (57744) and restarts at 56010.
Otherwise it goes to 56077. No zone is read.

Reloading ПУСК is not an overlay load: page 0 is ПУСК's home, and overlays
that run in page 0 overwrite it. ПУСК's entries from НАБЛ are at 010-015:
пб 1036, 1073, 1042, 0705, 1453, and `уиа 1141(М12); пб 1074`.

ПУСК 01453 scans its own (name, jump) table at 01463-01536 against 56222
(sentinel 01537). A miss goes to 01416: БАВТ (zone 051) → page 33, пб 66007,
and БАВТ handles the name (see the БАВТ section).
Many handlers end through 01037: print the text at 01041 (`ЕСТЬ`) with
76005, then leave through 76002 (back to НАБЛ via drum 27 zone 037).

| word | ПУСК | action | overlay |
|---|---|---|---|
| `диалог` | 01362 | copies words with Э75, then 11372 reads zones 064-067 → pages 0-3 and 070 → page 12 | ЭХОЛОТ zones + ДЖИП |
| `пк` | 0331 | internal; with no input prints «ПРОГ.ПК ПРИЗНАК КОНЦА ПУСТАЯ ПОСЫЛКА - ЕТХ» | — |
| `resist`, `канал` | 01540 | internal: Э71, parse 76016, Э50 0100 …; no output in the probe | — |
| `пз` | 01424 | Э70 with descriptor 01426 = `0062007600000000` (not a zone read), пб 64010; prints «О.К» | — |
| `печ` | 01427 | `Э62 76` (dispak: "drop incognito"), «ЕСТЬ» | — |
| `тур` | 01431 | plants `Э70` in cells 6-7 and runs them: unit 51 zone 0365 → page 1, zone 0364 → page 0. Unit 51 is not in pult.b6: АВОСТ 42 | unit 51 |
| `new` | 01036 | `Э62 43` = keep the job in the input queue for a future restart; dispak lacks it (АВОСТ 3, «Пока рано»; see TODO.md) | — |
| `связь` | 01042 | internal; prints `00:` | — |
| `я` | 01440 | ЗГЛВК (zone 036) → page 1, prints with Э64 01451 | ЗГЛВК |
| `инк` | 01244 | `Э62 44` (cancel output stream), «ЕСТЬ» | — |
| `дилос`, `dilos` | 01324 | builds a unit-40 descriptor from up to two arguments, пб 77400 (page 37): reads the zone (055 with no arguments) → page 1, writes it to drum 27 zone 020, reads unit 67 zone 077 (not mapped: АВОСТ 42) | yes |
| `джин` | 01337 | АДСИС (zone 006) → page 36, then cell 6 reads ДЖИП (zone 070) → page 0. Prints «*** ОШИБКА АРХ. = ТАКОГО ИМЕНИ НЕТ» without arguments | ДЖИП |
| `выд` | 01247 | `Э62 42` (flush output stream), «ЕСТЬ» | — |
| `nf` | 01345 | `Э66 1000`…`Э66 1003` (АВОСТ 42 in dispak), then falls into `get` | (u40 z01461) |
| `of` | 01343 | `уиа (М6); пб 6`. The probe saw an Э70 at 01672 and then БАВТ | — |
| `cl` | 01355 | u40 zone 01461 → page 33, пб 66007 | zone 01461 |
| `put` | 01347 | as `nf` from `Э66 1002` on | (zone 01461) |
| `get`, `del` | 01351/01353 | u40 zone 01461 → page 33, пб 66006 | zone 01461 |
| `inf` | 01357 | u40 zone 01461 → page 33, пб 66011 | zone 01461 |

Unit 40 zone 01461 = 2248 zone 02461, which lies outside the catalog. It
holds other code, so `cl`/`get`/`del`/`inf` fail with АВОСТ 22. The
NF…INF group belongs to an overlay that is not on this volume.

So the commands handled without an overlay are: in НАБЛ, the empty or
non-word line, `сис`, Latin `F`, `арх` and `конец`. `арх` and `конец`
continue in ПУСК, which is only reloaded. In ПУСК: `пк`, `resist`, `канал`,
`пз`, `печ`, `new`, `связь`, `инк` and `выд`. `nf`, `put` and `of` start
internally but end in a load or a crash. Everything else loads an overlay,
and an unknown name loads БАВТ.

## БАВТ names (page 33)

БАВТ's (name, word) table is at 66074-66177; 66200 ends it. The second
word is the handler's offset from 066000 (checked for the СТАТИС names:
0344 → 66344, etc.). A name in neither this table nor the ПУСК/НАБЛ tables
is looked up in the archive catalog through 76006 (next section). The results below are from `tools/probe.sh`
with no arguments and no `арх`. Every name first reloads ПУСК and loads БАВТ.

| name | loads | output with no arguments |
|---|---|---|
| `ред`, `м` | НОВРЕД (075-077) → pages 0-2, АДСИС → 36 | «ГДЕ ЖЕ ИМЯ ?» |
| `мавт` | — | «НЕТ СИМВОЛОВ КОНЦА» |
| `бавт` | unit 30 zone 01747 → page 0 (not mapped) | «Внутр.ош.эмул» |
| `пульт` | ПУЛЬТ (002) → page 0, ЗГЛВК → page 1 | «ШИФР  ЛЕНТ» |
| `дай` | ДАЙ (005) → page 0 | «НЕ ДАМ» |
| `паскал`, `пас` | ПАСК (050) → page 33, АДСИС, the translator zones 0101-0114 → pages 0-13. `пас` first reads unit 17 zone 037 | «ПАСКАЛЬ-АВТОКОД 9.(17.05.88)» |
| `конкат` | — | «QU» |
| `диспак` | — | a line of zeros |
| `форм` | — (writes page 27 to drum 27 zone 037) | «КОН СТР=000 ДЛИН=00000 ПРОГОН=0 КТ=000000» |
| `статис`, `врем`, `впак`, `дубна`, `гост`, `алгп` | СТАТИС (063) → page 0, АДСИС; mode 5…0 | `врем`: «ВЦП=0+0 СОТЫХ СЕК.ОСТ=3600.ВРЕМЯ БЭСМ=20.1.0»; the others «QU» |
| `чистка` | ЧИСТКА (060-062) → pages 0-2, АДСИС | «**** Ч И С Т К А ****» |
| `лес` | ЛЕС (055-057) → pages 0-2, АДСИС | «==> » |
| `загр` | unit 57 zone 0144 (2248 zone 01144) → page 20 | «ЗАТЕРТО СПО» |
| `ррr` | РРR (001) → page 0, АДСИС | «QU» |
| `пп`, `ппн`, `па` | — (drum 27: page 1 ← 037, page 37 → 031, page 1 → 037) | nothing |
| `зкан`, `сбуф` | — | «НЕТ» |
| `демос` | unit 66 zone 0700 (not mapped: АВОСТ 42) | |
| `энт` | unit 66 zone 01024 (not mapped: АВОСТ 42) | |
| `порц` | — (page 27 → drum 27 zone 037, page 37 → zone 031) | nothing |
| `ацпу` | АЦПУК (003) → page 36, drum 27 zone 0137 → page 36 | «ЧАСТЬ    000000» |
| `эхолот` | ЭХОЛОТ (064-067) → pages 0-3, АДСИС | «**** Э Х О Л О Т ****» |
| `струк` | СТРУК (073-074) → pages 0-1, АДСИС | «-=* СТРУКТУРА ПРОГРАММЫ *=-» |
| `сер`, `сервис` | СЕРВИС (031-033) → pages 0-2, АДСИС | «ПАСКАЛЬ-СЕРВИС» |

So `мавт`, `конкат`, `диспак`, `форм`, `пп`, `ппн`, `па`, `зкан`, `сбуф` and
`порц` are handled inside БАВТ. The others load a catalog entry or an
outside zone.

## Name lookup in the archive catalog (76006 → 76203)

Unit 40 zone 0240 is not a library. It is the default **archive catalog**.
БАВТ (and ПАСКАЛ) find a program in the user's archive by calling 76006
with the parameter block at 77770-77775 (77771 = the name, 77770 = a check
word). The routine at 76203:

1. 76237 reads drum 27 zone 036, the current archive catalog, into page 34
   (070000).
2. If 070000 (the catalog's first word) ≠ 77770, it reads the catalog from
   the descriptor in НАБЛ cell 57776 (default `0010 0000 0040 0240` = unit 40
   zone 0240) and writes it back to drum 27 zone 036 (76241-76242).
3. If the word still doesn't match, it stores both words in the message at
   76312-76317 and returns. The caller prints it: «СТОИТ <catalog's word>
   МЛ <expected>». dispak shows only «СТОИТ.176МЛ.176», because the
   message stops at the 0377 bytes in 76313.
4. Otherwise it searches page 34 for the name (76250-76257). If found, it
   reads the program's zones with Э70 (76260-76277) and returns to 1(М11).
   If not found, it returns to (М11) with the name in 76321.

`арх NAME,U,Z` reads that archive's catalog (unit U zone Z, here unit 50
zone 0100) into page 3 and writes it to drum 27 zone 036 (ПУСК 01176-01160).
After that the drum copy matches, and an unknown command such as `xyz`
prints «ХУZ .I»: name not found, with no tape read. Without `арх`, 2248 zone
01240 is read. It holds only 14 words: some code, then the ASCII text
`OVERLAY OT 27.06.85 M3 <<-->>`, and it is not a valid catalog. That is
where «СТОИТ…МЛ…» comes from. `ктл`, `упор` and `искл` (СЛУЖ) read the same
two places into page 3.

## СЛУЖ (zone 044)

Hand-written assembly with the same page-0 layout as ПУСК: words 0-7 are
the same header (`выпр 70707(17)`, …, 6 = `пб (3)`), and 010-013 are an
entry vector. НАБЛ reloads page 0 with СЛУЖ and jumps to:

| entry | target | commands |
|---|---|---|
| 010 | 0411 | `з`, `зап` |
| 011 | 040 | `ктл` |
| 012 | 0316 | `упор` |
| 013 | 0215 | `искл` |

All four work on the catalog of the attached archive (see «Name lookup in
the archive catalog»). Page 3 (06000-06377) holds the catalog: pairs of
(name, start << 24 | length) from 06001, with the number of words in
06377. Two copies of it are used:

- **МЛ**, the tape copy: НАБЛ 57776 (set by `арх`; default u40 z0240) plus
  page 3, in cells 022 (read) and 023 (write). In the test: u50 z0100.
- **МБ**, the drum copy: drum 27 zone 036, in cells 024 (read) and 025
  (write).

Each command reads the drum copy first. It also reads the tape copy when
НАБЛ 57770 ≠ 06000 (that state word is not understood). On the way out it
restores НАБЛ 57767/57770 and returns through 56010.

| command | what it does |
|---|---|
| `ктл`, `ктл мб` | lists the drum copy: « ИМЯ  НАЧАЛО ДЛИНА», then one line per entry (name, start zone, length) |
| `ктл мл` | lists the tape copy |
| `ктл млмб` | tape → drum, «СЧ КТЛ С МЛ» |
| `ктл мбмл` | drum → tape, «ЗП КТЛ НА МЛ» (at 0106-0111: МБ, МЛ, МЛМБ, МБМЛ) |
| `з NAME(N)` | allocates N zones for NAME after the last entry and prints «МСВ NAME Н=start Д=N» (МСВ = массив, an archive entry; Н = начало, Д = длина). If the name exists, its entry is reused; it moves to the end if it grows. Then it writes the edit buffer into the zones (0766-0773) and the catalog to both copies |
| `з NAME` | as above, with the length taken from the buffer (0700-0761, a second pass through 0512) |
| `искл A,B,…` | removes up to 7 names, shifting the entries down and decreasing 06377. Only the drum copy is written |
| `упор` | compacts the archive: it renumbers the entries from zone 1, moves their zones (Э70 loop 0352-0364, descriptors 0401/0402), and writes both copies |

Errors: «АРХИВ ПЕРЕПОЛНЕН. ЗАПИСЬ НЕВОЗМОЖНА» (0622, archive full), «  КТЛ
ПЕРЕПОЛНЕН…» (0620, catalog page full), «НЕПР. ИМЯ ЛЕНТЫ:» (no archive
attached), «НЕТ КТЛ НА МБ».

The format of the saved text depends on the current system (НАБЛ 57767):
0512 looks it up in АЛГ, АВТ, ЛИСП (0642-0644) and picks the end-of-text
codes at 0645-0654. The name БУФ (0660) is special.

Observed on a scratch archive (`дай новарх,50,100,вася`, `арх вася,50,100`,
volume 2399, a copy of 2345, deleted afterwards):
- `з аа(5)` → «МСВ АА Н=001 Д=005», and `зап вв(2)` → `Н=007 Д=002`.
- `з бб` (empty buffer) prints «АРХИВ ПЕРЕПОЛНЕН…» but still creates a
  one-zone entry at 006.
- `з нов(30)` is refused, and `з аа` for an existing name prints the same
  message.
- After `искл аа`, `упор` moved ББ from 006 to 001 and ВВ from 007 to 002.

`sessions/служ.txt` only runs the read-only forms, because pult.b6 has the
real 2345 as unit 50.

## ДАЙ (zone 005)

Hand-written assembly, not Pascal:

- БАВТ starts it without loading АДСИС. Every Pascal image (ЛЕС, ЧИСТКА,
  СТАТИС, …) gets АДСИС in page 36.
- Nothing in it refers to 074000-075777 (the runtime).
- It has none of the compiler's code shape. Subroutines are called by
  register linkage (`пв X(М3)`, `пв X(М16)`), it patches its own code with
  Э75 (cells 0262-0263), and data is mixed into the code. The command table
  is pairs of a name and a `пб`.
- Its messages are GOST, except the ITM texts at 0154-0205, which are
  messages for the batch job that ЛЕНЛЕН generates.

`syms/ДАЙ.sym` names the entry points. `sessions/dai.txt` runs the
subcommands that don't crash.

START (07) sets М16 = 76002 for the return. It looks up the first argument,
1(М17) (ПУЛЬТ's parsed command line: 2(М17)… are the next arguments), in
the (name, `пб`) pairs at 016-053 (sentinel 054). A miss prints «НЕ ДАМ».
The probe outputs below are with no arguments.

| sub | entry | what the code does | probe |
|---|---|---|---|
| `паузу N` | 061 | a loop around `Э50 7700` (A = 01000, an 80 ms × 01000 sleep) driven by the argument | nothing |
| `кодго X` | 070 | replaces the low byte of НАБЛ cell 57536 with the argument (one byte, else «НЕТ»), then writes page 27 back to drum 27 zone 037 | — |
| `вреш N` | 077 | `Э63 2` with the argument (default 060): set the time limit | АВОСТ 3 (dispak lacks Э63 2) |
| `разр` | 0104 | `Э61 0110` on the passport-like block at 0110-0134, then tests a bit of 0115 | «ЕСТЬ» |
| `деш` | 0327 | picks a table by the current system (НАБЛ 57767: АВТ or КОД) and XORs it into a code table | КОНТРОЛЬ КОМАНДЫ |
| `лент U ОПЦ` | 0404 | tape settings: ИМЯ (Э50 0105/0113), ЗП, СЧ, СДВИГ (Э50 0112), ПЕРЕИМ and СМЕНАП (Э72) | «НЕТ» |
| `шифр` | 0477 | prints the account id (Э50 0100) in octal | «412020000000» |
| `напнап` | 0507 | copies zones: builds Э70 descriptors 0272/0273 from the arguments and loops at 0230-0257 | « 1345 ЗОН С 0 . 1375 НА 1320 . 1334», «НЕТ» |
| `ленлен` | 0527 | tape-to-tape copy as a batch job: passport at 0110-0134 (ШИФР, ТРАКТ, ЛЕНТ, ВРЕМ, ВХОД, ЛИСТ, ЕКОНЕЦ at 0275), account id from Э50 0100 | «НЕТ» |
| `пампам` | 0713 | like `напнап` | « 1320 С 0 НА 1375», «НЕТ» |
| `ктлбиб` | 0754 | not analysed | «НЕТ» |
| `сравн` | 0776 | compares zones (texts «НЕ РАВНО», ЗОНА, АДРЕС at 01043-01046) | ends in the archive-catalog lookup, «СТОИТ.176МЛ.176» |
| `ацпу` | 01053 | not analysed | «НЕТ» |
| `новарх` | 01065 | creates an archive, e.g. `дай новарх,50,100,вася` in pasauto-re's pas.sh | «НЕТ» |
| `форт` | 01225 | reads zone 005 (ДАЙ itself) into page 36 twice, then unit 21 zone 0201 → page 1 | АВОСТ 24 |

None of the probes changed 2345 (unit 50, the only writable volume).

## СТАТИС (zone 063)

Decompiled and annotated in `statis.pas` (from pasauto-re, which has the
plain decompiled version). The main program dispatches on the
global `i` (its first variable), which БАВТ sets before it starts the image:
the handlers at 66344-66356 load a constant and go to 66357. The
`job: alfa` variable holds the argument. Mode by command:

| `i` | БАВТ | command | procedure | what it does |
|---|---|---|---|---|
| 0 | 66356 (A = 0) | `алгп` | АЛГОЛ | wraps the text as an ALGOL batch job (ПАСП '66', `$АЛГОЛ`) |
| 1 | 66355 (67352) | `гост` | ВЫДАТЬ | `job` = NEWS (Э62 43), АЦПУ, FREETT, RUNTT, `58`; otherwise recodes the text with `марга` |
| 2 | 66354 (67351) | `дубна` | ДУБНА | wraps the text as a Dubna-monitor batch job (ПАСП '44') |
| 3 | 66353 (67350) | `впак` | case 3 | builds an autocode job (ПАСП '33', `В10000А1`) from the text up to `"` |
| 4 | 66345 (67333) | `врем` | ВРЕМЯ | prints CPU time, time left and the BESM clock (Э63 0, Э63 4, Э53 10) |
| 5 | 66344 (67330) | `статис` | СТАТ | counts lines, characters, letters, digits and zones, and makes a histogram |

Anything outside 0..5 prints «НЕПР. ЗАПУСК». With nothing to work on,
modes 0, 1, 2, 3 and 5 print «QU» in the probe.

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
