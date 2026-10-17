# Volume 2068: ПУЛЬТ and Pascal

Zone, word, unit and memory addresses below are octal. Volume identifiers,
dates and differing-word counts are decimal.

## Build and use

```sh
make 2068
make check2068 DISPAK=/home/leob/git/dispak/build/dispak/dispak
make pult2068 DISPAK=/home/leob/git/dispak/build/dispak/dispak
make pult2068 SYSTEM_VOLUME=2148 DISPAK=/home/leob/git/dispak/build/dispak/dispak
```

`make 2068` creates `build/volumes/2068` and its provenance file
`build/volumes/2068.json`. It copies source images from `SOURCE_DISKS`
(default `/usr/local/share/besm6`) into the same build directory.
Python 3 is required. No source image or installed system disk is modified.
`make install2068` copies the image and provenance into `INSTALL_DISKS`
(default `~/.besm6`) only when 2068 is absent; existing installations are
left unchanged as a pair.
The generator and manifest live in `tools/`; the test lives in `tests/`.

`make pult2068` prepares its boot deck from `pult2068.b6` using writable private copies under
`build/pult2068`. БАВТ's Э72 operation changes unit 30 to read/write mode,
so the system image must be writable after switching. Existing private copies
are retained until their build inputs change. Set `DISPAK` to an emulator
with the small-disk wrapping and Э72 scratch-unit/physical-backing fixes.

The boot deck puts system volume 2248 (or 2148 with `SYSTEM_VOLUME=2148`)
on unit 57 at **offset 0371**, first in the passport for `ФИЗО МБ21`,
and volume 2068 on unit 40 with **no offset**. Unit 30 is a
scratch slice. КТЛБИБ retains the original archive descriptions:

```
СИСБИБ,40,0,100
PASCAL,40,100,20
```

The original ПРОБА description in КТЛБИБ is obsolete: zones 071–072 now
contain the executable ГОРОСК, not an archive catalog.

For example, `арх PASCAL,40,100` followed by `ктл` lists КВСЕ, КПЕЧ,
КБИЛИС and КСБRUN. User source archives are separate writable volumes;
the boot deck deliberately does not mount a real user's archive.

## Contents and provenance

Source zones `01000–01117` become `000–117`. The ПУЛЬТ catalog is at 000;
the separate Pascal catalog is at 100. Their relative entry addresses need
no adjustment. The full image has 02000 logical zones plus four reserved
physical zones. Zones after 117 are initially blank.

The base is 2248. Entire СЕРВИС zones `031–033` and entire compiler zones
`101–114` are replaced from 2148, with the two checked compiler repairs below.
Zones `071–072` also come from 2148, containing ГОРОСК dated 12.01.83.
The ПУЛЬТ catalog entry РЕЗРВ2 is renamed ГОРОСК, retaining start 071
and length 002.

Zone 026 is exposed as the callable one-zone **BD** dispatcher. For example,
`арх сисбиб,40,0` followed by `bd` loads it and prints «BD, А ДАЛЬШЕ».
Its subcommand table includes OPEN, OBTAIN, PUT, DELETE, MODIFY and GET.
РЕЗРВ1 is shortened to zones 007–025. Zones 027–030 retain their original
payloads outside callable catalog entries: 027 contains **БАНДИТ**, used
internally by BD, rather than a directly callable program. This follows
the distinction between the dispatcher at 026 (КОБЛА in Table 2) and
БАНДИТ at 027 in the PDF. **Zone 030 is КТЛБД, the non-executable
database catalog**, also outside callable entries. See [BD commands and
catalog](bd.md) for the manual’s command table (PDF page 33, right side;
printed page 63) and its comparison with the recovered dispatcher.

The BD entry is appended at catalog words 0075–0076; the zero sentinel and
the search bound at word 0377 both move from 0075 to 0077. The catalog
payload changes are checked patches; no dispatcher or БАНДИТ code is changed.
Neither source image is modified.
`tools/volume2068.json` records the source ranges and checked patches.
`build/volumes/2068.json` records full source-image hashes, per-zone source and output
payload hashes, differing-word/tag counts, patch details and output-image hash.
The generator rejects changed source payloads and unexpected patch values.

