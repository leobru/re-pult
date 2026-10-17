(*=T-,P-*)
_PROGRAM TEST;
_TYPE PW = @INTEGER;
_VAR
    I, W, COUNT: INTEGER;
    P, Q: PW;
    RESTORED: BOOLEAN;
    SAV: _ARRAY [0..479] _OF INTEGER;
_PROCEDURE P26; EXTERNAL;
(*=E+*)
_PROCEDURE PINT;
(*=E-*)
_BEGIN
    COUNT := COUNT + 1;
    WRITELN('ВЫЗОВ ', COUNT);
_END;
_PROCEDURE LAD(UNITZONE, ADDRESS: INTEGER);
_BEGIN
    ADDRESS := ADDRESS;
    CODE(УИ14=);
    UNITZONE := UNITZONE;
    CODE(15ПВLOAD=,);
_END;
_PROCEDURE ZAGR(ENABLE: BOOLEAN);
_BEGIN
    _FOR I := 0 _TO 479 _DO _BEGIN
        P := PTR(77040B + I);
        _IF ENABLE _THEN _BEGIN
            Q := PTR(61040B + I);
            SAV[I] := P@;
            P@ := Q@
        _END _ELSE
            P@ := SAV[I]
    _END
_END;
_BEGIN
    CODE(Э075=,);
    W := 0010300000500400C;
    I := ORD(REF(W));
    I := I;
    CODE(УИ14=14Э070,);
    ZAGR(TRUE);
    COUNT := 0;
    WRITELN('ЗАГРУЗКА 7');
    LAD(500300B,16000B);
    P26;
    CODE(15ПВUNLOAD=,);
    WRITELN('ВЫГРУЗКА 7');
    _FOR I := 0 _TO 1023 _DO _BEGIN
        P := PTR(16000B + I);
        P@ := 0
    _END;
    WRITELN('ЗАГРУЗКА 8');
    LAD(500300B,20000B);
    P26;
    CODE(15ПВUNLOAD=,);
    ZAGR(FALSE);
    RESTORED := TRUE;
    _FOR I := 0 _TO 479 _DO _BEGIN
        P := PTR(77040B + I);
        _IF P@ <> SAV[I] _THEN RESTORED := FALSE
    _END;
    _IF RESTORED = FALSE _THEN COUNT := -1;
    _IF COUNT = 2 _THEN
        WRITELN('СЕГМЕНТАЦИЯ ПРОШЛА')
    _ELSE
        WRITELN('ОШИБКА СЕГМЕНТАЦИИ ', COUNT)
_END.
