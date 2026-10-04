#ifndef WORLD_H
#define WORLD_H

// Alles, was sich von Welt zu Welt ändert: Hintergrund-Kacheln und -Palette, Boden, Hindernisse, Ziel, Physik, Wind.
// Die Daten erzeugt tools/gen_assets.py (London in assets.h, weitere Welten in eigenen ROM-Bänken).

typedef struct {                 // Hindernis vom Boden (Gebäude, Insel, Schiff, Stalagmit ...)
  const unsigned int *map;       // Tile-Nummern zeilenweise, unten bündig auf dem Boden
  const unsigned char *prof;     // je Kachelspalte: Oberkante (Bildschirm-y) für die Kollision
  unsigned char w, h;            // Breite/Höhe in Kacheln
  unsigned char hi;              // tiefste erlaubte Ballonhöhe (ypx) beim Überfliegen = niedrigste Oberkante - 30
  unsigned char shot_x, shot_y;  // Mündung (Kanone, Maul, Hand): Pixel von links im Objekt / Bildschirm-y; shot_y 0 = keine
  unsigned char shot_kind;       // Geschoss: 0 Kanonenkugel, 1 Feuerball, 2 Felsbrocken
  const unsigned char *prof2;    // Oberkanten in Animationsbild B (0 = gleich wie prof)
  unsigned char anim_id;         // zugehörige Animation (1 + Index in World.anim), 0 = keine
} Bld;

typedef struct {                 // Animation: ein zusammenhängender Block Kacheln wird zwischen zwei Bildern umgeschaltet
  unsigned char count;           // Anzahl Kacheln, 0 = unbenutzt
  unsigned int tile;             // erste Kachel im VRAM (Bild A liegt in bg_tiles, Bild B hier)
  const unsigned char *frame_b;
} Anim;

typedef struct {                 // hängendes Hindernis (Gewitterwolke, Stalaktit, UFO ...)
  const unsigned int *map;
  const unsigned char *prof;     // je Kachelspalte: Unterkante (Bildschirm-y)
  unsigned char w, h;
  unsigned char top_row;         // Tile-Zeile der Oberkante (mindestens 2)
  unsigned char lo;              // niedrigste erlaubte Ballonhöhe (ypx) = größte Unterkante - 3
  unsigned char bolt_x, bolt_y;  // Blitz bzw. Strahl: x-Versatz im Objekt / Bildschirm-y des Anfangs; bolt_y 0 = keiner
  unsigned char shot_x, shot_y;  // Schussmündung (UFO, Hubschrauber): feuert wie eine Kanone; shot_y 0 = schießt nicht
} Ceil;

typedef struct {
  const unsigned char *bg_tiles; // Welt-Sprites (Gegner), danach Hintergrund-Kacheln; geladen ab BG_TILE_BASE
  unsigned int bg_bytes;
  const unsigned char *bg_pal;   // 16 Bytes
  const unsigned int *bg_band;   // 32 x 19 Kacheln: Hintergrund hinter den Hindernissen (Tile-Zeilen 2..20)
  unsigned int ground[3][4];     // Tile-Zeilen 21..23, je 4 Kacheln im Wechsel (x & 3)
  const unsigned int *far_cloud; // 6 x 2 Kacheln, langsames Band oben
  Bld bld[8];                    // 0 = nichts (nur Decke), 1..6 Hindernisse, 7 = Ziel
  Ceil ceil[3];                  // 0 = keine Decke, 1..2 hängende Hindernisse
  unsigned char kind_bld[8];     // Abschnittsarten (zufällig gewählt): Bodenhindernis
  unsigned char kind_ceil[8];    //                                    hängendes Hindernis
  unsigned char sky;             // Palettenfarbe des Himmels (SMS-Farbbyte)
  unsigned char flash;           // Himmelfarbe beim Aufblitzen
  unsigned char special_finish;  // 1 = Ziel mit Sonderform (London: Tower Bridge mit spitzen Dächern)
  unsigned char down_acc, up_acc;   // Physik: Sinken / Brenner in 1/32 Pixel pro Bild^2
  unsigned char max_down, max_up;   //         Höchsttempo in 1/32 Pixel pro Bild
  unsigned char wind[4];         // Windstufen in 1/16 Pixel pro Bild
  unsigned int level_cols;       // Länge des Levels in Spalten
  unsigned char flyer_tile;      // Gegner im Flug (Möwe, Fledermaus, Flugzeug): erste Sprite-Kachel, Bild B folgt nach w*h Kacheln
  unsigned char flyer_w, flyer_h;   // in Kacheln; flyer_w 0 = keine fliegenden Gegner
  unsigned char flyer_hx0, flyer_hy0, flyer_hx1, flyer_hy1;   // Trefferfläche im Sprite
  unsigned char flyer_fast;      // zusätzliche Geschwindigkeit in 1/16 Pixel pro Bild
  unsigned char music;           // Musikstück (siehe sound.c)
  unsigned char sp_bld[2];       // Höhepunkte: Bodenhindernis (z. B. ein Monster), das genau einmal erscheint ...
  unsigned char sp_at[2];        // ... bei so viel Prozent des Levels
  unsigned char sp_ceil[2];      // dazu hängendes Hindernis (0 = keins)
  Anim anim[3];
  unsigned char align;           // Hindernisse beginnen auf einem Vielfachen dieser Spaltenzahl (Hintergrund wiederholt sich so oft), 0 = egal
} World;

#endif
