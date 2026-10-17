# АЛГ: verified file compilation and execution

On reconstructed 2068, АЛГ successfully compiles and executes a file created
by ПУЛЬТ in `сис алг` mode. The test program prints **123** to the terminal
and returns to the ПУЛЬТ command loop without an АВОСТ.

## Creating the file

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

## Regression coverage

`tests/pult-volume.py` creates `АТЕСТ` in the private archive using exactly
this terminal-input path, invokes `алг атест`, and requires the terminal
result `123` and no АВОСТ. Its trace also checks the translator read through
unit 57 zone 015 and the physical read from drum 22 track 034.
Run with `make check2068 DISPAK=/path/to/dispak` outside the sandbox.
The source disks are copied before execution and checked unchanged afterward.

This establishes compilation and execution of the small output program;
it does not establish complete ALGOL language or runtime coverage.
