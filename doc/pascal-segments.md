# Pascal segmentation regression

```sh
make checksegments DISPAK=/home/leob/git/dispak/build/dispak/dispak
```

The same test is included in `make check2068`. Run dispak outside the
sandbox. Sources are [main.pas](../tests/pascal-segments/main.pas) and
[segment.pas](../tests/pascal-segments/segment.pas); the standalone runner
is [tests/pascal-segments.py](../tests/pascal-segments.py).

## What is exercised

1. Create a private user archive and supply the two Pascal source files.
2. Compile SEGM with `X+`, exporting P26 (`E+`) and importing PINT
   (`EXTERNAL`). Save the based program using
   `пас сегм - зонгп 500300 1` to unit 50, zone 0300.
3. Compile/run the non-based main program. Export PINT and import P26.
4. Call LOAD with location 500300 and base 016000 (page 7).
5. Call P26 in the segment. It calls main's PINT, increments main's counter,
   and returns to the main program.
6. Call UNLOAD, then overwrite the entire former segment page with zeros.
7. LOAD the same segment at base 020000 (page 8), and call it again. An
   obsolete binding to the erased page would fail instead of passing.
8. UNLOAD again, restore every saved resident word, and compare the restored
   memory against the saved copy. Only a counter of two and exact resident
   restoration produce «СЕГМЕНТАЦИЯ ПРОШЛА».

Addresses, unit/zone numbers and Pascal B/C constants above are octal.
Page numbers 7/8 and the 480-word save area in the Pascal source are decimal.
The terminal must show two segment entries/returns, callbacks numbered 1
and 2, the success message, and normal return «ВСЕ СДЕЛАНО.» without АВОСТ.
The trace must contain exactly two segment reads from 50:0300. ЗАГР reads
into work page 035 and then relocates/copies to the requested destination;
it does not read directly into the final page.

## Temporary compatibility loader

The stock ПУЛЬТ resident does **not** contain the compiler's expected ЗАГР
at 077040. Therefore this is a segmentation test with a **temporary
compatible loader**, not evidence that the unchanged resident supports
segmentation directly.

The runner uses the existing loader from source 2248:01117, already copied
to 2068:0117. Its full six-byte-word source hash is checked:

```text
c1ed2fc74afae5244235810fa4c44f2873c3d6ebc86be8fd2b565cded7d4cf2c
```

Nine checked word replacements retarget the other monitor's register
save/restore entries, saved register cells, temporary words and restart to
those of the current ПУЛЬТ. These replacements reproduce the adaptation
in `pasauto-re/mkloader2.py`; the test has no runtime
dependency on that external repository and does not decode instructions.
The data mask at 077436 is copied unchanged. Only words 077040–077677 are
replaced; the rest of the loader fixture comes from the current resident.

This fixture is placed at zone 0400 of the private user disk. Main reads
it into page 30, saves words 077040–077777, installs the fixture during
LOAD/UNLOAD testing, and restores and checks all 480 words before returning.
Neither the built 2068 image nor either source system disk is modified.
The runner verifies their hashes after completion; HOME and writable disk
copies are isolated in a temporary directory.

## Results

The test passed with the repaired December compiler in reconstructed 2068:

```text
ЗАГРУЗКА 7
СЕГМЕНТ ВХОД
ВЫЗОВ          1
СЕГМЕНТ ВОЗВРАТ
ВЫГРУЗКА 7
ЗАГРУЗКА 8
СЕГМЕНТ ВХОД
ВЫЗОВ          2
СЕГМЕНТ ВОЗВРАТ
СЕГМЕНТАЦИЯ ПРОШЛА
ВСЕ СДЕЛАНО.
```

Session inputs, terminal output and extracode traces are written to
`build/pascal-segments/{archive,compile-segment,run}.{txt,out,trace}`.
