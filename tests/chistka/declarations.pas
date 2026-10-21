_program CHECK;
_label 10,20;
_const LIVE=1; DEAD=2;
_type USEDTY=integer; IDLETY=real;
_var USED:USEDTY; IDLE:IDLETY;
_proced CALLED;
_( write(USED) _);
_proced NEVER;
_( USED := DEAD _);
_( USED := LIVE; CALLED; 10: writeln(USED) _).
