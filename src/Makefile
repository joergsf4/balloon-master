DEVKITSMS ?= /opt/devkitSMS
SMSLIB_INCDIR = $(DEVKITSMS)/SMSlib/src
SMSLIB_LIB    = $(DEVKITSMS)/SMSlib/SMSlib.lib
CRT0          = $(DEVKITSMS)/crt0/crt0_sms.rel
OUT           = ../out
TARGET        = $(OUT)/rom

CC      = sdcc
CFLAGS  = -mz80 -I. -I$(SMSLIB_INCDIR) -I../res/generated --peep-file $(SMSLIB_INCDIR)/peep-rules.txt
CFLAGS += $(if $(LEVEL_COLS),-DLEVEL_COLS=$(LEVEL_COLS))
CFLAGS += $(if $(AUTOPLAY),-DAUTOPLAY)
CFLAGS += $(if $(START_WORLD),-DSTART_WORLD=$(START_WORLD))
CFLAGS += $(if $(FORCE_KIND),-DFORCE_KIND=$(FORCE_KIND))
CFLAGS += $(if $(GODMODE),-DGODMODE)
CFLAGS += $(if $(TEST_DIE_AT),-DTEST_DIE_AT=$(TEST_DIE_AT))
# ROM-Bänke ab 2: bank<N>.c (Titelbild = 2, Welten = 3, 4, ...) liegen als Segment BANK<N> bei <N>8000 (virtuelle Adresse)
BANKNUMS := $(sort $(patsubst bank%.c,%,$(wildcard bank?.c)))
BANKOBJS := $(foreach n,$(BANKNUMS),$(OUT)/bank$(n).rel)
LDFLAGS = -mz80 --no-std-crt0 --data-loc 0xC000 $(foreach n,$(BANKNUMS),-Wl-b_BANK$(n)=0x$(n)8000)

SRCS = main.c sound.c
OBJS = $(addprefix $(OUT)/,$(SRCS:.c=.rel))

all: $(TARGET).sms

$(OBJS): $(OUT)/%.rel: %.c ../res/generated/assets.h sound.h worlds_gen.h world.h music_data.h
	$(CC) $(CFLAGS) -c -o $@ $<

# .ihx immer neu linken: SDCC schreibt sie auch bei Linker-Fehlern.
.PHONY: $(TARGET).ihx
$(TARGET).ihx: $(OBJS) $(BANKOBJS)
	$(CC) $(LDFLAGS) -o $@ $(CRT0) $(SMSLIB_LIB) $(OBJS) $(BANKOBJS)

# Titelbild und Welten (von tools/make_title.py bzw. tools/gen_assets.py erzeugt): eigene Konstanten-Sektion je Bank
$(BANKOBJS): $(OUT)/bank%.rel: bank%.c bank%.h world.h
	$(CC) -mz80 -I. --constseg BANK$* -c -o $@ $<

$(TARGET).sms: $(TARGET).ihx
	makesms -pp $< $@
