_program CHECK;
_type NODE=_record X:integer; NEXT:@NODE _end;
_var P:@NODE;
_( NEW(P); P@.X:=1 _).
