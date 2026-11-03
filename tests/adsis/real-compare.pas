(*=R+,T-,P-*)
_PROGRAM CMPTEST;
_VAR X,Y:REAL; OK:BOOLEAN;
_BEGIN
    OK:=TRUE; X:=1000000.0; Y:=X+0.5;
    _IF X<>Y _THEN OK:=FALSE;
    _IF X<Y _THEN OK:=FALSE;
    _IF X>Y _THEN OK:=FALSE;
    WRITELN('ДОПУСК ',OK);
    Y:=X+2.0;
    _IF X=Y _THEN OK:=FALSE;
    _IF _NOT (X<Y) _THEN OK:=FALSE;
    _IF X>Y _THEN OK:=FALSE;
    _IF -X=Y _THEN OK:=FALSE;
    X:=0.0; Y:=0.0;
    _IF X<>Y _THEN OK:=FALSE;
    WRITELN('РАЗЛИЧИЕ ',OK);
    X:=1000000.0; Y:=X+0.5;
    (*=R-*)
    _IF X=Y _THEN OK:=FALSE;
    _IF _NOT (X<Y) _THEN OK:=FALSE;
    _IF OK _THEN WRITELN('СРАВНЕНИЯ ПРОШЛИ') _ELSE WRITELN('ОШИБКА СРАВНЕНИЯ')
_END.
