#!/bin/sh
# Zugriff auf den MiSTer (Heimnetz) per ssh/scp mit Passwort über expect. Das Passwort steht NICHT in dieser Datei:
#   MISTER_PW=... tools/mister.sh ssh "ls -l /media/usb0/games/SMS"
#   MISTER_PW=... tools/mister.sh scp out/rom.sms /media/usb0/games/SMS/BalloonMaster/
# Host-Schlüssel landen in out/mister_known_hosts (nicht in ~/.ssh). Vorher prüfen: nc -z -G 3 192.168.178.43 22
HOST="${MISTER_HOST:-192.168.178.43}"
cd "$(dirname "$0")/.." || exit 1
mkdir -p out
KH="$PWD/out/mister_known_hosts"
[ -n "$MISTER_PW" ] || { echo "MISTER_PW setzen"; exit 1; }
MODE="$1"; shift
export MISTER_PW KH HOST MODE
exec expect -f - "$@" <<'EXP'
set timeout 60
set opts [list -o UserKnownHostsFile=$env(KH) -o StrictHostKeyChecking=accept-new -o PubkeyAuthentication=no]
if {$env(MODE) eq "ssh"} {
  spawn ssh {*}$opts root@$env(HOST) [lindex $argv 0]
} else {
  set dest root@$env(HOST):[lindex $argv end]
  spawn scp {*}$opts {*}[lrange $argv 0 end-1] $dest
}
expect {
  "assword:" { send "$env(MISTER_PW)\r"; exp_continue }
  eof
}
catch wait result
exit [lindex $result 3]
EXP
