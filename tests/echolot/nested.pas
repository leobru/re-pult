_program CHECK;
_var G:_array[1..10] _of integer;
_proced LEAF(A:integer);
_var TMP:_array[1..5] _of real;
_( TMP[1]:=A; writeln(TMP[1]) _);
_proced TOP;
_var X:integer;
_( LEAF(X) _);
_( TOP _).
