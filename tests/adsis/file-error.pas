(*=T-,P-*)
_PROGRAM ADSERR;
_VAR F: _FILE _OF INTEGER;
_BEGIN
    REWRITE(F); F@:=17; PUT(F); RESET(F); GET(F); GET(F);
    WRITELN('ПРОПУЩЕН КОНТРОЛЬ EOF')
_END.
