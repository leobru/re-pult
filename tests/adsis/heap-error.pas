(*=K1,T-,P-*)
_PROGRAM HEAPTEST;
_TYPE BIG = _ARRAY [1..1025] _OF INTEGER;
_VAR P:@BIG; Q,SAVED:@INTEGER;
_BEGIN
    SETUP(SAVED);
    NEW(P);
    _IF P=_NIL _THEN WRITELN('БОЛЬШОЙ NIL') _ELSE WRITELN('ОШИБКА NEW');
    NEW(Q);
    _IF Q=_NIL _THEN WRITELN('ПОСЛЕ NIL') _ELSE WRITELN('ОШИБКА ГРАНИЦЫ');
    ROLLUP(SAVED); NEW(Q); Q@:=42;
    WRITELN('ВОССТАНОВЛЕНО ',Q@:0)
_END.
