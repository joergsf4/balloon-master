#!/bin/sh
# Test-ROM "Monstertest": Piratenbucht (Krake) und New York (Riesenaffe, Riesenechse) kurz hintereinander, unverwundbar, Tank immer voll.
#   Ergebnis: out/Balloon Master Monstertest.sms   (danach wird wieder die normale ROM gebaut)
cd "$(dirname "$0")/.." || exit 1
unset LEVEL_COLS AUTOPLAY START_WORLD FORCE_KIND GODMODE TEST_DIE_AT TEST_DIE_REPEAT NO_LEVEL_SELECT MONSTER_TEST SFX_DEMO
MONSTER_TEST=1 START_WORLD=1 LEVEL_COLS=90 GODMODE=1 NO_LEVEL_SELECT=1 ./build.sh > /dev/null || exit 1
cp out/rom.sms "out/Balloon Master Monstertest.sms"
./build.sh > /dev/null || exit 1
ls -l "out/Balloon Master Monstertest.sms"
