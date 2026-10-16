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
