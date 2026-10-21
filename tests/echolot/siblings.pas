_program CHECK;
_proced SMALL; _var X:integer; _( X:=1 _);
_proced BIG; _var A:_array[1..20] _of integer; _( A[1]:=1 _);
_proced DEAD; _var A:_array[1..100] _of integer; _( A[1]:=1 _);
_( SMALL; BIG _).
