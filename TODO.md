# TODO

## dispak

- Implement `Э62 43` (`reg[016] == 043` in `e62()`, dispak/extra.c): keep the
  job in the input queue for a future restart. ПУЛЬТ's `new` command
  (ПУСК 01036) issues it. dispak currently has no case for 043, so `new`
  stops with АВОСТ 3 («Пока рано»).
- Implement the other `Э62` subcodes that СТАТИС uses (`гост АЦПУ`,
  `гост FREETT`, `гост RUNTT`; see statis.pas):
  - 041: read an input or output stream, part k given in A (01340000+k);
  - 056: return the mask of occupied terminals;
  - 057: attach a free terminal;
  - 060: return the mask of free terminals.
  dispak's `e62()` handles 057 as "acquire a terminal by number" (a stub);
  041, 056 and 060 are missing.
- `Э62` "set volume offset" (default case of `e62()`, reg[016] = unit << 9 |
  offset) stores all 9 low bits as the offset. On a "29 MB" volume (dispak's
  disks ≥ 2048, cf. `Э50 0112`) the lowest 5 bits of the offset must be
  ignored. АЛГ issues `Э62 040302`: that should give offset 0300, so its
  translator image is 2248 zone 0315. dispak uses 0302 and reads zone 0317,
  so `алг` fails with «ПЛОХО С Э60» (see AGENTS.md, «АЛГ»).
- `--725` should also mask zone numbers to 01777 (`(zone + offset) &
  01777`), as `BESM6_SMALL_DISKS` does: ddio() (extra.c) picks the mask
  from that variable only, not from `SMALL_DISKS()`. БАВТ's `бавт` sets unit
  30's offset to 0200 and reads zone 01747, which on a 7.25 MB disk is zone
  0147 (БЕМШ). Without the mask, dispak reads zone 02147.
- `Э72` rename (037) and exchange (030) reject a scratch tape (`ЛЕНТ 30(1С)`):
  they test `disks[u].diskno`, which is 0 for scratch volumes, instead of
  also `diskh`. `бавт` exchanges units 40 and 30 (БАВТ 01302) and stops
  with АВОСТ 56 «ДАЙ РАБ.В ЭК.РЕС».
