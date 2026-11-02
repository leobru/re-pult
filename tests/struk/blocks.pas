_program BLOCKS;
_type REC=_record N:integer _end;
_var R:REC;
_proced WORK;
_(
 _if true _then _( R.N:=1 _);
 _case R.N _of 1:R.N:=2; 2:R.N:=3 _end
_);
_( WORK _).
