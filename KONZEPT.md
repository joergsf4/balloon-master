# Balloon Master — Konzept (Arbeitsgrundlage)

Sortierte Fassung der Rohideen aus [konzept-ideen](konzept-ideen). Technische Grenzen: siehe [SMS_DEV_NOTES.md](SMS_DEV_NOTES.md).

## Kernidee

Heißluftballon-Abenteuer, ein **Flappy Bird in langsam**: Der Ballon treibt automatisch seitwärts, der Spieler steuert nur die Höhe (Brenner = steigen, sonst sinken). Hindernisse werden durch Auf- und Absteigen umflogen. Der Reiz liegt in wechselnden Orten und Gegnern, nicht in Tempo.

## Stand der Umsetzung

Das Spiel ist von Anfang bis Ende spielbar: Titelbild, sechs Welten, Schlussbildschirm.

| # | Welt | Stand | Besonderheiten |
|---|---|---|---|
| 1 | **London** | fertig | hohe Gebäude, Gewitterwolken mit Blitz, Möwen, Ziel Tower Bridge mit Feuerwerk, Musik „London Bridge“ |
| 2 | **Piratenbucht** | fertig | Palmeninsel, Piratenschiff und Festung mit Kanonen (45° nach oben, ballistische Kugeln mit Rauchwarnung), Krake, der mit Tentakeln nach links schlägt (zwei Posen, Hitbox je Pose), Ziel Schatzinsel, Musik: flotter Shanty im Stil von „Drunken Sailor“ |
| 3 | **Gewitter** (kurz, 650 Spalten) | fertig | dunkler Himmel, Wolkentürme, viele Blitze, starker Wind, Ziel Regenbogen mit Sonne, Musik nach dem Motiv der Toccata |
| 4 | **Höhle** | fertig | Stalagmiten und Stalaktiten (Flappy-Lücken), Fledermäuse, Lava im Vordergrund, Ziel Höhlenausgang mit Tageslicht, Musik: esoterisch (Glockentöne über einem Bordun) |
| 5 | **Mond** | fertig | geringe Schwerkraft, langsamer Wind, UFOs mit Zap-Blitz, Mondlandefähre, Ziel Mondbasis mit Flagge, Musik: Raketenstart und schwebende Linien (im Stil von „Rocket Man“, eigene Komposition) |
| 6 | **New York** (Finale) | fertig | Wolkenkratzer, Zeppelin, Flugzeuge; **King Kong** (wirft Felsbrocken) und **Godzilla** (spuckt Feuerbälle) als Höhepunkte, Ziel Freiheitsstatue, danach „THE END“, Musik: Swing-Fanfare mit Walking Bass (im Stil von „New York, New York“, eigene Komposition) |

Checkpoints bei einem und zwei Dritteln der Strecke: der Tank wird dort nicht aufgefüllt, nach einem Absturz geht es dort mit vollem Tank weiter (Ballon steht sicher in einer Lücke, Level bleibt identisch, Punktestand vom Checkpoint).

Querschnitt: Titel mit Artwork (ROM-Bank 2), Parallax (Wolken oben langsam, Hindernisse im Spieltempo, Boden unten schneller), eigene PSG-Klang-Engine mit Musik pro Welt, Treibstoff mit Fässern am Seil, Fairness-Prüfung der Levelerzeugung, fester Level pro Welt.
Offen: Sandsack, Feinabstimmung der Schwierigkeit (Balance je Welt), Tests auf echter Hardware.

### Monster in der Spielmechanik

Die Monster sind **keine Gegner zum Besiegen**, sondern besondere Bodenhindernisse, die sich in vorhandene Mechaniken einfügen:

- **Auftritt:** Jedes Monster erscheint genau einmal als Höhepunkt (bei 38 und 72 Prozent der Strecke), mit viel Platz davor und danach. Die Liste steht in der Welt (`setpieces`).
- **Sicher von oben:** Wie Gebäude haben sie eine Trefferform aus der Grafik. Wer darüber fliegt, ist sicher.
- **Gefahr durch Würfe:** Kong schleudert Felsbrocken, Godzilla spuckt Feuerbälle. Beides läuft über die Kanonenmechanik: Wurfparabel, Rauchwarnung, ein Bogen, dem man über oder unter durch ausweichen kann.
- **Lebendig:** Arm bzw. Maul werden in zwei Bildern abwechselnd gezeigt (Kachel-Animation).

## Steuerung (Vorschlag)

| Taste | Aktion |
|---|---|
| Knopf 1 (halten) | Brenner: aufsteigen |
| Loslassen | langsam sinken |
| Knopf 2 (halten) | Seil mit Haken herablassen, loslassen = einholen (Fässer angeln, später Schätze/Personen) |
| Sandsack | noch offen: eigene Taste oder Doppeltipp auf Knopf 2 |

## Mechaniken

**Kern (Version 1)**
- Auto-Scroll nach rechts (Tempo wechselt mit dem Wind, siehe unten), Höhensteuerung mit Trägheit
- Hindernisse: Bäume, Häuser (Boden), später Vögel (Luft)
- Kollision = Leben verlieren oder Absturz; Ziel = Levelende erreichen

**Erweiterung**
- Sandsäcke: begrenzt, als Notbremse beim Aufsteigen
- Seil: Schatz bergen oder Person retten (Bonuspunkte / Extraleben)
- **Brennstoff (umgesetzt):** Der Brenner verbraucht Treibstoff (Tank = ca. 20 s Dauerbrennen). Kleine Fässer mit „F“ stehen auf dem Gehweg in den Lücken zwischen den Gebäuden. Das Seil mit Haken (Knopf 2) angelt sie: Das Fass hängt am Haken und wird eingeholt, oben am Korb gibt es +1/3 Tank und +25 Punkte. Ohne Treibstoff kein Steigen mehr.

## Welten / Level

Reihenfolge ist Vorschlag, steigend von leicht nach schwer:

| # | Ort | Hindernisse / Gegner | Besonderheit |
|---|---|---|---|
| 1 | **London** (Einstieg) | Häuser, Bäume, Vögel | Ziel: Tower Bridge mit Feuerwerk, die man überfliegt; Tutorial-Charakter |
| 2 | **Piratenbucht** (umgesetzt) | Palmeninsel, Piratenschiff und Festung mit Kanonen | Kanonenkugeln fliegen in einer Wurfparabel schräg nach oben und fallen ins Wasser; vorher steigt Rauch an der Mündung auf. Ziel: Schatzinsel |
| 3 | New York | Hochhäuser, Flugzeuge | enge Schluchten, viel Höhe nötig |
| 4 | Gewitter | Blitze, Wind | Wind schiebt Ballon vertikal |
| 5 | Höhle | Stalaktiten und Stalagmiten | Decke und Boden gleichzeitig, wie Flappy Bird |
| 6 | Weltraum | Satellit, Ufo | geringe Schwerkraft |
| 7 | Mond | Krater, Ufo | Finale |

**Spezialhindernisse:** King Kong (New York), Godzilla (Meer), Ufo. Es gibt keinen Kampf: Die Monster sind große, auffällige Hindernisse, die man umfliegen muss (z. B. Kong greift mit dem Arm nach dem Ballon, Godzilla steigt aus dem Meer auf, das Ufo schwebt mit Strahl). Pro Welt höchstens eines, als Höhepunkt des Levels.

## Wind (einfach)

Der Wind bestimmt nur, wie schnell die Landschaft vorbeizieht. Er hängt **nicht** von der Höhe ab (Höhenwind-Schichten sind verworfen, siehe unten) und wechselt von Zeit zu Zeit von allein.

- Drei bis vier feste Tempostufen, zum Beispiel Flaute, Brise, Wind, Sturm. Werte sind Vorschläge zum Abstimmen (Pixel pro Frame bei 60 Hz): 0,25 / 0,5 / 1 / 1,5.
- Der Wechsel kommt abschnittsweise aus dem Level (pro Welt eine Grundstufe, dazwischen Wechsel) und wird weich überblendet, nicht abrupt. Ein Hinweis (Fahne, Wolken, Rauch) kündigt ihn an.
- Der Spieler steuert nur die Höhe. Wind ändert das Tempo der Hindernisse, nicht die Steuerung.
- Technik: Geschwindigkeit als Festkomma (z. B. 8.8) und pro Frame zum Scrollwert addieren, ganze Pixel ans VDP-Scrollregister. Keine Division zur Laufzeit.

**Verworfen (Stand jetzt):** Windschichten mit unterschiedlicher Geschwindigkeit je nach Höhe, gegenläufiger Wind und Böen als Spielmechanik. Kann später als Erweiterung zurückkommen.

