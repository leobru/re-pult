(*=p-,t-,l-,k12*)_program ЭХОЛОТ(F=260000B 1);
(* Recovered source of the storage analysis in zones 01064-01067.
   Original entry addresses in comments are octal. Names have six significant
   characters. Sizes and addresses printed by the program are octal.
   The program reads source text; it does not execute the analyzed program. *)
_label 7560;
_const
 (* Original scalar/ALFA prefix, 00014..00057.
    Together with local CONST blocks and WRITE/BIND data this preserves
    every literal word at its original address, 00011..00530.
    Literals 00060..00064 are emitted in order by their uses. *)
 C00014=0000000000000021C;
 C00015=0000000000000037C;
 C00016=0000000000000200C;
 C00017=0000000000006060C;
 C00020=0000000000000011C;
 KWSelect='SELECT';
 KWLabel='0LABEL';
 KWType='00TYPE';
 ETX='≡377';
 KWBegin='0BEGIN';
 KWExtern='EXTERN';
 KWConst='0CONST';
 KWVar='000VAR';
 KWFunction='FUNCTI';
 KWProcedure='PROCED';
 KWNil='000NIL';
 KWRecord='RECORD';
 KWCase='00CASE';
 KWOf='0000OF';
 KWEnd='000END';
 KWArray='0ARRAY';
 KWFile='00FILE';
 KWSet='000SET';
 XtaName='0000СЧ';
 UtcName='0000ИА';
 C00045=0000000000000017C;
 C00046=0000000000000002C;
 C00047=0000000000000003C;
 C00050=0000000000000004C;
 C00051=0000000000000005C;
 C00052=0000000000000006C;
 C00053=0000000000000007C;
 C00054=0000000000000040C;
 C00055=0000000000000114C;
 C00056=0000000000000014C;
 C00057=0000000000000024C;
 Space=' ';
_type
 int=integer; letter='А'..'Z'; digit='0'..'9';
 chars6=_array[1..6] _of char;
 bitset=_set _of 0..31;
 nameclass=(TYPE,CONST,VAR,PROC,FIELD,TAGF,TAGV);
 tokenclass=(ОГ,ИД,ПС,ЦЕ,AL,RE,СН,CF);
 typeform=(kSc,kRng,kPtr,kSet,kArr,kRec,kFile,kAlias);
 (* Historical identifier layout; variant sizes are 9 and 6 words. *)
 identifier=_record
  name:alfa; level:integer; next,data:@identifier; kind:nameclass;
  _case nameclass _of
   TYPE:(size:integer; form:typeform;
    _case integer _of 0:(lower,upper:integer); 1:(rangeType:@identifier; stride:alfa);
                     2:(packing:integer));
   CONST:(consttype:@identifier; constvalue:alfa; constNext:@identifier);
   VAR:(vartype:@identifier; address:alfa; traced:boolean);
   PROC:(resulttype:@identifier; procFlags:integer; params:@identifier;
         entry,environment:alfa; nargs:integer; proc11,proc12:@identifier; proc13,proc14,proc15:boolean; proc16:integer; ownSize,peakSize:integer);
   FIELD,TAGF:(fieldChain,fieldType,owner:@identifier; fieldOffset:integer);
   TAGV:(tagNext:@identifier; variantSize:integer)
 _end;
 idptr=@identifier;
 hashtable=_array[0..127] _of idptr;
 labelentry=_record value,state1,level,state3:integer;
  next:@labelentry; state5:integer _end;
 filebinding=_record name:alfa; first,last:integer; used:boolean; next:@filebinding _end;
 comparelink=_record next:@comparelink; first,second:idptr _end;
 word=_record _case integer _of 0:(i:integer); 1:(b:bitset); 2:(a:alfa); 3:(r:real) _end;
 filewd=_file _of bitset;
 withitem=_record kind:integer; off,reg:alfa; typ:idptr;
  ins:@integer; inverted:boolean _end;
_var
 (* Historical global frame. Offsets in these comments are octal, from M1. *)
 (* 00012..00037 *)
 s00012:integer; realValue:real;
 s00014,s00015,s00016,s00017,optT,optS,hascod,optI,firstc:boolean;
 s00025,s00026,s00027,line,nameBucket,builtinNo,withIndex,withDepth:integer;
 (* 00040..00077 *)
 poolIndex,textLength,poolStart,poolBase,newcnt,reserv,s00043,s00044:integer;
 loadOp,diagWord:alfa; codeLevel,s00050,s00051:integer;
 newText,NilOffset:alfa; s00054:integer; s00055:idptr;
 lineEnd,seqGost,seqItm,diagChar:char; diagToken:tokenclass;
 lookupMode,pendingTypes,codepos,codeLast,codeStart,codePrev,codeend,s00072:integer;
 poolValue:word; allowForward,longStrings,s00076,knownIdent:boolean;
 (* 00100..00142 *)
 s00100,s00101,s00102,s00103:integer;
 s00104,s00105,s00106,s00107,s00110,s00111:boolean; s00112:integer;
 s00113,s00114,s00115,s00116:boolean; s00117:integer;
 diagIdent,forwardType,recordType,textType,inType,outType,nilType,setType,
 boolType,intType,realType,charType,alfaType:idptr;
 heap:@integer; s00136,s00137:integer; s00140,s00141:@filebinding; s00142:integer;
 (* 00143..01015 *)
 returnOps:_array[3..8,1..6] _of alfa;
 extraOps:_array[1..17] _of alfa;
 namehash,oldhash:hashtable;
 withTable:_array[0..17] _of withitem;
 withLast:withitem;
 savedChars:_array[1..4] _of char;
 (* 01016..07244 *)
 literalPool:_array[1..3120] _of integer;
 s07076:idptr; pairHead:@comparelink;
 (* 07100..07244: names of external procedures in ITM. *)
 savedNames:_array[0..100] _of alfa;
 (* 07245..07416; F starts at 07417. *)
 s07245,s07246,s07247,heapReserve,errors:integer;
 calls:_record top:integer; names:_array[1..100] _of alfa _end;
 (*=b4*)F:filewd;(*=b1*)

(* 00540: read one INPUT zone into page 34; zero length returns to PULT. *)
_proced BindInput(address,zones:integer);
_const InputReadZone=0010340000000000C;
_var base:integer;
_(
 base:=InputReadZone;
 code(2ЦС3=ЗЧ75211,2СЧ4=У076002,АВ13=ЗЧ75212,)
_);

(* 00552: spaces only; no line accounting is needed at the prompt. *)
_proced SkipPromptSpaces;
_( _while input@=Space _do get(input) _);

(* 00560: addresses 3/4 and word counters 9/10 of a Pascal file descriptor. *)
_proced SetCodeFile(_var filein:filewd; address,zones:integer);
_(
 code(2СЧ4=2ИК3,ЗЧ3=2СЧ5,2ИК3=ЗЧ4,);
 zones:=zones*1024;
 code(2ИК3=ЗЧ11,2ИК3=ЗЧ12,);
 reset(filein)
_);

