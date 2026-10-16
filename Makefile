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

diff: images
	@for f in images/2248/*.bin; do n=$$(basename $$f); \
	  cmp -s $$f images/2148/$$n || echo "differs: $$n"; done

clean:
	rm -rf build

.PHONY: all images vol traces listings diff clean
.PRECIOUS: build/%.trace
# dispak sessions share ~/.besm6/input_queue
.NOTPARALLEL:
