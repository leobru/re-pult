# re-pult: disassembly of the BESM-6 ПУЛЬТ interactive system.
#
#   make images     extract the catalog entries (zone 01000) of 2248 and 2148
#                   into images/<vol>/<NAME>.bin, list in images-<vol>.txt
#   make traces     run every sessions/*.txt under `dispak -t -t` and split the
#                   executed addresses per catalog image (tools/phasetrace.py)
#   make listings   build/<NAME>.lst for every image that executed in a session,
#                   disassembled at the address it runs at
#   make diff       catalog entries that differ between 2148 and 2248
#   make vol        ~/.besm6/2250: 2248 with patches-2248.txt applied; pult.b6
#                   boots from it (listings still come from the original 2248)
#
# syms/<NAME>.sym (disbesm6 symbol table) is used when present.

DIS      ?= $(HOME)/git/leobru/dispak-tools/disbesm6
VOL      ?= 2248
SESSIONS := $(basename $(notdir $(wildcard sessions/*.txt)))
STAMPS   := $(SESSIONS:%=build/t-%/.done)
PVOL     := $(HOME)/.besm6/2250
# 7.25 MB geometry: offsets set by Э50 0112 (ФОРТ) are then taken as given
DISPAKFLAGS ?= --725

all: listings

images: images/2248/.done images/2148/.done
images/%/.done: tools/extract.py tools/gost.py
	tools/extract.py $* > images-$*.txt
	touch $@

vol: $(PVOL)
$(PVOL): patches-2248.txt tools/patchvol.py
	tools/patchvol.py patches-2248.txt 2248 $@

traces: $(STAMPS)
build/t-%/.done: sessions/%.txt pult.b6 $(PVOL) tools/phasetrace.py images/$(VOL)/.done
	rm -rf build/t-$* $(HOME)/.besm6/input_queue; mkdir -p build
	timeout 300 dispak $(DISPAKFLAGS) -t -t -q pult.b6 < $< 2>&1 | \
	    tools/phasetrace.py build/t-$* images-$(VOL).txt > build/t-$*.summary
	touch $@

# Images seen in any session (evaluated after the traces exist).
listings: traces
	@$(MAKE) --no-print-directory $(patsubst %,build/%.lst,$(sort \
	    $(basename $(notdir $(wildcard build/t-*/*.trace)))))

build/%.trace: $(STAMPS)
	cat build/t-*/$*.trace 2>/dev/null | sort -u > $@

build/%.lst: build/%.trace images/$(VOL)/.done $(wildcard syms/*.sym)
	load=$$(cat build/t-*/$*.load | sort | uniq -c | sort -rn | awk 'NR==1{print $$2}'); \
	$(DIS) -b -a$$load -e$$load --trace=build/$*.trace \
	    $(if $(wildcard syms/$*.sym),-n syms/$*.sym) images/$(VOL)/$*.bin > $@

# ПУСК has explicit static entries and data boundaries; no emulator run needed.
pusk: build/ПУСК.lst build/ПУСК.dump
build/ПУСК.lst: images/$(VOL)/.done syms/ПУСК.sym
	mkdir -p build
	$(DIS) -b -a0 -e40 -n syms/ПУСК.sym images/$(VOL)/ПУСК.bin > $@

build/ПУСК.dump: images/$(VOL)/.done
	mkdir -p build
	besmtool dump $(VOL) --start=01040 --length=1 > $@

.PHONY: pusk

# НАБЛ uses M10 = 056000; static entries include the input trampoline at 57037.
nabl: build/НАБЛ.lst build/НАБЛ.dump
build/НАБЛ.lst: images/$(VOL)/.done syms/НАБЛ.sym
	mkdir -p build
	$(DIS) -b -a56000 -e56010 -n syms/НАБЛ.sym images/$(VOL)/НАБЛ.bin > $@

build/НАБЛ.dump: images/$(VOL)/.done
	mkdir -p build
	besmtool dump $(VOL) --start=01041 --length=1 > $@

.PHONY: nabl

