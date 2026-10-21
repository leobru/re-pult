_program GROUPS;
_type R=_record
 A,B:integer;
 _case K:boolean _of
 true:(C,D:integer);
 false:(E:integer)
_end;
_var G:R;
_proced P(X,Y:integer; _var U,V:R);
_var L:R;
_( _);
_( P(1,2,G,G) _).
