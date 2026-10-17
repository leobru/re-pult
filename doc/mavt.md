# МАВТ on reconstructed 2068

МАВТ is recognized, but autocode translation is not currently functional
with the standard `pult2068.b6` volume mapping.
All addresses below are octal; volume identifiers are decimal.

## Recognition and input

БАВТ's table contains `МАВТ` at **66076**, with handler offset **0714**
at 66077, giving entry **66714**. This table and handler are unchanged in
2068, 2148 and 2248.

- `мавт` uses the current text buffer. With an empty buffer, it prints
  «НЕТ СИМВОЛОВ КОНЦА» and returns normally.
- `мавт NAME` first calls archive lookup **76006**, at **66725**, to load
  the named source. It therefore requires a valid attached source archive.
- The buffer scanner at **66732–66757** looks for consecutive byte codes
  **063, 0140** before proceeding to the translator loader.

## Translator loading

The handler saves the source to drum 23 and then loads five translator zones.
At **66767–66775**, it compares unit 40's volume number with **2048**
(constant **67325 = 020110**, BCD). For 2048 it reads unit 40 zones
**01600–01604** using descriptor 67371. Otherwise, including 2068, it reads
**unit 57 zones 0600–0604** using descriptor 67372.

The standard reconstructed deck mounts unit 57 at offset **0371** for
Pascal's ITM assembler. Consequently these МАВТ reads address system-volume
zones **01171–01175**. The loaded image fails the check at **66776–66777**:
memory **04251** must equal constant **67373 = 0010063200120307**.
The failure path at **67000–67010** prints «НЕТ АВТОКОД ТРАНСЛЯТОРА» and
returns to the command loop.

This establishes a loader/layout failure with the current mapping. It does
not establish that a suitable translator is absent everywhere on 2148/2248.
The historical АВТТРН entry at zones 071–074 in PULT.pdf is not what this
later handler reads; those zones now contain other files.

## Verification

Three isolated runs used the current `build/volumes/2068`, private writable
copies of the disks, and dispak outside the sandbox:

| Input / setup | Result |
|---|---|
| `мавт`, empty buffer | «НЕТ СИМВОЛОВ КОНЦА», normal return |
| `мавт xyz`, no source archive attached | Archive diagnostic «СТОИТ…МЛ…», normal return |
| `мавт`, synthetic end-marker bytes 063,0140 at memory 010000 | Writes source to drum 23, reads unit 57 zones 0600–0604, then «НЕТ АВТОКОД ТРАНСЛЯТОРА» |

The synthetic buffer tests the loader path, not successful assembly of a
valid autocode program. Outputs and instruction traces are in
`build/mavt/{empty,named,terminated}.{out,trace}`; the probe is
`build/mavt/probe.py`. These build artifacts are not committed.
