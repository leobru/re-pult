# АЛГ: verified file compilation and execution

On reconstructed 2068, АЛГ successfully compiles and executes a file created
by ПУЛЬТ in `сис алг` mode. The test program prints **123** to the terminal
and returns to the ПУЛЬТ command loop without an АВОСТ.

## Creating the file

The runnable source-entry fixture is [tests/algol-shch.txt](../tests/algol-shch.txt).
It selects the existing ВАСЯ archive on unit 50, creates АТЕСТ, and runs it.
The current fixture prints four times arctan(1), approximately π; the
minimal recipe below prints 123.
The file contains a real ETX byte after `//` and the required trailing
space after `_end`; preserve both when editing. The regression test reads
this file directly. Create the private archive first as shown below.

With a private writable user archive on unit 50, zone 0100:

```text
дай новарх,50,100,вася
арх вася,50,100,100
сис алг
з тест(1)=тт
_begin output(`Щ',`z4d',123); _end 
//
алг тест
конец
```

The final `//` of the text must be followed by **ETX** (byte 03) to finish
terminal input. In the automated test it is sent as `//\x03\n`, not as
literal backslash characters. Keep the space after `_begin` and after
`_end`: ordinary input line feeds do not substitute for the reserved-word
separator in this path. No raw GOST payload is injected into the archive;
`з …=тт` performs the encoding and saving.

`Щ` is OUTPUT's special parameter enabling a terminal copy. Without it,
``output(`z4d',123)`` can run successfully while sending the value only to
the printout, which is not evidence of missing execution.

## Manual references

The searchable [user guide](PULT-User.md) describes:

- [PDF 18, printed p. 32](PULT-User.md#pdf-018): `СИС АЛГ` selects the
  editor/archive encoding independently of translator invocation.
- [PDF 22, printed p. 41](PULT-User.md#pdf-022): `З …=ТТ` opens terminal
  input, terminated by `//` and ETX.
- [PDF 39, printed p. 74](PULT-User.md#pdf-039): `АЛГ <имя-массива>` starts
  translation and execution; `(Т)` selects translation only.
- [PDF 41, printed p. 78](PULT-User.md#pdf-041): OUTPUT parameter `Щ`
  requests output to both printer and terminal.

## Terminal data input

The user guide, [§21.3, printed pp. 74–76](PULT-User.md#pdf-039),
specifies the library procedure `IN(variable_or_array, prompt)` for terminal
input. It prints `ДАЙ` followed by the prompt and accepts data in ALGOL-60
notation, ending with `;`. Array elements are separated by commas;
Boolean values are `1` and `0`; the exponent character ⏨ is typed as `_Ю`.
The procedure does not work in batch mode and does not check array bounds.

An example adapted to the source-entry syntax is:

```text
_БИБ : IN;
_begin _real X;
IN(X,`ВВОД X');
output(`Щ',`z4d',X);
_end
```

The expected exchange described by the guide is `ДАЙ ВВОД X`, followed by
the user's `123;`. This is a historical recipe, not a passing regression:
with either 2248 or 2148 on unit 57, compiling this example reports
`В БИБЛИОТЕКЕ НЕТ АЛГОРИММА С ИМЕНЕМ IN` before execution. Merely calling
`IN` without the library directive produces an undeclared-identifier error.
Keep a space after `_БИБ` in this input path; `_БИБ:` instead produces a
construction error before library lookup.

[§21.4, printed pp. 76–78](PULT-User.md#pdf-040) also describes
`INTEL(variable_or_array)`: in batch mode it acts as `INPUT`; in interactive
mode it takes a prompt comment from a prepared data group, ignores that
group's values, and opens terminal input. Its Boolean values are `T` and
`F`, and the last portion of input ends with `;`. The manual example
explicitly declares `PROCEDURE INTEL` but omits its body. Looking up
`INTEL` through `_БИБ` on 2148 also reports that the algorithm is absent.
Neither terminal-input procedure has yet been demonstrated executing in
this reconstruction.

The complete [standard-library catalog and `_БИБ` lookup](algol-library.md)
lists all 182 names with their addresses and dependencies. The library is
identical on 2148 and 2248; its catalog is in zone 0320. Initialization
reads zones 0320–0321 through physical drum 21 tracks 020–021.
`IN` and `INTEL` are absent, although
`READ`, `GET`, and `TEXTINPUT` are present; their presence alone does not
establish terminal-input support.

Passing `Щ` to standard `INPUT` does not enable terminal input in the
tested 2248 translator. `INPUT(`Щ',X)` is rejected during compilation as
incorrect use of the first parameter; `INPUT(X,`Щ')` is rejected for the
second parameter. `INPUT(`Щ',`z4d',X)` is rejected for both string
parameters. These probes do not reach execution or open terminal input.

## Regression coverage

`tests/pult-volume.py` creates `АТЕСТ` in the private archive using exactly
this terminal-input path, invokes `алг атест`, and requires the terminal
result prefix `3.14159265358` and no АВОСТ. Its trace also checks the translator read through
unit 57 zone 015 and the physical read from drum 22 track 034.
Run with `make check2068 DISPAK=/path/to/dispak` outside the sandbox.
The source disks are copied before execution and checked unchanged afterward.

This establishes compilation and execution of the small output program;
it does not establish complete ALGOL language or runtime coverage.
