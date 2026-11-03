(*=T-,P-*)
_PROGRAM BOUNDS;
_VAR T:TEXT; X:REAL; I,D:INTEGER;
_PROCEDURE PRINT;
_BEGIN
    _FOR D:=1 _TO 10 _DO _BEGIN
        WRITELN('[',I:0,'][',D:0,'][',X:26:D,']');
        WRITELN(T,'[',I:0,'][',D:0,'][',X:26:D,']')
    _END
_END;
_BEGIN
    REWRITE(T);
@CASES@
    RESET(T);
    _WHILE _NOT EOF(T) _DO _BEGIN
        _IF EOLN(T) _THEN WRITELN _ELSE WRITE(T@);
        GET(T)
    _END;
    WRITELN('ГРАНИЦЫ ПРОВЕРЕНЫ')
_END.
