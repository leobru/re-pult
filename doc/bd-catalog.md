# Zone 030: МАРС/БАНДИТ database catalog

All addresses, units, zones, counts in the tables, and raw words below are
octal. There are **21 entries** (decimal). Zone 01030 on 2148 and 2248 and
zone 030 on reconstructed 2068 contain identical payloads.

## Successful catalog listing

```text
арх сисбиб,40,0
bd open ктлBD
bd ктл
```

The `BD` suffix of **КТЛBD** must be Latin. Its GOST display is **КТЛВD**.
It is distinct from **КТЛБД**, which names another database at 40:0651.
Opening КТЛBD selects the catalog itself at **40:0030**. The emulator
successfully prints all 21 names; answer the `ИДТИ?` pagination prompt with
an empty input line. No disk patches or additional database zones are needed
for this listing. Listed database references need not themselves be mounted
or present on reconstructed 2068.

## Physical layout of this block

| Zone word(s) | Value / interpretation |
|---|---|
| 0000 | `0000000001400030`: one zone, logical unit 40, initial zone 0030 |
| 0001 | `0000000003446031`: service word, not decoded here |
| 0002 | Zero; the first-block validation requires this word to be zero |
| 0003 | `0000000000203677`: directory offset 1677, allocated length 0101 words |
| 0004–0031 | Record-slot table: one packed descriptor per slot |
| 0032–1622 | Space between slot table and live record bodies; contains stale words, including old code/text, not extra live catalog entries |
| 1623–1676 | 22 two-word record bodies described by the slots; slot order and physical body order differ |
| 1677–1750 | 21 `(six-character GOST name, record reference)` pairs, 052 words |
| 1751–1775 | Unused directory allocation, zero in this image |
| 1776 | `052`: number of used directory words, not number of names |
| 1777 | `01571`: footer service value; equals the size of gap 0032–1622, consistent with a free-word count (allocator updates not traced here) |

Directory allocation 1677 + 0101 reaches the end of the 02000-word block.
The directory is bounded by its count, not by the first zero-name word.
The directory leaves slot **017** unreferenced; that slot still has a record
body at **1651–1652**. Do not invent a directory name for it.

## Address and record fields

The used part of a directory reference is:

```text
reference = (slot << 10) | block
slot      = (reference & 03776000) >> 10
block     = reference & 01777
```

Here shifts are **10 decimal bits**. All directory references in this block
have `block = 0`. Thus `010000` refers to slot 004 of this first block.
The corresponding slot word encodes:

```text
body_offset = slot_word & 01777
body_words  = (slot_word & 03776000) >> 10
```

All named catalog records here occupy **two words**. Their first word is
record metadata, retained verbatim by the decoder; its date/author/flag
bit fields have not been established by this OPEN trace. The second word
is the database location:

```text
zone  = location & 07777
unit  = (location >> 12) & 077
zones = location >> 18
```

The latter shifts are **12 and 18 decimal bits**. The zone/unit pair is a
logical address, subject to the mounted unit's offset. The decoder handles
this single-block catalog and its two-word location records; it deliberately
rejects unimplemented multi-block or linked-record cases.

## Trace evidence

The captured `BD OPEN КТЛБД` trace shows the complete lookup mechanism,
including the later failure reading the database it names:

1. BD reads zone 027 into memory 074000, verifies the БАНДИТ signature at
   074001, supplies buffer base 070000, and passes the requested name in
   resident cell 074010.
2. **74273–74317:** БАНДИТ obtains its initial database descriptor from
   resident constant **74043 = 0000000001400030**, and reads unit 40
   zone 030 into memory 070000.
3. **74321–74322:** `(memory[070000] XOR expected descriptor) OR
   memory[070002]` must be zero. This check accepts the block in zone 030.
4. **74323–74331:** mask word 003 by 01777 to find directory 071677;
   read used-directory length 052 from 071776.
5. **74742–74747:** compare requested name with successive directory names,
   advancing by two words. КТЛБД matches at 071677; its reference is 010000.
