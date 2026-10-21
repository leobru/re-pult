(*=p-,t-,l-,k20*)_program ЧИСТКА;
(* Recovered from 2248/2148 zones 01060-01062, image dated 10.12.82.
   Mnemonic routine names describe behavior; comments and labels retain
   the original octal addresses. Only the first six name characters matter.
   Forward skips over statements are expressed as structured IF blocks.
   Remaining labels preserve shared destinations and parser loops.
   The source follows the underscore Pascal notation used by pretty.pas. *)
_label 5134,5142,5200;
_const
(* Explicit prefix of the original literal pool, 00014..00074.
   Further scalar and ALFA literals arise in original order from their uses.
   WRITE/BIND strings are emitted at each occurrence. Together with InputReadZone
   below they reproduce the complete pool 00011..00546. *)
 unus56=56;
 unus5=5;
 NBuiltins=280;
 Space=' ';
 Spaces='      ';
 EndOfLine='≡175';
 Colon=':';
 Comma=',';
 Apostrophe='''';
 OpenParen='(';
 CloseParen=')';
 Star='*';
 KwBegin='ВЕGIN ';
 KwEnd='ЕND   ';
 KwCode='СОDЕ  ';
 Underline='_';
 KwSelect='SЕLЕСТ';
 KwCase='САSЕ  ';
 KwExit='ЕХIТ  ';
 KwVar='VАR   ';
 KwConst='СОNSТ ';
 KwType='ТУРЕ  ';
 KwFunction='FUNСТI';
 KwProcedure='РRОСЕD';
 KwLabel='LАВЕL ';
 Equals='=';
 Plus='+';
 ETX='≡377';
 OpIK='ИК    ';
 OpSR='СР    ';
 Dot='.';
 KwArray='АRRАУ ';
 KwFile='FILЕ  ';
 KwSet='SЕТ   ';
 KwExtern='ЕХТЕRN';
 KwRecord='RЕСОRD';
 KwPacked='РАСКЕD';
 KwIn='IN    ';
 Semicolon=';';
 OpTsS='ЦС    ';
 OpSCh='СЧ    ';
 OpZCh='ЗЧ    ';
 OpLS='ЛС    ';
 EndOfText='≡172';
 OpAS='АС    ';
 OpSB='СБ    ';
 OpRB='РБ    ';
 OpSM='СМ    ';
 OpLU='ЛУ    ';
_type
 letter='А'..'Z'; digit='0'..'9';
 chars6=_array[1..6] _of char;
 name=_record nm:alfa; used:boolean; decl,count,line:integer; next:@name _end;
 namep=@name;
 block=_record nm:alfa; used,isfun,asm:boolean; first,last,depth:integer;
 next,child,parent:@block; consts,enums,vars,labels,refs,types:namep _end;
 blockp=@block;
_var builtin:_array[1..NBuiltins] _of alfa;
 clean,asmref:boolean; root,newblk:blockp; saved:@integer;
 newid,found,prevId,lhs:namep; line,depth,errors,refLn:integer;
 token:alfa; cold,cold1:boolean;
_proced SkipTrivia; +
_proced ParseRecord(_var l2a1z:namep; l2a2z:blockp); +
_proced ParseBlock(l2a1z:namep; l2a2z:blockp; l2a3z:boolean); +
(* 0547: ПРЕДОПРЕДЕЛЕННЫЕ_ИМЕНА; original lexical level 2. *)
_proced InitBuiltins;
_(

 builtin[1] := 'ВООLЕА';
 builtin[2] := 'INТЕGЕ';
 builtin[3] := 'СНАR  ';
 builtin[4] := 'RЕАL  ';
 builtin[5] := 'АLFА  ';
 builtin[6] := 'ТRUЕ  ';
 builtin[7] := 'FАLSЕ ';
 builtin[8] := 'ТЕХТ  ';
 builtin[9] := 'INРUТ ';
 builtin[10] := 'ОUТРUТ';
 builtin[11] := 'РUТ   ';
 builtin[12] := 'GЕТ   ';
 builtin[13] := 'RЕWRIТ';
 builtin[14] := 'RЕSЕТ ';
 builtin[15] := 'NЕW   ';
 builtin[16] := 'UNРСК ';
 builtin[17] := 'РСК   ';
 builtin[18] := KwExit;
 builtin[19] := 'НАLТ  ';
 builtin[20] := 'МАРIА ';
 builtin[21] := 'МАРАI ';
 builtin[22] := 'ТNL   ';
 builtin[23] := 'ГГ    ';
 builtin[24] := 'МАРГА ';
 builtin[25] := 'МАРЯГА';
 builtin[26] := KwCode;
 builtin[27] := 'SЕТUР ';
 builtin[28] := 'RОLLUР';
 builtin[29] := 'WRIТЕ ';
 builtin[30] := 'WRIТЕL';
 builtin[31] := 'DISРОS';
 builtin[32] := 'ВIND  ';
 builtin[33] := 'SQRТ  ';
 builtin[34] := 'SIN   ';
 builtin[35] := 'СОS   ';
 builtin[36] := 'АRСТАN';
 builtin[37] := 'АRСSIN';
 builtin[38] := 'LN    ';
 builtin[39] := 'ЕХР   ';
 builtin[40] := 'АВS   ';
 builtin[41] := 'ТRUNС ';
 builtin[42] := 'ОDD   ';
 builtin[43] := 'ОRD   ';
 builtin[44] := 'СНR   ';
 builtin[45] := 'SUСС  ';
 builtin[46] := 'РRЕD  ';
 builtin[47] := 'ЕОF   ';
 builtin[48] := 'RЕF   ';
 builtin[49] := 'РТR   ';
 builtin[50] := 'SQR   ';
 builtin[51] := 'RОUND ';
 builtin[52] := 'РОWЕR ';
 builtin[53] := 'МINЕL ';
 builtin[54] := 'SНIFТ ';
 builtin[55] := 'SЕL   ';
 builtin[56] := 'INS   ';

_);
(* 0641: ПРОПУСК_ПРОБЕЛОВ_И_СТРОК; original lexical level 2. *)
_proced SkipWhitespace;
_label 0643;
_(

 0643:
 _while input@ = Space _do _(
   get(input);
 _);
 _if input@ > chr(127) _then _(
   get(input);
   _goto 0643;
 _);
 _if input@ <> EndOfLine _then exit;
 line := line + 1;
 get(input);
 _goto 0643;
 code(=,)

_);
(* 0657: ПРОПУСК_ДО_СИМВОЛА; original lexical level 2. *)
_proced SkipThrough(l2a1z:char);
_label 0661;
_(

 0661:
 _while (input@ <> l2a1z) _and (input@ <> EndOfLine) _do _(
   get(input);
 _);
 _if input@ = l2a1z _then _(
   get(input); exit
 _);
 line := line + 1;
 get(input);
 _goto 0661;
 code(=,)
_);
(* 0675: СИНТАКСИЧЕСКАЯ_ОШИБКА; original lexical level 2. *)
_proced SyntaxError(l2a1z:integer);
_(

 write('ОШИБКА=':15, l2a1z:0);
 _( output@ := Space; put(output) _);
 write('СИМ=');
 output@ := input@;
 put(output);
 writeln(' СТР=', line);
 _goto 5134;

_);
(* 0721: ПРОПУСК_СТРОКИ_В_АПОСТРОФАХ; original lexical level 2. *)
_proced SkipString;
_(

 _while input@ = Apostrophe _do _(
   get(input);
   SkipThrough(Apostrophe);
 _);

_);
(* 0730: НОВЫЙ_БЛОК_16_СЛОВ; procedure; original lexical level 2. *)
_proced NewBlock;
_(
 new(newblk);
 _if newblk=_nil _then _( writeln('НЕ ХВАТАЕТ ПАМЯТИ ПОД ИДЕНТИФИКАТОРЫ.':28); _goto 5134 _);
 newblk@.next:=_nil; newblk@.consts:= ; newblk@.enums:= ;
 newblk@.vars:= ; newblk@.child:= ; newblk@.labels:= ;
 newblk@.refs:= ; newblk@.parent:= ; newblk@.types:= ;
 newblk@.used:=false; newblk@.isfun:= ; newblk@.asm:= ;
_);
(* 0761: НОВОЕ_ИМЯ_6_СЛОВ; procedure; original lexical level 2. *)
_proced NewName;
_( new(newid);
 _if newid=_nil _then _( writeln('НЕ ХВАТАЕТ ПАМЯТИ ПОД ИДЕНТИФИКАТОРЫ.':28); _goto 5134 _);
 newid@.used:=false; newid@.next:=_nil
_);
(* 1000: ПОИСК_ПРЕДОПРЕДЕЛЕННОГО_ИМЕНИ; function; original lexical level 2. *)
_function IsBuiltin:boolean;
_var i:integer;
_(
 _for i:=1 _to NBuiltins _do
  _if builtin[i]=token _then _(
    IsBuiltin:=true;
    exit
  _);
 IsBuiltin:=false
_);
(* 1014: ПЕЧАТЬ_ИМЕНИ; procedure; original lexical level 2. *)
_proced PrintName(l2a1z:alfa);
_var i:integer; a:chars6;
_( clean:=false; unpck(a[1],l2a1z);
 _for i:=1 _to 6 _do _(
  _if a[i]=Space _then exit
  _else write(a[i])
 _)
_);
(* 1071: ОТЧЕТ_ПО_ОБЪЯВЛЕНИЯМ; original lexical level 2. *)
_proced DeclReport(l2a1z:blockp);
_label 1215;
_var l2v1z:namep; l2v2z:namep; l2v3z:integer;
(* 1034: РЕКУРСИВНЫЙ_ПОИСК_ИМЕНИ_В_БЛОКАХ; original lexical level 3. *)
_function HasBlockName(l3a1z:blockp):boolean;
_(

 HasBlockName := true;
 _while l3a1z <> _nil _do _(
   _if token = l3a1z@.nm _then exit;
   _if HasBlockName( l3a1z@.child) _then exit;
   l3a1z := l3a1z@.next;
 _);
 HasBlockName := false;

_);
(* 1053: ОТМЕТИТЬ_ПРЕДОПРЕДЕЛЕННЫЕ_ИМЕНА; original lexical level 3. *)
_proced MarkBuiltins(l3a1z:namep);
_(

 _while l3a1z <> _nil _do _(
   _if _not l3a1z@.used _then _(
     token := l3a1z@.nm;
     _if IsBuiltin _then l3a1z@.used := true;
   _);
   l3a1z := l3a1z@.next;
 _);

_);
_(

 l2v1z := l2a1z@.labels;
 l2v3z := 0;
 _while l2v1z <> _nil _do _(
   _if _not l2v1z@.used _then _(
     _if l2v3z < l2v1z@.decl _then _(
       _if l2v3z <> 0 _then writeLN;
       l2v3z := l2v1z@.decl;
       write('В СТРОКЕ  ', l2v3z:4, ' ОПИСАНЫ НЕИСПОЛЬЗУЕМЫЕ  МЕТКИ    ');
       PrintName( l2v1z@.nm );
     _) _else _(
       _( output@ := Comma; put(output) _);
       PrintName( l2v1z@.nm );
     _);
   _);
   l2v1z := l2v1z@.next;
 _);
 _if l2v3z <> 0 _then writeLN;
 MarkBuiltins( l2a1z@.consts );
 l2v1z := l2a1z@.consts;
 l2v3z := 0;
 _while l2v1z <> _nil _do _(
   _if _not l2v1z@.used _then _(
     _if l2v3z < l2v1z@.decl _then _(
       _if l2v3z <> 0 _then writeLN;
       l2v3z := l2v1z@.decl;
       write('В СТРОКЕ  ', l2v3z:4, ' ОПИСАНЫ НЕИСПОЛЬЗУЕМЫЕ КОНСТАНТЫ ');
       PrintName( l2v1z@.nm );
     _) _else _(
       _( output@ := Comma; put(output) _);
       PrintName( l2v1z@.nm );
     _);
   _);
   l2v1z := l2v1z@.next;
 _);
 _if l2v3z <> 0 _then writeLN;
 MarkBuiltins( l2a1z@.enums );
 l2v1z := l2a1z@.enums;
 _while l2v1z <> _nil _do _(
   _if _not l2v1z@.used _then _(
     token := l2v1z@.nm;
     _if HasBlockName( l2a1z@.child) _then _(
       l2v1z@.used := true;
       _goto 1215;
     _);
     l2v2z := l2a1z@.vars;
     _while l2v2z <> _nil _do _(
       _if token = l2v2z@.nm _then _(
         l2v2z@.used := true;
         l2v1z@.used := ;
       _);
       l2v2z := l2v2z@.next;
     _);
   _);
   1215:
   l2v1z := l2v1z@.next;
 _);
 l2v1z := l2a1z@.enums;
 l2v3z := 0;
 _while l2v1z <> _nil _do _(
   _if _not l2v1z@.used _then _(
     _if l2v3z < l2v1z@.decl _then _(
       _if l2v3z <> 0 _then writeLN;
       l2v3z := l2v1z@.decl;
       write('В СТРОКЕ  ', l2v3z:4, ' В ТИПАХ НЕ ИСПОЛЬЗУЮТСЯ ИДЕНТИФИКАТОРЫ ');
       PrintName( l2v1z@.nm );
     _) _else _(
       _( output@ := Comma; put(output) _);
       PrintName( l2v1z@.nm );
     _);
   _);
   l2v1z := l2v1z@.next;
 _);
 _if l2v3z <> 0 _then writeLN;
 _if l2a1z@.depth = 1 _then _(
   l2v1z := l2a1z@.types;
   l2v3z := 0;
   _while l2v1z <> _nil _do _(
     _if _not l2v1z@.used _then _(
       _if l2v3z < l2v1z@.decl _then _(
         _if l2v3z <> 0 _then writeLN;
         l2v3z := l2v1z@.decl;
         write('В СТРОКЕ  ', l2v3z:4, ' ОПИСАНЫ НЕИСПОЛЬЗУЕМЫЕ  ТИПЫ     ');
         PrintName( l2v1z@.nm );
       _) _else _(
         _( output@ := Comma; put(output) _);
         PrintName( l2v1z@.nm );
       _);
     _);
     l2v1z := l2v1z@.next;
   _);
   _if l2v3z <> 0 _then writeLN;
 _);
 MarkBuiltins( l2a1z@.vars );
 l2v1z := l2a1z@.vars;
 l2v3z := 0;
 _while l2v1z <> _nil _do _(
   _if _not l2v1z@.used _then _(
     _if l2v3z < l2v1z@.decl _then _(
       _if l2v3z <> 0 _then writeLN;
       l2v3z := l2v1z@.decl;
       write('В СТРОКЕ  ', l2v3z:4, ' ОПИСАНЫ НЕИСПОЛЬЗУЕМЫЕ ИДЕНТИФИКАТОРЫ ');
       PrintName( l2v1z@.nm );
     _) _else _(
       _( output@ := Comma; put(output) _);
       PrintName( l2v1z@.nm );
     _);
     _if l2a1z@.asm _then _( output@ := Star; put(output) _);
   _);
   l2v1z := l2v1z@.next;
 _);
 _if l2v3z <> 0 _then writeLN;
 _if cold _then _(
   l2v1z := l2a1z@.vars;
   l2v3z := 0;
   _while l2v1z <> _nil _do _(
     _if l2v1z@.count = 1 _then _(
       _if l2v3z < l2v1z@.decl _then _(
         _if l2v3z <> 0 _then writeLN;
         l2v3z := l2v1z@.decl;
         write('В СТРОКЕ  ', l2v3z:4, ' ОПИСАНЫ ХОЛОСТЫЕ ИДЕНТИФИКАТОРЫ ');
         PrintName( l2v1z@.nm );
         _if l2a1z@.asm _then _( output@ := Star; put(output) _);
         _( output@ := OpenParen; put(output) _);
         write(l2v1z@.line:0);
         _( output@ := CloseParen; put(output) _);
       _) _else _(
         _( output@ := Comma; put(output) _);
         PrintName( l2v1z@.nm );
         _if l2a1z@.asm _then _( output@ := Star; put(output) _);
         _( output@ := OpenParen; put(output) _);
         write(l2v1z@.line:0);
         _( output@ := CloseParen; put(output) _);
       _);
     _);
     l2v1z := l2v1z@.next;
   _);
   _if l2v3z <> 0 _then writeLN;
 _);

_);
(* 1442: ОТЧЕТ_ПО_ПОДПРОГРАММАМ; original lexical level 2. *)
_proced BlockReport(l2a1z:blockp);
_var l2v1z:blockp;
_(

 l2v1z := l2a1z@.child;
 _while l2v1z <> _nil _do _(
   _if l2v1z@.used _then _(
     DeclReport( l2v1z );
     BlockReport( l2v1z );
   _) _else _(
     write('В СТРОКАХ ', l2v1z@.first:4);
     output@ := Space; put(output);
     write('-');
     output@ := Space; put(output);
     write(l2v1z@.last:4, ' ОПРЕДЕЛЕНА НЕИСПОЛЬЗУЕМАЯ ');
     _if l2v1z@.isfun _then _(
       write(' ФУНКЦИЯ  ');
     _) _else _(
       write('ПРОЦЕДУРА ');
     _);
     writeln(l2v1z@.nm);
     clean := false;
   _);
   l2v1z := l2v1z@.next;
 _);

_);
(* 1512: ДОБАВИТЬ_ОБЪЯВЛЕНИЕ; procedure; original lexical level 2. *)
_proced AddDeclaration(l2a1z:integer; _var l2a2z:namep; l2a3z:blockp);
_(
 NewName;
 _if l2a2z=_nil _then
  _case l2a1z _of
   1: l2a3z@.consts:=newid;
   2: l2a3z@.enums:=newid;
   3: l2a3z@.vars:=newid;
   4: l2a3z@.refs:=newid;
   5: l2a3z@.labels:=newid;
   6: l2a3z@.types:=newid
  _end
 _else l2a2z@.next:=newid;
 l2a2z:=newid; newid@.nm:=token; newid@.decl:=line;
 newid@.count:=0; newid@.line:=0
_);
(* 1563: ПРОПУСК_ЧИСЛА; procedure; original lexical level 2. *)
_proced SkipNumber;
_(
 _while input@ _in digit _do get(input);
 _if (input@='Т') _or (input@='С') _or (input@='В') _then get(input)
_);
(* 1604: СЧИТАТЬ_ИМЯ_ШЕСТЬ_СИМВОЛОВ; procedure; original lexical level 2. *)
_proced ReadIdentifier;
_var i:integer; a:chars6;
_(
 _if _not (input@ _in letter) _then SyntaxError(15);
 i:=1; token:=Spaces; unpck(a[1],token);
 _while (input@ _in letter) _or (input@ _in digit) _do _(
  _if i>6 _then get(input)
  _else _(
   a[i]:=input@;
   get(input);
   i:=i+1
  _)
 _);
 pck(a[1],token); SkipWhitespace
_);
(* 1644: КЛЮЧЕВОЕ_СЛОВО_ИЛИ_СКОБКА; original lexical level 2. *)
_proced ReadKeyword;
_(

 get(input);
 _if input@ _in letter _then _(
   ReadIdentifier;
 _) _else _(
   _if input@ = OpenParen _then _(
     token := KwBegin;
   _) _else _if input@ = CloseParen _then _(
     token := KwEnd;
   _) _else _(
     SyntaxError( 50 );
   _);
   get(input);
 _);
 SkipWhitespace;

_);
(* 1665: СЧИТАТЬ_МЕТКУ_ИЛИ_ИМЯ; procedure; original lexical level 2. *)
_proced ReadNameOrLabel;
_var i:integer; a:chars6;
_(
 _if input@ _in digit _then _(
  token:=Spaces; unpck(a[1],token); i:=1;
  _while input@ _in digit _do _(
   _if i>7 _then SyntaxError(700);
   a[i]:=input@; get(input); i:=i+1
  _);
  pck(a[1],token)
 _) _else ReadIdentifier
_);
(* 1714: ПРОПУСК_КОММЕНТАРИЯ; original lexical level 2. *)
_proced SkipComment;
_label 1717;
_var l2v1z:integer;
_(

 get(input);
 l2v1z := line;
 1717:
 _while (input@ <> Star)
   _and (input@ <> EndOfLine)
   _and (input@ <> OpenParen)
   _and (input@ <> EndOfText) _do _(
   get(input);
 _);
 _if input@ = EndOfText _then _(
   writeln('НЕЗАКРЫТЫЙ КОМ. СТР.= ', l2v1z:0);
   _goto 5134;
 _);
 _if input@ = EndOfLine _then _(
   line := line + 1;
   get(input);
   _goto 1717;
 _);
 _if input@ = OpenParen _then _(
   get(input);
   _if input@ = Star _then SkipComment;
   _goto 1717;
 _) _else _(
   get(input);
   _if input@ <> CloseParen _then _(
     _goto 1717;
   _);
   get(input);
   SkipWhitespace;
   SkipTrivia;
 _);

_);
(* 1762: ПРОПУСК_ПРОБЕЛОВ_И_КОММЕНТАРИЕВ; original lexical level 2. *)
_proced SkipTrivia+
_(

 SkipWhitespace;
 _if input@ = OpenParen _then _(
   get(input);
   _if input@ = Star _then SkipComment;
 _);

_);
(* 1773: ОТМЕТИТЬ_ССЫЛКУ_В_СПИСКЕ; original lexical level 2. *)
_function MarkReference(l2a1z:namep):boolean;
_label 1775;
_(

 1775:
 _if l2a1z <> _nil _then _(
   _if l2a1z@.nm = token _then _(
     MarkReference := true;
     _if _not l2a1z@.used _then l2a1z@.line := line;
     l2a1z@.used := true;
     l2a1z@.count := l2a1z@.count + 1;
     found := l2a1z;
     exit;
   _);
   l2a1z := l2a1z@.next;
   _goto 1775;
 _);
 MarkReference := false;

_);
(* 2017: ДОБАВИТЬ_НЕРАЗРЕШЕННУЮ_ССЫЛКУ; original lexical level 2. *)
_proced AddReference(l2a1z:blockp);
_var l2v1z:namep; l2v2z:namep;
_(

 l2v1z := l2a1z@.refs;
 _if l2v1z <> _nil _then _(
   _while l2v1z <> _nil _do _(
     _if l2v1z@.nm = token _then _(
       l2v1z@.count := l2v1z@.count + 1;
       found := l2v1z;
       exit;
     _) _else _(
       l2v2z := l2v1z;
       l2v1z := l2v1z@.next;
     _);
   _);
   NewName;
   l2v2z@.next := newid;
 _) _else _(
   NewName;
   l2a1z@.refs := newid;
 _);
 newid@.nm := token;
 newid@.decl := line;
 newid@.count := 1;
 newid@.line := refLn;
 found := newid;

_);
(* 2057: РАЗРЕШИТЬ_ССЫЛКИ; original lexical level 2. *)
_proced ResolveReferences(l2a1z:blockp; l2a2z:blockp);
_label 2146;
_var l2v1z:blockp; l2v2z:namep;
_(

 _if l2a1z@.refs = _nil _then exit;
 l2v2z := l2a1z@.refs;
 _while l2v2z <> _nil _do _(
   token := l2v2z@.nm;
   l2v1z := l2a2z@.child;
   refLn := l2v2z@.line;
   _while l2v1z <> _nil _do _(
     _if token = l2v1z@.nm _then _(
       _if l2v1z@.used _then _(
         _goto 2146;
       _);
       l2v1z@.used := true;
       ResolveReferences( l2v1z, l2a2z );
       _goto 2146;
     _) _else _(
       l2v1z := l2v1z@.next;
     _);
   _);
   _if _not MarkReference( l2a2z@.vars) _then _(
     _if _not MarkReference( l2a2z@.consts)
       _and _not MarkReference( l2a2z@.enums)
       _and _not MarkReference( l2a2z@.labels) _then _(
       AddReference( l2a2z );
       _if newid = found _then newid@.count := l2v2z@.count;
     _);
   _) _else _if found@.count = 1 _then _(
     found@.line := refLn;
     found@.count := l2v2z@.count;
   _);
   2146:
   l2v2z := l2v2z@.next;
 _);

_);
(* 2151: СЧИТАТЬ_МНЕМОНИКУ_ДВА_СИМВОЛА; procedure; original lexical level 2. *)
_proced ReadMnemonic;
_var a:chars6; i:integer;
_(
 token:=Spaces; unpck(a[1],token);
 _for i:=1 _to 2 _do
  _if input@ _in letter _then _( a[i]:=input@; get(input) _);
 SkipWhitespace; pck(a[1],token)
_);
(* 2172: СЧИТАТЬ_НОМЕР_МЕТКИ; function; original lexical level 2. *)
_function ReadOctalLabel:integer;
_var n,i,k,m:integer; a:_array[1..6] _of char;
_(
 n:=0; m:= ; k:=1;
 _while input@ _in digit _do _( n:=n+1; a[n]:=input@; get(input) _);
 _for i:=n _downto 1 _do _( m:=m+k*ord(a[i]); k:=k*8 _);
 SkipWhitespace; ReadOctalLabel :=m
_);
(* 2223: ОТМЕТИТЬ_ПЕРЕХОД_ИЛИ_МЕТКУ; original lexical level 2. *)
_proced MarkFrameReference(l2a1z:blockp; l2a2z:integer; l2a3z:integer);
_label 2235;
_var l2v1z:namep; l2v2z:integer;
_(

 _if l2a1z@.depth < l2a2z _then exit;
 asmref := true;
 _if l2a1z@.depth = l2a2z _then _(
   2235:
   _if (l2a2z <> 1) _and (l2a3z > 2) _or
       (l2a2z = 1) _and (l2a3z > 9) _then _(
     _if l2a1z@.isfun _then _(
       l2v2z := 4;
     _) _else _(
       l2v2z := 3;
     _);
     l2v1z := l2a1z@.vars;
     _while (l2v1z <> _nil) _and (l2v2z < l2a3z) _do _(
       l2v2z := l2v2z + 1;
       l2v1z := l2v1z@.next;
     _);
     _if l2v2z - 1 = l2a3z _then exit;
     _if l2v2z = l2a3z _then _(
       l2v1z@.used := true;
       l2v1z@.count := l2v1z@.count + 1;
       l2v1z@.line := line;
       exit;
     _);
     exit;
   _);
   _if (l2a3z = 7) _or (l2a3z = 8) _then exit;
   SyntaxError(301)
 _);
 _if l2a2z = 1 _then _(
   l2a1z := root;
   _goto 2235;
 _);

_);
(* 2310: РАЗБОР_CODE; original lexical level 2. *)
_proced ParseCode(l2a1z:blockp);
_label 2314,2340,2353,2400,2420,2432,2440,2464,2476,2562,2565;
_var l2v1z:boolean; l2v2z:boolean; l2v3z:boolean; l2v4z:integer; l2v5z:integer;
_(

 l2v2z := false;
 l2v3z := ;
 get(input);
 2314:
 _if input@ = '‘' _then _(
   get(input);
   SkipThrough('‘');
   SkipWhitespace;
 _);
 SkipWhitespace;
 l2v1z := false;
 _if input@ _in letter _then _(
   ReadMnemonic;
   _if input@ = Semicolon _then _(
     get(input);
     SkipWhitespace;
     _if token = 'К     ' _then _(
       l2v2z := false;
       l2v3z := ;
       _if input@ = CloseParen _then _(
         _goto 2432;
       _);
       2340:
       SkipWhitespace;
       _if input@ = '‘' _then _(
         get(input);
         SkipThrough('‘');
         SkipWhitespace;
       _);
       _if input@ _in letter _then _(
         ReadMnemonic;
         2353:
         _if (token <> OpSCh)
           _and (token <> OpZCh)
           _and (token <> OpTsS)
           _and (token <> OpLS)
           _and (token <> OpAS)
           _and (token <> OpSB)
           _and (token <> OpRB)
           _and (token <> OpSM)
           _and (token <> OpLU)
           _and (token <> OpIK)
           _and (token <> OpSR) _then _(
           _goto 2476;
         _);
         _if input@ = Colon _then _(
           get(input);
           _goto 2340;
         _);
         _if _not l2v1z _then _(
           2400:
           _while (input@ <> Equals)
             _and (input@ <> Comma)
             _and (input@ <> EndOfLine)
             _and (input@ <> CloseParen)
             _and (input@ <> OpenParen) _do _(
             get(input);
           _);
           _if input@ = EndOfLine _then _(
             line := line + 1;
             get(input);
             _goto 2400;
           _);
           _if input@ = Comma _then _(
             2420:
             get(input);
             SkipWhitespace;
             _if input@ = '‘' _then _(
               get(input);
               SkipThrough('‘');
               SkipWhitespace;
             _);
             _if input@ = CloseParen _then _(
               2432:
               get(input);
               SkipTrivia;
               exit;
             _);
             _goto 2314;
           _);
           _if input@ = Equals _then _(
             2440:
             get(input);
             SkipWhitespace;
             _if input@ = Comma _then _(
               _goto 2420;
             _);
           _);
           _if input@ = OpenParen _then _(
             _while input@ <> CloseParen _do _(
               get(input);
             _);
             get(input);
             _goto 2400;
           _);
           _if input@ = CloseParen _then _(
             _goto 2432;
           _);
           _goto 2340;
         _);
         _if input@ _in letter _then _(
           _goto 2400;
         _);
         _if input@ _in digit _then _(
           2464:
           l2v5z :=   ReadOctalLabel;
           _if _not l2v1z _then _(
             _goto 2400;
           _);
           MarkFrameReference( l2a1z, l2v4z, l2v5z );
           l2v1z := false;
           _goto 2400;
         _);
         _goto 2400;
         2476:
         _if token = 'Э     ' _then _(
           get(input);
           get(input);
           get(input);
           _if input@ _in digit _then _(
             _goto 2464;
           _);
           _goto 2400;
         _);
         l2v1z := false;
         _goto 2400;
       _);
       _if input@ _in digit _then _(
         _if l2v2z _then _(
           SkipThrough(Comma);
           _goto 2314;
         _);
         _if l2v1z _then _(
           _goto 2464;
         _);
         l2v1z := true;
         l2v4z :=   ReadOctalLabel;
         _if input@ _in letter _then _(
           _goto 2340;
         _);
         SyntaxError( 304 );
       _);
       _goto 2562;
     _);
     _if token = 'С     ' _then _(
       SkipThrough(Comma);
       l2v3z := false;
       l2v2z := true;
       _goto 2314;
     _) _else _if token = 'Л     ' _then _(
       SkipThrough(Comma);
       l2v3z := true;
       _goto 2314;
     _) _else _if token = 'В     ' _then _(
       _goto 2314;
     _) _else _if token = 'Н     ' _then _(
       SkipThrough(Comma);
       _goto 2314;
     _) _else _if token = 'Е     ' _then _(
       _goto 2314;
     _) _else _(
       SyntaxError( 305 );
       _goto 2562;
     _);
     2562:
     _goto 2565;
   _);
   _if _not l2v3z _then _(
     _goto 2353;
   _);
   2565:
   SkipThrough(Comma);
   _goto 2314;
 _);
 _if input@ _in digit _then _(
   _goto 2340;
 _);
 _if input@ = Equals _then _(
   _goto 2440;
 _);
 SyntaxError( 307 );

_);
(* 2576: ПОИСК_И_ОТМЕТКА_ИМЕНИ; original lexical level 2. *)
_proced UseIdentifier(l2a1z:blockp);
_var l2v1z:blockp; l2v2z:blockp;
_(

 _if token = KwCode _then _(
   ParseCode( l2a1z );
   exit;
 _);
 _if MarkReference( l2a1z@.vars) _then exit;
 _if MarkReference( l2a1z@.consts) _then exit;
 _if l2a1z@.nm = token _then _(
   found := _nil;
   exit;
 _);
 l2v1z := l2a1z@.child;
 _while l2v1z <> _nil _do _(
   _if l2v1z@.nm = token _then _(
     _if l2v1z@.used _then exit;
     l2v1z@.used := true;
     ResolveReferences( l2v1z, l2a1z );
     exit;
   _) _else _(
     l2v1z := l2v1z@.next;
   _);
 _);
 _if MarkReference( l2a1z@.enums) _then exit;
 _if MarkReference( l2a1z@.labels) _then exit;
 _if IsBuiltin _then _(
   l2v1z := l2a1z@.parent;
   found := _nil;
   _while l2v1z <> _nil _do _(
     l2v2z := l2v1z@.child;
     _while l2v2z <> _nil _do _(
       _if l2v2z@.nm = token _then _(
         refLn := 0;
         AddReference( l2a1z );
         exit;
       _) _else _(
         l2v2z := l2v2z@.next;
       _);
     _);
     l2v1z := l2v1z@.parent;
   _);
   exit;
 _);
 refLn := line;
 AddReference( l2a1z );
_);
(* 2701: ОБЪЯВЛЕНИЯ_LABEL; original lexical level 2. *)
_proced LabelDeclarations(l2a1z:blockp);
_label 2704;
_var l2v1z:namep;
_(

 l2v1z := _nil;
 2704:
 SkipTrivia;
 ReadNameOrLabel;
 AddDeclaration( 5, l2v1z, l2a1z );
 SkipTrivia;
 _if input@ = Comma _then _(
   get(input);
   _goto 2704;
 _);
 _if input@ <> Semicolon _then SyntaxError( 81 );
 get(input);
 SkipTrivia;
 _if input@ <> Underline _then SyntaxError( 82 );
 ReadKeyword;

_);
(* 2733: РАЗБОР_ТЕЛА_БЛОКА; original lexical level 2. *)
_proced ScanBody(l2a1z:blockp);
_label 2740,3013,3022,3034,3107,3155;
_var l2v1z:boolean; l2v2z:boolean; l2v3z:alfa;
_(

 prevId := _nil;
 lhs := ;
 l2v1z := true;
 l2v2z := false;
 2740:
 code(lp2733:);
 SkipWhitespace;
 _if input@ _in letter _then _(
   ReadIdentifier;
   l2v3z := token;
   UseIdentifier( l2a1z );
   _if (l2v3z = KwCode) _and (lhs <> _nil) _and l2v1z _and l2v2z _then _(
     lhs@.count := lhs@.count + 1;
     prevId := _nil;
     lhs := ;
     l2v2z := false;
     _if input@ = Semicolon _then get(input);
     _goto 2740;
   _);
   _if l2v1z _then _(
     prevId := found;
     l2v2z := false;
   _);
 _) _else _if input@ _in digit _then _(
   SkipNumber;
 _) _else _if input@ = Underline _then _(
   ReadKeyword;
   prevId := _nil;
   lhs := ;
   _if token = KwEnd _then exit
   _else _(
     _if (token <> KwBegin) _and (token <> KwCase) _and (token <> KwSelect) _then _(
       _goto 3013;
     _);
     ScanBody( l2a1z );
     _goto 3107;
     3013:
     _if token = KwExit _then _(
       SkipTrivia;
       _if input@ _in letter _then _(
         _goto 3022;
       _);
       SyntaxError( 110 );
       3022:
       ReadIdentifier;
       SkipTrivia;
       _if _not MarkReference( l2a1z@.refs) _then l2a1z := l2a1z;
     _) _else _(
       _if token = 'GОТО  ' _then _(
         3034:
         ReadNameOrLabel;
         UseIdentifier( l2a1z );
         _goto 3107;
       _);
       _if token = 'GО    ' _then _(
         _if input@ <> Underline _then SyntaxError( 80 );
         ReadKeyword;
         _if token = 'ТО    ' _then _(
           _goto 3034;
         _);
         SyntaxError( 80 );
       _) _else _if token = KwIn _then _(
         _if input@ _in letter _then _(
           ReadIdentifier;
           _if _not MarkReference( root@.types) _then UseIdentifier( l2a1z );
         _);
       _) _else _if token = 'FОR   ' _then _(
         ReadIdentifier;
         _if _not MarkReference( l2a1z@.vars) _then _(
           writeln('В СТРОКЕ ', line:5, ' ПЕРЕМЕННАЯ ЦИКЛА ГЛОБАЛЬНАЯ !!');
         _);
         UseIdentifier( l2a1z );
         UseIdentifier( l2a1z );
       _) _else _(
         _goto 3107;
       _);
     _);
   _);
   3107:
 _) _else _if input@ = Colon _then _(
   get(input);
   _if input@ = Equals _then _(
     get(input);
     SkipWhitespace;
     l2v2z := true;
     _if input@ = Semicolon _then _(
       get(input);
       _if lhs <> _nil _then lhs@.count := lhs@.count + 1;
       prevId := _nil;
       lhs := ;
       l2v1z := true;
       _goto 2740;
     _) _else _(
       lhs := prevId;
     _);
   _) _else _(
     prevId := _nil;
     lhs := ;
     l2v1z := true;
     l2v2z := false;
     _goto 2740;
   _);
 _) _else _if input@ = Semicolon _then _(
   get(input);
   lhs := prevId;
   l2v1z := true;
   _goto 2740;
 _) _else _if input@ = OpenParen _then _(
   SkipTrivia;
 _) _else _if input@ = Apostrophe _then _(
   SkipString;
 _) _else _(
   get(input);
   _goto 3155;
 _);
 3155:
 l2v1z := false;
 (* Keep the loop branch in its own word, as at 03156. *)
 code(ПБlp2733=,)

_);
(* 3160: ПРОСТАЯ_КОНСТАНТА; original lexical level 2. *)
_function ScanConstant:boolean;
_label 3171,3206,3222;
_(

 ScanConstant := false;
 _if (input@ <> Plus) _and (input@ <> '-') _then _(
   _goto 3206;
 _);
 get(input);
 SkipWhitespace;
 3171:
 _if input@ _in digit _then _(
   SkipNumber;
   exit;
 _) _else _(
   _if input@ _in letter _then _(
     ReadIdentifier;
     ScanConstant := true;
     exit;
   _);
   SyntaxError( 84 );
 _);
 _goto 3222;
 3206:
 _if input@ = Apostrophe _then _(
   SkipString;
   exit;
 _) _else _if input@ = Underline _then _(
   ReadKeyword;
   _if token = 'NIL   ' _then exit;
   SyntaxError( 390 );
 _) _else _(
   _goto 3171;
 _);
 3222:
 ScanConstant := false;

_);
(* 3224: ДИАПАЗОН_ИЛИ_ПЕРЕЧИСЛЕНИЕ; original lexical level 2. *)
_proced RangeOrEnum(_var l2a1z:namep; l2a2z:blockp);
_label 3232,3241,3252,3304,3346;
_var l2v1z:boolean;
_(

 l2v1z := true;
 3232:
 _if input@ _in letter _then _(
   ReadIdentifier;
   _if _not MarkReference( root@.types) _then ;
   3241:
   SkipTrivia;
   _if input@ = Dot _then _(
     get(input);
     SkipWhitespace;
     _if input@ <> Dot _then SyntaxError( 200 );
     3252:
     get(input);
     SkipTrivia;
     _if l2v1z _and _not MarkReference( l2a2z@.consts) _then AddReference( l2a2z );
     _if ScanConstant _and _not MarkReference( l2a2z@.consts) _then AddReference( l2a2z );
   _);
   _if input@ = Colon _then _(
     _goto 3252;
   _);
   SkipTrivia;
   exit;
 _);
 _if input@ = OpenParen _then _(
   get(input);
   _if input@ = Star _then _(
     SkipComment;
     _goto 3232;
   _);
   3304:
   SkipTrivia;
   _if input@ _in letter _then _(
     ReadIdentifier;
     AddDeclaration( 2, l2a1z, l2a2z );
     SkipTrivia;
     _if input@ = Comma _then _(
       get(input);
       _goto 3304;
     _);
     _if input@ = CloseParen _then _(
       get(input);
       SkipTrivia;
       exit;
     _);
     SyntaxError( 201 );
   _);
   SyntaxError( 202 );
 _);
 _if input@ _in digit _then _(
   SkipNumber;
   l2v1z := false;
   _goto 3241;
 _);
 _if input@ = Apostrophe _then _(
   SkipString;
   _goto 3241;
 _);
 _if (input@ <> Plus) _and (input@ <> '-') _then _(
   _goto 3346;
 _);
 get(input);
 _goto 3232;
 3346:
 SyntaxError( 203 );

_);
(* 3350: РАЗБОР_ТИПА; original lexical level 2. *)
_proced ParseType(_var l2a1z:namep; l2a2z:blockp);
_label 3372,3414,3465;
_(

 _if input@ = '↑' _then _(
   get(input);
   SkipWhitespace;
   _if input@ = Underline _then _(
     _goto 3372;
   _);
   ReadIdentifier;
   _if _not MarkReference( root@.types) _then ;
   SkipTrivia;
   exit;
 _);
 3372:
 _if input@ = Underline _then _(
   ReadKeyword;
   _if token = KwFile _then _(
     _if input@ = Underline _then _(
       ReadKeyword;
       ParseType( l2a1z, l2a2z );
     _) _else _(
       SyntaxError( 204 );
     _);
   _) _else _if token = KwArray _then _(
     _if input@ <> '[' _then SyntaxError( 205 );
     3414:
     get(input);
     RangeOrEnum( l2a1z, l2a2z );
     _if input@ = Comma _then _(
       _goto 3414;
     _);
     _if input@ <> ']' _then SyntaxError( 206 );
     get(input);
     SkipWhitespace;
     _if input@ <> Underline _then SyntaxError( 207 );
     ReadKeyword;
     ParseType( l2a1z, l2a2z );
   _) _else _if token = KwSet _then _(
     _if input@ <> Underline _then SyntaxError( 208 );
     ReadKeyword;
     RangeOrEnum( l2a1z, l2a2z );
   _) _else _if token = KwPacked _then _(
     _goto 3372;
   _) _else _if token = KwRecord _then _(
     ParseRecord( l2a1z, l2a2z );
   _) _else _(
     SyntaxError( 209 );
     _goto 3465;
   _);
   3465:
   SkipTrivia;
   exit;
 _);
 RangeOrEnum( l2a1z, l2a2z );
_);
(* 3472: РАЗБОР_RECORD; original lexical level 2. *)
_proced ParseRecord+
_label 3477,3526,3576,3607;
_(

 3477:
 SkipTrivia;
 _if input@ _in letter _then _(
   ReadIdentifier;
   AddDeclaration( 2, l2a1z, l2a2z );
   SkipTrivia;
   _if input@ = Comma _then _(
     get(input);
     _goto 3477;
   _);
   _if input@ <> Colon _then SyntaxError( 210 );
   get(input);
   ParseType( l2a1z, l2a2z );
   _if input@ = Semicolon _then _(
     get(input);
     _goto 3477;
   _);
   3526:
   _if input@ = CloseParen _then exit;
   _if input@ <> Underline _then SyntaxError( 211 );
   ReadKeyword;
   _if token = KwEnd _then exit;
   SyntaxError( 212 );
 _);
 _if input@ <> Underline _then SyntaxError( 213 );
 ReadKeyword;
 _if token = KwCase _then _(
   SkipTrivia;
   _if input@ _in letter _then _(
     ReadIdentifier;
     SkipTrivia;
     _if input@ = Colon _then _(
       AddDeclaration( 2, l2a1z, l2a2z );
       get(input);
       SkipTrivia;
       ReadIdentifier;
       SkipTrivia;
     _);
     _if input@ <> Underline _then SyntaxError( 501 );
     ReadKeyword;
     3576:
     SkipTrivia;
     _if _not _not ScanConstant _then _(
       _if _not MarkReference( l2a2z@.consts) _then AddReference( l2a2z );
       3607:
       SkipTrivia;
       _if input@ = Comma _then _(
         get(input);
         _goto 3576;
       _);
       _if input@ = Colon _then _(
         get(input);
         SkipThrough(OpenParen);
         ParseRecord( l2a1z, l2a2z );
         _if input@ <> CloseParen _then SyntaxError( 502 );
         get(input);
         SkipTrivia;
         _if input@ = Semicolon _then _(
           get(input);
           _goto 3576;
         _);
         _goto 3526;
       _);
       SyntaxError( 503 );
     _);
     _goto 3607;
   _);
   SyntaxError( 505 );
 _);
 SyntaxError( 215 );

_);
(* 3644: ОБЪЯВЛЕНИЯ_TYPE; original lexical level 2. *)
_proced TypeDeclarations(_var l2a1z:namep; l2a2z:blockp);
_label 3662,3721;
_var l2v1z:namep;
_(

 l2v1z := root@.types;
 _if l2v1z <> _nil _then _(
   _while l2v1z@.next <> _nil _do _(
     l2v1z := l2v1z@.next;
   _);
 _);
 SkipTrivia;
 3662:
 code(lp3644:);
 _if input@ _in letter _then _(
   ReadIdentifier;
   _if l2a2z@.depth = 1 _then AddDeclaration( 6, l2v1z, root );
   SkipTrivia;
   _if input@ <> Equals _then SyntaxError( 216 );
   get(input);
   ParseType( l2a1z, l2a2z );
   _if input@ <> Semicolon _then SyntaxError( 217 );
   get(input);
   SkipTrivia;
   _if input@ = Underline _then _(
     ReadKeyword;
     exit;
   _);
   _goto 3721;
 _);
 SyntaxError( 216 );
 3721:
 (* Keep the loop branch in its own word, as at 03721. *)
 code(ПБlp3644=,)

_);
(* 3723: ПРОВЕРКА_ПОВТОРНОГО_ИМЕНИ_ПОДПРОГРАММЫ; original lexical level 2. *)
_proced CheckRoutineName(l2a1z:blockp);
_var l2v1z:namep;
_(

 _while l2a1z <> _nil _do _(
   l2v1z := l2a1z@.enums;
   _while l2v1z <> _nil _do _(
     _if l2v1z@.nm = token _then _(
       writeln('ИДЕНТ. ПРОЦЕДУРЫ ',
         token,
         ' В СТР. = ',
         line:4,
         ' УЖЕ ВСТРЕЧАЕТСЯ В СТР. = ',
         l2v1z@.decl:4);
       exit;
     _) _else _(
       l2v1z := l2v1z@.next;
     _);
   _);
   l2a1z := l2a1z@.parent;
 _);

_);
(* 3761: РАЗБОР_FUNCTION; original lexical level 2. *)
_proced ParseFunction(_var l2a1z:blockp; l2a2z:blockp);
_label 4040,4061,4123,4160,4205;
_var l2v1z:namep; l2v2z:namep; l2v3z:blockp; l2v4z:boolean; l2v5z:boolean;
_(

 l2v1z := _nil;
 l2v2z := ;
 ReadIdentifier;
 l2v5z := false;
 SkipWhitespace;
 _if input@ = Plus _then _(
   get(input);
   SkipTrivia;
   l2a1z := l2a2z@.child;
   l2v5z := true;
   _while l2a1z <> _nil _do _(
     _if l2a1z@.nm = token _then _(
       _goto 4061;
     _) _else _(
       l2a1z := l2a1z@.next;
     _);
   _);
   SyntaxError( 112 );
 _);
 NewBlock;
 _if l2a1z = _nil _then _(
   l2a2z@.child := newblk;
 _) _else _(
   l2a1z@.next := newblk;
 _);
 newblk@.parent := l2a2z;
 l2a1z := newblk;
 newblk@.nm := token;
 newblk@.first := line;
 newblk@.depth := depth;
 CheckRoutineName( l2a2z );
 4040:
 _if input@ = Colon _then _(
   get(input);
   SkipWhitespace;
   _if input@ _in letter _then _(
     ReadIdentifier;
   _) _else _(
     SyntaxError( 101 );
   _);
   SkipTrivia;
   _if input@ <> Semicolon _then SyntaxError( 102 );
   get(input);
   SkipTrivia;
   4061:
   l2a1z@.isfun := true;
   ParseBlock( l2v1z, l2a1z, false );
   SkipWhitespace;
   SkipTrivia;
   _if l2v5z _then _(
     l2v3z := l2a1z;
     l2a1z := l2a1z@.next;
     _while l2a1z <> _nil _do _(
       l2v3z := l2a1z;
       l2a1z := l2a1z@.next;
     _);
     l2a1z := l2v3z;
   _);
   _if input@ = Underline _then _(
     ReadKeyword;
     exit;
   _);
   SyntaxError( 103 );
 _);
 _if input@ <> OpenParen _then SyntaxError( 104 );
 get(input);
 l2v4z := false;
 4123:
 SkipTrivia;
 _if input@ _in letter _then _(
   ReadIdentifier;
   AddDeclaration( 3, l2v1z, l2a1z );
   l2v1z@.count := 3;
   SkipTrivia;
   _if input@ = Comma _then _(
     get(input);
     _goto 4123;
   _);
   _if l2v4z _then _(
     _goto 4160;
   _);
   _if input@ <> Colon _then SyntaxError( 105 );
   get(input);
   SkipWhitespace;
   ParseType( l2v2z, newblk );
   4160:
   l2v4z := false;
   _if input@ = Semicolon _then _(
     get(input);
     _goto 4123;
   _);
   _if input@ = CloseParen _then _(
     get(input);
     SkipWhitespace;
     _goto 4040;
   _);
   SyntaxError( 106 );
 _);
 _if input@ <> Underline _then SyntaxError( 107 );
 ReadKeyword;
 l2v4z := false;
 _if (token <> KwVar) _and (token <> KwFunction) _then _(
   _goto 4205;
 _);
 _goto 4123;
 4205:
 _if token <> KwProcedure _then SyntaxError( 108 );
 l2v4z := true;
 _goto 4123;

_);
(* 4213: РАЗБОР_PROCEDURE; original lexical level 2. *)
_proced ParseProcedure(_var l2a1z:blockp; l2a2z:blockp);
_label 4272,4276,4341,4376,4423;
_var l2v1z:namep; l2v2z:namep; l2v3z:blockp; l2v4z:boolean; l2v5z:boolean;
_(

 l2v1z := _nil;
 l2v2z := ;
 ReadIdentifier;
 l2v5z := false;
 SkipWhitespace;
 _if input@ = Plus _then _(
   get(input);
   SkipTrivia;
   l2a1z := l2a2z@.child;
   l2v5z := true;
   _while l2a1z <> _nil _do _(
     _if l2a1z@.nm = token _then _(
       _goto 4276;
     _) _else _(
       l2a1z := l2a1z@.next;
     _);
   _);
   SyntaxError( 112 );
 _);
 NewBlock;
 _if l2a1z = _nil _then _(
   l2a2z@.child := newblk;
 _) _else _(
   l2a1z@.next := newblk;
 _);
 newblk@.parent := l2a2z;
 l2a1z := newblk;
 newblk@.nm := token;
 newblk@.first := line;
 newblk@.depth := depth;
 CheckRoutineName( l2a2z );
 4272:
 _if input@ = Semicolon _then _(
   get(input);
   SkipWhitespace;
   4276:
   ParseBlock( l2v1z, l2a1z, false );
   SkipWhitespace;
   SkipTrivia;
   _if l2v5z _then _(
     l2v3z := l2a1z;
     l2a1z := l2a1z@.next;
     _while l2a1z <> _nil _do _(
       l2v3z := l2a1z;
       l2a1z := l2a1z@.next;
     _);
     l2a1z := l2v3z;
   _);
   _if input@ = Underline _then _(
     ReadKeyword;
     exit;
   _);
   SyntaxError( 65 );
 _);
 _if input@ <> OpenParen _then SyntaxError( 66 );
 get(input);
 _if input@ = Star _then _(
   SkipComment;
   _goto 4272;
 _);
 l2v4z := false;
 4341:
 SkipTrivia;
 _if input@ _in letter _then _(
   ReadIdentifier;
   AddDeclaration( 3, l2v1z, l2a1z );
   l2v1z@.count := 3;
   SkipTrivia;
   _if input@ = Comma _then _(
     get(input);
     _goto 4341;
   _);
   _if l2v4z _then _(
     _goto 4376;
   _);
   _if input@ <> Colon _then SyntaxError( 67 );
   get(input);
   SkipWhitespace;
   ParseType( l2v2z, newblk );
   4376:
   l2v4z := false;
   _if input@ = Semicolon _then _(
     get(input);
     _goto 4341;
   _);
   _if input@ = CloseParen _then _(
     get(input);
     SkipWhitespace;
     _goto 4272;
   _);
   SyntaxError( 68 );
 _);
 _if input@ <> Underline _then SyntaxError( 69 );
 ReadKeyword;
 l2v4z := false;
 _if (token <> KwVar) _and (token <> KwFunction) _then _(
   _goto 4423;
 _);
 _goto 4341;
 4423:
 _if token <> KwProcedure _then SyntaxError( 70 );
 l2v4z := true;
 _goto 4341;

_);
(* 4431: ОБЪЯВЛЕНИЯ_CONST; original lexical level 2. *)
_proced ConstDeclarations(l2a1z:blockp);
_label 4435,4453,4476,4503;
_var l2v1z:namep;
_(

 l2v1z := _nil;
 SkipTrivia;
 4435:
 _if input@ _in letter _then _(
   ReadIdentifier;
 _) _else _(
   SyntaxError( 85 );
 _);
 AddDeclaration( 1, l2v1z, l2a1z );
 _if input@ <> Equals _then SyntaxError( 86 );
 4453:
 get(input);
 SkipTrivia;
 _if ScanConstant _and _not MarkReference( l2a1z@.consts) _then AddReference( l2a1z );
 SkipTrivia;
 _if (input@ <> '/') _and (input@ <> Star) _and (input@ <> '-') _and (input@ <> Plus) _then _(
   _goto 4476;
 _);
 _goto 4453;
 4476:
 _if (input@ <> 'Е') _and (input@ <> Dot) _then _(
   _goto 4503;
 _);
 _goto 4453;
 4503:
 _if input@ <> Semicolon _then SyntaxError( 87 );
 get(input);
 SkipTrivia;
 _if input@ = Underline _then _(
   ReadKeyword;
   exit;
 _);
 _goto 4435;
_);
(* 4516: РАЗБОР_БЛОКА; original lexical level 2. *)
_proced ParseBlock+
_label 4574,4617,4630,4743;
_var l2v1z:blockp; l2v2z:namep; l2v3z:namep;
_(

 _if input@ = Plus _then _(
   get(input);
   exit;
 _);
 _while input@ = OpenParen _do _(
   get(input);
   _if input@ = Star _then _(
     SkipComment;
   _) _else _(
     SyntaxError( 41 );
   _);
 _);
 _if input@ _in letter _then _(
   ReadIdentifier;
   _if token <> KwExtern _then SyntaxError( 800 );
   _if input@ <> Semicolon _then SyntaxError( 801 );
   get(input);
   exit;
 _);
 depth := depth + 1;
 l2v1z := _nil;
 l2v3z := ;
 l2v2z := l2a2z@.enums;
 _while l2v2z <> _nil _do _(
   l2v3z := l2v2z;
   l2v2z := l2v2z@.next;
 _);
 l2v2z := _nil;
 _if input@ <> Underline _then SyntaxError( 42 );
 ReadKeyword;
 4574:
 _if token = KwLabel _then _(
   LabelDeclarations( l2a2z );
   _goto 4574;
 _) _else _if token = KwConst _then _(
   ConstDeclarations( l2a2z );
   _goto 4574;
 _) _else _if token = KwType _then _(
   TypeDeclarations( l2v3z, l2a2z );
   _goto 4574;
 _) _else _if token = KwVar _then _(
   4617:
   SkipTrivia;
   _if input@ _in letter _then _(
     ReadIdentifier;
     AddDeclaration( 3, l2a1z, l2a2z );
     4630:
     _if input@ = Comma _then _(
       get(input);
       _goto 4617;
     _);
     _if input@ = Colon _then _(
       get(input);
       SkipWhitespace;
       ParseType( l2v3z, l2a2z );
     _);
     _if input@ = Semicolon _then _(
       get(input);
       SkipTrivia;
     _);
     _if input@ = Underline _then _(
       ReadKeyword;
       _goto 4574;
     _);
     _if input@ = OpenParen _then _(
       get(input);
       _if input@ = Star _then _(
         SkipComment;
       _) _else _(
         SyntaxError( 45 );
       _);
       _goto 4630;
     _);
     _goto 4617;
   _);
   _if input@ = OpenParen _then _(
     get(input);
     _if input@ = Star _then _(
       SkipComment;
     _) _else _(
       SyntaxError( 46 );
     _);
     _goto 4617;
   _);
   SyntaxError( 47 );
 _) _else _if token = KwProcedure _then _(
   ParseProcedure( l2v1z, l2a2z );
   l2v1z@.last := line - 1;
   _goto 4574;
 _) _else _if token = KwFunction _then _(
   ParseFunction( l2v1z, l2a2z );
   l2v1z@.last := line - 1;
   _goto 4574;
 _) _else _(
   _if token = KwBegin _then _(
     l2a2z@.used := l2a3z;
     asmref := false;
     ScanBody( l2a2z );
     SkipWhitespace;
     _if input@ = Semicolon _then _(
       get(input);
       depth := depth - 1;
       l2a2z@.asm := asmref;
       exit;
     _);
     _if input@ <> Dot _then SyntaxError( 49 );
     exit;
   _) _else _(
     SyntaxError( 50 );
     _goto 4743;
   _);
 _);
 4743:

_);
(* 4744: ПОДКЛЮЧИТЬ_ВХОДНОЙ_МАССИВ; procedure; original lexical level 2. *)
_proced BindInput(l2a1z:integer; l2a2z:integer);
_const InputReadZone=0010340000000000C;
_var base:integer;
_(
 base:=InputReadZone;
 code(2ЦС3=ЗЧ75211,2СЧ4=У076002,АВ13=ЗЧ75212,)
_);
(* 4756: ПРОПУСК_ПРОБЕЛОВ_В_ЗАПРОСЕ; original lexical level 2. *)
_proced SkipPromptSpaces;
_(

 _while input@ = Space _do _(
   get(input);
 _);

_);
(* 4764: ЗАПРОС_АДРЕСА_И_ДЛИНЫ; procedure; original lexical level 2. *)
_proced ReadRequest;
_label 5014;
_var address,zones:integer;
_(
 _if errors=5 _then writeln('ДЛЯ ВЫХОДА СДЕЛАЙТЕ "ЕТХ"');
 _if errors>10 _then _goto 5014;
 BIND(' ==> ≡172');
 cold1:=false;
 SkipPromptSpaces;
 _if input@=Equals _then _(
  _for address:=1 _to 3 _do _if input@<>ETX _then get(input);
  SkipPromptSpaces
 _);
 _if input@=ETX _then _( 5014: writeln('ВЫХОД В ПУЛЬТ'); code(ПБ76002=) _);
 address:=0;
 _while input@ < '9' _do _( address:=address*8+ord(input@); get(input) _);
 _if (address>671743B) _or (address<100000B) _then _(
  writeln('НЕ БУДУ.'); errors:=errors+1; _goto 5134
 _);
 _while _not (input@ _in digit) _and (input@<>ETX) _do get(input);
 _if input@=ETX _then _( write('ПОВТОРИТЕ'); errors:=errors+1; _goto 5134 _);
 zones:=0;
 _while input@ < '9' _do _( zones:=zones*8+ord(input@); get(input) _);
 _if (zones<1) _or (zones>77B) _then _(
  writeln('ВЕЛИК МАССИВ'); errors:=errors+1; _goto 5134
 _);
 _while input@=Space _do get(input);
 cold := input@='Х';
 _if cold _then _(
  get(input);
  cold1 := input@='1'
 _);
 BindInput(address,zones); reset(input)
_);
_(
 InitBuiltins;
 errors:=0;


 setup(saved);
 writeln('**** Ч И С Т К А ****':38);
 5134:
 cold1 := false;
 ReadRequest;
 rollup(saved);
 line := 1;
 clean := true;
 SkipWhitespace;
 5142:
 SkipTrivia;
 _if input@ = OpenParen _then _(
   _goto 5142;
 _);
 _if input@ <> Underline _then SyntaxError( 1 );
 ReadKeyword;
 _if token <> 'РRОGRА' _then SyntaxError( 2 );
 ReadIdentifier;
 NewBlock;
 newblk@.first := line;
 newblk@.depth := 1;
 newblk@.nm := Spaces;
 depth := 1;
 root := newblk;
 root@.types := _nil;
 writeln('ПРОГРАММА  ':30, token);
 writeLN;
 _if input@ = OpenParen _then _(
   5200:
   _while (input@ <> CloseParen) _and (input@ <> OpenParen) _do _(
     get(input);
   _);
   _if input@ = OpenParen _then _(
     SkipTrivia;
     _goto 5200;
   _);
   get(input);
   SkipTrivia;
 _);
 _if input@ <> Semicolon _then SyntaxError( 4 );
 get(input);
 SkipTrivia;
 ParseBlock( _nil, root, true );
 _if input@ <> Dot _then SyntaxError( 3 );
 DeclReport( root );
 BlockReport( root );
 _if clean _then _(
   writeln('ПРОГРАММА НАПИСАНА ЧИСТО !':42);
 _);
 writeLN;
 writeln('**** КОНЕЦ ****':35);
 writeLN;
 _goto 5134;

_).
