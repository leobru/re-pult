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
