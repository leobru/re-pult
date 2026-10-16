(* СТАТИС: ПУЛЬТ catalog entry, zone 01063 of 2248/2148 (unit 40 zone 063).
   Decompiled. It runs in page 0 with the Pascal runtime АДСИС in page 36.
   One image serves six БАВТ commands. Before starting it, БАВТ stores the
   mode in the first global variable i (handlers at 66344-66356):
     i=0 алгп   АЛГОЛ    wrap the text as an ALGOL batch job
     i=1 гост   ВЫДАТЬ   terminal/printer services, or recode the text
     i=2 дубна  ДУБНА    wrap the text as a Dubna-monitor batch job
     i=3 впак   (case 3) wrap the text as an ITM autocode batch job
     i=4 врем   ВРЕМЯ    print CPU time, time left and the time of day
     i=5 статис СТАТ     count lines/characters/letters/digits of the text
   job holds the command's argument (6 GOST characters, blank-padded).
   input is the text being processed, presumably the edit buffer. Modes
   0-3 write a whole job deck to output: passport (ПАСП), octal loader
   cards (СТАРТ), the text, and the end (ЕКОНЕЦ).
   code(...) is inline autocode. э06260 is extracode 062 with address 060;
   'x := ;' after a code() stores the accumulator in x. Э62 subcodes:
   041 read an input or output stream, 043 keep the job in the input queue
   for a later restart, 056 the mask of occupied terminals, 057 attach a
   free terminal, 060 the mask of free terminals. dispak has only a stub
   for 057.
   Comments like (* 0436 *) give object-code addresses. (L0436) and (x)
   are structural labels: a label in parentheses names the block that
   follows it and can be used only inside that block, by _goto (back to
   the start of the block) or _exit (leave the block). *)
