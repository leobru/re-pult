# TODO

## dispak

- Implement `Э62 43` (`reg[016] == 043` in `e62()`, dispak/extra.c): keep the
  job in the input queue for a future restart. ПУЛЬТ's `new` command
  (ПУСК 01036) issues it. dispak currently has no case for 043, so `new`
  stops with АВОСТ 3 («Пока рано»).
