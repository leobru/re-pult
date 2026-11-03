(*=T-,P-*)
_PROGRAM FILETEST;
_TYPE REC = _RECORD A,B,C:INTEGER _END;
_VAR F,G:_FILE _OF REC; P:_PACKED _FILE _OF 0..7;
     I,SUM:INTEGER; OK:BOOLEAN;
_BEGIN
    OK:=TRUE;
    REWRITE(F); REWRITE(G); REWRITE(P);
    _FOR I:=1 _TO 400 _DO _BEGIN
        F@.A:=I; F@.B:=I+1; F@.C:=I+2; PUT(F);
        G@.A:=-I; G@.B:=I*2; G@.C:=I*3; PUT(G)
    _END;
    _FOR I:=1 _TO 1030 _DO _BEGIN P@:=I _MOD 8; PUT(P) _END;
    RESET(F); RESET(G); SUM:=0;
    _FOR I:=1 _TO 400 _DO _BEGIN
        _IF (F@.A<>I) _OR (F@.B<>I+1) _OR (F@.C<>I+2) _THEN OK:=FALSE;
        _IF (G@.A<>-I) _OR (G@.B<>I*2) _OR (G@.C<>I*3) _THEN OK:=FALSE;
        SUM:=SUM+F@.A+F@.B+F@.C+G@.A+G@.B+G@.C;
        GET(F); GET(G)
    _END;
    _IF _NOT EOF(F) _OR _NOT EOF(G) _THEN OK:=FALSE;
    WRITELN('ЗАПИСИ ',SUM:0);
    RESET(P); SUM:=0;
    _FOR I:=1 _TO 1030 _DO _BEGIN
        _IF P@<>I _MOD 8 _THEN OK:=FALSE;
        SUM:=SUM+P@; GET(P)
    _END;
    _IF _NOT EOF(P) _THEN OK:=FALSE;
    WRITELN('УПАКОВКА ',SUM:0);
    _IF OK _THEN WRITELN('ФАЙЛЫ ПРОШЛИ') _ELSE WRITELN('ОШИБКА ФАЙЛОВ')
_END.
