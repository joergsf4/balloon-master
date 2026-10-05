#!/bin/bash
# Assembles site/ for the browser version (GitHub Pages): web/index.html, the ROM as balloon-master.sms and the
# EmulatorJS player with the SMS Plus core (downloaded once into site/data/). Same approach as the DnD project.
#   tools/make_web.sh [ROM]            default: out/Balloon Master Beta.sms, or out/rom.sms if that is missing
# Test locally: (cd site && python3 -m http.server 8000), then open http://localhost:8000/?autostart
set -euo pipefail
cd "$(dirname "$0")/.."

ROM="${1:-out/Balloon Master Beta.sms}"
[ -f "$ROM" ] || ROM=out/rom.sms
[ -f "$ROM" ] || { echo "build first: ./build.sh" >&2; exit 1; }
mkdir -p site
cp web/index.html web/LICENSES.txt site/
cp "$ROM" site/balloon-master.sms

BASE=https://cdn.emulatorjs.org/stable/data
FILES=(loader.js emulator.min.js emulator.min.css
       cores/smsplus-wasm.data cores/smsplus-legacy-wasm.data cores/reports/smsplus.json
       compression/extract7z.js)
for f in "${FILES[@]}"; do
    if [ ! -s "site/data/$f" ]; then
        mkdir -p "site/data/$(dirname "$f")"
        curl -fsSL -o "site/data/$f" "$BASE/$f"
        echo "downloaded $f"
    fi
done
ls -la site
