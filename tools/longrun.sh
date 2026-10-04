#!/bin/sh
# Langer Rauchtest: Autoplay-ROM spielt beide Welten durch, Mednafen nimmt auf, ffmpeg macht Bilderbögen.
#   tools/longrun.sh [SEKUNDEN] [BILD_ALLE_N_SEKUNDEN]      Standard: 540 s, alle 12 s ein Bild
# Ergebnis: out/shots/long_sheet_1.png, _2.png ... (je 6 x 5 Bilder). Am Punktestand oben links sieht man, ob der
# Pilot durchkommt (Zahl steigt) oder abstürzt (Zahl springt zurück auf 0), "LEVEL COMPLETE" zeigt geschaffte Welten.
# Der Pilot ignoriert Vögel und Kanonenkugeln, Abstürze dort sind also normal.
cd "$(dirname "$0")/.." || exit 1
SECS="${1:-540}"
EVERY="${2:-12}"
mkdir -p out/shots
AUTOPLAY=1 ./build.sh > /dev/null || exit 1
cp out/rom.sms out/rom_long.sms
./build.sh > /dev/null                      # normale ROM wiederherstellen
rm -f out/shots/long.mov
mednafen -sms.xscale 1 -sms.yscale 1 -qtrecord out/shots/long.mov out/rom_long.sms > out/shots/long.log 2>&1 &
PID=$!
sleep "$SECS"
kill -TERM $PID 2>/dev/null
wait $PID 2>/dev/null
sleep 2
rm -f out/shots/long_sheet_*.png
ffmpeg -v error -y -i out/shots/long.mov -vf "fps=1/$EVERY,crop=256:150:0:40,tile=6x5" -frames:v 30 out/shots/long_sheet_%d.png
ls out/shots/long_sheet_*.png
rm -f out/shots/long.mov