# СБОЙ is the resident page at 076000; entries and work areas are explicit.
sboy: build/СБОЙ.lst build/СБОЙ.dump
build/СБОЙ.lst: images/$(VOL)/.done syms/СБОЙ.sym
	mkdir -p build
	$(DIS) -b -a76000 -e76000 -n syms/СБОЙ.sym images/$(VOL)/СБОЙ.bin > $@

build/СБОЙ.dump: images/$(VOL)/.done
	mkdir -p build
	besmtool dump $(VOL) --start=01035 --length=1 > $@

.PHONY: sboy

# ДАЙ has explicit command entries, data and batch-job templates.
dai: build/ДАЙ.lst build/ДАЙ.dump
build/ДАЙ.lst: images/$(VOL)/.done syms/ДАЙ.sym
	mkdir -p build
	$(DIS) -b -a0 -e7 -n syms/ДАЙ.sym images/$(VOL)/ДАЙ.bin > $@

build/ДАЙ.dump: images/$(VOL)/.done
	mkdir -p build
	besmtool dump $(VOL) --start=01005 --length=1 > $@

.PHONY: dai

# АДСИС is the Pascal runtime page at 074000.
adsis: build/АДСИС.lst build/АДСИС.dump
build/АДСИС.lst: images/$(VOL)/.done syms/АДСИС.sym
	mkdir -p build
	$(DIS) -b -a74000 -e74003 -n syms/АДСИС.sym images/$(VOL)/АДСИС.bin > $@

build/АДСИС.dump: images/$(VOL)/.done
	mkdir -p build
	besmtool dump $(VOL) --start=01006 --length=1 > $@

.PHONY: adsis

# АВТПАК has a relative driver at 052000 and a packet reader at 004000.
avtpak: build/АВТПАК.lst build/АВТПАК-пакет.lst build/АВТПАК.dump
build/АВТПАК.lst: images/$(VOL)/.done syms/АВТПАК.sym
	mkdir -p build
	$(DIS) -b -a52000 -e52010 -e52011 -n syms/АВТПАК.sym images/$(VOL)/АВТПАК.bin > $@

build/АВТПАК-пакет.lst: images/$(VOL)/.done syms/АВТПАК-пакет.sym
	mkdir -p build
	$(DIS) -b -a4000 -e4040 -n syms/АВТПАК-пакет.sym images/$(VOL)/АВТПАК.bin > $@

build/АВТПАК.dump: images/$(VOL)/.done
	mkdir -p build
	besmtool dump $(VOL) --start=01047 --length=1 > $@

.PHONY: avtpak

# The callable ПУЛЬТ generator and the retained ПУЛЬТФ image.
launchers: build/ПУЛЬТ.lst build/ПУЛЬТФ.lst build/ПУЛЬТ.dump build/ПУЛЬТФ.dump
build/ПУЛЬТ.lst: images/$(VOL)/.done syms/ПУЛЬТ.sym
	mkdir -p build
	$(DIS) -b -a0 -e7 -n syms/ПУЛЬТ.sym images/$(VOL)/ПУЛЬТ.bin > $@

build/ПУЛЬТФ.lst: images/$(VOL)/.done syms/ПУЛЬТФ.sym
	mkdir -p build
	$(DIS) -b -a0 -e10 -n syms/ПУЛЬТФ.sym images/$(VOL)/ПУЛЬТФ.bin > $@

build/ПУЛЬТ.dump: images/$(VOL)/.done
	mkdir -p build
	besmtool dump $(VOL) --start=01002 --length=1 > $@

build/ПУЛЬТФ.dump: images/$(VOL)/.done
	mkdir -p build
	besmtool dump $(VOL) --start=01004 --length=1 > $@

.PHONY: launchers

# АЦПУК loads the monitor's formatter quarter dynamically from drum 27.
acpuk: build/АЦПУК.lst build/АЦПУК.dump
build/АЦПУК.lst: images/$(VOL)/.done syms/АЦПУК.sym
	mkdir -p build
	$(DIS) -b -a74000 -e74000 -n syms/АЦПУК.sym images/$(VOL)/АЦПУК.bin > $@