The physical format is little-endian 64-bit words: eight control words and
1024 payload words per zone. Payloads retain their original upper tag bits.
Control words are regenerated with volume 2068, relocated physical track
numbers, and recalculated end-around-carry checksums, following `disk.c`'s
default two-track convention. Time, date and user fields are zero so repeated
builds are identical.

## Historical catalog in PULT.pdf

The primary historical reference is [PULT.pdf](../PULT.pdf),
*Система ПУЛЬТ-78. Общая структура и рекомендации по обслуживанию*
(ВЦ АН СССР, 1978). The scan has no text layer; the following observations
were read from the page images. Printed page numbers differ from PDF pages:

- **Table 2, printed pp. 12–13, PDF page 8:** catalog of ПУЛЬТ modules,
  explicitly dated **21.06.77**.
- **§2.1.1, printed p. 11, PDF page 7:** the base system occupies 0100
  octal zones and may be placed at an arbitrary location on a disk or tape.
- **§8.1, printed p. 44, PDF page 24:** disk **2068**, with its catalog in
  **zone zero**; the commands `АРХ СИСБИБ,40` and `КТЛ` select and list it.
- **§8, printed p. 44, PDF page 24:** the base/additional ПУЛЬТ components
  are on 2068, while language translators accessible from ПУЛЬТ are on
  system disk **2048**. These are distinct storage roles.

Table 2 supports the reconstructed archive's placement and many fixed module
addresses, but describes an earlier revision than the images on 2148/2248.
The comparison below uses octal zones and lengths:

| Zone(s) | Table 2, 21.06.77 | Selected later archive |
|---|---|---|
| 006 | АДСИС, length 001 | АДСИС, length 001 |
| 007–030 | Separate printing, administration, batch, tape, startup, dispatch and database modules | РЕЗРВ1 at 007–025; BD dispatcher at 026; internal БАНДИТ starting at 027 and non-executable КТЛБД at 030. The first five zones hold a duplicate ITM assembler image on 2248 |
| 031–034 | СЕРВИС, length 004 | СЕРВИС, length 003; ПАСЛ at 034 |
| 035, 036 | СБОЙ and ЗГЛВК, one zone each | Same names and extents |
| 037 | ДАЙ, length 001; КТЛБИБ was at 021 | КТЛБИБ, length 001 |
| 040–054 | ПУСК 040/001, НАБЛ 041/001, АЛГ 042/002, СЛУЖ 044/001, СПИС 045/002, АВТПАК 047/001, ПАСК 050/001, БАВТ 051/001, ОТЛ 052/003 | Same names, starts and lengths |
| 055–062 | ЛИСП, length 006 | ЛЕС at 055/003 and ЧИСТКА at 060/003 |
| 063 | БДП, length 001, handling АЛПП/ДУБНА/ВРЕМ | СТАТИС, length 001 |
| 064–070 | ДИАЛОГ, length 005 | ЭХОЛОТ at 064/004 and ДЖИП at 070/001 |
| 071–074 | АВТТРН, length 004, used by МАВТ | ГОРОСК (renamed РЕЗРВ2), СТРУК and РЕЗРВ3 |
| 075–077 | ЛИСП2 at 075/002; ПАСП at 077/001 | НОВРЕД at 075/003 |
| 100–117 | ПАСКАЛ, length 020 | Separate PASCAL catalog and compiler/tools, total extent 020 |

In particular, the historical entries at 007 onward are not an instruction
to load ITM from archive unit 40. The later ПАСК driver still loads ITM
from **system unit 57**, as described below. The manual does not establish
offset 0371 for its 1977 installation; that offset is determined from the
later driver's descriptor and the actual assembler location on 2148/2248.

Table 2 also lists additional systems beyond the copied range: ПЛЭНЕР,
ПОПЛАН, ДЖИН, PASMON, APL, ЛОРД, АБВ and ДИЛОС components. The present image
contains the recovered later base archive and Pascal archive, not the entire
1977 distribution. The historical table alone does not identify matching
payloads for those additional systems in the available disk images.

## Comparison of 2148 and 2248

The two source catalogs are identical, as are all tags in the 80 source zones.
The reconstructed catalog adds BD, shortens РЕЗРВ1, updates the search bound,
and renames РЕЗРВ2 → ГОРОСК through checked patches.
The table lists **every zone with differing 48-bit payload words**. Counts
are positional comparisons, not counts of semantic changes.