(*=p-*)_program СТАТИС;
_const c5=5;eol='{175';eot='{172';eoc='{341';etx='{377';
_type t1=0..5;t2=0..255;
letter='a'..'z';digit='0'..'9';bitset=_set _of 0..47;
_var i:integer; (* the mode, set by БАВТ; later a scratch variable *)
job:alfa; (* the command's argument *)
g12z:boolean;
g13z:integer;
r:real; g15z, g16z:bitset; (* g15z, g16z: sets of terminal numbers *)

(* Not called. It attaches every free terminal: Э62 060 gives the mask
   of free terminals, then Э62 057 attaches each one, given [i]. When none
   is left: пб 76002. *)
_proced L0315;_label 1;
 _(
 code(э06260=,);
 g15z := ;
   1:
   i := minel(g15z);
   _if i <> -1 _then _(
   g16z := [i];
   code(э06257=,);
   g15z := g15z-g16z;
   _) _else code(пб76002=);
   _goto 1
 _);
_proced wrSet(l2a1z:bitset);
 _(
 _repeat
   i := minel(l2a1z);
 _if i <> -1 _then _(
   write(i + 1:3);
   l2a1z := l2a1z - [i];
   _)
   _until i = -1;
   writeLN;
 _);
(* гост FREETT: print the free terminals (Э62 060 mask), back to ПУЛЬТ. *)
_proced FREETT;
 _(
 code(э06260=,);
 g15z := ;
 wrSet( g15z );
 code(пб76002=,);
_);
(* гост АЦПУ: show the job's line-printer (АЦПУ) output on the terminal.
   Э62 041 with A = 01340000+k reads part k of the output stream into input
   (0 = no such part). The stream is in printer code (GOST+1, with
   run-length repeats) and one zone per part. *)
_proced АЦПУ;
_var l2v1z:char;
l2v2z, l2v3z, l2v4z, l2v5z:integer;
l2v6z, l2v7z:char;
l2v8z, l2v9z, l2v10z:integer;
(* Level 3 *) _proced L0367; (* skip the 12-character header of part 0 *)
_var l3v1z:integer;
_(
 _for l3v1z := 1 _to 12 _do get(input);
 l2v9z := l2v9z + 12;
 _);
_( (* АЦПУ *)
  l2v10z := 0;
  _for l2v2z := 1340000C _to 1340010C _do _(
  l2v3z := l2v2z;
  code(э06241=,); (* Э62 041: read output-stream part l2v2z *)
  l2v3z := ;
  _if l2v3z = 0 _then EXIT;
  l2v9z := 0;
  _if l2v2z = 1340000C _then  L0367;
  l2v1z := input@;
  _if (l2v10z = 0) _and (l2v1z = chr(154)) _then _( (* a banner, replaced by 'П У Л Ь Т ' *)
  l2v10z := 1;
  l2v9z := l2v9z + 1;
  get(input);
  _if (input@ = 'Щ') _then _(
  _while (input@ <> 'Г') _do _(  get(input); l2v9z := l2v9z + 1 _);
  write('П У Л Ь Т '); code(16пв74106=,)
  _)
  _); (* 0436 *)
  (L0436) _(
  l2v6z := l2v1z; l2v1z := input@;
  _if (l2v1z = '0') _then _(  get(input); _goto L0436 _);
  _if l2v1z = eol _then EXIT;
  _if l2v1z = chr(97) _then _( _) _else (x) _(
  _if l2v1z = chr(16) _then  l2v1z := chr(95);
  _if l2v1z < chr(97) _then l2v1z := pred(l2v1z) _else
  _if l2v1z > chr(127) _then l2v1z := ' ' _else
  _if l2v1z <> chr(127) _then l2v1z := eol _else _(
  get(input);
  l2v7z := input@;
  l2v9z := l2v9z + 1;
  _if l2v7z > chr(20) _then  l2v7z := chr(20);
  _for l2v8z := 1 _to ord(l2v7z) _do  write(l2v6z:1); _exit x
   _); (* 0502 *)
  write(l2v1z:1+0);
  _); (* 0505 *)
  _if (l2v9z > 6143) _then _( _) _else _( l2v9z := l2v9z + 1; get(input); _goto L0436 _);
  _)
  _); (* 0514 *)
_);

_proced ВЫДАТЬ;
_type byte='0'..'{377';(*=t-*)
_var a:_array [byte] _of char; c:char;
_(
  _case job _of
  'NEWS  ': code(э06243=,пб76002=); (* Э62 043: keep the job in the input queue for a later restart *)
  'АЦПУ  ': _( АЦПУ; EXIT _);
  'FRЕЕТТ': FREETT;
  'RUNТТ ': _( code(э06256=,); g15z := ; wrSet(g15z); code(пб76002=) _) (* Э62 056: mask of occupied terminals *)
  _end;
  _if (job = '  58  ') _then _(
  _for i := 0 _to 255 _do a[i] := ' ';
  _for i := 0 _to 91 _do _(  марга(chr(i), c);  a[c] := chr(i) _); (* МАРГА = runtime ГА (75104), a character recoding *)
  a[59] := eol;
  a[33] := '''';
  a[100] := chr(100);
  a[97] := chr(97);
  c := input@; get(input);
  _while (input@ <> chr(96)) _or (c <> 'Y') _do _(
  write(a[c]); c := input@; get(input)
  _);
  write(eot:1+0, eol:1+0);
  _) _else _( (* 0614 *)
  c := input@;
  get(input);
  _while (input@ <> eol) _or (c <> eot) _do _(
  _if (c  = chr(100)) _or (c = chr(97)) _then output@ := c _else
  _if c <= chr(91) _then марга(c, output@) _else
  _if c = eol _then output@ := 'Ь' _else output@ := ' ';
   _if output@ = etx _then  output@ := 'Б';
  put(output);
  c := input@;
  get(input);
  _); (* 0647 *)
   write('У{140');
  _); (* 0651 *)
_);
(* статис [C]: statistics of the text and a histogram of its characters.
   C, the first character of the argument, is the line separator. *)
_proced СТАТ;
_var строк, сум, симв, проб, букв, цифр, других:integer;
a:_array[0..255] _of integer;
c:char;
u:_array [0..5] _of char;
_(
  _if (job = '  58  ') _then  c := eol
  _else _( unpck(u[0], job); c := u[0] _);
 сум := 0;
 симв := ;
 проб := ;
 букв := ;
 цифр := ;
 других := ;
 _for строк := 0 _to 255 _do a[строк] := 0;
   строк := 0;
  _repeat симв := симв + 1;
  сум := сум + ord(input@);
  _if input@ _in letter _then букв := букв + 1 _else
  _if input@ _in digit _then цифр := цифр + 1 _else
  _if input@ = ' ' _then проб := проб + 1 _else
  _if input@ = c _then строк := строк + 1 _else
  других := других + 1;
  a[input@] := a[input@] + 1;
  get(input)
  _until input@ = eot;
   строк := строк + 1;
  writeln('ЧИСЛО СТРОК=', строк:0, '.СИМВОЛОВ=', симв:0, '.', eol:1,
  'ПРОБЕЛОВ=', проб:0, '.БУКВ=', букв:0, '.ЦИФР=', цифр:0,
  '.ДРУГИХ СИМВОЛОВ=', других:0, '.', eol:1,
  'СРЕДНЯЯ ДЛИНА СТРОКИ=', trunc(симв/строк):0+0, '.ЧИСЛО ЗОН=', trunc(симв/6144)+1:0+0,
  '.РЕЗЕРВ=', 6144 - симв _MOD 6144:0 );
 rewrite(output);
  _for c := '0' _to etx _do _if a[c] <> 0 _then _(
  _if c < chr(96) _then write(c:1+0) _else
  write(trunc(ord(c)/64):0, trunc(ord(c) _mod 64 / 8):0, ord(c) _mod 8:0, 'В');
  write('=', a[c]:0, '.')
  _);
  writeln
_);

(* врем: Э63 0 = time left (real, seconds), Э63 4 = CPU time used in
   1/50 s, Э53 010 = 1/50 s ticks since midnight (180000 per hour). *)
_proced ВРЕМЯ;
_const dot='.';
_var min, hr:integer;
_(
  code(э0630=,); r := ;
  code(э0634=,); i := ;
  write('ВЦП=', trunc(i / 50):0, '+', i _mod 50 * 2:0, ' СОТЫХ СЕК.ОСТ=');
  i := trunc(r);
  write( i:0, '.ВРЕМЯ БЭСМ=');
  code(э05310=,); i := ;
  hr := trunc(i / 180000);
  min := trunc(i _MOD 180000 / 3000);
  i := trunc(i _MOD 3000 / 50);
  writeln(hr:0, dot:1+0, min:0, dot:1+0, i:0 );
_);

_proced ПОВТ(c:char; n:integer);
_var i:integer;
_(
  output@ := c;
  _for i := 1 _to n _do put(output);
_);

_proced copy; _( output@ := input@; get(input); put(output) _);

_proced next;
 _(
 _if i = 5 _then _(  i := 1; get(input) _) _else  i := i + 1;
 get(input);
 _);

(* The user's account id: Э50 0100, masked with the constant маска. *)
_proced ШИФР(_var a:alfa);
_(
  code(э050100=,рбмаска=); 
  a := ; EXIT; code(а;маска:      ,к;иа=зч,);
_);

 _proced ЕКОНЕЦ; _( ГГ( 'ЕКОНЕЦ' ); ПОВТ(eoc, 6 ); ГГ( '{172{175') _);

(* Passport cards of the generated job (^ separates the cards); ШИФР
   is the user's own account id. *)
_proced ПАСП(tail, pasp:alfa);
_var id:alfa;
_(
 ШИФР( id );
 write('ТКН000ШИФР ');
 write(id);
 write(tail);
 _if (pasp = 'С1') _then
  write('^ТРАК 32^ЛЕНТ 30(2048)^РОСП 0^АЦПУ 10^ЛИСТ 0-37^ВРЕМ 200')
  _else  _if (pasp = 'ХХ') _then 
 write('З18^ЛИСТ 0-37^ВРЕМ 200^ТРАК 60^ЛЕНТ 57(2048)')
  _else ГГ( 'З', pasp );
 write('^ЛЕНТ 40(2068)^ВХОД 4000^Е{341');
 _);

(* Octal loader cards (В address, К word, С constant, Б text), like the
   ones in pult.b6: they read the translator in and start it. t1 and t2
   are fields in those cards, job is the name, sp the page count, e
   the entry and inmode the input mode (А3). *)
_proced СТАРТ(t1, t2, inmode:alfa; sp, e:integer);
_(
  write('В4020К000100000000400040С', t1, 'Б', job, 
  'В4000К000704020К000104022000000041К143100032К000104021000500112К152', t2, 
  'К0006600');
  _if sp < 10 _then  ГГ( '0' );
  write(sp:0, '000000100');
  _if e = 1 _then  ГГ( 'Е' );
  write('В', e:0 );
  ГГ( inmode );
  ГГ( eoc );
_);

_function isEnd(endl, endf:char):boolean;
_(
  _if endf <> input@ _then  ГГ( endl );
  isEnd := endf = input@;
_);

_proced ДОКОНЦА(endl:char; endf:char); 
_(
  _repeat _while input@ <> endl _do _(
  write(input@); get(input);
  _);
  get(input);
  _until isEnd(endl, endf);
_);

(* алгп: ALGOL job. The text is either plain ALGOL, with $-separated
   sections, or packed card images when it starts with '0'. *)
_proced АЛГОЛ;
_(
  ПАСП( '66', 'С3' );
  СТАРТ( '570302', '400100', 'А3', 11, 1 );
  write('$АЛГОЛ{341');
  _if (input@ <> '0') _then _(
  _repeat _while input@ <> '$' _do copy;
  write(eoc:1+0);
  get(input);
  g12z := input@ <> '9';
  _if g12z _then _( write('$', input@:1+0, eoc:1+0); get(input) _);
  _until _not g12z;
  _) _else (* 1437 *) _(
  _for i := 1 _to 13 _do get(input);
  i := 1;
  (L1445) _repeat
  _while input@ <> '$' _do _(
  _if input@ <> '0' _then write(chr(ord(input@) + 127)); (*! _mod 128 *)
  _if i = 5 _then _( i := 1; get(input) _) _else i := i + 1; get(input);
  _); (* 1462 *)
  ГГ( eoc );  next;
  g12z :=   isEnd('$', '{211' );
  _if _not g12z _then _if (input@ = '2') _then  write('2{341') _else _goto L1445;
  next;
  _until g12z;
  _); (* 1502 *)
  ПОВТ( '{342', 6 );
  ЕКОНЕЦ;
_);
(* дубна: Dubna-monitor job. *)
_proced ДУБНА;
_(
  ПАСП( '44', 'С2' );
  СТАРТ( '300200', '400200', 'А3', 5, 1 );
  ДОКОНЦА(eot, eol);
  ПОВТ( '{342', 6 );
  ЕКОНЕЦ;
_);

_(
  _if i _in [0..5] _then _(
  _case i _of
  0: АЛГОЛ;
  1: ВЫДАТЬ;
  2: ДУБНА;
  3: _( (* впак: ITM autocode job *)
  ПАСП( '33', 'ХХ' );
  g12z := false;
  write('В4000К000704020К000104021000000041К003000035В4020К000100000000400040Б');
  ГГ( job );
  write('В10000А1{341');
  _repeat _while (input@ <> '"') _and (input@ <> eot) _do copy;
   ПОВТ( ' ', 11 );
  _if (input@ = eot) _then g12z := true _else  get(input);
  _until g12z;
  ПОВТ( '!', 11 );  ГГ( '_$' );  ЕКОНЕЦ; (* the end of the autocode text *)
  _);
  4: _( ВРЕМЯ; code(пб76002=,) _);
  5: _( СТАТ; code(пб76002=) _)
  _end
  _) _else  writeln('НЕПР. ЗАПУСК');
  code(сч=зч74003,); (* clear runtime cell 74003 (purpose unknown) *)
_).

