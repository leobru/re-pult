_program FRAME;
_var G:integer;
_proced OUTER(_var A:integer; B,C:integer);
_var X:integer;
_function INNER(_var V:integer; N:integer):integer;
_( V:=V+N; INNER:=V _);
_( X:=INNER(A,B)+C _);
_( OUTER(G,2,3) _).
