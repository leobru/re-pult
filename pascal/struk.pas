(*=p-,t-,l-,k4*)_program СТРУК;
(* Structure of Pascal source, PULT 2148/2248 zone 01073, 11.11.86.
   Rebuild: tests/struk.py; all 1024 original words match with date 11.11.86.
   Addresses in comments are octal. Six initial identifier characters matter.
   SELECT and the final jumps preserve the original unreachable branches. *)
_label 1345,1407;
_const
 RowWords=8; Space=' '; Spaces='      ';
 KWBegin='BEGIN '; KWEnd='END   '; KWSelect='SELECT'; KWCase='CASE  ';
 KWProcedure='PROCED'; KWFunction='FUNCTI';
 EndText='≡172'; Star='*'; Quote=''''; EndLine='≡175'; Underline='_';
 Semicolon=';'; OpenParen='('; CloseParen=')';
_type
 letter='А'..'Z'; digit='0'..'9'; chars6=_array[1..6] _of char;
 row=_record name,parent:alfa; level,declared,first,last:integer;
             forward:boolean; isfunc:integer _end;
 rowptr=@row;
_var
 toFile,alphabet:boolean; base:rowptr; line,i,count:integer;
 option:alfa; isfunc:boolean;

(* 00166: diagnostics return to the command prompt. *)
_proced Fail(error:integer);
_(
 rewrite(output);
 writeln('ОШИБКА ',error:0,' СТР.=',line:0);
 code(16ПВ74070=,); (* АДСИС: print the current INPUT context. *)
 _goto 1345
_);

(* 00204: connect INPUT to contiguous zones. *)
_proced BindInput(address,zones:integer);
_const InputZone=0010340000000000C;
_var descriptor:integer;
_(
 descriptor:=InputZone;
 code(2ЦС3=ЗЧ75211,2СЧ4=У076002,АВ13=ЗЧ75212,)
_);

(* 00216: redirect OUTPUT to the requested storage area. *)
_proced BindOutput(address,zones:integer);
_const OutputZone=0000350000000000C;
_var descriptor:integer;
_(
 descriptor:=OutputZone;
 code(2ЦС3=ЗЧ75203,ЗЧ75223=2СЧ4,У076002=ЦС13,ЗЧ75204=,)
_);

(* 00231: terminate and flush a saved report; restore drum output. *)
_proced FlushReport;
_(
 write(EndText,EndLine,Spaces);
 code(СЧ75235=ЦС13,СР75204=У074275,Э07075223=,);
 BindOutput(270000B,1); rewrite(output)
_);

(* 00250: eight-word entries are contiguous in the Pascal heap. *)
_proced Allocate(_var p:rowptr);
_(
 new(p);
 _if p=_nil _then _(
  rewrite(output); writeln('КОНЧИЛОСЬ МЕСТО'); rollup(base); _goto 1345
 _);
 count:=count+1
_);

(* 00267: recursively nested Pascal comments. *)
_proced SkipComment;
_label 271;
_var previous:char;
_(
 271:
  previous:=input@; get(input);
  _select
  previous=EndText: _( rewrite(output); writeln('НЕЗАК.КОМ.'); Fail(3) _);
  previous=EndLine: line:=line+1;
  (previous=OpenParen) _and (input@=Star): _(
   get(input); SkipComment
  _);
  (previous=Star) _and (input@=CloseParen): _(
   get(input); exit
  _)
  _end;
 _goto 271
_);

(* 00322: spaces, line ends and comments. *)
_proced SkipSpaces;
_label 324;
_(
 324:
 _select
  input@=Space: get(input);
  input@=EndLine: _( line:=line+1; get(input) _);
  input@=OpenParen: _(
   get(input);
   _if input@=Star _then SkipComment
   _else _( input@:=OpenParen; exit _)
  _);
  true: exit
 _end;
 _goto 324
_);

(* 00346: six-letter token; excess letters and digits are consumed. *)
_proced ReadWord(_var word:alfa; skip:boolean);
_var chars:chars6; n:integer;
_(
 _if skip _then SkipSpaces;
 _if input@=OpenParen _then _( word:=KWBegin; get(input) _)
 _else _if input@=CloseParen _then _( word:=KWEnd; get(input) _)
 _else _(
  word:=Spaces; unpck(chars[1],word); n:=1;
  _while ((input@ _in letter) _or (input@ _in digit)) _and (n<7) _do _(
   chars[n]:=input@; n:=n+1; get(input)
  _);
  _while (input@ _in digit) _or (input@ _in letter) _do get(input);
  pck(chars[1],word)
 _)
_);

(* 00466: bubble sort, swapping complete eight-word entries. *)
_proced SortRows;
_var limit,j:integer; left,right,first:rowptr; saved:row; changed:boolean;
 (* 00434: compare the top byte, then the remaining 40 bits.
    CODE keeps the original shifts and accumulator transfers; M3 is this frame. *)
 _function Greater(_var a,b:alfa):boolean;
 _var headA,headB,tailA,tailB:integer;
 _(
  code(=3ИК4,СЧ=СД/-10/,МР=3ЗЧ6,3ИК5=СЧ,СД/-10/=МР,); headB:= ;
  _if headA<headB _then _( Greater:=false; exit _);
  _if headA>headB _then _( Greater:=true; exit _);
  code(3ИК4=СЧ,СД/-10/=СД/10/,3ЗЧ10=3ИК5,СЧ=СД/-10/,СД/10/=3ЗЧ11,);
  Greater:=tailA>tailB
 _);
_(
 _if count>2 _then _(
  limit:=count-1; first:=ptr(ord(base)+RowWords);
 _) _else exit;
 _repeat
  changed:=false; j:=1; left:=first;
  _while j<limit _do _(
   right:=ptr(ord(left)+RowWords);
   _if Greater(left@.name,right@.name) _then _(
    saved:=right@; right@:=left@; left@:=saved; changed:=true
   _);
   j:=j+1; left:=right
  _)
 _until _not changed
_);

(* 00537: skip literals and trivia, then return one Pascal token. *)
_proced NextWord(_var word:alfa);
_label 541;
_(
 541:
 _select
  input@=EndText: Fail(1);
  input@=EndLine: _( line:=line+1; get(input) _);
  input@=Quote: _(
   get(input);
   _while input@<>Quote _do _(
    _if input@=EndLine _then line:=line+1;
    get(input)
   _);
   get(input)
  _);
  input@=Underline: _(
   get(input); ReadWord(word,false); exit
  _);
  input@=OpenParen: _(
   get(input); _if input@=Star _then SkipComment
  _);
  true: get(input)
 _end;
 _goto 541
_);

(* 00604: terminal newline or a literal line end in the report file. *)
_proced NewLine;
_( _if toFile _then write(EndLine) _else writeln _);

(* 00613: four decimal digits, including leading zeroes. *)
(*=m-*)
_proced PrintLine(n:integer);
_(
 write(chr(n _div 1000)); n:=n _mod 1000;
 write(chr(n _div 100)); n:=n _mod 100;
 write(chr(n _div 10),chr(n _mod 10))
_);

(*=m+*)

(* 00635: source order (false) or alphabetical procedure listing (true). *)
_proced PrintTable(sorted:boolean);
_var p:rowptr; k:integer;
_(
 _if sorted _and (count<>1) _then _(
  count:=count-1; p:=ptr(ord(base)+RowWords);
 _) _else p:=base;
 _if toFile _then _(
  _if sorted _then write('ЬЬЛЬЬЗ')
  _else write('ЬЬМLУЬЬЗ')
 _)
 _else _if sorted _then _(
  NewLine;
  _for k:=1 _to 12 _do write('------');
  NewLine; NewLine
 _);
 _if sorted _then write('* * *   СПИСОК ПРОЦЕДУР/ФУНКЦИЙ   * * *')
 _else write('+ + +   ПРОГРАММА  ',p@.name,'   + + +');
 NewLine; NewLine;
 _for k:=1 _to count _do _(
  write(Star,p@.level:0,'* ');
  _if sorted _then write(p@.name)
  _else write(p@.name:(p@.level-2)*3+6);
  _if p@.level=1 _then write('     ')
  _else _(
   ГГ('0000 (');
   _if p@.isfunc=0 _then ГГ('000П) ')
   _else ГГ('000Ф) ')
  _);
  ГГ('00СТР=');
  _if p@.forward _then _(
   PrintLine(p@.declared); write('     +    ')
  _) _else _(
   PrintLine(p@.declared); write('-'); PrintLine(p@.first); write('-'); PrintLine(p@.last)
  _);
  _if sorted _and (p@.level>2) _then write(p@.parent:8);
  NewLine;
  p:=ptr(ord(p)+RowWords);
 _)
_);

(* 01005: recursively balance BEGIN/SELECT/CASE through END. *)
_proced SkipBody;
_label 1007;
_var word:alfa;
_(
 1007: NextWord(word);
  _select
  (word=KWBegin) _or (word=KWSelect) _or (word=KWCase): SkipBody;
  word=KWEnd: exit
  _end;
 _goto 1007
_);

(* 01025: recursively collect declarations, bodies and forward headers. *)
_proced ParseBlock(level:integer; parent:alfa);
_label 1076,1121;
_var p:rowptr; word,name:alfa;
_(
 Allocate(p);
 p@ := [ ,parent,level,line,line,line,false,ord(isfunc)];
 ReadWord(name,true); p@.name:=name;
 _if level<>1 _then _(
  _if input@=OpenParen _then _(
   _while true _do _(
    _select
     input@=OpenParen: _( get(input); _if input@=Star _then SkipComment _);
     input@=EndLine: _( line:=line+1; get(input) _);
     input@=CloseParen: _goto 1076;
     true: get(input)
    _end
   _);
   1076: get(input); SkipSpaces
  _);
  _if input@=':' _then _( get(input); ReadWord(word,true) _);
  _if (input@=Semicolon) _or (input@='+') _then _(
   get(input); SkipSpaces;
   _if input@='+' _then _( p@.forward:=true; exit _)
  _)
 _);
 1121: NextWord(word);
  _select
  (word=KWProcedure) _or (word=KWFunction): _(
   _if word=KWProcedure _then isfunc:=false _else isfunc:=true;
   ParseBlock(level+1,name)
  _);
  (word='CONST ') _or (word='TYPE  ') _or (word='LABEL ')
   _or (word='VAR   ') _or (word='FILE  ') _or (word='OF    ')
   _or (word='RECORD') _or (word='ARRAY ') _or (word='SET   ')
   _or (word=KWCase) _or (word=KWEnd) _or (word='NIL   ')
   _or (word='PACKED'): _(
  _);
  word=KWBegin: _(
   p@.first:=line; SkipBody; p@.last:=line;
   _if level=1 _then _(
    SkipSpaces; _if input@<>'.' _then Fail(4);
    PrintTable(false);
    _if alphabet _then _( SortRows; PrintTable(true) _);
    _if toFile _then FlushReport
   _);
   exit
  _);
  true: _( rewrite(output); writeln(word); Fail(2) _)
  _end;
 _goto 1121
_);

(* 01302: parse INPUT address/count, optional OUTPUT and T sorting. *)
_proced ReadRequest;
_var address,zones,outaddr,outzones:integer;
 (* 01222: octal accumulation; the digit predicate also accepts 8 and 9. *)
 _proced ReadAddress(_var address,zones:integer);
 _label 1234;
 _var value:integer;
 _(
  value:=0; address:= ; zones:= ;
  _if _not (input@ _in digit) _then _( 1234: writeln('ОШИБКА В ЧИСЛЕ'); _goto 1345 _);
  _while input@ _in digit _do _(
   value:=value*8+ord(input@); get(input)
  _);
  address:=value; _if input@='В' _then get(input); SkipSpaces; value:=0;
  _while input@ _in digit _do _( value:=value*8+ord(input@); get(input) _);
  SkipSpaces; zones:=value;
  _if (address<100000B) _or (address>677777B) _or (zones=0) _then _goto 1234
 _);
_(
 ReadAddress(address,zones);
 _if input@='/' _then _(
  get(input); SkipSpaces; ReadAddress(outaddr,outzones);
  toFile:=true; BindOutput(outaddr,outzones); rewrite(output)
 _);
 alphabet:=input@='Т'; BindInput(address,zones); reset(input)
_);
_(
 setup(base);
 writeln('-=* СТРУКТУРА ПРОГРАММЫ *=-':50);
 1345:
 toFile:=false; count:= ; rollup(base);
 bind(' ++> ≡377');
 SkipSpaces;
 _if input@='≡377' _then _(
  writeln('<*> ВОЗВРАТ <*>'); code(ПБ76002=)
 _);
 _if input@='+' _then _(
  _for i:=1 _to 4 _do _(
   _if input@='≡377' _then _goto 1345
   _else get(input)
  _);
  SkipSpaces
 _);
 _if input@ _in letter _then _(
  option:='000000';
  _for i:=1 _to 6 _do _(
   option:=option; (* Preserve the original load/store before shifting A. *)
   code(СД/-10/=1ЛС7,1ЗЧ20=); get(input);
   _if input@='≡377' _then _goto 1407
  _);
  1407:
  _select
  option='0000ПА': _( i:=2; code(ЗЧ76013=,) _);
  option='0000ПП': _( i:=3; code(ЗЧ76013=,) _);
  option='000ППН': _( i:=1; code(ЗЧ76013=,) _);
  true: writeln('ОШИБКА')
  _end;
  _goto 1345
 _);
 (* 01433: analyze a source-file request. *)
 ReadRequest; line:=1; NextWord(option);
 _if option<>'PROGRA' _then Fail(0);
 isfunc:=false; ParseBlock(1,Spaces);
 _goto 1345
_).
