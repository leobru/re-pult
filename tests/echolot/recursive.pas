_program CHECK;
_proced AGAIN(N:integer);
_var A:_array[1..5] _of integer;
_( _if N>0 _then AGAIN(N-1) _);
_( AGAIN(2) _).
