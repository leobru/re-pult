(* Читаемая декомпиляция СЕРВИС, сборка 21.11.88.
   Источник: /home/leob/src/bega-re/servic.pas.
   Образ: том 2148, зоны 01031-01033; на 2068 - зоны 031-033.
   Рекомпиляция: Паскаль-автокод 9 от 17.05.88, автокод ИТМ.
   Имена значимы в первых шести символах. Порядок объявлений сохранен.
   CODE, пустые присваивания и повторные присваивания передают
   значения через аккумулятор и сохраняют точное расположение кода.
   Все адреса в комментариях - восьмеричные; счетчики - десятичные.
   Проверка всего образа из 3072 слов: tests/servic.py. *)
(*=p-,t-,l-*)_program SERVIC(F=270000В 16); _label 5322, 5324, 5333;
_const sp=' ';dot='.';lf='≡214';eot='≡172';etx='≡377';
_type letter ='A'..'Z'; bitset=_set _of 0..47; hund=0..100;
unp6=_array [1..6] _of char; digit='0'..'9';
a15 = _array[1..15] _of integer;
(* Глобальные ячейки в порядке исходного кадра:
   SPARE - не используется; TXTBUF - база текста (010000);
   WORK - временное слово; SAVED - копия настройки НАБЛ 57756;
   BUFNUM - номер временного буфера; COLUMN - начало поля АЦПУ;
   CELL - указатель в НАБЛ; HASCMD - результат разбора приказа;
   DIRECT - режим выдачи без нумерации; UNREAD - буфер еще не прочитан;
   SEP - разделитель строк из 57757 (по умолчанию 0175);
   ARGSRC/ARGDST - копирование 15 слов параметров 57640 в 70001;
   HITS[0] - число сохраненных совпадений, HITS[1..100] - номера строк. *)
_var spare, txtbuf, work, saved, bufnum, column:integer;
cell:@integer;
hascmd, direct, unread:boolean;
sep:char;
argsrc, argdst:@a15;
cmd:alfa;
hits:_array[hund] _of integer;
F:text;

(* 01102. Установить базу и текущий адрес OUTPUT (75205, 75224). *)
_proced outbuf(a:integer); _( a := a; code(зч75205=зч75224,) _);

(* 01107. Установить базу INPUT (75207). RESET выполняется вызывающим кодом. *)
_proced inbuf(a:integer); _( a := a; code(зч75207=) _);

(* 01113. Собственный WRITELN; рабочий вход PR находится в 01115.
   Э64 обслуживает бит 2 режима 76013, Э71 - бит 1. Счетчик 76422
   задает остановки ИДТИ?; L1166/L1171 сохраняют и восстанавливают INPUT.
   Пустой ответ продолжает выдачу; другой ответ становится новым приказом.
   L1213 вызывает привязку INPUT через вход АДСИС 74066. *)
_proced wrline;
_(
  code(=16пае,pr:ви16=зчD1162,`переопределение writeln`);
  write('≡172      ');
  code(ви7=зчD1164,сч75205=уи7,сч76013=луD1163,у0L1124=э064D1160,L1124:сч76013=лу13,);
  code(у0L1154=cч76401,лсD1157=17зч1,17э0711=,э07176402=,сд/-26/=сд/-2/,мр=ср13,у0L1222=сч76422,);
  code(уи7=7са-1,ви7=зч76422,у1L1154=сч76421,зч76422=16пвL1166,);
  inbuf(28672);
  code(15паD1165=12пвL1213,сч70000=ср76727,у1L1151=);
  inbuf(4096);
  code(16пвL1171=,пбL1154=,L1151:);
  rewrite(output);
  _GOTO 5324;
  code(L1154:); rewrite(output);
  code(счD1164=уи7,икD1162=пб,c;D1157:3000000024000321,D1160:3400000034000000,40000000,);
  code(D1162:0,D1163:2,D1164:0,D1165:2746337700000000,к;);
  code(L1166:сч74220=зчD1211,сч75225=зчD1212,16пб=,L1171:счD1211=зч74220,счD1212=зч75225,);
  code(ик75225=сч,зч74217=сч74215,17зч1=ср74220,у1L1202=сч75225,уи15=15сч-1,луD1210=1зч7,16пб=,);
  code(L1202:сч74217=сд/-10/,зч74217=мр,1зч7=17сч1,сд/1/=17зч1,ср74220=у1L1202,16пб=,c;);
  code(D1210:377,D1211:0,D1212:0,к;L1213:ви12=зчD1221,12пв74066=,);
  code(сч76424=сд/-26/,сд/-2/=мр,ср13=у0L1222,икD1221=пб,);
  code(c;D1221:0,к;L1222:);
  rewrite(output);
  _GOTO 5322;
_);

(* Пропустить пробелы во входном тексте. *)
_proced skipsp; _( _while input@ = sp _do get(input) _);

(* Прочитать первые три буквы приказа, пропустив остальные буквы.
   Результат дополняется пробелами до шести символов ALFA. *)
_function getcmd(_var name:alfa):boolean;
_var chars:unp6; pos:integer;
_(
  skipsp;
  pos := 1;
  name := '      ';
  unpck(chars[1], name );
  _while (input@ _in letter) ∧ (pos < 4) _do _(
    chars[pos] := input@;
    get(input);
    pos := pos + 1;
  _);
  _while input@ _in letter _do  get(input);
  skipsp;
  pck(chars[1], name);
  getcmd := pos <> 1;
_);

(* Десятичное число. Коды цифр ГОСТ равны их числовым значениям.
   Проверка нижней границы отсутствует в исходной программе. *)
_function getnum:integer;
_var value:integer;
_(
  value := 0;
  skipsp;
  _while input@ <= '9' _do _( value := 10 * value + ord(input@); get(input) _);
  getnum := value;
_);

(* 01553. АЦПУ: распаковать печатный буфер и выдать его с заданной строки.
   COLUMN задает первую из 79 выводимых колонок. UNREAD разрешает
   однократное считывание буфера; затем используется сохраненный текст. *)