build/АЦПУК.dump: images/$(VOL)/.done
	mkdir -p build
	besmtool dump $(VOL) --start=01003 --length=1 > $@

.PHONY: acpuk

# СПИС shares two pages between the С and Р commands.
spis: build/СПИС.lst build/СПИС.dump
build/СПИС.lst: images/$(VOL)/.done syms/СПИС.sym
	mkdir -p build
	$(DIS) -b -a0 -e10 -e2010 -n syms/СПИС.sym images/$(VOL)/СПИС.bin > $@

build/СПИС.dump: images/$(VOL)/.done
	mkdir -p build
	besmtool dump $(VOL) --start=01045 --length=2 > $@

.PHONY: spis

# БАВТ is the command dispatcher and launcher in page 33.
bavt: build/БАВТ.lst build/БАВТ.dump
build/БАВТ.lst: images/$(VOL)/.done syms/БАВТ.sym
	mkdir -p build
	$(DIS) -b -a66000 -e66007 -n syms/БАВТ.sym images/$(VOL)/БАВТ.bin > $@

build/БАВТ.dump: images/$(VOL)/.done
	mkdir -p build
	besmtool dump $(VOL) --start=01051 --length=1 > $@

.PHONY: bavt

# ОТЛ is position independent; the default base is 050000 (page 024).
otl: build/ОТЛ.lst build/ОТЛ.dump
build/ОТЛ.lst: images/$(VOL)/.done syms/ОТЛ.sym
	mkdir -p build
	$(DIS) -b -a50000 -e50010 -n syms/ОТЛ.sym images/$(VOL)/ОТЛ.bin > $@

build/ОТЛ.dump: images/$(VOL)/.done
	mkdir -p build
	besmtool dump $(VOL) --start=01052 --length=3 > $@

.PHONY: otl

dzhin: build/ДЖИП.lst build/ДЖИП.dump
build/ДЖИП.lst: images/$(VOL)/.done syms/ДЖИП.sym
	mkdir -p build
	$(DIS) -b -a0 -e7 -n syms/ДЖИП.sym images/$(VOL)/ДЖИП.bin > $@

build/ДЖИП.dump: images/$(VOL)/.done
	mkdir -p build
	besmtool dump $(VOL) --start=01070 --length=1 > $@

.PHONY: dzhin