## Ansicht / Kamera (nah dran)

Die Kamera ist **nah am Ballon**, damit die Flappy-Bird-Idee funktioniert: Hindernisse füllen die Höhe des Bildschirms, und der Spieler weicht ihnen aus, indem er steigt oder sinkt. Weit entfernte Ansicht mit viel leerem Himmel hat das aufgeweicht.

- **Größen** (Bildschirm 256×192): Ballon 24×32, Vögel 16×16, Bäume 32×48, Häuser 48×48, Hochhäuser bis 40×120, Big Ben 32×96, Monster später ähnlich groß wie die Gebäude.
- **Hindernisse füllen die Höhe:** Gebäude und Türme reichen bis in die obere Bildhälfte. Dazwischen liegt die Lücke, durch die man fliegt, mit Höhenunterschieden von Hindernis zu Hindernis.
- **Kanonen:** Schiff und Festung schießen nur, wenn die Mündung noch weit rechts liegt (mindestens 1 Sekunde Flugzeit). Jede Kugel wird so berechnet, dass sie in einer zufälligen Höhe zwischen 64 und 127 an der Ballonspalte vorbeikommt. Der Spieler sieht die ganze Bahn und kann darüber oder darunter durchfliegen.
- **Sprite-Budget:** Der Ballon braucht 12 Sprites (3 breit, 4 hoch), also höchstens 3 pro Zeile. Es bleiben 5 pro Zeile für Gegner. Gebäude kommen aus der Hintergrund-Tilemap.
- **Vertikales Scrolling:** Nur nötig, wenn Level höher als ein Bildschirm sind. Für den Anfang reicht ein Bild Höhe.

### Grafikstil (Inspiration: Rampage, Master System)

- Hohe, flache Gebäude mit klarem Fensterraster, Fenster teils beleuchtet, teils dunkel.
- Mehrere Gebäudetypen: graues Hochhaus, gelbes Haus mit Rundbogenfenstern, rotes Backsteinhaus; dazu Big Ben als Wahrzeichen.
- Dunkle Skyline-Silhouette als Hintergrund hinter den Gebäuden, davor Straße mit Gehweg und Mittelstrich.
- Monster (King Kong, Godzilla) groß wie ein Gebäude, als Hindernis in der Szene, nicht als Gegner.
- Gebäude bekommen keinen Umriss, nur helle und dunkle Töne; Sprites (Ballon, Vögel) haben einen dunklen Umriss, damit sie sich vom Hintergrund lösen.

## Parallax-Scrolling

Ziel: Der Hintergrund (Skyline, Berge, Wolken) zieht langsamer vorbei als die Hindernisse. Das gibt Tiefe und passt zur nahen Kamera.

### Wie es auf dem Master System geht

- Es gibt nur **eine** Hintergrundebene. Parallax entsteht, indem der Bildschirm per **Zeileninterrupt** in waagerechte Bänder geteilt wird, und jedes Band bekommt seinen eigenen horizontalen Scrollwert. SMSlib bringt dafür Funktionen mit (Line-Interrupt-Handler, Zeilenzähler, Scroll-X des Hintergrunds).
- Der Interrupt muss pünktlich feuern und den Scrollwert innerhalb der Austastlücke setzen, sonst flackert die Zeile. Deshalb **wenige Bänder (3–4)**, der Handler bleibt kurz.
- **Wiederholende Bänder sind kostenlos:** Ein Band mit Skyline, Bergen oder Wolken ist 256 px breit und wiederholt sich nahtlos (linker und rechter Rand müssen gleich hoch enden). Es muss nie nachgeladen werden. Nur das Hindernisband braucht fortlaufend neue Spalten.
- Die linke Spalte (8 px) lässt sich beim Scrollen ausblenden, damit man das Nachladen nicht sieht.
- Zusätzliche Tiefe ohne Interrupt: Sonne, Mond oder Erde als Sprite oder fest stehende Tiles; Wolken als Sprites, die langsamer als der Wind ziehen.

### Die Einschränkung

Bänder sind **waagerechte Streifen**. In den Zeilen, in denen Hindernisse stehen, scrollt alles gleich schnell, auch die Skyline in den Lücken dazwischen. Ein hohes Hochhaus vor einer Skyline kann also **nicht** schneller laufen als die Skyline dahinter, solange beide in denselben Bildschirmzeilen liegen.