(* 00676: terminal request; ReadArrayAddress is physically before its body. *)
_proced ReadRequest;
_label 0730,1014;
_var address,zones,codeAddress,codeZones:integer;
(* 00577: only 0..8 are accumulated; 00630 is the separate digit predicate. *)
_proced ReadArrayAddress(_var a,z:integer);
_(
 a:=0;
 _while input@<'9' _do _( a:=a*8+ord(input@); get(input) _);
 _if (a>671734B) _or (a<100000B) _then _(
  writeln('НЕ БУДУ.'); errors:=errors+1; _goto 7560
 _);
 _while _not (input@ _in digit) _and (input@<>ETX) _do get(input);
 _if input@=ETX _then _(
  writeln('ПОВТОРИТЕ'); errors:=errors+1; _goto 7560
 _);
 z:=0;
 _while input@<'9' _do _( z:=z*8+ord(input@); get(input) _);
 _if (z<1) _or (z>77B) _then _(
  writeln('ВЕЛИК МАССИВ'); errors:=errors+1; _goto 7560
 _)
_);
_(
 _if errors=3 _then writeln('ДЛЯ ВЫХОДА СДЕЛАЙТЕ "ЕТХ"');
 _if errors>6 _then _goto 0730;
 optT:=false; optS:= ; optI:= ; hascod:= ; firstc:=true;
 bind(' ==> ≡172');
 SkipPromptSpaces;
 _if input@='=' _then
  _for address:=1 _to 3 _do _if input@<>ETX _then get(input);
 SkipPromptSpaces;
 _if input@=ETX _then _(
  0730:
  writeln('ВЫХОД В ПУЛЬТ'); code(ПБ76002=)
 _);
 _if input@='И' _then _(
  writeln('ФОРМА ОБРАЩЕНИЯ:
    НУЗЗЗЗВN [/NUZZZZВQ ] [И] [Т] [С]
НУЗЗЗЗВ N - НАЧАЛО И ЧИСЛО ЗОН ТЕКСТА ПРОГРАММЫ,
NUZZZZВ Q - НАЧАЛО И ЧИСЛО ЗОН КОДА ПРОГРАММЫ,
        И - ТОЛЬКО ИТОГОВЫЕ ДАННЫЕ,
        Т - ТАБЛИЦА ПРОЦЕДУР ТЕЛА ПРОГРАММЫ,
        С - СПИСОК ИМЕН ВНУТРЕННИХ ПРОЦЕДУР.');
  _goto 7560
 _);
 ReadArrayAddress(address,zones);
 SkipPromptSpaces;
 _if input@='/' _then _(
  get(input); SkipPromptSpaces;
  ReadArrayAddress(codeAddress,codeZones);
  hascod:=true;
  SetCodeFile(F,codeAddress,codeZones)
 _);
 _while _not (input@ _in letter) _and (input@<>ETX) _do get(input);
 _while input@ _in letter _do _(
  _if input@='Т' _then optT:=true
  _else _if input@='И' _then optI:=true
  _else _if input@='С' _then _( optS:=true; _goto 1014 _);
  1014: get(input);
  _while (input@=Space) _or (input@=',') _do get(input)
 _);
 BindInput(address,zones);
 reset(input)
_);


(* 01136: sequential code-file scan, with nested return/prologue recognizers.
   codepos is one greater than the address of the current word F@. *)
(*=c-*)
_proced ReadCodeBounds(_var first:boolean; _var beginCode,endCode:alfa);
_label 1147,1156,1161,1166;
_const
 CallLeft=6310000000000000C;
 CallRight=0000000063100000C;
 LCallMask=7774000000000000C;
 RCallMask=0000000077740000C;
 LeftReturn=0307401200000000C;
 AdvanceSP=7650000000000000C;
 RightReturn=0000000003074012C;
 StoreDisplay=0043000054000002C; (* ITS display register; ATX 2(M13). *)
 SetFrame=0037000374440013C; (* NTR 3; MTJ M17 -> M13. *)
 SaveFrameAndAdvance=0043001376500000C; (* ITS M13; UTM size(M17). *)
 SaveReturn=7444000000430016C; (* MTJ M17 -> display register; ITS M16. *)
 OpcodeLeftMask=7770000000000000C;
 LeftExit=0307400700000000C;
 RightExit=0000000003074007C;
 LeftHalfMask=7777777700000000C;
 RightHalfMask=0000000077777777C;
 MaskFrameAdvance=7777777777700000C;
 MaskSaveReturn=7774000077777777C;
 MaskStoreDisplay=7777000077777777C;
_var unused:integer; lastCode,prevCode:alfa;
(* 01030: find UJ 74012 / UJ 74007 in either half and consume that word. *)
_proced FindReturn;
_label 1032;
_(
 1032:
 _if (F@ ∧ LeftHalfMask = LeftReturn) _or
     (F@ ∧ RightHalfMask = RightReturn) _or
     (F@ ∧ LeftHalfMask = LeftExit) _or
     (F@ ∧ RightHalfMask = RightExit) _then _(
  codeLast:=codepos-1; get(F); codepos:=codepos+1; exit
 _);
 get(F); codepos:=codepos+1; _goto 1032
_);

(* 01057: recognize shared-helper and inline Pascal frame prologues.
   A failed match leaves every word inspected consumed. *)
_function IsPrologue:boolean;
_(
 IsPrologue:=false;
 _if (F@ ∧ LCallMask = CallLeft) _or
     (F@ ∧ RCallMask = CallRight) _then _(
  get(F); codepos:=codepos+1;
  _if F@ ∧ OpcodeLeftMask = AdvanceSP _then _(
   codeStart:=codepos-2; IsPrologue:=true; exit
  _)
 _) _else _if F@ ∧ MaskFrameAdvance = SaveFrameAndAdvance _then _(
  get(F); codepos:=codepos+1;
  _if F@=SetFrame _then _(
   get(F); codepos:=codepos+1;
   _if F@ ∧ MaskSaveReturn=SaveReturn _then _(
    get(F); codepos:=codepos+1;
    _if F@ ∧ MaskStoreDisplay=StoreDisplay _then _(
     get(F); codepos:=codepos+1;
     _if F@ ∧ OpcodeLeftMask=AdvanceSP _then _(
      codeStart:=codepos-5; IsPrologue:=true; exit
     _)
    _)
   _)
  _)
 _)
_);
_(
 _if first _then _(
  codepos:=12; first:=false;
  1147: _if IsPrologue _then _goto 1156;
  get(F); codepos:=codepos+1; _goto 1147;
  1156:
  codePrev:=codeStart
 _);
 _if codeLevel<>1 _then _(
  1161: FindReturn;
  _if IsPrologue _then _goto 1166;
  _goto 1161;
  1166:
  mapia(codeLast,lastCode); mapia(codePrev,prevCode);
  beginCode:=prevCode; endCode:=lastCode; codePrev:=codeStart
 _)
_);


(*=c+*)

(* 06137: main source analyzer; following helpers are lexically nested. *)
_proced analyze(_var paramName:alfa; _var paramBlock:idptr);
_label 6411,6504,6526,6644,6672,6727,6732,7117,7172,7201,7212;
_var p,t,c,previous,lastNode:idptr;
 scratchWord:word;
 globalText,procedureText,u13,sumText,frameNext:alfa;
 loopIndex,initindex:integer;
 (* Slots 022..061 belong to the original block-analysis frame. *)
 reportIndex:integer; savedOutput,columns,frameSize,frameTotal:integer; l00027:integer; savedCheck,isFunction:boolean; wasTerm,nextLine:boolean; chars:_array[0..12] _of char; scopeMark:idptr; savedForward:idptr; rightConst:idptr; currentLabel:@labelentry; savedLabels,l00056:idptr; binaryOp,leftValue:integer; listBegin:integer;
 sumCodeText,codeText:alfa; l00064:integer; bodyProc:idptr;

(* 01177: pad leading zero bytes; names use six columns, numbers five. *)
_proced PrintField(value:alfa);
_label 1242;
_var chars:_array[0..12] _of char; padding:alfa; i:integer; significant:boolean;
_(
 padding:='      '; unpck(chars[1],padding); unpck(chars[7],value);
 i:=1; significant:=false;
 _while i<7 _do _(
  _if (chars[i+6]<>'0') _or significant _then _(
   chars[i]:=chars[i+6]; significant:=true
  _);
  i:=i+1
 _);
 _if _not significant _then chars[6]:='0';
 significant:=false;
 _for i:=1 _to 6 _do _if chars[i] _in letter _then _(
  significant:=true; _goto 1242
 _);
 1242:
 _if significant _then i:=1 _else i:=2;
 _for i:=i _to 6 _do _( output@:=chars[i]; put(output) _)
_);

(* 01256: left-justify a name, padding the vacated bytes with spaces. *)
_function TrimName(value:alfa):alfa;
_var chars:_array[0..12] _of char; padding:alfa; i:integer;
_(
 padding:='      '; unpck(chars[7],padding); unpck(chars[1],value);
 i:=1;
 _while i<7 _do _(
  _if chars[i]<>'0' _then _(
   pck(chars[i],padding); TrimName:=padding; exit
  _);
  i:=i+1
 _);
 TrimName:=padding
_);

(* 01302: add a numeric displacement to an address held as ALFA. *)
_proced AddAddress(_var address:alfa; amount:integer);
_var number:integer;
_( mapai(address,number); mapia(amount+number,address) _);

(* 01314: skip through a delimiter, counting every intervening line end. *)
_proced SkipThrough(delimiter:char);
_label 1316;
_(
 1316:
 _while (input@<>lineEnd) _and (input@<>delimiter) _do get(input);
 _if input@=delimiter _then _( get(input); exit _);
 get(input); line:=line+1; _goto 1316
_);

(* 01332: historical parser diagnostic; enum tables supply CLASS and VSCT. *)
_proced Diagnostic(n:integer);
_(
 writeln('ЕRRОR = ',n:5,' NL= ',line:4,' NАМЕ=',diagIdent@.name,
         ' СLАSS=',diagIdent@.kind,' С=',diagChar,
         ' VSСТ=',diagToken,' ЯП=',diagWord);
 _goto 7560
_);

(* 01470: initialization owns the three original level-4 constructors. *)
_proced InitHistorical;
_var hash:integer;
(* 01401: nine-word type/name header, linked into the 128-bucket hash. *)
_proced NewIdentifier(packedName:alfa; _var result:idptr);
_var bucket:integer; node:idptr;
_(
 new(node;upper);
 (*=c-*)mapai(packedName ∧ '000177',bucket);(*=c+*)
 node@ := [packedName,0,namehash[bucket],_nil,TYPE,1,kSc];
 namehash[bucket]:=node; result:=node
_);
(* 01427: constant type and value occupy words 5 and 6. *)
_proced NewConstant(packedName,value:alfa);
_var node:idptr;
_(
 NewIdentifier(packedName,node); node@.kind:=CONST;
 node@.consttype:=diagIdent; node@.constvalue:=value
_);
(* 01445: six-word builtin header; DATA holds its consecutive number. *)
_proced NewBuiltin(packedName:alfa);
_var node:idptr;
_(
 new(node;resulttype);
 (*=c-*)mapai(packedName ∧ '000177',hash);(*=c+*)
 node@ := [packedName,0,namehash[hash], ,PROC,diagIdent];
 node@.data:=ptr(builtinNo); builtinNo:=builtinNo+1;
 namehash[hash]:=node
_);
_(
 (*=c-*)
pairHead := _nil;
 s07245 := 1;
 s07246:= ;
 s07247:= ;
 calls.top:= ;
 _for hash:=0 _to 127 _do _(
  namehash[hash]:=_nil; oldhash[hash]:=_nil
 _);
 s00076 := 1;
 s00017 := ;
 s00100 := ;
 s00101 := ;
 s00072 := 1;
 s00110 := 1;
 s00107 := 1;
 s00104 := 0;
 s00105 := 1;
 s00106 := 1;
 s00043 := 0;
 s00044 := 1;
 s00014 := 0;
 s00103 := 0;
 s00112 := ;
 s00015 := ;
 s00016 := ;
 s00111 := 0;
 s00102 := ;
 longStrings := ;
 s00116 := ;
 loadOp := XtaName;
 s00054 := 0;
 lineEnd := '≡175';
 s00136 := -1;
 s00137 := ;
 newcnt := 0;
 s00012 := 1;
 reserv := 100;
 withDepth := 0;
 lookupMode := 0;
 s00027 := 0;
 s00142 := ;
 s00050 := ;
 poolStart:=ord(ref(literalPool[9])); poolBase:=poolStart-9;
 s00055:=_nil; diagIdent:=_nil; recordType:=_nil; s07076:=_nil; s00141:= ;
 s00025:=0; s00026:=10; line:=1; NilOffset:='000011'; codeLevel:=1;
 literalPool[9]:=ord(_nil); literalPool[9+1]:=0; literalPool[9+2]:=1;
 poolIndex:=11; seqGost:='А'; mapгa(seqGost,seqItm); tnl(seqItm);
 _for hash:=1 _to 17 _do extraOps[hash]:='000000';
 extraOps[15]:=UtcName;
 _for hash:=3 _to 8 _do
  _for initindex:=1 _to hash-2 _do returnOps[hash,initindex]:='000000';

 NewIdentifier( 'ВООLЕА', boolType );
 NewIdentifier( 'INТЕGЕ', intType );
 NewIdentifier( '00СНАR', charType );
 NewIdentifier( '000000', setType );
 setType@ := [,,,intType,,,kSet];
 NewIdentifier( '00RЕАL', realType );
 NewIdentifier( '00АLFА', alfaType );
 NewIdentifier( '0УКNIL', nilType );
 nilType@.form := kPtr;
 diagIdent := boolType;
 NewConstant( '0FАLSЕ', '000000' );
 NewConstant( '00ТRUЕ', '000013' );
 NewIdentifier( '00ТЕХТ', textType );
 textType@.data := charType;
 textType@.form := kFile;
 textType@.size := 30;
 textType@.packing := 8;
 NewIdentifier( '0INРUТ', inType );
 inType@.kind := VAR;
 inType@.vartype := textType;
 inType@.address := '000007';
 NewIdentifier( 'ОUТРUТ', outType );
 outType@.kind := VAR;
 outType@.vartype := textType;
 outType@.address := '000010';
 forwardType := intType;
 diagIdent := _nil;
 builtinNo := 0;
 NewBuiltin( '000РUТ' );
 NewBuiltin( '000GЕТ' );
 NewBuiltin( 'RЕWRIТ' );
 NewBuiltin( '0RЕSЕТ' );
 NewBuiltin( '000NЕW' );
 NewBuiltin( '0UNРСК' );
 NewBuiltin( '000РСК' );
 NewBuiltin( '00ЕХIТ' );
 NewBuiltin( 'РRINТО' );
 NewBuiltin( '00НАLТ' );
 NewBuiltin( '0МАРIА' );
 NewBuiltin( '0МАРАI' );
 NewBuiltin( '000ТNL' );
 NewBuiltin( '0000ГГ' );
 NewBuiltin( '0МАРГА' );
 NewBuiltin( 'МАРЯГА' );
 NewBuiltin( '00СОDЕ' );
 NewBuiltin( '0SЕТUР' );
 NewBuiltin( 'RОLLUР' );
 NewBuiltin( '0WRIТЕ' );
 NewBuiltin( 'WRIТЕL' );
 NewBuiltin( 'DISРОS' );
 NewBuiltin( '00RЕАD' );
 NewBuiltin( 'RЕАDLN' );
 NewBuiltin( '0ОРЕND' );
 NewBuiltin( '00РUТD' );
 NewBuiltin( '00GЕТD' );
 NewBuiltin( '00DЕLD' );
 NewBuiltin( '00МОDD' );
 NewBuiltin( '00NЕWD' );
 NewBuiltin( '00ВIND' );
 NewBuiltin( '000INS' );
 builtinNo := 0;
 diagIdent := realType;
 NewBuiltin( '00SQRТ' );
 NewBuiltin( '000SIN' );
 NewBuiltin( '000СОS' );
 NewBuiltin( 'АRСТАN' );
 NewBuiltin( 'АRСSIN' );
 NewBuiltin( '0000LN' );
 NewBuiltin( '000ЕХР' );
 NewBuiltin( '000АВS' );
 diagIdent := intType;
 NewBuiltin( '0ТRUNС' );
 diagIdent := boolType;
 NewBuiltin( '000ОDD' );
 diagIdent := intType;
 NewBuiltin( '000ОRD' );
 diagIdent := charType;
 NewBuiltin( '000СНR' );
 NewBuiltin( '00SUСС' );
 NewBuiltin( '00РRЕD' );
 diagIdent := boolType;
 NewBuiltin( '000ЕОF' );
 diagIdent := nilType;
 NewBuiltin( '000RЕF' );
 NewBuiltin( '000РТR' );
 diagIdent := intType;
 NewBuiltin( '000SQR' );
 NewBuiltin( '0RОUND' );
 NewBuiltin( '000SЕL' );
 NewBuiltin( '00САRD' );
 NewBuiltin( '0МINЕL' );
 diagIdent := boolType;
 NewBuiltin( '00ЕОLN' );
 NewBuiltin( '0SНIFТ' );
 (*=c+*)
_);

(* 02015: OR mask 6400000000000000C into a raw integer word. *)
_proced AddExponent(_var source,dest:integer);
_(
 code(=ЗЧ,15ПА15=ВИ15,СД/4/=МР,3ИК3=ЛС,); dest:= ;
_);

(* 02027: intern a literal, or append it unconditionally for FORCE. *)
_proced PutLiteral(_var offset:alfa; force:boolean);
_var i:integer;
_(
 _if _not force _then _(
  poolStart:=poolStart; code(=ЗЧ,УИ5=);
  i:=9-poolIndex; code(УИ4=);
  poolValue.i:=poolValue.i;
  code(ЗЧ1=,pfnd:СЧ1=5СР,У0pdone=5СА1,4КЦpfnd=,)
 _);
 poolIndex:=poolIndex+1;
 _if poolIndex>=3120 _then Diagnostic(23);
 literalPool[poolIndex]:=poolValue.i;
 mapia(poolIndex,offset);
 exit; code(pdone:ВИ5=);
 i:= ; i:=i-poolBase; mapia(i,offset)
_);

(* 02463: historical scanner; helpers precede its body physically. *)
_proced ScanToken;
_label 2465,2532,2657,3123,3143,3221;
_const MaxNumber=1000000000000;
_var nameChars:_array[0..12] _of char; nameIndex,loopIndex:integer;
 scanId,scanNext:idptr; building:boolean; numeric,scale:real;
 packedValue:alfa; textChars:_array[1..20] _of char;
 stringLength,precision:integer;

(* 02066: consume the second character of a digraph when it matches. *)
_proced Digraph(second,replacement:char);
_var first:char;
_(
 first:=input@; get(input);
 _if input@=second _then _( diagChar:=replacement; get(input) _)
 _else diagChar:=first
_);

(* 02102: original recovery paths follow the non-returning diagnostic. *)
_proced ScanError(n:integer);
_(
 Diagnostic(n);
 _if n<5 _then _case n _of
  0: ;
  1: builtinNo:=1;
  2,3,4: _(
   _while input@<>'''' _do get(input);
   get(input); _goto 2657
  _)
 _end
_);

(* 02131: three octal digits, first digit limited to 0..3. *)
_proced OctalEscape;
_(
 get(input);
 _if input@>'3' _then ScanError(2);
 builtinNo:=ord(input@);
 _for loopIndex:=0 _to 1 _do _(
  get(input);
  _if input@>'7' _then _( ScanError(3); exit _);
  builtinNo:=builtinNo*8+ord(input@)
 _);
 input@:=chr(builtinNo)
_);

(* 02156: consume the whole name; retain the first six GOST characters. *)
_proced ReadIdentifier;
_(
 nameIndex:=6; building:=true; diagWord:='000000';
 unpck(nameChars[0],diagWord);
 _repeat
  _if building _then _(
   nameChars[nameIndex]:=input@;
   _if nameIndex=11 _then building:=false;
   nameIndex:=nameIndex+1
  _);
  get(input)
 _until _not (input@ _in letter) _and (input@>'9');
 pck(nameChars[nameIndex-6],diagWord)
_);
(* 02276: option comments own the three level-5 helper procedures. *)
_proced OptionComment;
_var bad:boolean;

(* 02206: nested comments, with a line counter reset at every line end. *)
_proced SkipComment;
_label 2210;
_var previous:char;
_(
 2210:
 previous:=input@; get(input);
 _select
  (previous='*') _and (input@=')'): _( get(input); exit _);
  (previous='(') _and (input@='*'): _( get(input); SkipComment _);
  input@=lineEnd: _( line:=line+1; s00027:=0 _)
 _end;
 _goto 2210
_);

(* 02233: decimal option value with a caller-supplied upper bound. *)
_proced ReadBound(_var result:integer; limit:integer);
_(
 get(input); result:=0; bad:=true;
 _if input@<='9' _then
  _while input@<='9' _do _(
   result:=result*10+ord(input@); get(input); bad:=false
  _);
 _if result>limit _then bad:=true
_);

(* 02260: a sign changes the flag and accepts this option. *)
_proced ReadSwitch(_var enabled:boolean);
_(
 get(input);
 _if (input@='-') _or (input@='+') _then _(
  enabled:=input@='+'; get(input); bad:=false
 _)
_);
_(
 get(input);
 _if input@='=' _then _repeat
  get(input); bad:=true;
  _case input@ _of
   'N': _( get(input); lineEnd:=input@; get(input); bad:=input@<>',' _);
   'У': ReadSwitch(s00114);
   'Е': ReadSwitch(s00104);
   'Г': ReadSwitch(s00115);
   'F','V','G','S': ReadSwitch(s00014);
   'L': ReadSwitch(s00111);
   'Р': ReadSwitch(s00105);
   'Т': ReadSwitch(s00106);
   'Д': ReadSwitch(s00111);
   'О','Ч','Л': ReadSwitch(s00111);
   'А': ReadBound(s00072,1);
   'С': ReadSwitch(s00076);
   'R': ReadSwitch(s00107);
   'М': ReadSwitch(s00110);
   'Х': ReadSwitch(s00116);
   'В': ReadBound(s00012,4);
   'К': ReadBound(reserv,25);
   'D': ReadSwitch(s00014);
   'I': ReadSwitch(s00113)
  _end;
  _if bad _then ScanError(13)
 _until input@<>',';
 SkipComment; _goto 2465
_);

_(
 2465:
 _while (input@=Space) _or (input@>chr(128)) _do get(input);
 _if input@=lineEnd _then _(
  line:=line+1; s00027:=0; get(input); _goto 2465
 _);
 s00027:=s00027+1;
 _if input@ _in letter _then _(
  diagToken:=ИД; ReadIdentifier; knownIdent:=false;
  (*=c-*)mapai(diagWord ∧ '000177',nameBucket);(*=c+*)
  _case lookupMode _of
   0: _(
    diagIdent:=namehash[nameBucket];
    _while diagIdent<>_nil _do _(
     _if diagIdent@.level=codeLevel _then _(
      _if diagIdent@.name<>diagWord _then diagIdent:=diagIdent@.next
      _else _( knownIdent:=true; _goto 2657 _)
     _) _else _goto 2657
    _)
   _);
   1: 2532: _(
    diagIdent:=namehash[nameBucket];
    _while diagIdent<>_nil _do _(
     _if diagIdent@.name<>diagWord _then diagIdent:=diagIdent@.next
     _else _goto 2657
    _)
   _);
   2: _(
    _if withDepth=0 _then _goto 2532;
    diagIdent:=oldhash[nameBucket]; withIndex:=-1;
    _while diagIdent<>_nil _do _(
     _if diagIdent@.name=diagWord _then _(
      scanId:=diagIdent@.owner;
      _for nameIndex:=withDepth _downto 1 _do
       _if withTable[nameIndex].typ=scanId _then _(
        diagToken:=CF;
        _if nameIndex>withIndex _then _( withIndex:=nameIndex; scanNext:=diagIdent _);
        nameIndex:=0
       _)
     _);
     diagIdent:=diagIdent@.next
    _);
    _if withIndex=-1 _then _goto 2532 _else diagIdent:=scanNext
   _);
   3: _(
    diagIdent:=oldhash[nameBucket]; diagToken:=CF;
    _while diagIdent<>_nil _do _(
     _if diagIdent@.name<>diagWord _then diagIdent:=diagIdent@.next
     _else _if recordType=diagIdent@.owner _then _goto 2657
     _else diagIdent:=diagIdent@.next
    _)
   _)
  _end;
  _goto 2657
 _);
 _if input@='_' _then _(
  get(input); diagToken:=ПС;
  _if _not (input@ _in letter) _then _(
   _if (input@=')') _or (input@='(') _then _(
    _if input@='(' _then diagWord:=KWBegin _else diagWord:=KWEnd;
    get(input)
   _) _else _( diagToken:=ОГ; exit _)
  _) _else ReadIdentifier;
  2657: lookupMode:=1; diagChar:=chr(254); exit
 _);
 _if input@<='9' _then _(
  diagToken:=ЦЕ; nameIndex:=0;
  _repeat
   nameIndex:=nameIndex+1;
   _if nameIndex<=17 _then textChars[nameIndex]:=input@
   _else _( ScanError(0); nameIndex:=1 _);
   get(input)
  _until input@>'9';
  builtinNo:=0;
  _if (input@='В') _or (input@='С') _or (input@='Т') _then _(
   _for loopIndex:=1 _to nameIndex _do
    _if textChars[loopIndex]>'7' _then ScanError(5);
   _if input@='Т' _then _(
    _for loopIndex:=nameIndex _downto 1 _do _(
     builtinNo:=builtinNo; code(СД/3/=17ЗЧ,);
     builtinNo:=ord(textChars[loopIndex]); code(СД/3/=МР,17СР=);
     builtinNo:= ;
    _)
   _) _else _(
    _for loopIndex:=1 _to nameIndex _do _(
     builtinNo:=builtinNo; code(СД/-3/=17ЗЧ,);
     builtinNo:=ord(textChars[loopIndex]); code(17СР=);
     builtinNo:= ;
    _)
   _);
   get(input)
  _) _else _(
   (*=m-*)
   _for loopIndex:=1 _to nameIndex _do
    _if builtinNo<=MaxNumber _then builtinNo:=10*builtinNo+ord(textChars[loopIndex])
    _else _( ScanError(7); builtinNo:=0 _);
   precision:=0;
   _if input@='.' _then _(
    get(input);
    _if input@='.' _then _( input@:=':'; _goto 2657 _);
    realValue:=builtinNo; diagToken:=RE;
    (*=m-*)
    _if input@>'9' _then ScanError(8) _else _repeat
     realValue:=10.0*realValue+ord(input@); precision:=precision-1;
     get(input)
    _until input@>'9'
   _);
   _if input@='Е' _then _(
    _if precision=0 _then _( realValue:=builtinNo; diagToken:=RE _);
    building:=false; get(input);
    _case input@ _of
     '+': get(input);
     '-': _( building:=true; get(input) _)
    _end;
    stringLength:=0;
    _if input@>'9' _then ScanError(9) _else _repeat
     stringLength:=10*stringLength+ord(input@); get(input)
    _until input@>'9';
    _if building _then precision:=precision-stringLength
    _else precision:=precision+stringLength
   _);
   _if precision<>0 _then _(
    scale:=1.0; building:=precision<0; precision:=abs(precision); numeric:=10.0;
    _if precision>18 _then _( precision:=1; ScanError(10) _);
    _repeat
     _if odd(precision) _then scale:=scale*numeric;
     precision:=trunc(precision/2);
     _if precision<>0 _then numeric:=numeric*numeric
    _until precision=0;
    _if building _then realValue:=realValue/scale _else realValue:=realValue*scale
   _)
  _);
  (*=m+*) _goto 2657
 _);
 _if input@='''' _then _(
  _if _not longStrings _then _(
   diagWord:='000000'; unpck(nameChars[0],diagWord); nameIndex:=6;
   3123: get(input);
   _if input@='≡125' _then OctalEscape
   _else _if input@='''' _then _( get(input); _if input@<>'''' _then _goto 3143 _);
   _if nameIndex=12 _then _( ScanError(4); _goto 3143 _);
   nameChars[nameIndex]:=input@; nameIndex:=nameIndex+1; _goto 3123;
   3143: pck(nameChars[nameIndex-6],diagWord);
   _if nameIndex>7 _then diagToken:=AL _else diagToken:=СН;
   _goto 2657
  _) _else _(
   diagToken:=AL; textLength:=0; knownIdent:=false;
   _for loopIndex:=0 _to 250 _do _(
    packedValue:='000000'; unpck(nameChars[0],packedValue);
    _for nameIndex:=0 _to 5 _do _(
     get(input);
     _if input@='≡125' _then OctalEscape
     _else _if input@='''' _then _(
      get(input);
      _if input@<>'''' _then _(
       _if nameIndex<>0 _then _( knownIdent:=true; _goto 3221 _);
       _goto 2657
      _)
     _) _else _(
      _if input@=lineEnd _then line:=line+1;
      _if s00072=0 _then mapгa(input@,input@)
     _);
     nameChars[nameIndex]:=input@; textLength:=textLength+1
    _);
    3221: pck(nameChars[0],packedValue); poolValue.a:=packedValue;
    PutLiteral(packedValue,true);
    _if longStrings _then _( longStrings:=false; diagWord:=packedValue _);
    _if knownIdent _then _goto 2657
   _);
   ScanError(1)
  _)
 _);
 diagToken:=ОГ;
 _if input@ _in ['.','(','<','>',':'] _then _case input@ _of
  ':': Digraph('=',chr(128));
  '.': Digraph('.',':');
  '>': Digraph('=','⩾');
  '<': _(
   Digraph('=','⩽');
   _if (diagChar='<') _and (input@='>') _then _( get(input); diagChar:='≠' _)
  _);
  '(': _( get(input); _if input@='*' _then OptionComment _else diagChar:='(' _)
 _end _else _(
  _if input@='≡172' _then _(
   rewrite(output); writeln('ВСТРЕТИЛСЯ СИМВОЛ КОНЦА ПРОГРАММЫ (≡172)');
   code(ПБ76002=)
  _) _else diagChar:=input@;
  get(input)
 _)