diff: images
	@for f in images/2248/*.bin; do n=$$(basename $$f); \
	  cmp -s $$f images/2148/$$n || echo "differs: $$n"; done

clean:
	rm -rf build

.PHONY: all images vol traces listings diff clean
.PRECIOUS: build/%.trace
# dispak sessions share ~/.besm6/input_queue
.NOTPARALLEL:

# Relocated PULT and Pascal archives on volume 2068. The original pult.b6
# and 2250 reconstruction above remain available for disassembly sessions.
PYTHON       ?= python3
DISPAK       ?= dispak
SOURCE_DISKS ?= /usr/local/share/besm6
SYSTEM_VOLUME ?= 2248
VOLUME_DIR   := build/volumes
INSTALL_DISKS ?= $(HOME)/.besm6

2068: $(VOLUME_DIR)/2068 $(VOLUME_DIR)/2068.json

$(VOLUME_DIR)/2148: $(SOURCE_DISKS)/2148
	mkdir -p $(VOLUME_DIR)
	cp -fp $< $@

$(VOLUME_DIR)/2248: $(SOURCE_DISKS)/2248
	mkdir -p $(VOLUME_DIR)
	cp -fp $< $@

$(VOLUME_DIR)/2068: tools/make2068.py tools/volume2068.json $(VOLUME_DIR)/2148 $(VOLUME_DIR)/2248
	$(PYTHON) tools/make2068.py --2148 $(VOLUME_DIR)/2148 --2248 $(VOLUME_DIR)/2248 --output $@

$(VOLUME_DIR)/2068.json: $(VOLUME_DIR)/2068
	@test -f $@ || $(PYTHON) tools/make2068.py --2148 $(VOLUME_DIR)/2148 --2248 $(VOLUME_DIR)/2248 --output $(VOLUME_DIR)/2068

check2068: 2068
	$(PYTHON) tests/pult-volume.py "$(DISPAK)" $(VOLUME_DIR)
	$(PYTHON) tests/pascal-segments.py --dispak "$(DISPAK)" --volumes $(VOLUME_DIR)

checksegments: 2068
	$(PYTHON) tests/pascal-segments.py --dispak "$(DISPAK)" --volumes $(VOLUME_DIR)

checkadsis: 2068
	$(PYTHON) tests/adsis.py --dispak "$(DISPAK)" --volumes $(VOLUME_DIR)

.PHONY: checkadsis

build/pult2068/2148 build/pult2068/2248: build/pult2068/%: $(VOLUME_DIR)/%
	mkdir -p build/pult2068
	cp -p $< $@
	chmod u+w $@

build/pult2068/2068: $(VOLUME_DIR)/2068
	mkdir -p build/pult2068
	cp -p $< $@
	chmod u+w $@

pult2068: 2068 build/pult2068/$(SYSTEM_VOLUME) build/pult2068/2068
	sed 's/57(2248-371)/57($(SYSTEM_VOLUME)-371)/' pult2068.b6 > build/pult2068/pult.b6
	$(DISPAK) $(DISPAKFLAGS) --path=$(abspath build/pult2068):$(abspath $(SOURCE_DISKS)) build/pult2068/pult.b6

.PHONY: 2068 check2068 checksegments pult2068

# Preserve an existing installed image and its provenance as a pair.
install2068: 2068
	mkdir -p "$(INSTALL_DISKS)"
	@if test -e "$(INSTALL_DISKS)/2068"; then \
	    echo "$(INSTALL_DISKS)/2068 already exists; left unchanged"; \
	else \
	    cp $(VOLUME_DIR)/2068 $(VOLUME_DIR)/2068.json "$(INSTALL_DISKS)/"; \
	fi

.PHONY: install2068

# Exact reconstruction of the November 1988 СЕРВИС with the May compiler.
checkservic: 2068
	$(PYTHON) tests/servic.py --dispak "$(DISPAK)" --volumes $(VOLUME_DIR)

.PHONY: checkservic

# ЧИСТКА: Pascal declaration/reference analysis, image 10.12.82.
chistka: build/ЧИСТКА-static.lst build/ЧИСТКА.dump
build/ЧИСТКА-static.lst: images/$(VOL)/.done syms/ЧИСТКА.sym
	mkdir -p build
	$(DIS) -b -a0 -e7 -n syms/ЧИСТКА.sym images/$(VOL)/ЧИСТКА.bin > $@

build/ЧИСТКА.dump: images/$(VOL)/.done
	mkdir -p build
	besmtool dump $(VOL) --start=01060 --length=3 > $@

checkchistka: 2068
	$(PYTHON) tests/chistka.py --dispak "$(DISPAK)"

.PHONY: chistka checkchistka

# ЭХОЛОТ: Pascal storage-depth and compiled-code analysis, image 24.10.86.
echolot: build/ЭХОЛОТ-static.lst build/ЭХОЛОТ.dump
build/ЭХОЛОТ-static.lst: images/$(VOL)/.done syms/ЭХОЛОТ.sym
	mkdir -p build
	$(DIS) -b -a0 -e7 -n syms/ЭХОЛОТ.sym images/$(VOL)/ЭХОЛОТ.bin > $@

build/ЭХОЛОТ.dump: images/$(VOL)/.done
	mkdir -p build
	besmtool dump $(VOL) --start=01064 --length=4 > $@

checkecholot: 2068
	$(PYTHON) tests/echolot.py --dispak "$(DISPAK)"

.PHONY: echolot checkecholot

# Readable Pascal reconstructions: compilation and historical behavior probes.
# A separate --exact option rejects all binary differences (currently expected).
checkanalyzers: 2068
	$(PYTHON) tests/rebuild-analyzers.py --dispak "$(DISPAK)" --disassembler "$(DIS)"

.PHONY: checkanalyzers
