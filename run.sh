#!/bin/sh
# Startet die ROM in Mednafen (Standard-Mapping: WASD + Numpad, siehe SMS_DEV_NOTES.md).
# Fenstergröße als Vergrößerungsfaktor: SCALE=2 ./run.sh (Standard 3). Die eigene
# Mednafen-Konfiguration bleibt unverändert, der Wert gilt nur für diesen Start.
cd "$(dirname "$0")"
ROM="${1:-out/rom.sms}"      # optional: andere ROM, z. B. ./run.sh out/rom_ziel_test.sms
[ -f "$ROM" ] || ./build.sh
SCALE="${SCALE:-3}"
exec mednafen -sms.xscale "$SCALE" -sms.yscale "$SCALE" "$ROM"
