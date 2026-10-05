# Balloon Master (Sega Master System)

Balloon Master: Heißluftballon-Abenteuer. Der Ballon treibt durch eine scrollende Stadt, der Spieler steuert nur die Höhe. Konzept: [KONZEPT.md](KONZEPT.md). Hardware-Wissen und Stolperfallen: [SMS_DEV_NOTES.md](SMS_DEV_NOTES.md).

```
./build.sh        # -> out/rom.sms (Docker, SDCC + devkitSMS), erzeugt auch out/art_preview.png
./run.sh          # startet Mednafen (WASD + Numpad)
./build.sh clean

LEVEL_COLS=150 ./build.sh        # kurze Zielstrecke zum Testen des Endes
START_WORLD=3 ./build.sh         # beginnt in einer anderen Welt (0 London, 1 Piratenbucht, 2 Gewitter, 3 Höhle, 4 Mond, 5 New York)
tools/worldtest.sh 5 - 30 2      # Kurztest einer Welt: Test-ROM, Bilderbogen nach out/shots/test_sheet.png
AUTOPLAY=1 ./build.sh            # Version, die den Titel überspringt und selbst fliegt
tools/shot.sh out/rom.sms 3 8    # eigene Screenshots (Mednafen-Aufnahme + ffmpeg) nach out/shots/
```

## Steuerung (Prototyp)

- Knopf 1 oder Hoch: Brenner, der Ballon steigt. Sonst sinkt er langsam.
- Knopf 2 (bei dir linke Umschalttaste): Seil mit Haken herablassen, loslassen zieht es wieder ein; das Seil darf höchstens 3 Sekunden am Stück draußen sein (Ausfahren + Einholen), dann wird es eingeholt und 1 Sekunde gesperrt. Fässer stehen auf dem Gehweg zwischen den Gebäuden. Trifft der Haken eins, hängt es am Seil, und der Tank füllt sich, sobald es oben am Korb ankommt.
- Der Brenner verbraucht Treibstoff (Anzeige oben links, rot blinkend wenn fast leer). Ohne Treibstoff sinkt der Ballon nur noch.
- Knopf 1 startet und startet nach dem Absturz neu. Nach dem Ziel (Tower Bridge, Schatzinsel) führt Knopf 1 in die nächste Welt.
- Beim Einschalten erscheint zuerst das Logo von Retro Computer Dresden (2,5 s, jede Taste überspringt es), dann das Titelbild.
- Vorführung (Attract-Modus): 10 s ohne Tastendruck im Titel, dann fliegt das Spiel 25 s selbst (unverwundbar, "DEMO" blinkt) – bei jedem Durchlauf in der nächsten Welt –, danach zurück zum Titel. Jede Taste beendet die Vorführung.
- Monstertest (`tools/monstertest.sh` → `Balloon Master Monstertest.sms`): Piratenbucht (Krake), danach New York (Riesenaffe, Riesenechse), je kurz, unverwundbar, Tank immer voll. Die Monster haben eigene Laute (Platsch, Brüllen, Grollen).
- Zwei Varianten (`tools/release.sh`): **Balloon Master Beta** ohne Weltauswahl, **Balloon Master Testing** mit Weltauswahl: Im Titel wählt man mit links/rechts die Startwelt, Taste 1 startet.
- Sechs Welten nacheinander: London, Piratenbucht, Gewitter (kurz), Höhle, Mond, New York (mit Riesenaffe und Riesenechse). Danach der Schluss und zurück zum Titel.
- Drei Leben (kleine Ballons unter dem Tank). Ein Absturz kostet ein Leben, es geht ab dem letzten Checkpoint mit vollem Tank weiter (Taste 1). Sind alle Leben weg: „GAME OVER“ mit Continue-Countdown von 9 bis 0 (Taste 1 = Continue, unendlich oft: wieder drei Leben, der Level beginnt von vorn; bei 0 geht es zurück zum Titel). Texte stehen auf einer dunklen Fläche. Übrige Leben bleiben beim Wechsel in die nächste Welt erhalten.
- Checkpoints bei einem und zwei Dritteln der Strecke („CHECK POINT“, kein Auftanken). Nach einem Absturz geht es dort mit vollem Tank weiter.
- Berührung von Gebäude, Gewitterwolke oder Boden = Absturz. Die Zahl oben links ist die Strecke.
- Der Wind (Scrolltempo) wechselt alle paar Sekunden von allein.

## Struktur

| Pfad | Inhalt |
|---|---|
| `src/main.c` | Spiel: Scrolling, Spaltenerzeugung, Steuerung, Kollision, Weltwechsel |
| `src/world.h` | Beschreibung einer Welt (Hindernisse, Hintergrund, Boden, Ziel); London steckt in `assets.h`, die Piratenbucht in ROM-Bank 3 (`bank3.c`) |
| `src/sound.c` | PSG-Klang-Engine: Musik pro Welt, Effekte |
| `tools/art/palette.py` | Das feste Farbschema (Stilanker), zwei 16er-Paletten |
| `tools/art/artdefs.py` | Grafiken von London und alle Sprites |
| `tools/art/sea.py`, `storm.py`, `cave.py`, `moon.py`, `ny.py` | je eine Welt: Grafiken und Beschreibung (`SPEC`) |
| `tools/music.py` | Musik der Welten 3 bis 6 |
| `tools/art/pixelart.py` | ASCII → Tiles, Umriss, PNG-Vorschau |
| `tools/gen_assets.py` | erzeugt `res/generated/assets.h` und `out/art_preview.png` |
| `tools/shot.sh` | Screenshots für die eigene Prüfung (Mednafen-Aufnahme + ffmpeg) |
| `tools/art/title_art.py` | zeichnet das Titelbild im Spielstil (`res/gfx/title_art.png`) |
| `tools/make_logo.py` | Vorspann-Logo „RCD“ (`src/bank9.c`, ROM-Bank 9) |
| `tools/make_title.py` | Titelbild → `src/bank2.c`, ROM-Bank 2 (für das gezeichnete Bild: `SPREAD=0 COLOR=1 CONTRAST=1 BRIGHT=1 SHARP=1`) |

## Lizenz und Herkunft
- Code, Grafiken und Musik sind eigene Werke und stehen unter der MIT-Lizenz (siehe `LICENSE`). Die Musik besteht aus eigenen Kompositionen im Stil der jeweiligen Welt sowie gemeinfreien Melodien (London Bridge, Shanty-Anlehnung, Toccata-Motiv von Bach, US-Hymne von J. S. Smith).
- Gebaut mit SDCC und devkitSMS (SMSlib, PSGlib: gemeinfrei; Startcode `crt0_sms.s`: GPL2 mit Linking-Ausnahme).
- Die Titelgrafik ist selbst gezeichnet (`tools/art/title_art.py`), ebenso das Vorspann-Logo (`tools/make_logo.py`, Buchstabenblöcke aus dem Projekt master-system-game).
