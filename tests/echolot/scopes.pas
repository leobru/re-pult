_program SCOPES;
_type R=_array[1..2] _of integer;
_proced FIRST;
_type R=_array[1..5] _of integer;
_proced LEAF;
_var X:R;
_( _);
_( LEAF _);
_proced SECOND;
_var X:R;
_( _);
_( FIRST; SECOND _).