_proced prtout(jobno:integer);
_const eol='≡175';
_var packed, lastch, col, line, first, ones, rem100:integer; finite, spare:boolean;

  (* 01312. Распаковка блока из 256 слов в странице 070000.
       Заголовок: длина в младших 12 битах, сдвиг в следующих 15 битах.
       Коды: 0 и 97 - пропуск; 124 - конец блока; 0175 - конец текста;
       127 - повтор предыдущего символа; больше 128 - переход к колонке.
       L1435 извлекает байт, L1470 выводит его и объединяет переводы строк. *)
  _function decblk(offset:integer):boolean;
  _var header, length, shift, spare1, spare2, count, i:integer; final, waslf:boolean;
  _(
    code(=3сч4,уи5=5са70000,7па1=6па6,5сч=); header := ;
    _if offset = 0 _then _(
      length := sel(header, 0, 12);
      finite := length <> 0;
      _if finite _then _(
        shift := sel(header, 12, 15);
        code(зчD1462=);
        _if shift <> 0 _then  shift := trunc((32768 - shift) / 8);
        shift := shift;
        code(зчD1463=);
      _)_); (* 1343 *)
    final := finite ∧ (offset + 256 >= length);
    decblk := ;
    code(зчD1460=);
    _if final _then _( length := length - offset - 1; code(=зчD1461,) _);
    code(16пвL1435=,); (b) _(code(16пвL1435=,);
      packed := ;
      _select
        packed = 0: _goto b;
        packed = 124: _exit b;
        packed = 175В: _( decblk := true; exit _);
        packed = 97: _goto b;
        packed < 97: packed := (packed - 1);
        (packed > (128)): _(
          count := ((packed - (128)) - col);
          _for i := 1 _to count _do code(15па17=ви15,16пвL1470=,);
          _goto b
        _);
        packed <> 127: _( code(счD1466=16пвL1470,); _goto b _);
        true: _( code(16пвL1435=,); count := ;
          _for i := 1 _to count _do _( lastch := lastch; code(=16пвL1470,) _);
          _goto b
        _)
      _end;
      lastch := packed; code(16пвL1470=,); _goto b
    _);
    code(L1434:); exit;
    code(L1435:ви6=срD1465,у1L1455=7са1,ви7=овD1467,у1L1434=счD1460,у0L1453=ви7,овD1461=у0L1445,);
    code(счD1466=16пвL1470,пбL1434=,);
    code(L1445:ви7=срD1461,у1L1453=5иа,7сч=икD1462,сд/0/=зчD1464,счD1463=уи6,пбL1455=,);
    code(L1453:6па=5иа,7сч=зчD1464,);
    code(L1455:6са1=счD1464,сд/-10/=зчD1464,мр=16пб,с;);
    code(D1460:0,D1461:0,D1462:0,D1463:0,D1464:0,D1465:6,D1466:175,D1467:377,к;);
    code(L1470:);
    output@ := ; code(=ви16,зчD1506=1сч10,срD1466=у1L1501,);
    _if waslf _then code(икD1506=пб,);code(16пвOWL=,);
    waslf := true;
    col := 0;
    code(икD1506=пб,);
    code(L1501:); waslf := false; col := (col + 1); (q) put(output);
    code(икD1506=пб,c;D1506:0,к;);
  _);

  (* 01510. Э62 041 читает части печатного буфера; каждая содержит
       четыре блока по 256 слов. Распакованный текст пишется с 010000,
       обычный буфер OUTPUT затем возвращается на 072000. *)
  _proced rdprt;
  _var block, status:integer;
  _(
    reset(input);
    outbuf( (4096) );
    (loop) _for block := (1340000C) _to (1340020C) _do _(
      status := ((jobno * 100000000В) + block);
      code(э06241=,);
      status := ;
      _if (status = 0) _then _exit loop;
      _for status := 0 _to 3 _do  _(
        _if (decblk(256*status)) _then _exit loop;
      _);
    _);
    write(eot, ' ':5);
    outbuf( (29696) );
    rewrite(output);
  _);

_( (* PRTOUT, 01553 *)

  line := 1;
  col := 0;
  spare := false;
  rewrite(output);
  _if (input@ = etx) _then first := 1 _else _(
    first :=   getnum;
    _if (first = 0) _then _( writeln('ОШ. В НОМЕРЕ СТРОКИ'); EXIT _);
  _);
  _if unread _then _(  rdprt;  unread := false _);
  inbuf( (4096) );
  reset(input);
  line := 1;
  col := 0;
  _while input@ <> eot _do _(
    _if (line >= first) _then _(
      _if (input@ = eol) _then _(
        line := (line + 1);
        _if _not (col >= (column + (79))) _then writeln;
        col := 0;
      _) _else _(
        col := col + 1;
        _if (col >= column) _and (col <= column + 79) _then _(
          _if (col > column + 78) _then writeln _else write(input@);
        _);
      _);
    _) _else _if input@ = eol _then  line := (line + 1);
    get(input);
  _); (* 1637 *)
  line := line - 1;
  _if line = 0 _then  rewrite(output);
  write(' ДЛИНА БУФЕРА ', line:0, ' СТРОК');
  ones := line _MOD 10;
  rem100 := line _MOD 100;
  _if ((rem100 < 5) _or (rem100 > 20)) _and (ones <> 0) _then _(
    _if ones = 1 _then write('А')
  _else _if ones < 5 _then  write('И');
  _);
  writeln
_);

(* 01674. Десятичное число с ведущими нулями до WIDTH позиций. *)
_proced padnum(value, width:integer);
_var i, power:integer;
_(
  _if value < 0 _then  write('-');
  value := abs(value);
  _if width < 1 _then  width := 1;
  power := 1;
  _for i := 1 _to (width - 1) _do  power := (power * (10));
  _for i := 1 _to (width - 1) _do _(
    _if _not (value >= power) _then  write('0');
    power := round(power / 10);
  _);
  write( value:0 );
_);

(* 01742. Перевести отсчеты по 1/50 секунды в секунды и сотые доли. *)
_proced ticks(value:integer);
_var cents:integer;
_(
  write(trunc(value / 50):0, '.');
  cents := value _MOD 50 * 2;
  padnum(cents, 2);
  write('  ');
_);

(* ВРЕ: время процессора через Э63 4 и оставшееся время через Э63 0. *)
_proced ВРЕ;
_var cpu:integer; left:real;
_(
  write('ВЦП '); code(э0634=,); cpu := ; ticks( cpu );
  write('ОСТ '); code(э0630=,); left := ; writeln(trunc(left):0 );
_);

(* 02045. С/СПИС: диапазоны строк или строки, сохраненные поиском НАЙ.
   RANGES хранит введенные интервалы, CHOSEN - фактически выбранные.
   По умолчанию диапазон 1:100000. Суффикс меняет разделитель строк.
   DIRECT убирает номера и увеличивает ширину до 10000 символов. *)
