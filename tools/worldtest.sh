#!/bin/sh
# Kurzer Test einer Welt oder eines Sonderfalls: Test-ROM (unverwundbar, selbstfliegend, kurze Strecke) bauen,
# kurz aufnehmen und einen Bilderbogen erzeugen. Danach wird die normale ROM wieder gebaut.
#   tools/worldtest.sh WELT [ART|-] [SEKUNDEN] [BILD_ALLE_N_SEK]
#   WELT: 0 London, 1 Piratenbucht, 2 ...   ART: erzwingt Abschnittsart 0..7 (siehe kind_bld/kind_ceil der Welt), - = normal
#   Umgebung: SKIP=n beginnt den Bilderbogen erst bei Sekunde n. REUSE=1 nimmt die vorhandene Test-ROM nur neu auf. LEVEL_COLS (Standard 260) setzt die Streckenlänge, die Höhepunkte (Monster) erscheinen anteilig darin.
# Ergebnis: out/shots/test_sheet.png (je 4 x 4 Bilder)
cd "$(dirname "$0")/.." || exit 1
WORLD="${1:-0}"; KIND="${2:--}"; SECS="${3:-24}"; EVERY="${4:-1.5}"
export START_WORLD="$WORLD" AUTOPLAY=1 GODMODE=1 LEVEL_COLS="${LEVEL_COLS:-260}"
[ "$KIND" != "-" ] && export FORCE_KIND="$KIND"
if [ -z "$REUSE" ]; then                  # REUSE=1: vorhandene out/rom_test.sms noch einmal aufnehmen
  ./build.sh > /dev/null || exit 1
  cp out/rom.sms out/rom_test.sms
  unset START_WORLD AUTOPLAY GODMODE LEVEL_COLS FORCE_KIND TEST_DIE_AT TEST_DIE_REPEAT MONSTER_TEST SFX_DEMO
  ./build.sh > /dev/null
fi
mkdir -p out/shots
rm -f out/shots/test.mov
mednafen -sms.xscale 1 -sms.yscale 1 -qtrecord out/shots/test.mov out/rom_test.sms > out/shots/test.log 2>&1 &
PID=$!
sleep "$SECS"
kill -TERM $PID 2>/dev/null
wait $PID 2>/dev/null
sleep 2
ffmpeg -v error -y -ss "${SKIP:-2}" -i out/shots/test.mov -vf "fps=1/$EVERY,crop=512:340:0:40,scale=256:-1,tile=4x4" -frames:v 1 out/shots/test_sheet.png
rm -f out/shots/test.mov
echo "out/shots/test_sheet.png"
