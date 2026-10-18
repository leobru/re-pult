(*=T+,P-*)
_PROGRAM ADSERR;
_VAR A: _ARRAY [1..2] _OF INTEGER; I: INTEGER;
_BEGIN
    I:=3; A[I]:=7;
    WRITELN('ПРОПУЩЕН КОНТРОЛЬ ИНДЕКСА')
_END.
