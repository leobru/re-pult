(*=T-,P-*)
_PROGRAM LIMIT;
_VAR T:TEXT; X:REAL; D:INTEGER;
_BEGIN
    CODE(СЧRAW=ПБREADY,С;RAW:@WORD@,К;READY:);
    X:=;
    REWRITE(T);
    _FOR D:=1 _TO 10 _DO _BEGIN
        WRITELN('[',D:0,'][',X:26:D,']');
        WRITELN(T,'[',D:0,'][',X:26:D,']')
    _END;
    WRITELN('ТЕКСТ'); RESET(T);
    _WHILE _NOT EOF(T) _DO _BEGIN
        _IF EOLN(T) _THEN WRITELN _ELSE WRITE(T@);
        GET(T)
    _END;
    WRITELN('ПРЕДЕЛ ПРОВЕРЕН')
_END.
