(*=T-,P-*)
_PROGRAM REALPR;
_VAR T:TEXT; I,W,D,K:INTEGER; X:REAL;
_PROCEDURE PRINT(N:REAL);
_BEGIN
    I:=I+1;
    _FOR K:=0 _TO 7 _DO _BEGIN
        _CASE K _OF
        0: _BEGIN W:=0; D:=0 _END;
        1: _BEGIN W:=1; D:=1 _END;
        2: _BEGIN W:=10; D:=3 _END;
        3: _BEGIN W:=20; D:=6 _END;
        4: _BEGIN W:=26; D:=10 _END;
        5: _BEGIN W:=26; D:=11 _END;
        6: _BEGIN W:=20; D:=-1 _END;
        7: _BEGIN W:=0; D:=10 _END
        _END;
        WRITELN('[',I:0,'][',W:0,'][',D:0,'][',N:W:D,']');
        WRITELN(T,'[',I:0,'][',W:0,'][',D:0,'][',N:W:D,']')
    _END;
    WRITELN('[',I:0,'][',N,'][',N:20,']');
    WRITELN(T,'[',I:0,'][',N,'][',N:20,']')
_END;
_BEGIN
    I:=0; REWRITE(T);
    PRINT(0.0); PRINT(1.0); PRINT(-1.0);
    PRINT(9.25); PRINT(-9.25); PRINT(0.125); PRINT(-0.125);
    PRINT(1.25); PRINT(1.75); PRINT(9.5); PRINT(-9.5);
    PRINT(9.9994); PRINT(9.9995); PRINT(9.9996);
    PRINT(99.994); PRINT(99.995); PRINT(99.996);
    PRINT(0.99994); PRINT(0.99995); PRINT(0.99996);
    PRINT(1.2345678901); PRINT(-1.2345678901);
    X:=1.0/1.0E18; PRINT(X/10.0); PRINT(-X/10.0);
    PRINT(X); PRINT(1.0E-10); PRINT(1.0E10);
    PRINT(1.0E18); PRINT(-1.0E18);
    X:=1.0; _FOR W:=1 _TO 60 _DO X:=X*0.5;
    PRINT(X); PRINT(X*0.5); PRINT(-X*0.5);
    X:=1.0;
    _FOR W:=1 _TO 63 _DO X:=X*0.5;
    X:=X*0.5; PRINT(X); X:=X*0.5; PRINT(X);
    X:=1.0; _FOR W:=1 _TO 62 _DO X:=X*2.0;
    PRINT(X); PRINT(-X); PRINT(X*1.5); PRINT(-X*1.5);
    WRITELN('ТЕКСТ'); RESET(T);
    _WHILE _NOT EOF(T) _DO _BEGIN
        _IF EOLN(T) _THEN WRITELN _ELSE WRITE(T@);
        GET(T)
    _END;
    WRITELN('ВЕЩЕСТВЕННЫЕ ПРОВЕРЕНЫ')
_END.