_);

(* 03316: decode an ALFA pool index; an all-zero word denotes no literal. *)
_function PoolWord(offset:alfa):integer;
_var index:integer;
_(
 _if offset='000000' _then PoolWord:=0
 _else _( mapai(offset,index); PoolWord:=literalPool[index] _)
_);

(* 03346: structural compatibility; recursive pointer pairs break cycles. *)
_function TypeCheck(t1,t2:idptr):boolean;
_label 3356;
_var pair:@comparelink; first,second:idptr;
(* 03327: retain the compared pair while descending through pointers. *)
_proced Chain;
_(
 new(pair); pair@ := [pairHead,first,second]; pairHead:=pair;
 TypeCheck:=TypeCheck(first,second)
_);
_(
 code(=ЗЧ,);
 _if _not s00076 _or (t1=t2) _then _(
  3356: TypeCheck:=true; exit
 _) _else
 _if t1@.form=t2@.form _then _case t1@.form _of
 kSc:
  _if (t1=alfaType) _and (t2=charType) _or
      (t1=charType) _and (t2=alfaType) _then _goto 3356;
 kRng:
  _if (t1@.lower=t2@.lower) _and (t1@.upper=t2@.upper) _and
      TypeCheck(t1@.data,t2@.data) _then _goto 3356;
 kPtr:
  _if (t1=nilType) _or (t2=nilType) _then _goto 3356 _else _(
   first:=t1@.data; second:=t2@.data;
   _if pairHead<>_nil _then _(
    pair:=pairHead;
    _while pair<>_nil _do _(
     _if (pair@.first=first) _and (pair@.second=second) _or
         (pair@.second=first) _and (pair@.first=second)
     _then _goto 3356 _else pair:=pair@.next
    _);
    Chain
   _) _else _( setup(t1); Chain; pairHead:=_nil; rollup(t1) _);
   exit
  _);
 kSet: _goto 3356;
 kArr:
  _if TypeCheck(t1@.data,t2@.data) _and
      TypeCheck(t1@.rangeType,t2@.rangeType) _then _goto 3356;
 kAlias: Diagnostic(2);
 kFile:
  _if TypeCheck(t1@.data,t2@.data) _and (t1@.packing=t2@.packing)
  _then _goto 3356;
 kRec: _(_)
 _end;
 TypeCheck:=false
_);