Daraus folgen drei Möglichkeiten, die sich nach Welt unterscheiden dürfen:

| Variante | Aufbau | Passt zu |
|---|---|---|
| **A: Hohe Hindernisse** | Oben Wolken (langsam), Mitte Hindernisband mit normalem Tempo, unten Straße/Boden (am schnellsten). Die Skyline gehört ins Hindernisband und bekommt kein eigenes Tempo. | Stadtwelten mit hohen Gebäuden (London, New York) |
| **B: Flache Hindernisse** | Hindernisse reichen nur bis etwa zwei Drittel der Höhe. Darüber liegen eigene Bänder für Skyline/Berge (halbes Tempo) und Wolken (Viertel). | Meer, Inseln, Berge, Mond |
| **C: Gemischt** | Hohe Hindernisse hängen von oben herein (Zeppelin, Brücke) oder fliegen als Sprites frei durchs Bild (Vögel, Flugzeug, Ufo). | Wetter, Weltraum |

**Entscheidung: Variante A.** Hohe Hindernisse füllen die Höhe, das Hindernisband bleibt im Spieltempo. Parallax gibt es oben (Wolken, langsam) und unten (Straße/Boden/Wellen, am schnellsten). Die dunkle Skyline aus der Demo steht als Bild hinter den Gebäuden und scrollt mit ihnen. Variante B bleibt als Option für einzelne Welten mit niedrigem Gelände (Meer, Mond), falls dort mehr Tiefe gewünscht ist.

### Ideen pro Welt

| Welt | Fernes Band (langsam) | Nahes Band (schnell) |
|---|---|---|
| London | Skyline-Silhouette, Wolken | Straße, Gehweg, Laternen |
| Meer / Insel | ferne Inseln, Wolken | Wellen (fester Streifen unten) |
| New York | Skyline mit Wahrzeichen im Dunst | Straßenschlucht, Feuerleitern |
| Gewitter | dunkle Wolkenwand, Blitzflackern per Palette | Regenstreifen |
| Höhle | ferne Stalaktiten-Silhouetten | nahe Felsen |
| Weltraum | Sterne (zwei Schichten, langsam), Erde | Satelliten als Sprites |
| Mond | Berge am Horizont, Erde am Himmel | Krater |

### Folgen für die Umsetzung

- Grafik: Skylines und Bergreihen als 256 px breite Streifen, nahtlos wiederholbar. Die Skyline in [tools/art/artdefs.py](tools/art/artdefs.py) ist bereits 256 px breit, ihre Ränder müssen noch aneinander passen.
- Level: Das Hindernisband liegt in einem festen Zeilenbereich je Welt. Dort laufen Hindernisse; darüber und darunter sind die Parallaxbänder.
- Test zuerst: Ein kleiner Prototyp mit drei Bändern (Wolken, Skyline, Straße), um Timing und Flackern auf echtem Hardware-Verhalten (Emulator) zu prüfen, bevor Level darauf aufbauen.

## Fairness: keine unlösbaren Stellen

Der Level wird zufällig erzeugt, soll aber nie unlösbar oder extrem schwer werden. Umgesetzt in [src/main.c](src/main.c):

- **Korridore:** Jeder Abschnitt hat einen erlaubten Höhenbereich für den Ballon (über dem Gebäude, unter der Wolke, dazwischen). Der Generator vergleicht ihn mit dem Korridor des vorherigen Abschnitts. Überlappen beide um weniger als 12 Pixel, wird die Lücke so groß gemacht, dass man mit der echten Ballonphysik (gleiche Zahlen wie die Steuerung) rechtzeitig den Höhenunterschied schafft, auch beim schnellsten Wind.
  - Beispiel: Hinter dem grauen Hochhaus braucht es 9 Spalten, bevor eine Gewitterwolke folgen darf, sonst gelten die normalen 6 bis 9.
- **Blitze** schlagen nur bei Wolken ein, unter denen kein Gebäude steht. Dort kann man immer unten ausweichen.
- **Vögel** starten nur, wenn in den nächsten etwa 30 Spalten kein enger Korridor (unter 40 Pixel) liegt. Sie erscheinen mit mindestens einer Sekunde Reaktionszeit.
- **Treibstoff:** Bei weniger als der Hälfte des Tanks wird sicher ein Fass vor dem Spieler erzeugt, sofern noch keins vor ihm liegt.

