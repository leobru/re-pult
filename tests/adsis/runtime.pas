(*=T-,P-*)
_PROGRAM ADSIS;
_TYPE
    BITS = _SET _OF 0..47;
    NODE = _RECORD VALUE: INTEGER; NEXT: @NODE _END;
_VAR
    I,J,K,SUM: INTEGER;
    X,Y: REAL;
    OK: BOOLEAN;
    P,Q: @NODE;
    F: _FILE _OF INTEGER;
    T: TEXT;
    A,B: ALFA;
    CH: CHAR;
    CHARS: _ARRAY [1..6] _OF CHAR;
    S: BITS;
_PROCEDURE ADD(N:INTEGER);
    _PROCEDURE INNER;
    _BEGIN SUM:=SUM+N _END;
_BEGIN INNER _END;
_BEGIN
    OK:=TRUE;
    SUM:=0; ADD(7); ADD(8);
    _IF SUM<>15 _THEN OK:=FALSE;
    I:=37; J:=5; K:=I _DIV J;
    _IF (K<>7) _OR (I _MOD J<>2) _THEN OK:=FALSE;
    X:=I; Y:=X/4;
    _IF (TRUNC(Y)<>9) _OR (ROUND(Y)<>9) _THEN OK:=FALSE;
    WRITELN('АРИФМЕТИКА ',K:0,' ',I _MOD J:0,' ',Y:10:3);
    NEW(P); NEW(Q); P@.VALUE:=17; P@.NEXT:=Q; Q@.VALUE:=25;
    _IF P@.VALUE+P@.NEXT@.VALUE<>42 _THEN OK:=FALSE;
    DISPOSE(Q); DISPOSE(P);
    WRITELN('ПАМЯТЬ ',OK);
    A:='ABCXYZ'; UNPCK(CHARS[1],A); PCK(CHARS[1],B);
    _IF A<>B _THEN OK:=FALSE;
    MAPIA(12345B,A); MAPAI(A,I);
    _IF I<>12345B _THEN OK:=FALSE;
    MAPГA('A',CH); MAPЯГA('ABCXYZ',B);
    WRITELN('ПЕРЕКОДИРОВКА ',A,' ',ORD(CH):0);
    I:=3; J:=5; S:=[I,J..7];
    _IF (CARD(S)<>4) _OR (MINEL(S)<>3) _THEN OK:=FALSE;
    _IF _NOT (6 _IN S) _THEN OK:=FALSE;
    WRITELN('МНОЖЕСТВА ',CARD(S):0,' ',MINEL(S):0);
    REWRITE(F);
    _FOR I:=1 _TO 1030 _DO _BEGIN F@:=I; PUT(F) _END;
    RESET(F); SUM:=0;
    _FOR I:=1 _TO 1030 _DO _BEGIN
        _IF F@<>I _THEN OK:=FALSE;
        SUM:=SUM+F@; GET(F)
    _END;
    _IF (SUM<>530965) _OR _NOT EOF(F) _THEN OK:=FALSE;
    WRITELN('ФАЙЛ ',SUM:0,' ',EOF(F));
    REWRITE(T); WRITELN(T,'123 45'); RESET(T);
    I:=0; _WHILE T@<>' ' _DO _BEGIN I:=10*I+ORD(T@); GET(T) _END;
    GET(T); J:=0; _WHILE _NOT EOLN(T) _DO _BEGIN J:=10*J+ORD(T@); GET(T) _END;
    _IF (I<>123) _OR (J<>45) _THEN OK:=FALSE;
    WRITELN('ТЕКСТ ',I:0,' ',J:0);
    _IF OK _THEN WRITELN('АДСИС ПРОШЛА')
    _ELSE WRITELN('ОШИБКА АДСИС')
_END.
