(*=T-,P-*)
_PROGRAM INTPR;
_VAR T:TEXT; I,J,P:INTEGER;
_PROCEDURE PRINT(N:INTEGER);
_BEGIN
    WRITELN('[',N:0,'][',N:5,'][',N:16,'][',N,']');
    WRITELN(T,'[',N:0,'][',N:5,'][',N:16,'][',N,']')
_END;
_BEGIN
    REWRITE(T); PRINT(0); P:=1;
    _FOR I:=0 _TO 12 _DO _BEGIN
        _FOR J:=-1 _TO 1 _DO _BEGIN
            PRINT(P+J); PRINT(-P-J)
        _END;
        _IF I<12 _THEN P:=P*10
    _END;
    P:=1;
    _FOR I:=1 _TO 39 _DO _BEGIN
        P:=P+P;
        PRINT(P-1); PRINT(-P); PRINT(-P+1);
        PRINT(P); PRINT(P+1)
    _END;
    PRINT(P-1+P); PRINT(-P-P); PRINT(-P-P+1);
    WRITELN('ТЕКСТ'); RESET(T);
    _WHILE _NOT EOF(T) _DO _BEGIN
        _IF EOLN(T) _THEN WRITELN _ELSE WRITE(T@);
        GET(T)
    _END;
    WRITELN('ЦЕЛЫЕ ПРОВЕРЕНЫ')
_END.
