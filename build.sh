#!/bin/sh
# Baut out/rom.sms im Docker-Container. "./build.sh clean" räumt auf.
set -e
cd "$(dirname "$0")"
IMAGE=sms-dev

if [ "$1" = "clean" ]; then
  rm -rf out/*.rel out/*.ihx out/*.sms out/*.asm out/*.lst out/*.sym out/*.map out/*.lk out/*.noi
  exit 0
fi

mkdir -p out
docker image inspect "$IMAGE" >/dev/null 2>&1 || docker build -t "$IMAGE" .
# Zum Testen der Zielstrecke: LEVEL_COLS=150 ./build.sh (main.c wird dann neu übersetzt)
# START_WORLD=1 ./build.sh: beginnt in der zweiten Welt (Piratenbucht)
# AUTOPLAY=1 ./build.sh: Version, die den Titel überspringt und selbst fliegt (für tools/shot.sh)
# Wechseln die Schalter, muss main.c neu übersetzt werden (make sieht das sonst nicht)
FLAGS="LEVEL_COLS=$LEVEL_COLS AUTOPLAY=$AUTOPLAY START_WORLD=$START_WORLD FORCE_KIND=$FORCE_KIND GODMODE=$GODMODE TEST_DIE_AT=$TEST_DIE_AT"
[ "$(cat out/.buildflags 2>/dev/null)" = "$FLAGS" ] || { rm -f out/main.rel; echo "$FLAGS" > out/.buildflags; }
docker run --rm -e LEVEL_COLS -e AUTOPLAY -e START_WORLD -e FORCE_KIND -e GODMODE -e TEST_DIE_AT -v "$PWD":/work "$IMAGE" sh -c "python3 tools/gen_assets.py && make -C src"
echo "OK: out/rom.sms"