| Destination zone(s) | Differing words per zone | Interpretation and choice |
|---|---|---|
| 007, 010, 011, 012, 013 | 1024, 1024, 1024, 1024, 1022 | 2248 contains a five-zone ITM assembler copy identical to zones 0400–0404 on both system volumes. 2148's РЕЗРВ1 contents differ. Preserve 2248's archive contents; ПАСК loads the system copy through unit 57. |
| 031, 032, 033 | 1010, 1024, 961 | СЕРВИС builds 21.11.88 (2148) and 03.12.86 (2248). Use the complete newer 2148 build. |
| 035 | 3 | Resident СБОЙ state and diagnostic text; use 2248. |
| 037 | 12 | КТЛБИБ starts with unrelated user archive descriptions on 2148, but describes these system/Pascal/ПРОБА archives on 2248. Use 2248. |
| 047 | 1 | АВТПАК diagnostic terminator/padding byte. Use 2248. |
| 050 | 3 | ПАСК location constants differ; use the unchanged 2248 driver and mount the system volume with the appropriate unit-57 offset. |
| 071, 072 | 1022, 1008 | 2148 contains ГОРОСК dated 12.01.83; 2248 contains ПРОБА and its sample program text. Use 2148 and name the entry ГОРОСК; the old ПРОБА description in КТЛБИБ no longer applies. |
| 101, 102 | 848, 1020 | Start of compiler КВСЕ, including diagnostic strings and version. |
| 103, 104, 105, 106, 107, 110, 111 | 1024 each | Compiler body; many shifted addresses. |
| 112, 113, 114 | 791, 182, 158 | Compiler tail, including substantive instruction differences. |

### Small differences

At `035:0012`, the saved exchange descriptor is
`0010010000402667` on 2148 and `0010010000400037` on 2248. Words
`035:0312–0313` change the diagnostic from `НЕ ПОНЯТНО` to `СТОИТ…МЛ…`.
These are resident state/message differences, not a different service entry
vector. At `047:1375`, `1302557603777433` becomes `1302557677777433`:
one space byte becomes 0377 in the same diagnostic.

The 2148 versus 2248 ПАСК constants are:

| Word in zone 050 | 2148 | 2248 |
|---|---|---|
| 1142 | 0570670 | 0570007 |
| 1221 | 0402000 | 0400000 |
| 1226 | 0570670 | 0570007 |

The first is the primary assembler descriptor. The second belongs to the
special unit-40 volume-2048 branch. The third is used by the physical-drum
assembler fallback. All three remain unchanged in 2068.

ПАСК reads the assembler through **unit 57**, retaining descriptor `0570007`.
Mounting `лент 57(2248-371)` (or `2148-371`) maps zones 007–013 to
system-volume zones **0400–0404**, because `0371 + 007 = 0400`.
The earlier patch redirecting the descriptor to unit 40 has been removed.
Archive zones 007–013 remain preserved as archive contents; compilation
does not depend on that duplicate assembler image.

### СЕРВИС

These are different complete builds, not a few saved-state words. Both
contain text insertion/search/listing, volume/resource controls and
`ПАСКАЛЬ-СЕРВИС`. The newer 2148 help explicitly enumerates fifteen commands,
including БОБ, ОТК, ПАР, МОТ, НАП, ТРАК, РЕС, ОБЛ, ВСТ, НАЙ, СПИС, АЦПУ,
МАГ, ДИС and ВЫБ. The older build also contains job-catalog/status messages
such as `ВСЕГО ЗАДАЧ`, `НЕТ ТАКОЙ`, `СТОП` and `ЖДЕТ` absent from the newer
first-zone text. Keep all three zones together; absolute instruction addresses
and embedded text moved substantially.

### Compiler

2148 has `COMPIL 201288`, banner `9.(09.12.88)`; 2248 has `COMPIL 180588`,
banner `9.(17.05.88)`. The December diagnostic `НЕЛЬЗЯ ПРИСВ ФАЙЛЫ` is one
word shorter than May's `НЕЛЬЗЯ ПРИСВАИВАТЬ ФАЙЛЫ`. The ensuing one-word
shift changes many instruction operands, so a near-total positional zone
diff does not establish a large algorithmic rewrite. The compiler is selected
as one twelve-zone image, never as independently selected zones.