(* 03520: read a scalar literal or named constant, with an optional sign. *)
_proced ScalarConstant(_var result:idptr; _var offset:alfa; signed:boolean);
_label 3531,3567,3570,3601,3666;
_var expected:idptr; sign:char;
_(
 code(=ЗЧ,);
 expected:=result;
 _case diagToken _of
 ПС: _(
  _if diagWord<>KWNil _then _goto 3666;
  3531: result:=nilType; offset:=NilOffset
 _);
 ИД: _(
  _if diagIdent=_nil _then _goto 3666;
  _if (diagIdent@.kind<>CONST) _or (diagIdent@.data<>_nil)
  _then _goto 3666;
  _if diagIdent@.consttype@.form<>kSc _then
   _if diagIdent@.consttype=nilType _then _goto 3531 _else _goto 3666;
  result:=diagIdent@.consttype; offset:=diagIdent@.constvalue;
  poolValue.i:=PoolWord(offset)
 _);
 CF: _goto 3666;
 AL: _(
  result:=alfaType;
  3567: poolValue.a:=diagWord;
  3570: PutLiteral(offset,false)
 _);
 ЦЕ: _( result:=intType; poolValue.i:=builtinNo; _goto 3570 _);
 RE: _(
  result:=realType;
  3601: poolValue.r:=realValue; _goto 3570
 _);
 СН: _( result:=charType; _goto 3567 _);
 ОГ: _(
  _if _not signed _then _goto 3666;
  _if (diagChar='+') _or (diagChar='-') _then sign:=diagChar
  _else _goto 3666;
  ScanToken; ScalarConstant(result,offset,false);
  _if result=_nil _then _goto 3666;
  _if sign='-' _then
   _if result=intType _then _( poolValue.i:=-builtinNo; _goto 3570 _)
   _else _if result=realType _then _( realValue:=-realValue; _goto 3601 _)
   _else _goto 3666
 _)
 _end;
 _if (expected=_nil) _or TypeCheck(expected,result) _then exit;
 3666: result:=_nil; code(=ЗЧ,)
_);

