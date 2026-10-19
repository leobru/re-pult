(*=p-,t-*)_program ДЖИН;
(* Reconstructed from PULT ДЖИП, zones 01070 on 2148/2248.
   Words 00000..00301 are reproduced exactly with compilation date 07.12.87.
   CODE handles the original low-level ARFA, device and overlay interfaces.
   Constant order, half-word alignment and redundant assignments are intentional.
   Identifiers are significant in their first six characters. *)
_const
 work1='ДЖИН.Р'; work2='АБОЧ/4'; work3=0020340703407026C;
 prog1='ДЖИН.П'; prog2='РОГР/4'; c47=47; c2=2;
_type request=_record ctrl:integer; nm1,nm2,nm3:alfa _end;

(* 00046: decode an ARFA status into three ALFA words and return to PULT. *)
_proced fail(err:integer);
_const arfaerr=4000000000000000C;
_var msg:_array[0..2] _of alfa; mask:integer;
_(
 code(=2ИА4,15ПА=ВИ15,); mask := ; code(=УИ15,);
 mask := arfaerr;
 code(2ЛС3=Э050202,);
 write(' *** ОШИБКА АРХ. = ', msg[0], msg[1], msg[2]);
 writeln;
 code(ПБ76002=);
_);

(* 00071: u42 zones 2..5 -> pages 1..4, then zone 1 -> page 0. *)
_proced loadProgram;
_(
 code(Э070rd1=,Э070rd2=,Э070rd3=,Э070rd4=,СЧlast=Э0756,ПБ6=,last:Э070rd0=,);
 code(С;rd1:0010010000420002,rd2:0010020000420003,rd3:0010030000420004,rd4:0010040000420005,rd0:0010000000420001,К;);
_);

(* 00110: release the selected logical unit. *)
_proced detach(u:integer);
_const release=2000770000000000C;
_var mask:integer;
_(
 mask := release;
 code(2СЧ3=СД34,2ЛС4=); u := ;
 code(2Э0723=,);
_);

(* 00117: preserve identifiers above 9999; convert a four-digit BCD number. *)
_function volume(u:integer):integer;
_const c9999=9999; c4=4; c10=10; c3=3;
_var result, i, digit:integer;
_(
 result := 0;
 code(2СЧ4=СД64,Э050105=,); u := ;
 _if u > c9999 _then _( volume := u; exit _);
 code(ИА=2СЧ4,СД40=2ЗЧ4,);
 i := 1;
 _while i <= 4 _do _(
   code(2СЧ4=СД74,2ЗЧ4=МР,); digit := ;
   result := result*10+digit;
   i := i+1;
 _);
 volume := result;
_);

(* 00166: attach ДЖИН.РАБОЧ and ДЖИН.ПРОГР to logical units 41 and 42. *)
_proced attach;
_label 1;
_const openis=1300000000000010C; key='КЛЮЧАР'; c9=9;
 units=0006000000000000C; workunit=33;
 mountis=1200000000000010C; unitbit=0004000000000000C;
 progunit=34; readis=1200000000004010C;
_var old:integer; keyval:alfa; available:integer; args:request;

(* 00147: obtain the ARFA identifier for the name in args. *)
_function archive:integer;
_var info:integer; k:alfa;
_(
 info := openis;
 code(=2ИА6,11ПА=3СЧ4,11ЗЧ=,);
 code(СЧ=СД160,);
 k := key;
 code(7Э063=,); archive := ;
 code(ВИ16=); info := ;
 _if info <> 0 _then fail(info);
_);

_(
 available := units;
 code(=2ИА6,11ПА=СЧ14,11ЗЧ1=СЧ15,11ЗЧ2=СЧ16,11ЗЧ3=2ИА6,15ПА=ВИ15,);
 old := ; code(=УИ7,);
 old := volume(workunit);
 _if old = archive _then _goto 1;
 _if old <> 0 _then detach(workunit);
 old := mountis;
 code(2ИА6=11ПА,2СЧ3=11ЗЧ,);
 available := available;       % Load the allocation mask into A for the following shift into RMR.
 code(ИА=СД160,);
 keyval := key;
 code(7Э063=,ВИ16=); old := ;
 _if old <> 0 _then fail(old);
 1:
 code(СЧ43=СР74000,2ЛУ5=); available := ;
 code(2ИА6=11ПА,СЧ17=11ЗЧ1,СЧ20=11ЗЧ2,);
 old := volume(progunit);
 _if old = archive _then exit;
 _if old <> 0 _then detach(progunit);
 old := readis;
 code(2ИА6=11ПА,2СЧ3=11ЗЧ,);
 available := available;       % Load the allocation mask into A for the following shift into RMR.
 code(ИА=СД160,);
 keyval := key;
 code(7Э063=,ВИ16=); old := ;
 _if old <> 0 _then fail(old);
_);

_( attach; loadProgram _).