Offen: ein Bot-Test am Rechner, der tausende Seeds auf Lösbarkeit prüft. Lohnt sich, wenn die Regeln nicht reichen.

## Machbarkeit auf dem Master System

- **Sprite-Limit 8 pro Zeile**: Ballon (3×4 Sprites, also 3 pro Zeile) plus Gegner schnell am Limit. Gegner sparsam, Hindernisse als **BG-Tilemap**.
- **Scrolling**: VDP scrollt horizontal in Hardware. Level als Tilemap-Streifen, Spalte für Spalte nachladen.
- **Hintergründe wie Häuser, Bäume, Höhle, Skyline** gehören in die Tilemap und sind günstig.
- **Riesenmonster (Kong, Godzilla, Ufo)**: als BG-Tiles oder wenige große Sprites, nicht als Sprite-Haufen. Da sie keine Kämpfe sind, reicht ein einfaches, geskriptetes Auf und Ab.
- **Gewitter/Blitze**: Palettenwechsel für den Blitzeffekt, billig.
- **Sound**: PSG, 3 Töne + Noise. Brenner = Noise, Kanone/Blitz = Noise-Burst, Musik pro Welt kurz und einfach.
- **Speicher**: 8 KB RAM, ROM 32 KB reichen für wenige Welten; mehr Welten brauchen Banking.

## Prioritäten

1. **Prototyp**: Ballon (24×32), Steuerung mit Trägheit, horizontales Scrolling, hohe Gebäude mit Lücken als Hindernisse, Kollision
2. **Parallax-Test (Variante A)**: drei Bänder (Wolken oben langsam, Hindernisband in der Mitte, Straße unten schnell) mit Zeileninterrupt, Flackern prüfen
3. **London komplett**: Level, Vögel, Windwechsel, HUD (Leben, Sandsäcke), Game Over
4. **Sandsack und Seil** (Schatz/Rettung)
5. **Zweite und dritte Welt** (Meer mit Piraten, New York)
6. **Wetter, Höhle, Weltraum**
7. **Spezialhindernisse** (Kong, Godzilla, Ufo)
8. Musik, Titelbild, Feinschliff

## Offene Fragen

- Treibt der Ballon automatisch, oder kann der Spieler auch vor und zurück steuern?
- Brennstoff: Stimmt die Balance (Tankgröße, Abstand der Fässer)? Ist der Hakenweg zu kurz oder zu lang?
- Tod bei Berührung oder Lebensenergie (z. B. 3 Herzen)?
- Ein langes Level pro Welt oder mehrere kurze Abschnitte?
- Punkte, Highscore, Passwort/Fortschritt (kein Batterie-Save vorausgesetzt)?
- Ton der Welt: realistisch, oder bewusst albern (Kong, Godzilla, Ufo in einem Spiel)?
- Name und Look des Ballons (Hauptfigur?)
- Wind: Wie oft wechselt er, und wie stark ist der Unterschied zwischen Flaute und Sturm?
- Hindernis-Abstände: Wie groß sind die Lücken, und wie stark variiert ihre Höhe?

## Nicht übernommen / zurückgestellt

- Mehrere Orte nur namentlich (z. B. weitere Städte): erst nach London und New York
- Satellit und Flugzeug zählen als Hindernisse der Welten 3 und 6, kein eigenes Level


## Nachtrag: Bedrohungen pro Welt
- **Höhle:** Lavakrater schießen Lavabomben in Wurfparabeln (Mechanik der Kanonen, Rauch als Warnung).
- **Mond:** UFOs haben zusätzlich zum Strahl Plasmaschüsse (Funken als Vorwarnung); zweiter, großer Krater.
- **New York:** dichte Hintergrund-Skyline; Zeppelin und Ufos (Außerirdische greifen an, schießen) von oben; Musik: US-Hymne (gemeinfrei).

- **Leben:** drei Leben (kleine Ballons unter dem Tank, `lives` in `main.c`), Absturz = ein Leben weniger und Neustart am Checkpoint; ohne Leben „CONTINUE“ (unendlich): drei Leben, Level von vorn. Test: `TEST_DIE_AT=<Spalte> TEST_DIE_REPEAT=1 AUTOPLAY=1`.