_proced list(_var found:_array[hund] _of integer; _var delim:char);
_const c96=96;
_type rec=_record lo, hi:integer _end;
_var i, j, dest, nhits, count, col, nlines, line, width:integer;
alive:@integer;
word:alfa;
ranges, chosen:_array[1..100] _of rec;
ch:char;
usehit:boolean;
range:@rec;

  (* 02004. Конец текста при выдаче: итог и переход к запросу приказа. *)
  _proced finish;
  _(
    _if direct _then code(пб76002=,);
    writeln('≡175ВСЕГО ', line:0, ' СТРОК.');
    inbuf( (28672) );
    _GOTO 5322;
  _);

  (* 02023. Отказ при пустом списке найденных строк. *)
  _proced nohits;
  _(
    writeln('ПУСТОЙ СПИСОК СТРОК');
    _GOTO 5322;
  _);

  (* 02031. После строки проверить флаг продолжения в ячейке 4. *)
  _proced poll(_var count:integer);
  _(
    _if (count > 200000) _or (alive@ = 0) _then _(
      alive@ := 1;
      _GOTO 5322;
    _);
    count := count + 1;
  _);

_( (* LIST, 02045 *)
  alive := ptr(4);
  alive@ := 1;
  _if direct _then  width := 10000 _else width := 70;
  usehit := input@ = 'Н';
  _if usehit _then _(
    _if getcmd( word) _then ;
    nhits := found[0];
    _if _not (nhits >= 1) _then  nohits;
  _); (* 2076 *)
  ranges[1].lo := 1;
  ranges[1].hi := 100000;
  i := 1;
  skipsp;
  (a) _select
    input@ = etx: _exit a;
    input@ = lf: _( get(input); skipsp; _goto a _);
    input@ > ':': delim := input@;
    input@ > '9': _(  writeln('ОШ В СПИСКЕ'); _GOTO 5322 _);
    true: _(
      range := ref(ranges[i]);
      range@.lo := getnum;
      skipsp;
      _if input@ = ':' _then _(  get(input); range@.hi :=   getnum _)
    _else  range@.hi := range@.lo;
      i := i + 1;
      skipsp;
      _if i < 30 _then _goto a;
    _)
  _end;
  _if i > 1 _then  count := i - 1 _else  count := 1;
  _if _not usehit _then chosen := ranges _else _(
    dest := 1;
    _for i := 1 _to count _do _(
      j := 1;
      (L2175) _( _select
          (j <> 1) _and (found[j] = found[j - 1]): _(
            j := j + 1;
            _goto L2175
          _);
          found[j] > ranges[i].hi: _exit L2175;
          found[j] >= ranges[i].lo: _(
            range := ref(chosen[dest]);
            range@.lo:= found[j];
            range@.hi := range@.lo;
            dest := (dest + 1);
          _)
        _end; (* 2243 *)
        j := j + 1;
        _if j <= nhits _then _goto L2175;
      _)
    _); (* 2251 *)
    count := dest - 1;
    _if count < 1 _then  nohits;
  _); (* 2255 *)
  inbuf( txtbuf );
  reset(input);
  line := 1;
  col := 0;
  nlines := 0;
  _for j := 1 _to count _do _(
    _while line < chosen[j].lo _do _(
      _select
        (input@ = eot) _or (input@ = '≡140'): finish;
        input@ = delim: line := line + 1
      _end;
      get(input)
    _); (* 2305 *)
    _while line <= chosen[j].hi _do _(
      ch := input@;
      _select
        (ch = eot) _or (ch = '≡140'): finish;
        ch <> delim: _(
          _select (col = 0) : _if _not direct _then write( line:4, ': ');
            (col > width): _(
              writeln;
              _if _not direct _then write(' ':6);
              col := 0;
              poll( nlines );
            _) (* 2344 *)
          _end;
          write(ch);
          col := col + 1;
        _);
        (ch = delim): _(
          _if (col = 0) _and _not direct _then write( line:4, ':');
          writeln;
          col := 0;
          line := line + 1;
          poll( nlines );
        _)
      _end;
      get(input);
    _); (* 2372*)
  _) (* 2374 *)
_);

(* НАЙ: поиск образца в кавычках в заданном диапазоне строк.
   Апостроф внутри образца кодируется двумя апострофами.
   Сохраняются первые 100 номеров строк; подсчитываются все совпадения.
   Алгоритм последовательно потребляет INPUT при сравнении образца. *)
