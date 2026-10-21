_(
 InitHistorical; allowForward:=false; pendingTypes:=0;
 ParseType(0,'000000',s00141,0);
 _if (s00141@.form<>kArr) _or (s00141@.size<>3) _then _goto 7560;
 writeln('ARRAY OK');
 ParseType(0,'000000',s00141,0);
 _if (s00141@.form<>kRec) _or (s00141@.size<>3) _then _goto 7560;
 writeln('RECORD OK');
 ParseType(0,'000000',s00141,0);
 _if (s00141@.size<>3) _or (s00141@.data@.kind<>TAGF) _then _goto 7560;
 writeln('VARIANT OK');
 ParseType(0,'000000',s00141,0);
 _if (s00141@.form<>kFile) _or (s00141@.packing<>8) _or (s00141@.size<>28)
 _then _goto 7560;
 writeln('PACKING OK');
 ParseType(0,'000000',s00141,0);
 _if (s00141@.packing<>3) _or (s00141@.size<>38) _then _goto 7560;
 writeln('RANGE OK');
 ParseType(0,'000000',s00141,0);
 _if (s00141@.packing<>0) _or (s00141@.size<>22) _then _goto 7560;
 writeln('WIDE OK');
 ParseType(0,'000000',s00141,0);
 _if (s00141@.packing<>15) _or (s00141@.size<>25) _then _goto 7560;
 writeln('POINTER OK');
 ParseType(0,'000000',s00141,0);
 _if s00141<>setType _then _goto 7560;
 writeln('SET OK');
 allowForward:=true;
 ParseType(0,'000000',s00141,0);
 _if (pendingTypes<>1) _or (s00141@.data@.form<>kPtr) _then _goto 7560;
 writeln('FORWARD OK');
 s00141:=_nil; ScanToken; ScalarConstant(s00141,diagWord,true);
 _if (s00141<>intType) _or (poolValue.i<>-17) _then _goto 7560;
 writeln('SIGNED OK');
 ScanToken; ScanToken; s00141:=_nil; ScalarConstant(s00141,diagWord,false);
 _if s00141<>charType _then _goto 7560;
 writeln('CHAR OK');
 ScanToken; ScanToken; s00141:=_nil; ScalarConstant(s00141,diagWord,false);
 _if (s00141<>nilType) _or (diagWord<>NilOffset) _then _goto 7560;
 writeln('NIL OK');
 ScanToken; ScanToken; s00141:=_nil; ScalarConstant(s00141,diagWord,false);
 _if (s00141<>boolType) _or (poolValue.i<>1) _then _goto 7560;
 writeln('NAMED OK');
 ScanToken; ScanToken; s00141:=_nil; ScalarConstant(s00141,diagWord,false);
 _if (s00141<>realType) _or (poolValue.r<>1.5) _then _goto 7560;
 writeln('REAL OK');
 new(s00141;form); new(s07076;form);
 s00141@ := [0,0, ,s00141,TYPE,1,kPtr];
 s07076@ := [0,0, ,s07076,TYPE,1,kPtr];
 _if _not TypeCheck(s00141,s07076) _or (pairHead<>_nil) _then _goto 7560;
 writeln('CYCLE OK');
 s00141@.form:=kRec; s07076@.form:=kRec;
 _if TypeCheck(s00141,s07076) _then _goto 7560;
 _if _not TypeCheck(alfaType,charType) _then _goto 7560;
 s00076:=false;
 _if _not TypeCheck(intType,realType) _then _goto 7560;
 writeln('TYPES OK');
 s00076:=true; new(s00141;upper); new(s07076;upper);
 s00141@ := [0,0, ,intType,TYPE,1,kRng,0,7];
 s07076@ := [0,0, ,intType,TYPE,1,kRng,0,7];
 _if _not TypeCheck(s00141,s07076) _then _goto 7560;
 s07076@.upper:=8;
 _if TypeCheck(s00141,s07076) _then _goto 7560;
 writeln('BOUNDS OK');
 ScanToken; ScanToken;
 new(s00141;peakSize); s00141@.nargs:=0; loadOp:='000003';
 FormalParams(s00141,loadOp);
 _if (s00141@.nargs<>5) _or (loadOp<>'000010') _then _goto 7560;
 s07076:=s00141@.params;
 _if (s07076@.kind<>CONST) _or (s07076@.consttype<>intType)
     _or (s07076@.constvalue<>'000003') _then _goto 7560;
 s07076:=s07076@.data;
 _if (s07076@.kind<>CONST) _or (s07076@.constvalue<>'000004') _then _goto 7560;
 writeln('VALUES OK');
 s07076:=s07076@.data;
 _if (s07076@.kind<>VAR) _or (s07076@.address<>'000005')
     _or (s07076@.vartype@.form<>kArr) _or (s07076@.vartype@.size<>2)
 _then _goto 7560;
 writeln('REFERENCE OK');
 s07076:=s07076@.data;
 _if (s07076@.kind<>PROC) _or (s07076@.resulttype<>realType)
     _or (s07076@.entry<>'000006') _then _goto 7560;
 writeln('FUNCTION OK');
 s07076:=s07076@.data;
 _if (s07076@.kind<>PROC) _or (s07076@.resulttype<>_nil)
     _or (s07076@.entry<>'000007') _or (s07076@.data<>s00141)
 _then _goto 7560;
 writeln('PROCEDURE OK');
 new(s00141;upper); s00141@.next:=_nil;
 new(scopeMark;upper); scopeMark@.next:=s00141;
 new(s07076;upper); s07076@.next:=scopeMark;
 namehash[0]:=s00141; namehash[1]:=s07076; namehash[127]:=_nil;
 oldhash[0]:=_nil; oldhash[127]:=s07076;
 PruneHash(namehash); PruneHash(oldhash);
 _if (namehash[0]<>s00141) _or (namehash[1]<>s00141)
     _or (namehash[127]<>_nil) _or (oldhash[0]<>_nil)
     _or (oldhash[127]<>s00141) _then _goto 7560;
 writeln('HASH OK')
_);
