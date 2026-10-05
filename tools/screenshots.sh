#!/bin/sh
# Bilder fuer README/Web: Test-ROM einer Welt (selbstfliegend, unverwundbar) aufnehmen und Kandidatenbilder ablegen.
#   tools/screenshots.sh WELT LEVEL_COLS SEKUNDEN [INTERVALL]      -> out/cand/w<WELT>/c<NNN>.png (768x576, 3x Pixel)
#   tools/screenshots.sh pick WELT SEK NAME                         -> docs/screenshots/NAME.png aus der Aufnahme von WELT
cd "$(dirname "$0")/.." || exit 1
if [ "$1" = "pick" ]; then
  ffmpeg -v error -y -ss "$3" -i out/cand/w$2.mov -frames:v 1 -vf "crop=512:384:0:48,scale=256:192:flags=neighbor,scale=768:576:flags=neighbor" "docs/screenshots/$4.png" && echo "docs/screenshots/$4.png"
  exit 0
fi
WORLD="$1"; COLS="$2"; SECS="$3"; EVERY="${4:-2}"
unset LEVEL_COLS AUTOPLAY START_WORLD FORCE_KIND GODMODE TEST_DIE_AT TEST_DIE_REPEAT NO_LEVEL_SELECT MONSTER_TEST SFX_DEMO
START_WORLD=$WORLD LEVEL_COLS=$COLS AUTOPLAY=1 GODMODE=1 ./build.sh > /dev/null || exit 1
cp out/rom.sms out/rom_shots.sms
./build.sh > /dev/null
mkdir -p out/cand
rm -f out/cand/w$WORLD.mov
mednafen -sms.xscale 2 -sms.yscale 2 -qtrecord out/cand/w$WORLD.mov out/rom_shots.sms > out/cand/log.txt 2>&1 &
PID=$!
sleep "$SECS"
kill -TERM $PID 2>/dev/null
wait $PID 2>/dev/null
sleep 2
rm -rf out/cand/w$WORLD; mkdir -p out/cand/w$WORLD
ffmpeg -v error -y -i out/cand/w$WORLD.mov -vf "fps=1/$EVERY,crop=512:384:0:48,scale=256:192:flags=neighbor,scale=768:576:flags=neighbor" out/cand/w$WORLD/c%03d.png
ls out/cand/w$WORLD | wc -l
