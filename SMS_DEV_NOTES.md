# Master System Entwicklung — Basics & Stolpersteine

Zusammenfassung dessen, was beim RCD-Breakout-Port (dieses Repo) schon herausgefunden wurde. Zum Einstieg in neue Sessions gedacht, damit nichts neu recherchiert werden muss. Spielspezifisches steht in [README.md](README.md), die Hardware-Analyse vor der Portierung in [MASTER_SYSTEM_PORT.md](MASTER_SYSTEM_PORT.md).

## Toolchain (funktioniert, so benutzt)

- **SDCC** (Z80) + **[devkitSMS](https://github.com/sverx/devkitSMS)** (SMSlib, PSGlib, crt0, ihx2sms). Kein SGDK, kein 68000-Code wiederverwendbar.
- Läuft komplett in **Docker** (`debian:bookworm-slim`, `apt install sdcc`, devkitSMS per `git clone --depth 1` nach `/opt/devkitSMS`). Siehe [Dockerfile](Dockerfile).
- **`ihx2sms` selbst kompilieren** (`gcc` aus `devkitSMS/tools/legacy/ihx2sms/src/ihx2sms.c`): Die mitgelieferte Binary ist x86-64-Linux und läuft auf Apple Silicon/arm64-Docker nicht.
- Build: `./build.sh` (baut Image, ruft `python3 tools/gen_assets.py && make -C src` im Container, Ergebnis `out/rom.sms`). `./build.sh clean` räumt auf.
- Compiler-/Linker-Flags ([src/Makefile](src/Makefile)):
  - `CFLAGS = -mz80 -I$(SMSLIB_INCDIR) --peep-file $(SMSLIB_INCDIR)/peep-rules.txt`
  - `LDFLAGS = -mz80 --no-std-crt0 --data-loc 0xC000` (RAM beginnt bei 0xC000)
  - Link-Reihenfolge: `crt0_sms.rel`, dann `SMSlib.lib`, dann eigene `.rel`
  - `.ihx` per `.PHONY` immer neu linken: SDCC schreibt auch bei Linker-Fehlern eine `.ihx`, make hielte sie sonst beim nächsten Lauf für aktuell.
- ROM-Header in `main.c` am Dateiende: `SMS_EMBED_SEGA_ROM_HEADER(productCode, revision)` und `SMS_EMBED_SDSC_HEADER_AUTO_DATE(...)`. Ohne Sega-Header bootet die echte Hardware/manche Emulatoren die ROM nicht.

## Emulatoren

- **Mednafen** (`brew install mednafen`, `./run.sh`): Standard-Tastenmapping für SMS ist **WASD + Numpad**, nicht Pfeiltasten. Umbelegen in `~/.mednafen/mednafen.cfg`, Schlüssel `sms.input.port1.gamepad.{left,right,up,down,fire1}` (SDL-Scancodes, z. B. Pfeile 80/79/82/81, Space 44). Siehe README.
- **Emulicious** wäre wegen Debugger/VRAM-Viewer die bessere Wahl für Fehlersuche (noch nicht eingerichtet). BlastEm ist Mega Drive/SMS-fähig, hier aber (noch) nicht genutzt. Falls BlastEm automatisiert getestet wird, gelten die Hinweise aus der globalen CLAUDE.md (eigenes HOME, `machine_freeze_action debug`).

## Hardware-Eckdaten (VDP Mode 4, 315-5124)

- Z80, 8 KB RAM (`0xC000`–`0xDFFF`), 16 KB VRAM, 256×192 Pixel = **32×24 Tiles** (Tilemap 32×28 im VRAM).
- Je **eine 16-Farben-Palette für BG und eine für Sprites** (6-Bit-RGB, je 2 Bit pro Kanal). Mit `RGBHTML(0xRRGGBB)` in SMSlib wird auf die 64 Farben gerundet. Sprite-Farbe 0 ist immer transparent.
- **Max. 64 Sprites, max. 8 pro Scanline** (Überzählige werden nicht gezeichnet; zählt Objekte, nicht Farben). Sprites sind 8 px breit (8×8 oder 8×16). Daher: Bricks/Wände als **BG-Tilemap** statt Sprites, Sprites nur für Paddle/Ball.
- Tiles sind **4bpp planar**, 32 Bytes pro 8×8-Tile. Der Konverter [tools/gen_assets.py](tools/gen_assets.py) erzeugt sie aus 2-Farb-PNGs (reine Python-Stdlib, eigener PNG-Decoder, nur Colortype 3/8 Bit/ohne Interlace) samt handgebautem 5×7-Pixelfont und schreibt `res/generated/assets.h`.
- Kein PCM, nur **SN76489 PSG**: 3 Tonkanäle + 1 Noise.

## Stolperfallen (schon getappt)

1. **Sprites unsichtbar, BG sichtbar**: Das Sprite-Pattern-Generator-Bit (VDP-Register 6) wählt Tiles 0–255 oder 256–511. Reset-Default = obere Hälfte; SMSlib fasst das Register nicht an. Liegen die Sprite-Tiles bei Index 0–35, **`SMS_useFirstHalfTilesforSprites(TRUE)`** vor `SMS_displayOn()` aufrufen. BG-Tilemap adressiert alle 512 Tiles direkt, daher fällt der Fehler nur bei Sprites auf.
2. **Tiles/VRAM nur bei ausgeschaltetem Display** bulk-laden: `SMS_displayOff()` → `SMS_VRAMmemsetW(0, 0, 16384)` (VRAM leeren), `SMS_loadTiles(...)`, Tilemap/Paletten setzen → `SMS_displayOn()`.
3. **Kein 32-Bit-Division/Float zur Laufzeit** auf dem Z80: Werte vorab berechnen (z. B. PSG-Tonperioden als Konstanten: `period = 3579545 / (32 * freq)`).
4. HUD-Text muss selbst gebaut werden (kein Systemfont): Font-Tiles ins VRAM, Zeichen per `SMS_setTileatXY(x, y, FONT_TILE_START + idx)`.

## SMSlib-Muster (aus [src/main.c](src/main.c))

- Hauptschleife: Eingabe `SMS_getKeysStatus()` (Bitmasken `PORT_A_KEY_LEFT/RIGHT/1/2`), Logik, Sprites neu aufbauen, am Schleifenende `SMS_waitForVBlank()`.
- Sprites pro Frame: `SMS_initSprites()` → `SMS_addSprite(x, y, tile)` / `SMS_addFourAdjoiningSprites(x, y, tile)` (32 px breit) → `SMS_copySpritestoSAT()`.
- Hintergrund: `SMS_setTileatXY(col, row, tile)`; Brick zerstören = leeres Tile setzen.
- Paletten: `SMS_loadBGPalette(arr)`, `SMS_loadSpritePalette(arr)` (16 Einträge, `RGBHTML(...)`).
- Bricks als Tile-Koordinaten halten; Kollision = Ballposition → Tile-Koordinate statt Sprite-Liste durchsuchen.
- Zeit: 60 Hz (NTSC) angenommen, Zeitwerte in Frames zählen.

## Sound (PSG direkt, ohne PSGlib)

Siehe [src/psg.c](src/psg.c). Die PSG liegt auf **I/O-Port 0x7F**; in SDCC per `__sfr __at 0x7f PSGPort;`.

- Latch-Bytes: Ton0 `0x80`, Vol0 `0x90`, Ton1 `0xA0`, Vol1 `0xB0`, Ton2 `0xC0`, Vol2 `0xD0`, Noise `0xE0`, VolN `0xF0`.
- Tonperiode 10 Bit: erst Latch-Byte mit unteren 4 Bit, danach Datenbyte mit oberen 6 Bit. Lautstärke 0 = laut, `0x0F` = still (invertiert!).
- Noise: Bit 2 = Feedback (1 = weißes Rauschen), Bits 1–0 = Rate. Gut für Brick-Break-SFX.
- Musik als Tabellen aus Periodenwert + Dauer in Frames, pro Frame weitergezählt (Melodie auf Kanal 0, einfacher Bass auf Kanal 1). Alternative wäre PSGlib aus devkitSMS.

## Workflow / Projektstruktur

```
src/        main.c, psg.c/.h, Makefile
res/gfx/    Quell-PNGs (2 Farben, indexed)
res/generated/assets.h   generiert, eingecheckt
tools/gen_assets.py      PNG + Font -> 4bpp-Tiles als C-Header
out/rom.sms              Build-Ergebnis (gitignored)
```

- `build.sh` regeneriert `assets.h` bei jedem Build.
- Debugging ohne Debugger: Symptom → Ursache über Hardware-Wissen eingrenzen (siehe Stolperfallen 1). Für echtes Debugging Emulicious (VRAM-/Sprite-Viewer) verwenden.
- Markenfarben RCD: Koralle `#E74E52`, Orange `#ED9055`, Teal `#30B2A1`.

## Erkenntnisse aus dem Spielprojekt (Stolperfallen, Ergänzung)

- **Tiles nur 0..447**: Ab Tile 448 liegen im VRAM die Hintergrundkarte (0x3800) und die Sprite-Tabelle (0x3F00). Mehr Tiles überschreiben beides. Sprites müssen mit `SMS_useFirstHalfTilesforSprites(1)` unter Tile 256 liegen, Hintergrund-Tiles dürfen dahinter anschließen.
- **Große VRAM-Ladevorgänge und eigene Interrupt-Handler**: `SMS_loadTiles`/`SMS_loadTileMap` schützen nur das Setzen der Adresse, nicht die Datenschleife. Ein Handler, der ins VDP-Steuerregister schreibt (Scrollwert per `INLINE_SMS_setBGScrollX`), verstellt die laufende Adresse und zerstört das Ergebnis. Vorher Zeilen- und Frame-Handler abschalten (`SMS_disableLineInterrupt`, `SMS_setFrameInterruptHandler(0)`), danach wieder einschalten.
- **Zeileninterrupt für Parallax**: Zähler alle 8 Zeilen (Zähler 7) und im Handler mitzählen, statt den Zähler im Handler umzustellen (eine Änderung wirkt erst beim übernächsten Neuladen). Scrollwerte vom Spiel in `next_*` ablegen und im Frame-Handler atomar übernehmen.
- **SDCC lässt `x = bedingung ? KONSTANTE_A : KONSTANTE_B;` aus** (mit `&&` in der Bedingung zusammen mit der Peephole-Datei der SMSlib): die Variable bleibt ungesetzt. Als `if` schreiben und im erzeugten Assembler prüfen (`sdcc -S`). Als Funktionsargument funktioniert `?:`.
- **ROM über 32 KB**: Daten in eine eigene `.c`-Datei, mit `--constseg BANK2` übersetzen, beim Linken `-Wl-b_BANK2=0x28000` und die Datei zuletzt, dann `makesms -pp` (statt ihx2sms). Zugriff nach `SMS_mapROMBank(2)`. Code bleibt in den ersten 32 KB. Das Docker-Image baut `makesms` selbst.
- **Titelbild**: Der VDP wählt pro Tile zwischen BG- und Sprite-Palette (Attributbit 11): 2 x 16 Farben. `tools/make_title.py` rechnet ein Artwork automatisch um (siehe Kopfkommentar, braucht numpy und Pillow, das Ergebnis `src/bank2.c` ist eingecheckt).
- **Eigene Screenshots**: BlastEms Debugger (`-d`) reagiert im Master-System-Modus nicht auf Befehle, das Mega-Drive-Verfahren aus anderen Projekten geht hier nicht. Stattdessen `tools/shot.sh ROM SEK ...`: Mednafen nimmt mit `-qtrecord` ein Video auf, ffmpeg zieht Bilder heraus. Eingaben gibt es nicht, für Spielbilder `AUTOPLAY=1 ./build.sh` (überspringt den Titel und fliegt selbst).
- **Welten**: Eine Welt ist eine `World`-Struktur (`src/world.h`): Kachel-Daten und Palette, Hintergrund hinter den Hindernissen, Boden, ein bis drei Hindernistypen mit Oberkanten-Profil je 8-px-Spalte, Ziel, Abschnittsarten. Der Generator (`tools/gen_assets.py`) berechnet die Profile aus der Grafik (erste Zeile mit mindestens 4 gefüllten Pixeln je Spalte, dünne Masten zählen nicht) und daraus die tiefste erlaubte Ballonhöhe. London liegt im Hauptspeicher, weitere Welten in je einer ROM-Bank; vor dem Zugriff `SMS_mapROMBank` (siehe `select_world`).
- **Durchsichtige Pixel in Hintergrund-Kacheln**: Der VDP kennt für Hintergrund-Kacheln keine Transparenz. Liegt hinter einem Hindernis nur Himmel und waagerechte Streifen (Meer), werden die leeren Pixel beim Umrechnen mit der Farbe der jeweiligen Bildschirmzeile gefüllt (`bake` in `tools/art/sea.py`): dann passt es überall. Bei der Skyline in London geht das nicht, dort sind die Gebäude rechteckig.
- **Kachelbudget pro Welt**: Sprites belegen 113 Kacheln, ein Hintergrund darf bis Kachel 447 gehen, also rund 335. Gleiche Kacheln werden zusammengelegt: Muster in das 8-px-Raster legen (Ziegel mit Fugen alle 8 Pixel) und keine zufälligen Körnungen verwenden.
- **Ballistik**: Kanonenkugeln in Festkomma (1/64 Pixel): `x -= vx; y += vy; vy += g`. Anfangsgeschwindigkeit aus Flugzeit T und Zielhöhe ht: `vx = dx/T`, `vy0 = ((y0 - ht) + g*T^2/2) / T`. Die Rechnung weicht um höchstens 2 Pixel von der Zielhöhe ab.
- **Autoplay-Pilot** (`AUTOPLAY=1`): Fliegt in die Mitte des Korridors der nächsten Hindernisse, ignoriert aber Vögel und Kugeln. Reicht als Rauchtest für Levelablauf und Weltwechsel (`LEVEL_COLS=150`).
- **Mehrere Welten**: `tools/gen_assets.py` kennt eine Liste `WORLD_MODULES` (Reihenfolge = Spielreihenfolge). Jedes Modul in `tools/art/` liefert eine `SPEC` (Palette, Hintergrundfarbe je Zeile, Boden, Hindernisse, Ziel, Physik, Wind, Musik ...). Daraus entstehen `src/bank<N>.c/.h` und `src/worlds_gen.h`. Das Makefile findet alle `bank?.c` selbst. Gewitter, Höhle, Mond und New York sind so entstanden; `tools/art/preview.py <Modul>` zeigt eine Welt vor dem Bauen als Bild.
- **Hängende Hindernisse** (`ceil`): Unterkanten-Profil je 8-px-Spalte; optionaler Blitz bzw. Strahl darunter (`bolt`). Erste Pixelzeile des Objekts leer lassen (siehe nächster Punkt).
- **Zeileninterrupt kommt etwa eine Zeile zu spät**: Die erste Zeile des Hindernisbands (Bildschirmzeile 16) wird noch mit dem Scrollwert des langsamen Wolkenbands gezeichnet. Deshalb müssen Objekte, die an Zeile 16 beginnen, dort eine leere Pixelzeile haben.
- **Auftritte und Monster**: `setpieces` in der Welt, `shot_kind` (0 Kanonenkugel, 1 Feuerball, 2 Felsbrocken) und `anim` (Kachelblöcke, die abwechselnd Bild A und B bekommen; Bild B liegt als eigenes Array in der Bank). Der Generator erkennt die Kacheln, die sich zwischen A und B unterscheiden, und legt sie ohne Zusammenlegen ab.
- **Tests ohne lange Läufe**: `tools/worldtest.sh WELT [ART|-] [SEK] [ALLE_N_SEK]` baut eine Test-ROM (unverwundbar `GODMODE`, selbstfliegend `AUTOPLAY`, kurze Strecke `LEVEL_COLS`, optional erzwungene Abschnittsart `FORCE_KIND`) und liefert einen Bilderbogen `out/shots/test_sheet.png`. `SKIP=n` beginnt später, `REUSE=1` nimmt die vorhandene Test-ROM neu auf.
- **Musik**: `tools/music.py` erzeugt die Stücke 1 bis 5 nach `src/music_data.h` (Notennamen statt Frequenzen, Staccato und Ausklingzeit pro Stück) und prüft, dass Melodie und Bass gleich lang sind. Stück 0 (London Bridge, gemeinfrei) steht in `src/sound.c`. Bekannte geschützte Lieder werden nicht nachgebaut, sondern nur im Stil angelehnt. Kontrolle ohne Ohren: Aufnahme (`-qtrecord`) mit ffmpeg als WAV ausziehen und per FFT die vorherrschende Tonhöhe je Zeitfenster mit den Noten vergleichen.


## Hintergrundmuster hinter Hindernissen (New York)
Durchsichtige Pixel der Hindernis-Kacheln werden beim Erzeugen mit dem Hintergrund gefüllt. Ist der Hintergrund nur von y abhängig, geht das immer; hat er ein festes Muster (Skyline), muss das Hindernis genau darauf passen: Das Muster wiederholt sich alle 64 Pixel, die Hindernisse beginnen auf Vielfachen von 8 Spalten (`align` in `World`, `spec["align"]`), und `bake()` im Generator nimmt das Muster aus `spec["band"]`. Sonst entstehen Kästen in Himmelsfarbe um die Hindernisse.


## SMS_addSprite in Schleifen
`SMS_addSprite_f` ist `__naked __preserves_regs(d,e,...)`. In einer Schleife mit Zählvariable zeichnete sie bei `draw_lives` nur das erste Sprite (der Zähler ging verloren, kein Fehler beim Bauen). Gelöst durch drei einzelne Aufrufe; die Schleife in `draw_fuel` ging zufällig gut. Bei neuen Schleifen mit `SMS_addSprite` im Screenshot nachzählen.


## Bank 8, 256-KB-ROM, Textfläche
- London liegt wie die anderen Welten in einer ROM-Bank (Bank 8, `src/bank8.c`); die ROM ist damit 256 KB groß. Der feste Bereich (Bank 0 und 1) hat dadurch wieder etwa 8 KB frei. Gemeinsame Sprites (`sprite_tiles`, `sprite_palette`) stehen in `src/shared_data.c` im festen Bereich, `assets.h` enthält nur noch `#define`s und `extern`s (sonst würden die Arrays in jede Bank-Übersetzung gelangen).
- Textfläche: Eine Sprite-Kachel (`PANEL`) wird mit gesetztem Attribut-Bit 11 (Sprite-Palette) als Hintergrundkachel in die Tilemap geschrieben. Das Rechteck wird erst in der Austastlücke und höchstens 4 Zeilen je Bild gezeichnet. Der Hintergrund darf in dieser Zeit nicht scrollen (Bildschirmspalte k = Kartenspalte `(dcol + k) & 31`, plus Unterpixel `sub >> 4`, deshalb je 1 Spalte Rand). Neustart lädt alle Spalten neu und entfernt die Fläche.

## VRAM-Schreibzugriffe nur in der Austastlücke (Löcher auf echter Hardware)
Der Emulator (Mednafen) zeigte die Löcher in der Textfläche nie, der MiSTer schon: Die Fläche wurde Kachel für Kachel (`SMS_setTileatXY` in einer Schleife, 4 Zeilen je Bild) nach `SMS_waitForVBlank()` geschrieben und lief ins sichtbare Bild; dort verliert der VDP schnelle Schreibzugriffe. Behoben durch: gleich nach `SMS_waitForVBlank()` schreiben, jede Zeile am Stück mit `SMS_loadTileMap` (eine Adresse, danach Datenstrom), höchstens 3 Zeilen je Bild. Faustregel: alles, was nicht klein ist, auf mehrere Bilder verteilen (Anim-Kacheln: 6 je Bild), und Änderungen an VRAM-Schreibcode immer auf dem MiSTer prüfen, nicht nur im Emulator.


## Performance: Takt festnageln statt Last drücken
Die Hauptschleife wartet mit `SMS_waitForVBlank()` auf den nächsten Bildwechsel. Dauert die Arbeit auch nur etwas länger als ein Bild, kostet das sofort ein ganzes zweites Bild, und der Durchlauf schwankt je nach Last zwischen 1, 2 und 3 Bildern (die Ruckler, und die Musik wurde mit). Messungen mit dem V-Zähler (`SMS_getVCount`, 262 Zeilen je Bild, Bildinterrupt bei Zeile 192) zeigten rund 1,9 Bilder je Durchlauf in allen Welten; Einsparungen von 25 bis 30 Prozent Rechenzeit änderten daran kaum etwas, weil die Last zwischen 1 und 2 Bildern lag. Deshalb ist der Takt jetzt fest 2 Bilder je Durchlauf (30 Durchläufe/s, `tail_vb`), das Budget (524 Zeilen) ist reichlich, die Musik holt über `vb_count` verpasste Bilder nach.
Was sich dabei lohnte:
- **Zeileninterrupts:** 24 Interrupts je Bild (alle 8 Zeilen) verschlangen mehr als die Hälfte der Rechenzeit. Jetzt nur noch drei (Zeile 16, 32, 168): Zähler im Bildinterrupt auf 15, im ersten Zeileninterrupt auf 135, im zweiten auf 255.
- **Strukturfelder in Schleifen:** SDCC rechnet bei `ring[i].feld` mit Multiplikation, wenn die Strukturgröße keine Zweierpotenz ist (`Seg` jetzt 16 Byte), und `W->bld[x].feld` multipliziert bei jedem Zugriff. Zeiger in den Abschnitten (`bp`, `cp`), Zeiger statt Indizes in den Spaltenschleifen, einmal je Bild die Bildschirmposition (`seg_left`) und die Liste der sichtbaren Abschnitte (`act`) berechnen.
- **Messen:** Mit `LOOPMETER=1 ./build.sh` zeigt eine Test-ROM links die Bilder je Durchlauf x100 (200 = 30 Durchläufe/s). Beim Zählen ergab die einfache Formel `Bildinterrupts*262 + Zeilendifferenz` zu große Werte, weil der Bildinterrupt mitten im Bild (Zeile 192) liegt; die Dauer muss aus Phase und Anzahl der Interrupts berechnet werden. Außerdem verfälscht eine aufwendige Messanzeige (Divisionen, viele Sprites) die Messung selbst stark.

### Gewitter: Ablauf, Monster, Leistung
- Decke und Boden haben je eine eigene Phasenfolge (frei, Anfangskappe, ruhig, schwer, Endkappe), dadurch beginnen und enden die Bänder versetzt. Decke: Module 1,2 ruhig, 3..5 schwer, 6 Anfang, 7 Ende; Boden: 1,2 ruhig, 3,4 schwer, 5 Anfang, 6 Ende (Slots der Engine: `ceil[8]`, `bld[8]` mit Ziel = 7). Die Kappen bestehen aus ganzen Kreisen ohne Turm zum Rand, sonst bleibt am Ende eine senkrechte Wand.
- Hintergrund ab y=144 ist das Grau der Wolken; die untere Parallaxebene sind dunkelgraue Kuppen mit weißer Kontur. Nur y-abhängige Hintergründe lassen sich so einfärben (die Hindernis-Kacheln backen die Farbe ein).
- Sturm-Monster (`update_boss`/`draw_boss`): ein 48x40-Sprite (6x5 Kacheln, Welt-Sprites müssen unter Kachel 256 liegen, Bild B folgt nach 30). Gezeichnet werden nur Zeilen oberhalb von y=144, so taucht der Kopf aus der grauen Ebene auf (Sprites liegen sonst immer vor dem Hintergrund). Es erscheint nur bei freiem Himmel über ihm (`sky_clear`); fällig ab 52 % und 82 % hält der Generator die Decke frei. Währenddessen Windstille (`wind_tgt = 4`). Die Blitzkugeln sind `fire_ball` mit Art 4.
- Leistung: teure Prüfungen (`frames_to_shift` läuft bis zu 600 Runden) nicht in Wiederholungsschleifen der Wolkenwahl aufrufen (dort `corridor_overlaps`); der Regen rechnet nur mit Bytes (16-Bit-Modulo ist auf dem Z80 teuer).