There are also concrete instruction differences that must not be dismissed
as relocation. In source zone 01114 (destination 114), words 1105 and 1106
execute at 27105 and 27106:

| Address | December / 2148 | May / 2248 |
|---|---|---|
| 27105 | `сч 12; дел 6214(М1)` | `сч 12; зп 65(М1)` |
| 27106 | `нед 71156(М4)` | `пв 06157(М16)` |

December's parser call target corresponding to May's 06157 is 06156.
The untouched December image stops with АВОСТ 16 at 27105 after a variable
declaration. A repair restoring the store and calling 06156
compiles and executes programs with variables, procedures and an integer
function. These two repairs are included in 2068; the same regression program
is also run against the intact May compiler. This is dynamic evidence of
damaged words, not merely a suspicious disassembly.

At `114:1322–1331` (memory 27322–27331), December's eight case-table jumps
have modifier М10, whereas May's have modifier 0. An integer-returning
function executes successfully with those entries unchanged after the
two-word parser repair. Their existence alone is insufficient evidence to
change them.

## Relocation patches and emulator behavior

The generator checks the original 48-bit value before applying each patch:

| Zone:word | Change | Reason |
|---|---|---|
| 000:0016 | РЕЗРВ1 length `022 → 017` | End the reserve entry at 025 before BD. |
| 000:0075–0077 | BD name, `026/001`, zero sentinel | Expose only the dispatcher as callable. |
| 000:0377 | `0075 → 0077` | Include BD in archive name lookup. |
| 000:0065 | `РЕЗРВ2 → ГОРОСК` | Identify the program selected from 2148 at zones 071–072. |
| 042:0135 | `мода 40302 → мода 40300` | АЛГ must select system offset 0300 under `--725`. |
| 042:0137 | `мода 57302 → мода 57300` | Same correction on the native 2068 branch, using unit 57. |
| 114:1105 | `0010001204166214 → 0010001204000065` | Restore the December compiler's lookup reset. |
| 114:1106 | `2123115600000000 → 7310615600000000` | Restore the December compiler's parser call, with its own relocated target 06156. |

The volume-2068 comparisons remain unchanged. АЛГ now chooses system unit
57 rather than moving the archive unit's offset. БАВТ moves/exchanges system
unit 57 to 30, leaves archive unit 40 available, sets unit 30's offset to
0200, and reads zones 01747–01752. With small-disk wrapping, the actual
system zones are 0147–0152.

Э72 transfers full disk descriptors, including scratch backing handles and
slice offsets. Numeric-volume rename retains the established offset reset;
scratch rename retains its backing offset. Physical-drum backing follows the
system volume's unit through either rename or exchange. АРФА regions have
additional per-unit state and are not newly enabled for these operations.

## Verification and limits

`make check2068` checks provenance, all populated payloads/tags, regenerated
control words, catalog bounds, deterministic rebuilding, and unchanged source
images. Its isolated sessions cover boot, Pascal catalog selection, BD dispatch and catalog listing, СЕРВИС
help, both БАВТ switch branches, АЛГ translator loading and file compilation/
execution, and Pascal compilation
and execution, including variables, a procedure and an integer function with
a May-compiler comparison. Compilation is also tested with both system
volumes on unit 57 at offset 0371 and the duplicate archive assembler erased.
Traces must show unit-57 reads of zones 007–013 and no assembler read through
unit 40. The emulator repository's `disk-units` test additionally reads and
writes scratch and numeric storage after Э72 operations and checks physical
reads before and after moves.
The integration tests use temporary HOME and private writable images.

АЛГ also compiles and executes a file created through `сис алг` and
`з …=тт`, printing 123 to the terminal; see [the verified recipe](algol.md).
СЕРВИС help works;
unimplemented historical OS/resource commands are not thereby implemented.
Overlays referenced outside zones 000–117 are not reconstructed. Pascal's
based/segmented loader mismatch with this ПУЛЬТ resident remains outside
this relocation.

МАВТ is recognized but its translator check fails with the standard unit-57
mapping; see [МАВТ recognition and loader investigation](mavt.md).
