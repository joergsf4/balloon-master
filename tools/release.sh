#!/bin/sh
# Baut die beiden ROM-Varianten:
#   out/Balloon Master Beta.sms     ohne Weltauswahl im Titel (fuer Spieler)
#   out/Balloon Master Testing.sms  mit Weltauswahl (links/rechts im Titel, zum Testen)
# Danach steht wieder die Testing-Variante in out/rom.sms.
cd "$(dirname "$0")/.." || exit 1
unset LEVEL_COLS AUTOPLAY START_WORLD FORCE_KIND GODMODE TEST_DIE_AT TEST_DIE_REPEAT MONSTER_TEST NO_LEVEL_SELECT
NO_LEVEL_SELECT=1 ./build.sh > /dev/null || exit 1
cp out/rom.sms "out/Balloon Master Beta.sms"
./build.sh > /dev/null || exit 1
cp out/rom.sms "out/Balloon Master Testing.sms"
ls -l out/Balloon\ Master\ *.sms