(* 04354: declarations of scalar, structured and named types. *)
_proced ParseType(limit:integer; tname:alfa; _var result:idptr; bucket:integer);
_label 4511,4513,4515,4535,5041,5147;
_const FileBaseSize=22; Packed='PACKED';
_var baseType,curType,node:idptr; isPacked:boolean;
 offset:alfa; value:word; count,span:integer;
(* 03671: zero denotes a type without the supported packed representation. *)
_function BitWidth(t:idptr):integer;
_label 3675;
_var bits:integer;
_(
 _if t@.size<>1 _then 3675: BitWidth:=0
 _else _if t@.form=kRng _then _(
  bits:=t@.lower; _if bits<0 _then _goto 3675;
  bits:=t@.upper; _if bits>=48 _then _goto 3675;
  code(4СЧ5=ВН,4ЗЧ5=,);
  BitWidth:=49-bits
 _) _else _if t@.form=kPtr _then BitWidth:=15
 _else _if t@.form=kSc _then _(
  _if t=boolType _then BitWidth:=1
  _else _if t=charType _then BitWidth:=8 _else _goto 3675
 _) _else _goto 3675
_);

(* 03735: fixed fields and recursive CASE variants, including selector lists. *)
_proced Fields(_var size:integer; rec,head:idptr);
_label 3763,4054,4276;
_var last,item,fieldType,choice,tag,branch,found,groupHead:idptr;
 currentSize,savedBucket:integer; selector,tagName:alfa; first,colon:boolean;
_(
 first:=true; last:=_nil;
 _repeat
  groupHead:=_nil; lookupMode:=3; ScanToken;
  _if diagToken=CF _then _goto 3763 _else _goto 4054;
  _repeat
   lookupMode:=3; ScanToken;
   _if diagToken<>CF _then Diagnostic(0);
   3763:
   _if diagIdent<>_nil _then Diagnostic(1);
   new(item;fieldOffset);
   item@ := [diagWord,codeLevel,oldhash[nameBucket],head,FIELD,_nil, ,rec];
   oldhash[nameBucket]:=item;
   _if first _then _(
    _if head=_nil _then rec@.data:=item _else head@.next:=item;
    first:=false
   _);
   _if groupHead=_nil _then groupHead:=item _else last@.fieldChain:=item;
   last:=item; ScanToken
  _until diagChar<>',';
  _if diagChar<>':' _then Diagnostic(2);
  ParseType(1,'000000',fieldType,0);
  currentSize:=fieldType@.size; recordType:=rec;
  _while groupHead<>_nil _do _(
   groupHead@.fieldType:=fieldType; groupHead@.fieldOffset:=size;
   size:=size+currentSize; groupHead:=groupHead@.fieldChain
  _)
 _until diagChar<>';';
 exit;
 4054:
 _if (diagToken<>ПС) _or (diagWord<>KWCase) _then Diagnostic(3);
 lookupMode:=3; ScanToken;
 _if diagToken<>CF _then Diagnostic(4);
 tagName:=diagWord; savedBucket:=nameBucket; found:=diagIdent;
 new(item;fieldOffset);
 item@ := [diagWord,codeLevel, ,head,TAGF,_nil, ,rec,size];
 _if first _then _(
  first:=false;
  _if head=_nil _then rec@.data:=item _else head@.next:=item
 _) _else item@.fieldChain:=item;
 ScanToken;
 _if diagChar=':' _then _(
  _if found<>_nil _then Diagnostic(11);
  item@.next:=oldhash[savedBucket]; oldhash[savedBucket]:=item;
  ParseType(2,'000000',fieldType,0); savedBucket:=1
 _) _else _(
  found:=namehash[savedBucket]; savedBucket:=0;
  _while found<>_nil _do _(
   _if found@.name<>tagName _then found:=found@.next _else _(
    _if found@.kind<>TYPE _then Diagnostic(12) _else _(
     _if found@.form=kAlias _then found:=found@.data;
     _if found@.form<>kSc _then Diagnostic(13)
    _);
    fieldType:=found; found:=_nil; tagName:='000000'
   _)
  _);
  _if tagName<>'000000' _then _( Diagnostic(14); fieldType:=nilType _)
 _);
 item@.fieldType:=fieldType; size:=size+savedBucket;
 _if (diagToken<>ПС) _or (diagWord<>KWOf) _then Diagnostic(6);
 last:=_nil; savedBucket:=size;
 _repeat
  branch:=_nil; currentSize:=savedBucket; ScanToken;
  _repeat
   choice:=fieldType; ScalarConstant(choice,selector,false);
   _if choice=_nil _then Diagnostic(-1);
   new(tag;variantSize);
   (*=c-*)tag@ := [0,selector,_nil, ,TAGV,_nil];(*=c+*)
   _if branch=_nil _then tag@.data:=item _else tag@.data:=branch;
   branch:=tag; choice:=last;
   _while choice<>_nil _do _(
    (*=c-*)tagName:=choice@.level;(*=c+*)
    _if selector>tagName _then _(
     tag@.fieldChain:=choice; _goto 4276
    _) _else _if selector<tagName _then _(
     found:=choice; choice:=choice@.fieldChain
    _) _else Diagnostic(8)
   _);
   4276:
   _if last=choice _then last:=tag _else found@.fieldChain:=tag;
   ScanToken;
   _if (diagChar<>',') _and (diagChar<>':') _then Diagnostic(7);
   colon:=diagChar=':'; ScanToken
  _until colon;
  _if diagChar<>'(' _then Diagnostic(10);
  Fields(currentSize,rec,branch);
  _if diagChar<>')' _then Diagnostic(9);
  _if currentSize>size _then size:=currentSize;
  _while branch<>item _do _(
   branch@.variantSize:=currentSize; branch:=branch@.data
  _);
  ScanToken
 _until diagChar<>';';
 item@.fieldChain:=last
_);