6. **74156–74203:** decode block 0 / slot 004; load the slot descriptor at
   070004, `05675`, giving record offset 1675 and length 2.
7. **74775–75005:** skip the metadata word at 071675 and copy the data word
   at **071676 = 0000000001400651** into resident database descriptor 074026.
8. **74304–74322:** decode that location and read unit 40 zone 0651. The
   blank reconstructed zone fails first-block validation, producing
   «ЗАТЕРТ 1Й ЛИСТ БД».

The separate successful `BD OPEN КТЛBD` trace follows the same directory
scan to **071737**, whose reference **052000** selects slot **025**.
The slot descriptor is **05633**, pointing to words **1633–1634**;
word 1634 is **0000000001400030**, selecting this catalog block itself.
`BD КТЛ` then enumerates names using the resident routines at
**74050–74105**. The full terminal list agrees with the host decoder below.

## Decoded catalog

All numbers except the entry count are octal.

Entries: 21. Directory starts at 1677, length 052 words.

| Name (GOST display) | Unit | First zone | Zones | Slot | Record words |
|---|---|---|---|---|---|
| КТЛБД | 40 | 0651 | 001 | 004 | 1675–1676 |
| БД7154 | 51 | 0061 | 005 | 007 | 1673–1674 |
| БДО | 51 | 0746 | 001 | 010 | 1671–1672 |
| БАЗА | 56 | 0537 | 001 | 011 | 1667–1670 |
| С | 42 | 1323 | 001 | 006 | 1665–1666 |
| ПИРИН | 40 | 0242 | 001 | 012 | 1663–1664 |
| БАЗ | 56 | 0554 | 002 | 013 | 1661–1662 |
| FFА | 30 | 0020 | 010 | 015 | 1657–1660 |
| SIМ | 30 | 0020 | 010 | 016 | 1655–1656 |
| 0000Р0 | 30 | 0020 | 010 | 014 | 1653–1654 |
| НОВАЯ | 30 | 0020 | 010 | 020 | 1647–1650 |
| БУФ | 27 | 0000 | 020 | 005 | 1645–1646 |
| БУФ1 | 30 | 0020 | 010 | 021 | 1643–1644 |
| БПИР | 40 | 0674 | 004 | 022 | 1641–1642 |
| БДЛОТ | 51 | 1172 | 005 | 024 | 1637–1640 |
| БДФОЙ | 51 | 0601 | 001 | 026 | 1635–1636 |
| КТЛВD | 40 | 0030 | 001 | 025 | 1633–1634 |
| ТУФТА | 51 | 0753 | 002 | 027 | 1631–1632 |
| ЧИСЛА | 54 | 0145 | 015 | 023 | 1627–1630 |
| БПАКП | 30 | 0007 | 001 | 030 | 1625–1626 |
| ВОСЬМР | 30 | 0004 | 002 | 031 | 1623–1624 |

The unusual name **0000Р0** is printed that way by ПУЛЬТ too. Its raw name
word is **0000000000030000**, preserved without an inferred replacement.
`FFА` and `SIМ` use the Cyrillic display of shared GOST letter codes;
Latin input `FFA` and `SIM` denotes the same words.

## Reproduction and checks

```sh
python3 tools/bdcatalog.py 2148 --zone 01030
python3 tools/bdcatalog.py 2248 --zone 01030
python3 tools/bdcatalog.py --image build/volumes/2068 --zone 030
python3 tools/bdcatalog.py --image build/volumes/2068 --zone 030 --json
```

The JSON includes raw names, references, slot/body offsets, metadata and
location words, so field interpretations can be reviewed independently.
Outputs from all three images compare identical. The isolated emulator
captures are in `build/bd-catalog/trace.txt` (Cyrillic suffix) and
`build/bd-catalog/open-latin/{output,trace}.txt` (Latin suffix).
`tests/pult-volume.py` exercises the successful OPEN/list sequence and
requires reads of zones 027 and 030, with no read of 0651.
