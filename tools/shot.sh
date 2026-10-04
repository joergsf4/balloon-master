#!/bin/sh
# Eigene Screenshots zum Prüfen: Mednafen nimmt per -qtrecord ein Video auf, ffmpeg zieht Bilder heraus.
#   tools/shot.sh [ROM] SEK [SEK ...]      z. B. tools/shot.sh out/rom_autoplay.sms 3 8 15
# Ergebnis: out/shots/t<SEK>.png. Ein Mednafen-Fenster ist kurz sichtbar. Eingaben gibt es nicht:
# für Spielbilder eine Autoplay-ROM benutzen (AUTOPLAY=1 ./build.sh, siehe README).
# (BlastEm lässt sich im Master-System-Modus nicht über den Debugger steuern, deshalb nicht BlastEm.)
cd "$(dirname "$0")/.." || exit 1
ROM=out/rom.sms
case "$1" in *.sms) ROM="$1"; shift;; esac
[ $# -ge 1 ] || { echo "Aufruf: $0 [ROM] SEK [SEK ...]"; exit 1; }
mkdir -p out/shots
MOV=out/shots/rec.mov
rm -f "$MOV"
LAST=0; for s in "$@"; do [ "$s" -gt "$LAST" ] && LAST=$s; done
mednafen -sms.xscale 2 -sms.yscale 2 -qtrecord "$MOV" "$ROM" > out/shots/mednafen.log 2>&1 &
PID=$!
sleep $((LAST + 3))
kill -TERM $PID 2>/dev/null
wait $PID 2>/dev/null
sleep 1
for s in "$@"; do
  ffmpeg -v error -y -ss "$s" -i "$MOV" -frames:v 1 "out/shots/t$s.png" && echo "out/shots/t$s.png"
done