_(
 ScanToken; isPacked:=false;
 _case diagToken _of
 ОГ: _(
  _if diagChar='(' _then _(
   baseType:=_nil; new(curType;upper);
   curType@ := [tname, , , ,TYPE,1,kSc];
   _if tname<>'000000' _then _(
    curType@ := [,codeLevel,namehash[bucket]]; namehash[bucket]:=curType
   _);
   count:=0; result:=curType;
   _repeat
    lookupMode:=0; ScanToken;
    _if diagToken<>ИД _then Diagnostic(1);
    _if knownIdent _then Diagnostic(2);
    new(node;constNext); poolValue.i:=count; PutLiteral(offset,false);
    node@ := [diagWord,codeLevel,namehash[nameBucket],_nil,CONST,curType,offset];
    namehash[nameBucket]:=node; count:=count+1;
    _if baseType=_nil _then curType@.data:=node _else baseType@.constNext:=node;
    baseType:=node; ScanToken
   _until diagChar<>',';
   _if diagChar<>')' _then Diagnostic(4);
   node@.constNext:=_nil; curType@.lower:=count; curType@.upper:=0
  _) _else _(
   _if diagChar='↑' _then _(
    ParseType(1,'000000',baseType,0); new(result;form);
    result@ := [tname,codeLevel, ,baseType,TYPE,1,kPtr]; _goto 5147
   _); _goto 4535
  _);
  4511: ScanToken; exit;
  4513: ScanToken;
  4515: result:=curType;
  _if tname='000000' _then _( exit; _goto 4535 _);
  new(node;form);
  node@ := [tname,codeLevel,namehash[bucket],curType,TYPE, ,kAlias];
  namehash[bucket]:=node; exit;
  4535:
  baseType:=_nil; ScalarConstant(baseType,offset,true);
  _if baseType=_nil _then Diagnostic(13);
  count:=poolValue.i; ScanToken;
  _if diagChar<>':' _then Diagnostic(14);
  ScanToken; ScalarConstant(baseType,value.a,true);
  _if baseType=_nil _then Diagnostic(15);
  span:=poolValue.i;
  _if (baseType<>intType) _and (baseType<>charType) _and (baseType@.data=_nil)
      _or (baseType@.form<>kSc) _then Diagnostic(16);
  new(curType;upper);
  curType@ := [0,codeLevel,_nil,baseType,TYPE,1,kRng,count,span];
  _goto 4513
 _);
 ИД: _(
  _if diagIdent=_nil _then _(
   _if allowForward _and (tname='000000') _then _(
    new(result;form); pendingTypes:=pendingTypes+1;
    result@ := [diagWord,codeLevel,namehash[nameBucket],_nil,TYPE,1,kPtr];
    namehash[nameBucket]:=result; _goto 4511
   _) _else Diagnostic(19)
  _);
  _if diagIdent@.kind<>TYPE _then _goto 4535;
  _if diagIdent@.form=kAlias _then diagIdent:=diagIdent@.data;
  _if (limit=1) _and (diagIdent@.form=kFile) _then Diagnostic(20);
  _if (limit=2) _and (diagIdent@.form<>kSc) _and (diagIdent@.form<>kRng)
  _then Diagnostic(21);
  curType:=diagIdent; _goto 4513
 _);
 ПС: _(
  _if limit=2 _then Diagnostic(22);
  _if diagWord=Packed _then _(
   isPacked:=true; ScanToken; _if diagToken<>ПС _then Diagnostic(40)
  _);
  _if diagWord=KWRecord _then _(
   new(baseType;form); count:=0;
   baseType@ := [tname, , , ,TYPE, ,kRec];
   baseType@ := [,codeLevel,namehash[bucket]]; namehash[bucket]:=baseType;
   recordType:=baseType; Fields(count,baseType,_nil);
   _if (diagToken<>ПС) _or (diagWord<>KWEnd) _then Diagnostic(23);
   baseType@.size:=count; result:=baseType; _goto 4511
  _);
  _if diagWord=KWArray _then _(
   ScanToken; _if diagChar<>'[' _then Diagnostic(24);
   curType:=_nil;
   _repeat
    ParseType(2,'000000',baseType,0); new(node;stride);
    node@ := [tname, ,curType, ,TYPE, ,kArr,baseType];
    _if curType=_nil _then _(
     result:=node;
     _if tname<>'000000' _then _(
      node@ := [,codeLevel,namehash[bucket]]; namehash[bucket]:=node
     _)
    _) _else curType@.data:=node;
    curType:=node
   _until diagChar<>',';
   _if diagChar<>']' _then Diagnostic(25);
   ScanToken;
   _if (diagToken<>ПС) _or (diagWord<>KWOf) _then Diagnostic(26);
   ParseType(1,'000000',baseType,0); node@.data:=baseType; count:=baseType@.size;
   _goto 5041;
   _repeat
    curType:=curType@.next;
    5041: node:=curType@.rangeType;
    _if node@.form=kRng _then span:=node@.upper-node@.lower+1
    _else Diagnostic(28);
    _if count=1 _then curType@.stride:='000000' _else _(
     value.i:=count; AddExponent(value.i,poolValue.i); PutLiteral(value.a,false);
     curType@.stride:=value.a
    _);
    count:=count*span; curType@.size:=count
   _until curType=result;
   exit
  _);
  _if diagWord=KWFile _then _(
   ScanToken;
   _if (diagToken<>ПС) _or (diagWord<>KWOf) _then Diagnostic(29);
   ParseType(1,'000000',baseType,0); span:=FileBaseSize;
   _if isPacked _then count:=BitWidth(baseType) _else count:=0;
   _if (count<>0) _and (count<=24) _then span:=trunc(48/count)+span _else count:=0;
   new(result;packing);
   result@ := [0, , ,baseType,TYPE,span,kFile,count];
   5147:
   _if tname<>'000000' _then _(
    result@ := [tname,codeLevel,namehash[bucket]]; namehash[bucket]:=result
   _);
   exit
  _);
  _if diagWord=KWSet _then _(
   ScanToken; _if diagWord<>KWOf _then Diagnostic(-1);
   ParseType(2,'000000',baseType,0);
   _if ((baseType@.form<>kRng) _or (baseType@.lower<0) _or (baseType@.upper>47))
    _and (((baseType@.level<>0) _or _not TypeCheck(baseType,boolType))
     _and ((baseType@.level=0) _or (baseType@.lower>47)) _or (baseType@.form<>kSc))
   _then Diagnostic(0);
   curType:=setType; _goto 4515
  _);
  Diagnostic(33)
 _);
 ЦЕ,AL,RE,СН: _goto 4535;
 CF: Diagnostic(3)
 _end;
 Diagnostic(4)
_);

(* 05245: grouped value, VAR, function and procedure parameters. *)
_proced FormalParams(_var owner:idptr; _var cursor:alfa);
_label 5305;
_var node,last,group:idptr; words:integer;
 mode:(byValue,byRef,byFun,byProc); done:boolean; form:typeform;
_(
 owner@.params:=_nil;
 _repeat
  group:=_nil; lookupMode:=0; mode:=byValue; ScanToken;
  _if diagToken=ИД _then _goto 5305;
  _if diagToken<>ПС _then Diagnostic(0);
  _if diagWord=KWVar _then mode:=byRef
  _else _if diagWord=KWFunction _then mode:=byFun
  _else _if diagWord<>KWProcedure _then Diagnostic(1) _else mode:=byProc;
  _repeat
   lookupMode:=0; ScanToken;
   5305:
   owner@.nargs:=owner@.nargs+1;
   _if (diagToken<>ИД) _or knownIdent _then Diagnostic(2);
   _case mode _of
    byValue: _( new(node;constNext); node@.kind:=CONST _);
    byRef: _( new(node;address); node@.kind:=VAR _);
    byFun,byProc: _( new(node;peakSize); node@.kind:=PROC _)
   _end;
   node@ := [diagWord,codeLevel,namehash[nameBucket]];
   namehash[nameBucket]:=node;
   _if owner@.params=_nil _then owner@.params:=node _else last@.data:=node;
   last:=node;
   _if group=_nil _then group:=node;
   ScanToken
  _until diagChar<>',';
  words:=1;
  _if mode=byProc _then node:=_nil _else _(
   _if diagChar<>':' _then Diagnostic(3);
   ParseType(0,'000000',node,0); form:=node@.form;
   _if mode=byValue _then words:=node@.size;
   _if (mode=byValue) _and (words<>1) _or (mode=byFun) _and (form>kSet)
   _then Diagnostic(4)
  _);
  _repeat
   _if mode<byFun _then _(
    group@.consttype:=node; group@.constvalue:=cursor
   _) _else _(
    group@.resulttype:=node; group@.entry:=cursor
   _);
   AddAddress(cursor,words); done:=last=group; group:=group@.data
  _until done
 _until diagChar<>';';
 _if diagChar<>')' _then Diagnostic(5);
 ScanToken; last@.data:=owner
_);

(* 05465: PROGRAM header, recursive block analysis and final storage report. *)
_proced ProgramHeader;
_var programBlock:idptr; frame:alfa;
(* 05454: consume the PROGRAM file list through its closing parenthesis. *)
_proced SkipParameters;
_(
 _while diagChar<>')' _do ScanToken;
 ScanToken
_);
_(
 ScanToken; new(programBlock;peakSize);
 _if _not s00076 _then _(
  _for loopIndex:=0 _to 47 _do literalPool[9+1+loopIndex]:=loopIndex;
  poolIndex:=9+loopIndex
 _);
 _if diagWord<>'PROGRA' _then Diagnostic(0) _else _(
  ScanToken;
  _if diagToken<>ИД _then Diagnostic(1) _else _(
   write('ПРОГРАММА ':29); PrintField(diagWord); writeln;
   programBlock@.name:=diagWord; programBlock@.kind:=PROC;
   programBlock@.ownSize:=0; programBlock@.proc15:=false;
   programBlock@.proc16:=0; programBlock@.peakSize:=0;
   _if hascod _then _(
    get(F);
    (*=c-*)
    _if TrimName(diagWord)<>F@ _then _(
     writeln('НЕ ТЕ КОДЫ !'); _goto 7560
    _);
    _for loopIndex:=1 _to 4 _do get(F);
    diagWord:=F@; codeend:= ;
    (*=c+*)
    _for loopIndex:=1 _to 6 _do get(F)
   _);
   ScanToken;
   _if diagChar='(' _then SkipParameters;
   _if diagChar<>';' _then Diagnostic(2) _else ScanToken
  _)
 _);
 (*=c-*)programBlock@.environment:=8228;(*=c+*)
 programBlock@.entry:='0000СА'; programBlock@.params:=_nil; programBlock@.nargs:=0;
 frame:='000012'; analyze(frame,programBlock);
 _if diagChar<>'.' _then Diagnostic(6);
 write('ПРОГР '); PrintField(programBlock@.name);
 mapia(programBlock@.peakSize-programBlock@.ownSize,procedureText);
 _if s00015 _or s00016 _then _(
  programBlock@.peakSize:=programBlock@.peakSize+3;
  programBlock@.ownSize:=programBlock@.ownSize+3
 _);
 _if s00015 _then _(
  programBlock@.peakSize:=programBlock@.peakSize+128;
  programBlock@.ownSize:=programBlock@.ownSize+128
 _);
 mapia(programBlock@.ownSize,globalText); heapReserve:=0;
 _if _not s00017 _then mapai(newText,heapReserve);
 mapia(programBlock@.peakSize+heapReserve,sumText);
 mapia(programBlock@.peakSize+codeend+heapReserve,sumCodeText);
 mapia(codeend,codeText);
 write('  ГЛОБ.ПЕРЕМ='); PrintField(globalText);
 write('  ПРОЦЕДУРЫ='); PrintField(procedureText);
 _if hascod _then _( write('КОД=':11); PrintField(codeText) _);
 writeln;
 _if _not s00017 _then _(
  write('NEW=':25); PrintField(newText); write('СУММА=':12); PrintField(sumText)
 _) _else _( write('СУММА=':42); PrintField(sumText) _);
 _if hascod _then _( write(Space:11); PrintField(sumCodeText) _);
 writeln
_);