_proced НАЙ(_var found:_array[hund] _of integer; _var delim:char); _label 2556;
_var line, length, pos, count, first, last: integer;
sample:_array[1..100] _of char; ch:char;

  (* 02375. Считать непустой образец; проверить закрывающую кавычку. *)
  _proced quoted;
  _(
    _if (input@ = '''') _then _(
      length := 0;
      get(input);
      (L2402) _(
        _select (input@ = eot) _or (input@ = '≡140'): _(
            writeln('НЕТ ВТОРОЙ КАВЫЧКИ');  _GOTO 5322;
          _);
          (input@ = ''''): _(
            get(input);
            _if (input@ = '''') _then _(
              length := (length + 1);
              sample[length] := input@;
              get(input);
            _) _else _exit L2402;
          _);
          true:_( length := (length + 1); sample[length] := input@; get(input) _)
        _end;
        _goto L2402;
      _);
      _if (length = 0) _then _( writeln('ДЛ=0'); _GOTO 5322 _)
    _) _else _( writeln('НЕТ СТРОКИ В КАВЫЧКАХ'); _GOTO 5322 _)
  _);

  (* 02450. Получить символ, обновить номер строки и проверить конец поиска. *)
  _proced nextch;
  _(
    ch := input@;
    get(input);
    _select (ch = delim): line := (line + 1);
      (ch = eot) _or (ch = '≡140') _or (line > last) : _(
        _if (count > (100)) _then found[0] := (100) _else found[0] := count;
        _if _not (last <= line) _then  last := line;
        writeln('≡175ПРОСМОТРЕНЫ СТРОКИ С ', first:0, ' ПО ', last:0, '. ВСЕГО ', count:0, ' ВХОЖДЕНИЙ');
        inbuf( (28672) );
        _GOTO 5322;
      _) _end
  _);

_( (* НАЙ *)
  first :=   getnum;
  _if _not (first <> 0) _then  first := 1;
  skipsp;
  _if _not (input@ <> ':') _then  get(input);
  last :=   getnum;
  _if _not (last >= first) _then  last := 100000;
  skipsp;
  quoted;
  skipsp;
  _if _not (input@ = etx) _then  delim := input@;
  line := 1;
  inbuf( txtbuf );
  reset(input);
  count := 0;
  2556:
  nextch;
  _if (ch = sample[1]) _and (line >= first) _then (a) _(
    ch := input@;
    _if (ch <> sample[1]) _or (length <= 1) _or (ch = sample[2]) _then _(
      _for pos := 2 _to length _do _(
        nextch;
        _if (ch <> sample[pos]) _then _exit a
      _);
      count := (count + 1);
      write(line:5);
      _if _not (count > (100)) _then  found[count] := line;
      _if count _MOD 10 = 0 _then writeln
    _)
  _);
  _goto 2556
_);

(* ВСТ: вставить файл F после заданной строки текста INPUT.
   F связан с барабаном 027, зоной 0, размером 16 зон в заголовке.
   OUTPUT сначала использует дескриптор барабана 026; готовые зоны
   считываются в память через Э70. Одна зона содержит 6144 символа. *)
_proced ВСТ(_var delim:char);
_var lines, added, total, nchars, after, zone, nzones, desc:integer;
ch:char;
exists:boolean;
_(
  after :=   getnum;
  _if (after < 1) _then _( writeln('НЕТ НОМЕРА СТРОКИ'); EXIT _);
  total := 0;
  nchars := ;
  lines := ;
  added := ;
  exists := true;
  inbuf( txtbuf );
  reset(input);
  rewrite(output);

  _repeat
  ch := input@;
  _if _not (ch <> delim) _then  lines := (lines + 1);
  total := (total + 1);
  output@ := ch;
  put(output);
  get(input);
_until (lines = after) _or (ch = '≡140') _or (ch = eot);
  _if (lines <> after) _then exists := false _else _(
    reset(F);
    _while (F@ <> '≡140') _and (F@ <> eot) _and (nchars < (60000)) _do _(
      output@ := F@;
      _if _not (F@  <> delim) _then  added := (added + 1);
      nchars := (nchars + 1);
      put(output);
      get(F);
    _);
    total := (total + nchars);
    lines := (lines + added);
    _while (input@ <> '≡140') _and (input@ <> eot) _do _(
      output@ := input@;
      _if _not (input@ <> delim) _then  lines := (lines + 1);
      put(output);
      get(input);
      total := (total + 1);
    _);
    write('≡172≡175', ' ':6);
    total := (total + 2);
    nzones := trunc((total + 6143) / 6144);
    code(сч75205=ср75224,у0L2735=э07075223,L2735:);
    desc := (10040000260000C);
    _for zone := 0 _to nzones-1 _do _(
      desc := desc;
      code(17зч1=17э0701,);
      desc := (desc + 10000000001В);
    _)
  _); (* 2750 *)
  outbuf( (29696) );
  rewrite(output);
  inbuf( (28672) );
  _if exists _then
  writeln('ВСТАВЛЕНО ', nchars:0, ' СИМВОЛОВ (', added:0, ' СТРОК) ПОСЛЕ СТРОКИ N ',
  after:0, ' .≡214ВСЕГО СТРОК ', lines:0, ', СИМВОЛОВ ', total:0, ' (', nzones:0, ' ЗОН)')
_else  writeln('НЕТ СТРОКИ N ', after:0 );
_);

(* Восьмеричное число. Как и GETNUM, полагается на коды цифр ГОСТ. *)
_function getoct:integer;
_var value:integer;
_(
  value := 0;
  skipsp;
  _while input@ < '8' _do _( value := value * 8 + ord(input@); get(input) _);
  skipsp;
  getoct := value;
_);

(* ТРАК: освободить тракт через Э62 0130; без аргумента перебрать
   номера 010..026. Тракт 027 зарезервирован для ПУЛЬТа. *)
_proced ТРА;
_var unit, freed:integer;
_(
  _if input@ = etx _then _(
    freed := 0;
    _for unit := 8 _to 22 _do code(2сч3=э062130,2цс4=2зч4,);
  _) _else _(
    unit :=   getoct;
    _if (unit < 8) _or (unit > 23) _then _( writeln('БОЛЬШОЙ РАЗМАХ !'); EXIT _);
    _if (unit = 27В) _then _( writeln('НЕ РУБИ СУК !'); EXIT _);
    code(2сч3=э062130,2зч4=);
  _);
  writeln('ОСВОБОЖДЕНО ', freed:0, ' ТРАКТОВ');
_);

(* 03101. Отключить логический НУ 030..067 через Э72. *)
_proced detach(unit:integer);
_var mask:integer; name:alfa;
_(
  _if (unit < 30В) _or (unit > 67В) _then _(
    mapia( unit, name );
    write('ОТКАЗ ОТ НУ=');
    ГГ( name , ' !!!' );
    writeln;
    _GOTO 5322;
  _);
  mask := (2000770000000000C);
  (* Упаковка номера НУ и маски отключения для Э72. *)
  code(2сч3=сд/-44/,2лс4=2зч3,2э0723=,);
_);
(*=m-*)

(* 03123. Разложить десятичное число на шесть цифр ГОСТ, собрать ALFA.
   Пустое присваивание берет результат из аккумулятора. *)
_function digits(value:integer):alfa;
_var i, digit, power:integer;
chars:unp6; result:alfa;
_(
  power := (303240C);
  _for i := 1 _to 6 _do _(
    digit := trunc(value / power);
    chars[i] := ;
    value := value - digit * power;
    power := power _DIV 10;
  _);
  pck(chars[1], result);
  digits := result;
_);

(* 03151. ПАР: проверить наличие пароля (Э50 0127) или передать
   пароль через Э50 0121. MODE: 0 - запись, 1 - чтение. *)
_proced passwd(mode, pass, volume:integer);
_var number, mask:alfa; flags:bitset; access:alfa;
_(
  _if volume = 0 _then  EXIT;
  mask := '    ';
  number :=   digits( volume );
  code(2сб7=сд/40/,);
  number := ;
  _if pass = 0 _then _(
    code(2сч6=э050127,сд/2/=мр,);
    flags := ;
    _if mode _IN flags _then _(
      write('ИМЕЕТСЯ ПАРОЛЬ ');
      _if mode = 0 _then  access := 'ЗП' _else access := 'СЧ';
      ГГ( access );
      writeln(' НА БОБ ', volume:0 );
      EXIT;
    _)
  _);
  code(2сч3=сд/-16/,2зч3=);
  mode := (mode + pass);
  code(уи15=2сч6,э050121=,);
_);

(* 03216. Принять том через Э50 0131. Вернуть статус ОС.
   При успехе установить смещение Э50 0112 и подтвердить пароли.
   При занятости BUSYUN содержит освобождаемый номер устройства. *)
_function mount(volume, unit, offset:integer):integer;
_var number, status, busyun:integer; chars:alfa;
_(
  mount := 1;
  _if volume <= 0 _then  EXIT;
  chars := digits( volume );
  status := 1703607417В;
  busyun := 177777В;
  code(2сч12=2сб10,2рб11=);
  number := ;
  status := 77В;
  code(2сч5=сд/-6/,2лс10=сд/-44/,2лс7=э050131,); status := ;
  code(ви16=); busyun := ;
  _if (status = 0) _then _(
    write('БОБИНА ', volume:0, ' ПРИНЯТА');
    _if offset <> 0 _then _(
      offset := unit * 4096 + offset;
      code(э050112=,);
      offset := unit * 4096;
      code(э050113=,сд/30/=);
      offset := ;
      offset := offset * 32;
      write(' (СДВИГ=', offset:0в, ')');
    _);
    writeln;
    passwd( 1, 0, volume );
    passwd( 0, 0, volume );
  _);
  _if status = 2 _then _(
    _if busyun = 0 _then _(
      writeln('БОБИНА ', volume:0, ' ЗАНЯТА');
      _GOTO 5322;
    _);
    detach( busyun );
  _);
  mount := status;
_);

(* 03322. Э50 0105: определить том НУ и преобразовать BCD в число.
   Идентификаторы больше 9999 сохраняются. Для буфера 32767
   дополнительный номер берется из М16 в глобальную BUFNUM. *)
_function volnum(unit:integer):integer;
_var number, i, digit:integer;
_(
  number := 0;
  bufnum := ;
  code(2сч4=сд/-14/,э050105=,);
  unit := ;
  _if (unit > 9999) _then _(
    _if _not (unit <> (32767)) _then  _( code(ви16=); bufnum := ; _);
    volnum := unit;
    EXIT;
  _);
  code(=2сч4,сд/-40/=); unit := ;
  _for i := 1 _to 4 _do _(
  (* Сдвиг следующей цифры BCD в аккумулятор. *) code(2сч4=сд/-4/,2зч4=мр,);
    digit := ;
  (*=m+*) number := number * 10 + digit;
  _);
  volnum := number;
_);

(* 03355. Найти подключенный том перебором НУ 030..067; 0 - нет. *)
_function findun(volume:integer):integer;
_var number, unit:integer;
_(
  findun := 0;
  _for unit := 30В _to 67В _do _(
    number :=   volnum( unit );
    _if (number = volume) _then _( findun := unit; EXIT _)
  _);
_);

(* 03374. Проверить номер тома, освободить занятый НУ, принять том.
   Статус 2 повторяет попытку после освобождения занятого устройства. *)
_proced attach(volume, unit, offset:integer);
_var oldvol:integer;
_(
  _if volume = 0 _then _( writeln('НЕВЕРНЫЙ НОМЕР БОБИНЫ'); _GOTO 5322 _);
  oldvol :=   volnum( unit );
  _if oldvol = volume _then _(  writeln('УЖЕ ЕСТЬ'); EXIT  _);
  _if oldvol <> 0 _then  detach( unit );
  (L3423) _case mount( volume, unit, offset ) _of
    0: EXIT;
    1: writeln('НЕТ БОБИНЫ ', volume:0 );
    2: _goto L3423;
    7: writeln('ЧИСЛО ЛЕНТ = 12')
  _end;
  _GOTO 5322;
_);

(* 03454. Э50 0202: декодировать ответ АРФА в три слова ALFA.
   После сообщения возврат к запросу приказа. *)
_proced arferr(status:integer);
_var msg:_array[1..3] _of alfa; mask:bitset;
_(
  code(=2иа4,15па=ви15,2зч7=уи15,);
  mask := [0];
  code(2лс3=э050202,);
  writeln(msg[1], msg[2], msg[3]);
  _GOTO 5322;
_);

(* ОБЛ: сформировать имя области АРФА и запрос КЛЮЧАР через Э63.
   В 071777 лежит управляющее слово; ключ З разрешает запись. *)
_proced ОБЛ;
_var module:alfa; ctrl, unit:integer; units:bitset;

  (* 03476. Переписать имя и шифр владельца в формат запроса АРФА. *)
  _proced owner; _label 3533;
  _var i:integer;
  _(
    _while input@ _in letter _do _(
      _while (input@ _in letter) _or (input@ _in digit) _do _( write(input@); get(input) _);
      skipsp;
      _if input@ = dot _then _( write(input@);  get(input); skipsp _);
    _);
    _if (input@ <> '/') _then 3533: _(
      rewrite(output);
      writeln('НЕТ ХОЗЯИНА');
      _GOTO 5322;
    _);
    write('/');
    get(input);
    skipsp;
    _if _not (input@ _in digit) _and _not (input@ = '.') _then _goto 3533;
    _for i := 1 _to 6 _do _(
      _if (input@ _in digit) _or (input@ = '.') _then _( write(input@); get(input) _) _else write(dot);
    _);
    write(';000000');
    skipsp;

  _);

_( (* ОБЛ *)
  ctrl := (1200000000004010C);
  code(=зч71777,);
  _if _not (input@ _in letter) _then _(
    writeln('ДАЙ ИМЯ ОБЛ.');
    EXIT
  _);
  owner;
  unit :=   getoct;
  _if (unit < 30В) _or (unit > 67В) _then _(
    rewrite(output);
    writeln('ОШ. В <НУ>');
    EXIT _);
  code(7па71777=);
  _if (input@ = 'З') _then _(
    ctrl := (7777777777773777C);  code(7лу=7зч,);
  _);
  units := [unit-30В];
  code(=сд/60/,);
  module := 'КЛЮЧАР';
  code(7э063=,ви16=);
  ctrl := ;
  rewrite(output);
  arferr( ctrl );
_);

(* 03643. Запросить имя области по идентификатору через КЛЮЧАР.
   Печатать имя и шесть символов шифра после косой черты. *)
_proced arfnam(handle:integer);
_var words:_array [0..10] _of alfa;
chars:unp6;
status, tail:integer; module:alfa;
_(
  code(=2иа4,15па=ви15,2зч25=уи7,);
  (*=c-*)
  words[1] := handle;
  status := 13T;
  words[0] := status;
  (*=c+*)
  code(ви7=сд/60/,);
  module := 'КЛЮЧАР';
  code(7э063=,ви16=);
  status :=;
  _if status <> 0 _then  arferr( status );
  tail := 0;
  _for status := 0 _to 10 _do _(
    unpck( chars[1], words[status]);
    _for handle := 1 _to 6 _do _(
      _if (chars[handle] <> '≡143') _and (chars[handle] <> ' ') _then  write(chars[handle]);
      _if tail = 6 _then EXIT _else
      _if tail <> 0 _then tail := tail + 1 _else
      _if chars[handle] = '/' _then  tail := 1;
    _)
  _)
_);

(* БОБ: список подключенных томов, поиск НУ, подключение тома
   или заказ временного буфера БУФ. Рабочий НУ 040 защищен.
   Для БУФ размер переводится в единицы ОС множителем 037. *)
_proced БОБ;
_var volume, unit, col, avail, offset:integer;
word:alfa; buffer:boolean;
_(
  buffer := false;
  _if input@ = etx _then _(
    writeln('ВАШИ БОБИНЫ -');
    col := 1;
    _for volume := 30В _to 67В _do _(
      unit :=   volnum( volume );
      _if unit <> 0 _then _(
        mapia( volume, word );
        ГГ( word );
        write(' - ');
        _if unit = 32767 _then  write('БУФ', bufnum:0 )
      _else _if unit > 9999 _then arfnam( unit ) _else write( unit:0 );
        write(' ':3);
        _if col _MOD 5 = 0 _then writeln;
        col := col + 1;
      _);
    _);
    writeln;
    exit;
  _);
  _if getcmd( word) _then _(
    buffer := word = 'БУФ   ';
    _if _not buffer  _then _(  writeln(word, ' - ОШИБКА'); EXIT _);
    volume :=   getnum;
    _if volume = 0 _then _(  writeln('ОШИБКА В ЧИСЛЕ КУСКОВ'); EXIT _);
  _) _else _( (* 4025 *)
    volume :=   getnum;
    _if (volume = 0) _or (volume > (2999)) _then _(
      writeln('НЕТ БОБИНЫ С ТАКИМ НОМЕРОМ'); EXIT _);
  _); (* 4037 *)
  unit :=   getoct;
  offset :=   getoct;
  _if (unit = 0) _and _not buffer _then _(
    unit :=   findun( volume );
    _if unit <> 0 _then _(
      mapia( unit, word );
      write('БОБИНА ', volume:0, ' ИМЕЕТ НУ='); ГГ( word );
      writeln; EXIT
    _);
    writeln('БОБИНЫ ', volume:0, ' В ЗАДАЧЕ НЕТ');
    EXIT
  _);
  _if (unit < 30В) _or (unit > 67В) _then _( writeln('ОШИБКА В <НУ>'); EXIT _);
  _if unit = 40В _then _( writeln('А ВОТ ЭТОГО НЕЛЬЗЯ !'); EXIT _);
  _if buffer _then _(
    unit := unit * 4096 + 2000000В;
    volume := volume * 37В;
    code(2лс4=э050177,);
    volume := ; code(мр=);
    avail := ;
    _if volume > 4 _then _(  writeln('ОШ. В ЭКС.'); EXIT _);
    avail := trunc((avail + 31)/32);
    _case volume _of
      0: writeln('ЕСТЬ');
      1: _( writeln('НЕТ РЕСУРСА У ОС');
        writeln('ИМЕЮЩИЙСЯ РЕСУРС = ', avail:0 );
      _);
      2: _(  writeln('ЗАКАЗ > МАХ');  writeln('МАХ ЗАКАЗ = ', avail:0 ) _);
      3: writeln('УЖЕ ЗАНЯТО 12 НУ');
      4: writeln('ТАКОЙ НУ ЗАНЯТ')
    _end
  _) _else attach( volume, unit, offset );
_);

(* РЕС: дополнительный заказ памяти или трактов через Э50 0177. *)
_proced РЕС;
_var kind:alfa; status, avail:integer;
_(
  _if getcmd( kind) _then _(
    _select
      (kind = 'ТРА   '): status := 1000000В;
      (kind = 'ПАМ   '):  status := 0;
      true: _( writeln(kind, ' - ОШИБКА'); EXIT _)
    _end;
    status := sel(getnum, 0, 18) + status;
    code(=э050177,);
    status := ;
    code(мр=);
    avail := ;
    _if (status > 2) _then _(  writeln('ОШ. В ЭКС.'); EXIT _);
    _case status _of
      0: writeln('СДЕЛАНО');
      1: _( writeln('НЕТ РЕСУРСА У ОС'); writeln('ИМЕЮЩИЙСЯ РЕСУРС : ', avail:0 ) _);
      2: _( writeln('ЗАКАЗ > МАХ'); writeln('МАХ ЗАКАЗ : ', avail:0 ) _)
    _end;
    exit
  _); (* 4303 *)
  writeln('МОЖНО "ТРАК" ИЛИ "ПАМ"');
_);

(* ОТК: отключение НУ; рабочий НУ 040 защищен. *)
_proced ОТК;
_var unit:integer;
_(
  unit :=   getoct;
  _if unit = 40В _then _(  writeln('ЭТОГО ДЕЛАТЬ НЕЛЬЗЯ !'); EXIT _);
  detach( unit );
  writeln('СДЕЛАНО');
_);

(* ПАР С/З: подтверждение пароля чтения или записи на том. *)
_proced ПАР;
_var volume, pass:integer; access: alfa;
_(
  _if _not getcmd(access)  _then _(  writeln('НЕТ ПРИЗНАКА'); _GOTO 5322 _);
  volume :=   getnum;
  pass :=   getoct;
  _if (volume = 0) _or (volume > (2999)) _then _(
    writeln('ОШИБКА В НОМЕРЕ БОБИНЫ');
    _GOTO 5322
  _);
  _select
    (access = 'С     '): passwd( 1, pass, volume );
    (access = 'З     '): passwd( 0, pass, volume );
    true: _( writeln(access, '- ОШИБКА'); _GOTO 5322 _)
  _end;
  writeln('ЕСТЬ');
_);

(* МОТ: позиционирование подключенной магнитной ленты через Э72. *)
_proced МОТ;
_var unit, zone:integer;ctrl:alfa; volume:integer;
_(
  volume :=   getnum;
  zone :=   getoct;
  _if (volume = 0) _or (volume > 2047) _then _( writeln('ОШИБКА В НОМЕРЕ БОБИНЫ'); EXIT _);
  unit :=   findun( volume );
  _if (unit = 0) _then _( writeln('БОБИНЫ ', volume:0, ' В ЗАДАЧЕ НЕТ'); EXIT _);
  ctrl := '.0';
  code(2лс3=сд/-14/,2лс4=сд/-30/,2зч5=2э0725,);
  writeln('СДЕЛАНО');
_);
(*=m-*)

(* НАП: номер тома и смещение НУ; для буфера выводится его номер. *)
_proced НАП;
_var volume, unit:integer;
_(
  unit :=   getoct;
  _if (unit < 10В) _or (unit > 67В) _then _( writeln('ОШИБКА В <НУ>');  exit _);
  volume :=   volnum( unit );
  write('БОБИНА ');
  _if volume = 32767 _then  write('БУФ', bufnum:0) _else _(
    write( volume:0 );
    unit := unit * 4096;
    code(э050113=,сд/30/=);
    volume := ;
    write(' (', volume*32:0в, ')');
  _);
  writeln
_);

(* 04507. АЦПУ ОСТ: Э65 получает остаток бумаги.
   Младшие 16 бит пересчитываются множителем 192/460 в сотые метра. *)
_proced paper;
_var remain:integer; status:bitset;
_(
  code(э0650=,уи7=7э06540,);
  status := ;
  status := status _mod [0..47];
  remain := sel(status, 0, 16) * 192 _DIV 460;
  writeln('ОСТАЛОСЬ ', trunc(remain / 100):0, '.', remain _MOD 100:0, ' М. БУМАГИ');
_);

(* SYS: цикл опроса системных текстов и сигнатур.
   Числовой аргумент задает НУ и зону, буквенный - имя в тексте,
   на который указывает 76012. Пустой ответ возвращает в ПУЛЬТ. *)
_proced SYS; _label 4613;
_const rdpg32 =  001032Т; rdpg34 =  001034Т;
_var addr, number:integer;
name, word:alfa;

  (* 04541. Прочитать указанную зону в страницу 032 через Э70. *)
  _proced rdzone(addr:integer); _( addr := addr + rdpg32; code(3э0703=,) _);

  (* 04546. XOR двух слов прочитанной страницы, 065532 и 065375. *)
  _function ident:alfa;
  _(
    code(иа64000=сч1532,иа64000=ср1375,);
    ident := ;
  _);

  (* 04553. Дескриптор INPUT: страница 034 и заданный НУ/зона. *)
  _proced txtin(addr:integer; active: boolean);
  _var desc:integer;
  _(
    desc := rdpg34;
    code(3цс3=зч75211,3сч4=у076002,ав13=зч75212,);
  _);
  (*=m+*)

  (* 04565. Считать имя до шести букв, дополнить пробелами справа. *)
  _function getnam:alfa;
  _var name:alfa; pos, shift:integer;
  _(
    pos := 1;
    name := '      ';
    _while (input@ _in letter) _and (pos < 7) _do _(
      shift := (6 - pos) * 8;
      pos := pos + 1;
      ins(name, input@, shift, 8);
      get(input);
    _);
    getnam := name;
  _);

_( (* SYS *)
  4613: code(в;ф=L1213,к;); bind('? ≡377'); code(е;к;);
  _if input@ = etx _then code(пб76002=,);
  _if input@ _in digit _then _(
    addr :=   getoct;
    _if (addr < 270000C) _or (addr > 677777C) _then _(
      writeln('ОШИБКА В <НУ>');
      _goto 4613
    _);
    rdzone( addr );
    name :=   ident;
    writeln(name);
  _) _else _if input@ _in letter _then _(
    name :=   getnam;
    _if (name = 'КОНЕЦ ') _then _(  writeln('НЕЛЬЗЯ'); _goto 4613 _);
    code(сч76012=); addr := ;
    txtin( sel(addr, 0, 18), true );
    reset(input);
    _while input@ <> eot _do _(
      word :=   getnam;
      _if name = word _then _(
        get(input);
        write(word, ' - ');
        addr :=   getoct;
        get(input);
        number :=   getoct;
        mapia( addr, word );
        word := word;
        code(сд/-40/=);
        word := ;
        mapia( number, name );
        ins(word, name, 0, 32);
        write(word, ' (');
        get(input);
        number :=   getoct;
        mapia( number, word );
        ГГ( word, ')' );
        writeln;
        _goto 4613
      _) _else _while input@ <> '^' _do get(input);
      get(input)
    _); (* 4736 *)
    writeln('ИМЯ ', name, ' НЕ НАЙДЕНО');
  _) _else _( writeln(input@, ' - ОШИБКА'); _goto 4613 _);
  _goto 4613
_);
(*=m-*)

(* 04756. Выдать владельцев дисководов группы через Э65.
   Индекс системной таблицы: GROUP * 8 + DRIVE + 435. *)
_proced dskrow(group, first, last:integer);
_const c = 435;
_var drive, owner, status:integer;
_(
  _for drive := first _to  last _do write( group:4, '-', drive:1, ' ');
  writeln;
  _for drive := first _to last _do _(
    owner := group * 8 + drive + c;
    code(уи7=7э065,);
    status := ;
    owner := sel(status,0, 12);
    _if (owner < 1) _then write('  СВОБ ') _else write( owner:6, ' ');
  _);
  writeln
_);

(* ДИС: группы дисководов 0-0..0-3, 5-0..5-7, 6-4..6-7. *)
_proced ДИС;
_(
  dskrow( 0, 0, 3 ); writeln;
  dskrow( 5, 0, 7 ); writeln;
  dskrow( 6, 4, 7 );
_);

(* 05042. Выдать владельцев магнитофонов группы через Э65.
   Индекс системной таблицы: (GROUP - 3) * 8 + DRIVE + 403. *)
_proced taprow(group, first, last:integer);
_const c = 403;
_var drive, status, owner:integer;
_(
  _for drive := first _to  last _do write( group:4, '-', drive:1, ' ');
  writeln;
  _for drive := first _to last _do _(
    owner := (group - 3)*8 + drive + c;
    code(уи7=7э065,);
    status := ;
    owner := sel(status,0, 12);
    _if (owner < 1) _then write('  СВОБ ') _else write( owner:6, ' ');
  _);
  writeln
_);

(* МАГ: группы магнитофонов 3-0..3-3 и 4-0..4-3. *)
_proced МАГ;
_(
  taprow( 3, 0, 3 );  writeln;
  taprow( 4, 0, 3 );
_);

(* ВЫБ: удалить задачу из каталога по номеру канала, Э62 0100. *)
_proced ВЫБ;
_var channel:integer;
_(
  channel :=   getoct;
  code(=уи15,);
  channel := (77700000C);
  code(э062100=,);
  writeln('ЕСТЬ');
_);

(* ИНФ: встроенная справка по пятнадцати основным приказам. *)
_proced ИНФ;
_(

  writeln('ИСПОЛНЯЮТСЯ ПРИКАЗЫ :', lf,
  ' 1. БОБ  [<НБОБ> [<НУ>]]      - ВЫДАЧА <НУ> БОБИН И ИХ ПРИЕМ', lf,
  ' 2. ОТК  <НУ>                 - ОТКАЗ ОТ <НУ>', lf,
  ' 3. ПАР  С/З <НБОБ> <ПАР>     - ПОДТВЕРЖДЕНИЕ ПАРОЛЯ НА БОБИНУ', lf,
  ' 4. МОТ  <НБОБ>  <НЗОН>       - ПОДВОД МЛ К ЗАДАННОЙ ЗОНЕ', lf,
  ' 5. НАП  <НУ>                 - ОПРОС <НУ>', lf,
  ' 6. ТРАК  [ <НУ> ]            - ОСВОБОЖДЕНИЕ ЗАНЯТЫХ ТРАКТОВ', lf,
  ' 7. РЕС  ТРАК/ПАМ  <РЕС>      - ДОЗАКАЗ ТРАКТОВ И ПАМЯТИ', lf,
  ' 8. ОБЛ <ИМЯ>/<ШИФР> <НУ> [З] - ПРИНЯТИЕ ОБЛАСТИ АРХИВА', lf,
  ' 9. ВСТ   <НСТР>              - ВСТАВКА ТЕКСТА ПОСЛЕ ЗАДАННОЙ СТРОКИ', lf,
  '10. НАЙ [N1:N2] ''<ОБРАЗЕЦ>''   - ПОИСК ОБРАЗЦА В ТЕКСТЕ', lf,
  '11. СПИС  [НАЙ]/<N1:N2>       - СПИСОК НАЙДЕННЫХ СТРОК/ДИАПАЗОНА СТРОК', lf,
  '12. АЦПУ  [ОСТ]               - СЧИТЫВАНИЕ БУФЕРА/ОСТАВШИЙСЯ РЕСУРС', lf,
  '13. МАГ                       - ЗАНЯТОСТЬ МАГНИТОФОНОВ', lf,
  '14. ДИС                       - ЗАНЯТОСТЬ ДИСКОВОДОВ', lf,
  '15. ВЫБ  <НОМ. КАНАЛА>        - ВЫБРОС ЗАДАЧИ ИЗ КАТАЛОГА');
_);

(* 05236. Инициализация, копирование параметров из НАБЛ, разбор вызова.
   05322 - запрос нового приказа; 05324 - разбор уже введенного ответа;
   05333 - диспетчер. Пустой приказ завершает работу через 76002. *)
_(
  txtbuf := 4096;
  column := 1;
  unread := true;
  hits[0] := 0;
  cell := ptr(57756В);
  saved := cell@;
  cell := ptr(57757В);
  work := cell@;
  _if (work = 0) _then  sep := '≡175' _else sep := chr(work);
  work := (350000260000C);
  code(зч75203=зч75223,);
  rewrite(output);
  argsrc := ptr(57640В);
  argdst := ptr(70001В);
  argdst@ := argsrc@;
  _for work := 1 _to 6 _do get(input);
  hascmd := getcmd(cmd);
  direct := cmd = 'A     ';
  _if direct _then _goto 5333;
  writeln('ПАСКАЛЬ-СЕРВИС');
  _if getcmd(cmd) _then _goto 5333;
  5322: inbuf( 70000В );
  code(в;ф=L1213,к;); bind('::≡146≡146≡172'); code(е;к;);
  5324: _if _not getcmd( cmd) _then _( writeln('ВЫХОД В ПУЛЬТ'); code(пб76002=,) _);
  5333: _select
    ('ВРЕ   ' = cmd): ВРЕ;
    ('Н     ' = cmd) _or
    ('НАЙ   ' = cmd): НАЙ( hits, sep );
    ('С     ' = cmd): list( hits, sep );
    ('ВСТ   ' = cmd) _or
    ('В     ' = cmd): ВСТ( sep );
    ('КОН   ' = cmd) _or
    ('F     ' = cmd): code(э062=);
    (cmd = 'ПОЛ   ') _or
    (cmd = 'П     '): _(
      column :=   getnum;
      write('ПОЛЕ ВЫДАЧИ: ');
      _if column = 0 _then  column := 1;
      writeln(column:0, ' - ', column + 78:0 );
    _);
    ('АЦП   ' = cmd) _or
    ('А     ' = cmd):_if (input@ = 'О') _then paper _else  prtout( 0 );
    ('ТРА   ' = cmd): ТРА;
    ('БОБ   ' = cmd): БОБ;
    ('РЕС   ' = cmd): РЕС;
    ('ОТК   ' = cmd): ОТК;
    ('ПАР   ' = cmd): ПАР;
    ('МОТ   ' = cmd): МОТ;
    ('НАП   ' = cmd): НАП;
    ('SУS   ' = cmd): SYS;
    ('ОБЛ   ' = cmd): ОБЛ;
    ('МАГ   ' = cmd): МАГ;
    ('ВЫБ   ' = cmd): ВЫБ;
    ('ДИС   ' = cmd): ДИС;
    ('ПУЛ   ' = cmd):
    code(пбL5500=,c;D5476:10000000400040,D5477:7777,к;L5500:э070D5476=,счD5477=зч37,пб40=,);
    ('ИНФ   ' = cmd): ИНФ;
    ('ППН   ' = cmd): _( work := 1; code(зч76013=) _);
    ('ПП    ' = cmd): _( work := 3; code(зч76013=) _);
    ('ПА    ' = cmd): _( work := 2; code(зч76013=) _);
    ('НП    ' = cmd): _( work := 0; code(зч76013=) _);
    true:  writeln('НЕТ ПРИКАЗА ', cmd)
  _end; _goto 5322
_).
