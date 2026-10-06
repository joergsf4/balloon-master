#!/bin/sh
# Wie flüssig läuft eine ROM? Nimmt SEK Sekunden auf (Mednafen) und zählt, wie oft sich das Bild wirklich ändert.
#   tools/fps.sh out/rom_test.sms [SEK]      (Test-ROM mit AUTOPLAY=1 GODMODE=1 bauen, sie fliegt selbst)
# Ausgabe: Aktualisierungen je Sekunde (60 = jedes Bild neu) und mittlere Bilder je Aktualisierung.
cd "$(dirname "$0")/.." || exit 1
ROM="$1"; SECS="${2:-26}"
MOV=out/shots/fps.mov
rm -f "$MOV"
mednafen -sms.xscale 1 -sms.yscale 1 -qtrecord "$MOV" "$ROM" > out/shots/fps.log 2>&1 &
PID=$!
sleep "$SECS"
kill -TERM $PID 2>/dev/null
wait $PID 2>/dev/null
sleep 2
ffmpeg -v error -ss 8 -t 12 -i "$MOV" -map 0:v:0 -vf "crop=256:192:0:24" -f framemd5 - 2>/dev/null | grep -v '^#' | awk -F, '{print $6}' | uniq -c | awk '{runs++; frames+=$1} END {printf "Bilder %d, Aktualisierungen %d, je Sekunde %.1f, mittlere Laenge %.2f Bilder\n", frames, runs, runs*60/frames, frames/runs}'
