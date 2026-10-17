# BD and the database catalog

All zone and memory addresses below are octal.

## Disk layout on 2068

| Zone | Contents | Use |
|---|---|---|
| 026 | BD dispatcher (КОБЛА in the historical module catalog) | Callable command; parses database subcommands |
| 027 (start) | БАНДИТ implementation | Loaded internally; no directly callable archive entry |
| 030 | КТЛБД | Database catalog, non-executable; no callable archive entry |

The implementation starts at 027; its exact active code extent is not
established here. Zone 030 has the
separate catalog role, not an executable BD subcommand overlay.
On both source disks these correspond to zones 01026, 01027 and 01030.
Their payloads are identical between 2148 and 2248 and are preserved in 2068.
In zone 030, word 1677 contains the GOST name `КТЛБД`; the following words
include database names and location values. The catalog's role does not
make preceding code-looking words an executable entry point.

Select the archive with `арх сисбиб,40,0`, then enter `bd` to invoke the
restored dispatcher. With no subcommand it prints «BD, А ДАЛЬШЕ».
This entry and the read of unit 40 zone 026 have been tested under dispak.

## Commands in the manual

Source: [Markdown transcription](PULT.md#pdf-033) of [PULT.pdf](../PULT.pdf),
**PDF page 33, right-hand side,
printed page 63**, §II.3, «Приказы базы данных МАРС».
This is the manual's historical command table; its prefix is printed `БД`.
The tested reconstructed archive entry is Latin `BD`.

| Manual command | Short form / synonym shown | Meaning in the manual |
|---|---|---|
| `БД NEW` | — | Create a new database |
| `БД OPEN` | `ОТ` | Open a database from the common КТЛБД catalog |
| `БД PUT` | `П` | Store a record |
| `БД GET` | `Ч`, `БД OBTAIN`, `БД OBT` | Read a record |
| `БД DELETE` | `БД DEL`, `У` | Delete a record |
| `БД КТЛ` | `К` | Print the database catalog |
| `БД ИНФ` | — | Information on who wrote it and when |
| `БД OPENT` | — | Open one's own/current database |
| `БД MOD` | `М` | Write a record under an existing name |
| `БД ПЕРЕБД` | — | Rewrite the database |

The manual lists the short forms as separate commands. Their presence in
this table alone does not establish that this later ПУЛЬТ build implements
them, or that the Cyrillic prefix is an alias for the restored Latin entry.

## Evidence from the surviving dispatcher

At runtime base 066000, the name/handler table at **66472–66521** contains:
`NEW`, `OPEN`, `OBTAIN`, `OBT`, `PUT`, `DELETE`, `DEL`, `MODIFY`, `MOD`,
`GET`, `ИНФ`, `КТЛ`. It is followed by another table at **66523–66537**
containing `СИС`, `ТАБ`, `БУФ`, `ДЛВ`, `СИМ`, `СЛО`.
`OPENT` and `ПЕРЕБД` are not present in these dispatcher tables;
the historical manual therefore must not be presented as a list of tested
commands for the recovered version.

Descriptors at **66174** and **66245** read unit 40 zone 027, independently
of the callable archive catalog. Thus exposing the dispatcher at 026 does
not require making БАНДИТ a callable file. The implementation and catalog
zones remain outside callable catalog entries on reconstructed 2068.
The integration tests verify dispatch and the catalog listing described below.
Creation/modification of database records is not covered.

## Observed `BD КТЛ` result on 2068

An isolated run of `арх сисбиб,40,0`, `bd ктл`, `конец` prints:

```text
СТЕРТА БД-СИСТЕМА
```

It returns normally to the command loop, without listing database names.
The extracode trace shows loading the dispatcher from unit 40 zone 026,
but no subsequent read of zone 027 or 030. Thus the dispatcher is callable,
while this invocation does not yet reach the database catalog. This message
alone does not establish that the disk copy of БАНДИТ is damaged.
The captured session and output are in `build/bd-catalog/`.

The failure is an **in-memory БАНДИТ signature check**, not a disk check:

```text
66016  XTA 1011(13); ATX 1012(13)     base pointer at 67012 := 074000
66724  WTC 1012(13); XTA 1           read memory[074001]
66725  AEX 1016(13); U1A 112(13)     compare with 67016 = БАНДИТ
```

The trace records memory 074001 as `0000000000000000`, while the expected
GOST word is `1022005511024062` (БАНДИТ). The mismatch branches to 66112.
Register 16 was set to the message address 66204 at 66723; 66112 copies it
to register 15, and 66113 calls print entry 76005. The dispatcher therefore
requires БАНДИТ already resident at base 074000 for this catalog invocation.

### Opening КТЛБД first

Running `bd open ктлбд` before `bd ктл` changes the result:

```text
bd open ктлбд
ЗАТЕРТ 1Й ЛИСТ БД
bd ктл
000000
```

The OPEN trace reads unit 40 zone 027 into page 36 and the БАНДИТ
signature at 074001 then passes. БАНДИТ reads unit 40 zone 030 into page
34, followed by zone 0651. Zone 0651 lies outside reconstructed 2068's
populated range 000–117 and is blank. The subsequent `BD КТЛ` no longer
reports a missing БАНДИТ image, but prints `000000`; it reads zone 0651
again. This is not a successful listing of the database catalog.
The latest captured session in `build/bd-catalog/` contains this sequence.

### Successful catalog selection

The self-entry is **КТЛBD**, with Latin BD (displayed as КТЛВD), not
КТЛБД. `bd open ктлBD` followed by `bd ктл` successfully lists all
21 directory names. See [zone format, trace and complete decoded catalog](bd-catalog.md).
