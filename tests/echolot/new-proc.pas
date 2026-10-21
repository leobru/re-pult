_program CHECK;
_type NODE=_record X:integer; NEXT:@NODE _end;
_var P:@NODE;
_proced ALLOC;
_( NEW(P) _);
_( ALLOC _).