(* 05725: append an ALFA callee once within the current block's slice. *)
_proced RememberCall(name:alfa);
_var index:integer;
_(
 _for index:=listBegin _to calls.top-1 _do
  _if calls.names[index]=name _then exit;
 calls.names[calls.top]:=name; calls.top:=calls.top+1
_);

(* 05743: recursive statement scan and simultaneous call-frame depth. *)
_proced ScanBody;
_label 5745,5751,6103;
_var own,peak:integer; size:alfa;
_(
 _while true _do _(
 5745: longStrings:=true; lookupMode:=2; ScanToken;
 5751:
 _if diagToken=ПС _then _(
  _if diagWord=KWEnd _then exit;
  _if (diagWord=KWBegin) _or (diagWord=KWSelect) _or (diagWord=KWCase)
  _then ScanBody
 _) _else _if diagToken=ИД _then
  _if diagIdent@.kind=PROC _then _(
   _if diagIdent@.level<>0 _then _(
    _if paramBlock@.name=diagWord _then _(
     lookupMode:=2; ScanToken;
     _if diagChar<>chr(128) _then _(
      _if _not optI _then _(
       write('РЕКУРСИЯ - ':15); PrintField(paramBlock@.name);
       writeln(' СТР. = ',line:0)
      _);
      _if paramBlock@.level=diagIdent@.level _then
       paramBlock@.proc16:=paramBlock@.peakSize
      _else Diagnostic(59);
      RememberCall(paramBlock@.name); lookupMode:=0; _goto 5751
     _)
    _) _else _(
     own:=paramBlock@.ownSize; RememberCall(diagWord);
     _if diagIdent@.proc13 _and _not optI _then _(
      write('ПРОЦ. ':10); PrintField(diagWord);
      writeln(' ИМЕЕТ ТОЛЬКО FORWARD  СТР. = ',line:0)
     _);
     _if paramBlock@.proc15 _then _(
      peak:=diagIdent@.peakSize+own;
      _if peak>paramBlock@.peakSize _then paramBlock@.peakSize:=peak;
      _if codeLevel=1 _then _(
       mapia(diagIdent@.peakSize,size);
       _if optT _and _not optI _then _(
        write('ПРОЦЕДУРА  '); PrintField(diagIdent@.name);
        write('МАХ=':8); PrintField(size); writeln
       _)
      _)
     _) _else Diagnostic(500)
    _)
   _);
   6103:
   _if diagWord='00CODE' _then _( SkipThrough(')'); _goto 5745 _);
   _if diagWord='000NEW' _then newcnt:=newcnt+1
  _);
 _)
_);

(* 06114: discard hash-chain heads allocated in the current scope. *)
_proced PruneHash(_var table:hashtable);
_(
 _for loopIndex:=0 _to 127 _do _(
  t:=table[loopIndex];
  _while (t<>_nil) _and (t>=scopeMark) _do t:=t@.next;
  table[loopIndex]:=t
 _)
_);

(* 06137: source block analyzer body. *)
(*=c-*)
_(
 (* 06144: resident output mode; savedOutput occupies M2:023. *)
 code(СЧ76013=2ЗЧ23,);
 (*=c-*)wasTerm:=savedOutput ∧ 1 > 0;(*=c+*)
 _if diagWord='00000 ' _then _(
  InitHistorical; ProgramHeader; exit
 _);
 (* 06156: block state retained across nested declarations. *)
 frameNext:=paramName; savedCheck:=s00076;
 allowForward:=true; pendingTypes:=0;
 l00064:=0; l00027:=0; l00056:=_nil;
 savedForward:=forwardType; s00044:=1; savedLabels:=s07076;
 _if diagToken<>ПС _then Diagnostic(1);
 (* 06173: declared numeric labels are linked in reverse declaration order. *)
 _if diagWord=KWLabel _then _(
  _repeat
   ScanToken;
   _if diagToken<>ЦЕ _then Diagnostic(24) _else _(
    (* NEW of six words via the historical AL vector; M2:054 holds the pointer. *)
    code(2ИА54=14ПА,12ПА6=16ПВ74025,);
    currentLabel@.value:=builtinNo;
    currentLabel@.level:=codeLevel;
    currentLabel@.state3:=0; currentLabel@.state1:=0; currentLabel@.state5:=0;
    (*=c-*)currentLabel@.next:=s07076; s07076:=currentLabel;(*=c+*)
    ScanToken
   _);
   _if (diagChar<>',') _and (diagChar<>';') _then Diagnostic(25)
  _until diagChar<>',';
  _if diagChar=';' _then ScanToken;
  _if diagToken<>ПС _then Diagnostic(1)
 _);
 (*=c-*)
 (* 06232..06417: named constants and one optional binary operation. *)
 _if diagWord=KWConst _then _(
  lookupMode:=0; ScanToken;
  _if diagToken<>ИД _then Diagnostic(2);
  _while diagToken=ИД _do _(
   _if knownIdent _then Diagnostic(2);
   (* NEW(t;constNext): eight words through the historical AL vector. *)
   code(2ИА6=14ПА,12ПА10=16ПВ74025,);
   t@ := [diagWord,codeLevel,namehash[nameBucket],_nil,CONST,intType];
   namehash[nameBucket]:=t;
   ScanToken;
   _if diagChar='=' _then ScanToken _else Diagnostic(3);
   p:=_nil; ScalarConstant(p,t@.constvalue,true);
   _if p=_nil _then Diagnostic(4) _else _(
    t@.consttype:=p; ScanToken
   _);
   binaryOp:=0;
   _if diagChar='+' _then binaryOp:=1
   _else _if diagChar='-' _then binaryOp:=2
   _else _if diagChar='*' _then binaryOp:=3
   _else _if diagChar='/' _then binaryOp:=4;
   _if binaryOp>0 _then _(
    ScanToken;
    (* A temporary constant descriptor occupies M2:053. *)
    code(2ИА53=14ПА,12ПА10=16ПВ74025,);
    rightConst@ := [0,codeLevel,namehash[nameBucket],_nil,CONST,intType];
    p:=_nil; ScalarConstant(p,rightConst@.constvalue,false);
    _if p=_nil _then Diagnostic(6) _else _(
     _if (p=t@.consttype) _and (p=intType) _then _(
      leftValue:=PoolWord(t@.constvalue);
      _case binaryOp _of
       0: _goto 6411;
       1: poolValue.i:=poolValue.i+leftValue;
       2: poolValue.i:=leftValue-poolValue.i;
       3: _(
        (* Integer product through the historical CY correction vector. *)
        code(2СЧ60=ЛС74022,1АУ73=16ПВ74060,); poolValue.i:= ;
       _);
       4: _(
        _if poolValue.i=0 _then _( Diagnostic(6); _goto 6411 _);
        (* Integer-to-real conversions and truncation through ADSIS vectors. *)
        code(1СЧ73=16ПВ74024,2СМ60=16ПВ74024,17АД=16ПВ74057,);
        poolValue.i:= ;
       _)
      _end;
      PutLiteral(t@.constvalue,false); ScanToken
     _) _else 6411: Diagnostic(6)
    _)
   _);
   _if diagChar=';' _then _( lookupMode:=0; ScanToken _)
   _else Diagnostic(5)
  _)
 _);
 (* 06420: type declarations, including completion of forward pointers. *)
 _if diagWord=KWType _then _(
  lookupMode:=0; ScanToken;
  _repeat
   _if diagToken<>ИД _then Diagnostic(2);
   _if knownIdent _then _(
    _if (diagIdent@.kind=TYPE) _and (diagIdent@.form=kPtr)
        _and (diagIdent@.data=_nil) _then _(
     p:=diagIdent; ScanToken;
     _if diagChar<>'=' _then Diagnostic(3);
     ScanToken;
     _if diagChar<>'↑' _then Diagnostic(30);
     pendingTypes:=pendingTypes-1; lookupMode:=0; ScanToken;
     _if (diagToken<>ИД) _or _not knownIdent _or (diagIdent@.kind<>TYPE)
     _then Diagnostic(31);
     _if diagIdent@.form=kAlias _then diagIdent:=diagIdent@.data;
     _if diagIdent@.form>kRec _then Diagnostic(32);
     p@.data:=diagIdent; ScanToken; _goto 6504
    _) _else Diagnostic(2)
   _);
   scratchWord.a:=diagWord; loopIndex:=nameBucket; ScanToken;
   _if diagChar<>'=' _then Diagnostic(3);
   ParseType(0,scratchWord.a,p,loopIndex);
   6504:
   _if diagChar<>';' _then Diagnostic(6);
   lookupMode:=0; ScanToken;
  _until diagToken<>ИД;
  _if diagToken<>ПС _then Diagnostic(1)
 _);
 allowForward:=false;
 _if pendingTypes<>0 _then Diagnostic(33);
 (* 06521: variables share a parsed type and receive consecutive addresses. *)
 _if diagWord=KWVar _then _(
  t:=_nil;
  _repeat
  lookupMode:=0; ScanToken;
  6526:
  _if (diagToken<>ИД) _or knownIdent _then Diagnostic(2);
  new(p;address);
  p@ := [diagWord,codeLevel,namehash[nameBucket],_nil,VAR,_nil];
  namehash[nameBucket]:=p;
  _if t=_nil _then t:=p _else lastNode@.vartype:=p;
  lastNode:=p; ScanToken;
  _until diagChar<>',';
  _if diagChar<>':' _then Diagnostic(7);
  ParseType(0,'000000',c,0); loopIndex:=c@.size;
  _if c@.form=kFile _then _(
   mapia(s00012,globalText); mapia(c@.packing,procedureText);
   initindex:=c@.data@.size; poolValue.i:=s00012*256;
   _if poolValue.i>=initindex _then
    loopIndex:=loopIndex+poolValue.i-poolValue.i _mod initindex
   _else loopIndex:=loopIndex+initindex;
   mapia(initindex,scratchWord.a);
   isFunction:=(codeLevel=1) _and (s00141<>_nil);
   _if isFunction _then s00016:=true;
   _while t<>_nil _do _(
    p:=t@.vartype; t@.vartype:=c; t@.address:=frameNext;
    _if isFunction _then _(
     s00140:=s00141;
     _repeat
      _if s00140@.name=t@.name _then _goto 6644;
      s00140:=s00140@.next
     _until s00140=_nil;
     s00015:=true; _goto 6672;
     6644: s00140@.used:=true;
     _if s00140@.last=0 _then _(
      initindex:=-10-3*s00140@.first;
      mapia(initindex,u13); mapia(initindex+1,sumText)
     _) _else _(
      poolValue.i:=s00140@.first; PutLiteral(u13,false);
      poolValue.i:=s00140@.last; PutLiteral(sumText,false)
     _);
     6672:
    _) _else s00015:=true;
    AddAddress(frameNext,loopIndex); t:=p
   _)
  _) _else _while t<>_nil _do _(
   p:=t@.vartype; t@.address:=frameNext;
   AddAddress(frameNext,loopIndex); t@.vartype:=c; t:=p
  _);
  _if diagChar<>';' _then Diagnostic(8);
  lookupMode:=0; ScanToken;
  _if diagToken=ИД _then _goto 6526;
  _if diagToken<>ПС _then Diagnostic(1)
 _);
 (* 06727: nested PROCEDURE/FUNCTION and the FORWARD chain. *)
 6727:
 _if diagWord=KWProcedure _then _(
  isFunction:=false;
  6732: lookupMode:=0; ScanToken;
  _if diagToken<>ИД _then Diagnostic(2);
  _if knownIdent _then _(
   _if diagIdent@.kind<>PROC _then Diagnostic(20)
   _else _if diagIdent@.proc11=_nil _then Diagnostic(20)
   _else _if diagIdent@.level<>codeLevel _then Diagnostic(21);
   procedureText:=codeLevel; globalText:=diagIdent@.entry;
   AddAddress(codeLevel,1); p:=diagIdent;
   _if forwardType=diagIdent _then forwardType:=diagIdent@.proc11
   _else _(
    lastNode:=forwardType;
    _while diagIdent<>lastNode _do _(
     previous:=lastNode; lastNode:=lastNode@.proc11
    _);
    previous@.proc11:=diagIdent@.proc11
   _);
   diagIdent@.proc11:=_nil; ScanToken;
   _if diagChar<>'+' _then Diagnostic(22);
   ScanToken; t:=p@.params; p@.proc13:=false;
   _if t=_nil _then _goto 7172;
   _while t<>p _do _(
    mapai(t@.name ∧ '000177',loopIndex);
    t@.next:=namehash[loopIndex]; namehash[loopIndex]:=t; t:=t@.data
   _);
   _goto 7172
  _);
  new(p;peakSize); tnl(scratchWord.a); tnl(globalText);
  p@ := [diagWord,codeLevel,namehash[nameBucket],_nil,PROC,_nil,0,_nil,
         globalText,scratchWord.a,0,_nil];
  namehash[nameBucket]:=p;
  p@.ownSize:=0; p@.peakSize:=0; p@.proc16:=0;
  p@.proc15:=false; p@.proc13:= ; p@.proc14:=isFunction;
  procedureText:=codeLevel; AddAddress(codeLevel,1);
  _if isFunction _then globalText:=4 _else globalText:=3;
  setup(scopeMark); ScanToken;
  _if diagChar='(' _then FormalParams(p,globalText);
  setup(lastNode);
  _if isFunction _then _(
   _if diagChar<>':' _then Diagnostic(15);
   ScanToken;
   _if (diagToken<>ИД) _or (diagIdent=_nil) _then Diagnostic(16);
   _if diagIdent@.kind<>TYPE _then Diagnostic(17);
   7117:
   _case diagIdent@.form _of
    kSc,kRng,kPtr,kSet: p@.resulttype:=diagIdent;
    kArr,kRec,kFile: Diagnostic(18);
    kAlias: _( diagIdent:=diagIdent@.data; _goto 7117 _)
   _end;
   ScanToken
  _);
  _if diagChar<>';' _then Diagnostic(9);
  isFunction:=false; ScanToken;
  _if diagWord=KWExtern _then _(
   s00136:=s00136+1; mapяга(p@.name,savedNames[s00136]);
   p@.entry:=KWExtern; ScanToken; _goto 7212
  _) _else _if diagChar='+' _then _(
   p@.entry:=globalText; p@.proc11:=forwardType; forwardType:=p;
   p@.proc13:=true; p@.proc12:=lastNode
  _) _else _( _goto 7201;
  7172:
  tnl(scratchWord.a); p@.entry:=scratchWord.a; setup(scopeMark); lastNode:=scopeMark;
  isFunction:=true;
  7201: analyze(globalText,p);
  mapai(globalText,loopIndex); mapia(loopIndex-2,globalText);
  7212: _if diagChar<>';' _then Diagnostic(10)
   _);
  codeLevel:=procedureText; ScanToken; rollup(lastNode);
  PruneHash(namehash); PruneHash(oldhash);
  _if isFunction _then _(
   t:=p@.params;
   _if t<>_nil _then _while t<>p _do _(
    mapai(t@.name ∧ '000177',loopIndex); c:=namehash[loopIndex];
    _if c=t _then namehash[loopIndex]:=c@.next
    _else _(
     _while c<>t _do _( previous:=c; c:=c@.next _);
     previous@.next:=c@.next
    _);
    t:=t@.data
   _)
  _);
  _if diagToken<>ПС _then Diagnostic(11)
  _else _goto 6727
 _);
 _if diagWord=KWFunction _then _( isFunction:=true; _goto 6732 _);
 _if forwardType<>savedForward _then Diagnostic(23);
 _if diagWord<>KWBegin _then Diagnostic(13);
 (* 07272: frame size and root NEW reservation, before scanning the body. *)
 listBegin:=calls.top; mapai(frameNext,heapReserve);
 _if paramBlock<>_nil _then _(
  bodyProc:=paramBlock;
  _if bodyProc@.kind=PROC _then _(
   bodyProc@.ownSize:=heapReserve; bodyProc@.peakSize:=heapReserve
  _)
 _);
 _if codeLevel=1 _then _(
  _if (newcnt<>0) _and (reserv=0) _then Diagnostic(40);
  isFunction:=((newcnt=0) _and (reserv=100)) _or (reserv=0);
  _if reserv=100 _then reserv:=4;
  _if _not isFunction _then _( mapia(reserv*1024,newText); s00017:=isFunction _)
 _);
 s00051:=0; mapai(frameNext,frameSize); frameTotal:= ;
 paramBlock@.proc15:=true; lookupMode:=2;
 ScanBody; ScanToken; bodyProc:=paramBlock;
 _if bodyProc@.proc16<>0 _then bodyProc@.peakSize:=bodyProc@.peakSize+bodyProc@.ownSize;
 (* 07353: per-procedure storage, optional code bounds and call names. *)
 _if (codeLevel<>1) _and _not optI _then _(
  _if paramBlock@.proc14 _then write('ФУНК') _else write('ПРОЦ');
  mapai(paramBlock@.level,heapReserve); heapReserve:=heapReserve+1;
  write(heapReserve:2,Space); PrintField(paramBlock@.name);
  _if paramBlock@.proc13 _then write('*') _else write(Space);
  mapia(paramBlock@.ownSize,scratchWord.a); write(' ЛОК='); PrintField(scratchWord.a);
  mapia(paramBlock@.peakSize-paramBlock@.ownSize,scratchWord.a);
  write('  ВХОД='); PrintField(scratchWord.a);
  mapia(paramBlock@.peakSize,scratchWord.a); write('  СУМ='); PrintField(scratchWord.a);
  _if hascod _then _(
   ReadCodeBounds(firstc,scratchWord.a,diagWord);
   mapai(diagWord,heapReserve); mapai(scratchWord.a,lookupMode);
   mapia(heapReserve-lookupMode+1,diagWord);
   scratchWord.b:=((scratchWord.b _mod [3,5,7]) ∧ [8..47]) _mod [3,5,7];
   write('  КОД',scratchWord.a,':'); unpck(chars[1],diagWord);
   _for reportIndex:=3 _to 6 _do _( output@:=chars[reportIndex]; put(output) _);
   reportIndex:=64;
   _if wasTerm _then columns:=2 _else columns:=8
  _) _else _(
   reportIndex:=48;
   _if wasTerm _then columns:=4 _else columns:=10
  _);
  _if (calls.top>listBegin) _and optS _then _(
   write(Space); savedOutput:=0; nextLine:= ;
   _for heapReserve:=listBegin _to calls.top-1 _do _(
    savedOutput:=savedOutput+1;
    _if nextLine _then _( write(Space:reportIndex); nextLine:=false _);
    PrintField(calls.names[heapReserve]);
    _if savedOutput=columns _then _(
     savedOutput:=0; nextLine:=true; writeln
    _) _else write(Space)
   _)
  _);
  _if savedOutput>0 _then writeln
 _);
 mapia(frameTotal,paramName); calls.top:=listBegin
_);

_(
 errors:=0; setup(heap);
 writeln('**** Э Х О Л О Т ****':37);
 7560: ReadRequest; rollup(heap); diagWord:='00000 '; s00117:=0;
 analyze(diagWord,diagIdent);
 writeln; writeln('**** КОНЕЦ ****':34); writeln; _goto 7560
_).
