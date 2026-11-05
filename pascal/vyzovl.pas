(*=p-,t-,l-*)_program ВЫЗОВЛ;
(* PULT 2148:01074, 03.07.86. Addresses in comments are octal.
   Six significant initial identifier characters; no underscores.
   Rebuild: make checkvyzovl. All words before 00441 match the disk;
   the 1988 compiler changes two ADSIS targets in its initializer.
   CODE preserves the 1986 ADSIS entry vector and unit-66 bootstrap. *)
_label 327;
_const
 (* Original literal order, 00014..00030; range/packing constants are
    also created later by the compiler and share these pool entries. *)
 FirstLetter='А'; LastLetter='Z'; LastDigit='9'; Space=' ';
 MaxIndex=1023; NameSize=6; Spaces='      '; CharSpan=44; NameLimit=7;
 CatalogRead=0010320000270036C; Forty=40; Eight=8; ETX='≡377';
_type
 letter=FirstLetter..LastLetter; digit='0'..LastDigit;
 chars6=_array[1..NameSize] _of char;
 words=_array[0..MaxIndex] _of alfa;
_var
 (* M1 offsets: buffer 012, linebuf 013, name 014, archive 015,
    index 016, info 017, address 020, zones 021, memory 022. *)
 buffer,linebuf:integer;
 name,archive:alfa;
 index,info,address,zones:integer;
 memory:@words;

(* 00102: skip spaces in the current INPUT. *)
_proced SkipSpaces;
_( _while input@=Space _do code(=16ПВ74026,) _);

(* 00110: one to six letters/digits, first character must be a letter.
   Leaves excess characters in INPUT when the six-character limit is reached. *)
_function ReadName(_var word:alfa):boolean;
_var chars:chars6; n:integer;
_(
 SkipSpaces;
 (* 74033 is UNPCK: array address in M15, packed word in A. *)
 ReadName:=false; n:=1; word:=Spaces; code(2ИА5=15ПА,2ИК4=СЧ,16ПВ74033=,);
 _if _not (input@ _in letter) _then exit;
 _while ((input@ _in letter) _or (input@ _in digit)) _and (n<NameLimit) _do _(
  chars[n]:=input@; code(16ПВ74026=,); n:=n+1
 _);
 (* 74023 is PCK; store its accumulator result through the VAR parameter. *)
 code(2ИА5=15ПА,16ПВ74023=,2ИК4=ЗЧ,); ReadName:=true
_);

(* 00157: read the current catalog from drum 27:036 into 064000.
   Return its title and the descriptor held by НАБЛ at 057776. *)
_function GetArchive(_var descriptor:integer; _var title:alfa):boolean;
_var exchange:integer;
_(
 code(ИА57776=СЧ,2ИК4=ЗЧ,);
 exchange:=CatalogRead;
 code(2Э0706=,ИА64000=СЧ,2ИК5=ЗЧ,);
 GetArchive:=chr(sel(title,Forty,Eight)) _in letter
_);

(* 00200: bind contiguous zones to INPUT on ADSIS page 36. *)
_proced BindInput(first,length:integer);
_const ReadZones=0010340000000000C;
_var exchange:integer;
_(
 exchange:=ReadZones;
 code(2ЦС3=ЗЧ75211,2СЧ4=У076002,АВ13=ЗЧ75212,)
_);

(* 00212: bind contiguous zones to OUTPUT. *)
_proced BindOutput(first,length:integer);
_const WriteZones=0000350000000000C;
_var exchange:integer;
_(
 exchange:=WriteZones;
 code(2ЦС3=ЗЧ75203,ЗЧ75223=2СЧ4,У076002=ЦС13,ЗЧ75204=,)
_);

(* 00225: terminate and flush the Lisp source; restore drum OUTPUT. *)
_proced FlushOutput;
_(
 write('≡172≡175      ');
 code(СЧ75235=ЦС13,СР75204=У074275,Э07075223=,);
 BindOutput(270000B,1); code(=16ПВ74032,)
_);

(* 00237: command arguments are copied out of НАБЛ before RESET. *)
_(
 linebuf:=57640B; buffer:=70000B;
 code(=1ИК13,ИА=12ПА,1ИК12=ИА,16ПА=15ПА-16,copy:12ИА=15СЧ16,16ИА=15ЗЧ16,15КЦcopy=ЗЧ,);
 code(СЧcmdin=Э07574243,);
 code(15ПВ74027=,);
 _if ReadName(name) _then ;             (* Discard the command name. *)
 _if _not ReadName(name) _then _( writeln('ГДЕ ЖЕ ИМЯ ?'); exit _);
 memory:=_nil;                         (* NIL is the physical address 064000. *)
 code(СЧtextin=Э07574243,);
 _if _not GetArchive(info,archive) _then _(
  writeln('НЕТ НАСТРОЙКИ НА АРХИВ'); exit
 _);
 info:=sel(info,0,18);
 index:=1;
 _while index<512 _do _(
  _if memory@[index]=name _then _goto 327;
  index:=index+2
 _);
 writeln('В АРХИВЕ ',archive,' НЕТ ИМЕНИ ',name); exit;
 327:
 index:=index+1;
 (* Read the full 48-bit descriptor as INTEGER from the ALFA catalog. *)
 code(=1СЧ16,1АС22=17ЗЧ,17ИК=СЧ,); index:=;
 address:=sel(index,24,24)+info;
 zones:=sel(index,0,24);
 BindInput(address,zones); code(15ПВ74027=,);
 BindOutput(100000B,zones);
 _while input@<>'≡172' _do _(
  _if input@='≡175' _then write(' ') _else _( output@:=input@; code(16ПВ74030=,) _);
  code(16ПВ74026=,)
 _);
 FlushOutput;
 (* Load and identify page 2 before replacing the remaining low pages. *)
 code(Э070rd2=,СЧ5252=); name:= ;
 _if name<>'NONE  ' _then _( writeln('ИСПОРЧЕН ЛИСП-ТРАНСЛЯТОР'); exit _);
 code(Э070rd1=,Э070rd3=,Э070rd4=,СЧrd0=ЗЧ70003,СЧboot0=Э07570000,СЧboot1=Э07570001,СЧstamp=ЗЧ70002,);
 name:=Spaces; code(ЗЧ70012=);
 name:='<*> ФИ'; code(=ЗЧ,ЗЧ70013=);
 name:='НАЛ <*'; code(=ЗЧ,ЗЧ70014=);
 name:='>≡172≡000≡000≡000≡000'; code(=ЗЧ,ЗЧ70015=ЗЧ,);
 index:=2264253121233462C;              (* ASCII KEYE72. *)
 code(Э07270010=,СЧleave0=Э07570010,СЧleave1=Э07570011,);
 write('РАБОТАЕТ ЛИСП-ТРАНСЛЯТОР':30); writeln; writeln;
 code(ПБ70000=,); exit;                (* Original unreachable return at 00417. *)
 (* 00420..00433: patches, exchange words, finish handler and bootstrap. *)
 code(С;
cmdin:0100435600000000,textin:0100435601704357,
rd0:0010000000661651,rd1:0010010000661652,rd2:0010020000661653,
rd3:0010030000661654,rd4:0010040000661655,
leave0:6647001273176005,leave1:0307600200000000,
boot0:0170000300000000,boot1:7247000203000410,stamp:0020001000031000,К;)
_).
