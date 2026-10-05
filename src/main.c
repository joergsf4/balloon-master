#include "SMSlib.h"
#include "assets.h"
#include "sound.h"
#include "bank2.h"
#include "bank9.h"
#include "worlds_gen.h"

// Prototyp: Ballon fliegt durch eine endlos scrollende Stadt.
// Knopf 1 / Hoch = Brenner (steigen), sonst sinkt der Ballon langsam. Berührung = Absturz.
//
// Parallax per Zeileninterrupt, drei Bänder (Variante A im Konzept):
//   Zeilen   0..15  ferne Wolken, 1/4 Tempo
//   Zeilen  16..167 Hindernisse und Skyline, Spieltempo
//   Zeilen 168..191 Gehweg und Straße, 1,5-faches Tempo

#define SKY_BACKDROP 14      // Sprite-Palettenplatz mit Himmelblau (SPRITE_PAL in tools/art/palette.py)
#define BALLOON_X    116     // fester Bildschirm-x des Ballons
#define Y_MIN        10       // darunter beginnt die Punkte-/Tankzeile
#define GROUND_Y     168     // Gehweg beginnt in Tile-Zeile 21
#define MAP_TOP      2       // Tile-Zeilen 2..20 werden gestreamt (Hindernisband)
#define MAP_ROWS     19
#define BAND_CLOUDS  16      // erste Bildschirmzeile des Hindernisbands
#define BAND_STREET  168     // erste Bildschirmzeile der Straße (= GROUND_Y)
#define LINE_STEP    8       // Zeileninterrupt alle 8 Zeilen (Zähler 7): 2. Auslösung = Zeile 16, 21. = Zeile 168
#define RING         8
#define MAX_BIRDS    2
#define MAX_BARRELS  4
#define MAX_BALLS    3
#define BALL_G       3        // Schwerkraft der Kanonenkugeln: 3/64 Pixel pro Bild^2
#define MAX_SPARKS   12
#define LEVEL_SEED   0x1D2Bu  // fester Startwert: jede Welt ist bei jedem Versuch derselbe Level
// Länge des Levels steht in der Welt (W->level_cols); zum Testen: LEVEL_COLS=150 ./build.sh überschreibt sie.
#define FUEL_MAX     600      // Brennerbilder bei vollem Tank (ca. 10 s Dauerbrennen; Level sind kurz)
#define FUEL_BARREL  200
#define ROPE_MAX     72

enum { ST_TITLE, ST_PLAY, ST_DEAD, ST_WIN };
enum { B_NONE, B_FINISH = 7 };               // Bodenhindernisse 1..6 stehen in der Welt, 7 = Ziel

// ---------------------------------------------------------------- Welten
static const World *W = &world_london;   // aktuelle Welt: Hindernisse, Hintergrund, Boden, Ziel

#ifndef START_WORLD
#define START_WORLD 0                    // zum Testen: START_WORLD=1 ./build.sh beginnt in der Piratenbucht
#endif
static unsigned char world_idx;
static unsigned char anim_pos[3];       // bereits geladene Kacheln des gerade umgeschalteten Blocks (255 = fertig)
static unsigned char anim_state[3];     // welches der zwei Bilder gerade im VRAM liegt (0 = A)
#ifdef MONSTER_TEST                       // Test-ROM mit den drei Monstern: Piratenbucht (Krake), dann New York (Riesenaffe, Riesenechse)
#define NEXT_WORLD(i) ((i) == 1 ? 5 : (i) + 1)
#else
#define NEXT_WORLD(i) ((i) + 1)
#endif
#define START_LIVES 3
static unsigned char lives;               // verbleibende Leben (Anzeige: kleine Ballons unter dem Tank)
static unsigned char cp_idx, cp_msg;     // erreichte Checkpoints (0..2) / Anzeigedauer der Meldung
static unsigned int cp_trigger[2];       // Spalten, ab denen ein Checkpoint gilt: 1/3 und 2/3 der Strecke
static unsigned int saved_bonus;         // Bonuspunkte beim letzten Checkpoint

// Welt wählen: Weltdaten liegen teils in einer ROM-Bank, die vor jedem Zugriff eingeblendet sein muss
static void select_world(unsigned char i) {
  world_idx = i;
  cp_idx = 0;                                    // neue Welt: kein Checkpoint
  if (world_bank[i]) SMS_mapROMBank(world_bank[i]);
  W = worlds[i];
  snd_track(W->music);                           // jede Welt hat ihre eigene Musik
}

#define CORR_MARGIN  12       // so viel Spielraum (px) soll der nächste Korridor mindestens bieten

typedef struct {
  unsigned int start;      // erste Welt-Spalte
  unsigned char w;         // Breite in Spalten, 0 = unbenutzt
  unsigned char bld;       // Bodenhindernis (Index in W->bld), 0 = keins
  unsigned char ceil;      // hängendes Hindernis (Index in W->ceil), 0 = keins
  unsigned char lo, hi;    // Korridor: erlaubte Ballonhöhe (ypx) beim Durchfliegen dieses Abschnitts
} Seg;

static unsigned int level_len, intro_end, mid_start, finale_start;   // Levellänge und Abschnitte (in Spalten)

static Seg ring[RING];
static unsigned char ring_head;
static unsigned int gen_end;          // erste Spalte hinter dem letzten erzeugten Abschnitt
static unsigned int rng, rng_lvl;
static unsigned int dcol;             // ganze Spalten gescrollt
static unsigned int colbuf[MAP_ROWS];

typedef struct {
  int x;                // Bildschirm-x der linken Kante
  unsigned char y;
  unsigned char on;
} Bird;
typedef struct {
  unsigned int col;     // Welt-Spalte der linken Kante
  unsigned char y;      // Bildschirm-y der Oberkante (Fass steht auf dem Gehweg)
  unsigned char on;
} Barrel;
static Barrel barrels[MAX_BARRELS];
static unsigned char barrel_head, since_barrel;
static unsigned int fuel, bonus;
static unsigned char rope, carrying;      // carrying: ein Fass hängt am Haken

typedef struct {
  int x, y;
  signed char vx, vy;
  unsigned char life, col;
} Spark;
static Spark sparks[MAX_SPARKS];

typedef struct {
  int x, y;             // Position in 1/64 Pixel (linke obere Ecke auf dem Bildschirm)
  int vx, vy;           // Geschwindigkeit in 1/64 Pixel pro Bild; vy wächst um BALL_G (Schwerkraft)
  unsigned char on;
  unsigned char kind;   // 0 Kanonenkugel, 1 Feuerball, 2 Felsbrocken
} Ball;
static Ball balls[MAX_BALLS];

static Bird birds[MAX_BIRDS];
static unsigned char bird_timer, bird_sub;

static unsigned char rand8(void) {
  rng = rng * 25173u + 13849u;
  return (unsigned char)(rng >> 8);
}

// Eigener Zufallsgenerator nur für die Levelerzeugung: unabhängig davon, was der Spieler tut
static unsigned char lvl_rand8(void) {
  rng_lvl = rng_lvl * 25173u + 13849u;
  return (unsigned char)(rng_lvl >> 8);
}

static void spawn_barrel(Seg *s) {
  Barrel *b = &barrels[barrel_head];
  barrel_head = (barrel_head + 1) & (MAX_BARRELS - 1);
  b->on = 1;
  b->col = s->start - 4 + (rand8() & 1);     // in der Lücke vor dem Abschnitt, auf dem Gehweg
  b->y = (unsigned char)(GROUND_Y - 16);   // Fass (16 px hoch) steht auf dem Gehweg
}

static unsigned char prev_lo, prev_hi;   // Korridor des vorherigen Abschnitts
static unsigned char sp_done, last_special, sp_follow;   // Höhepunkte (z. B. Monster) bereits erschienen / letzter Abschnitt war einer

// Bilder, die der Ballon aus der Ruhe braucht, um px Pixel zu sinken (down) oder zu steigen.
// Gleiche Zahlen wie update_balloon (Physik der aktuellen Welt).
static unsigned int frames_to_shift(unsigned char px, unsigned char down) {
  int y = 0, v = 0, goal = px * 32;
  unsigned int t = 0;
  while (t < 600) {
    t++;
    if (down) {
      v += W->down_acc;
      if (v > W->max_down) v = W->max_down;
    } else {
      v += W->up_acc;
      if (v > W->max_up) v = W->max_up;
    }
    y += v;
    if (y >= goal) break;
  }
  return t;
}

// Lücke (in Spalten) so groß machen, dass man vom vorherigen in den neuen Korridor kommt, auch beim stärksten
// Wind der Welt (wind[3] in 1/16 Pixel pro Bild; eine Spalte = 8 Pixel = 128 Einheiten).
static unsigned char gap_for_corridor(unsigned char lo, unsigned char hi, unsigned char gap) {
  int ov_lo = lo, ov_hi = hi, overlap, shift;
  unsigned char down;
  unsigned int cols;
  if (prev_lo > ov_lo) ov_lo = prev_lo;
  if (prev_hi < ov_hi) ov_hi = prev_hi;
  overlap = ov_hi - ov_lo;
  if (overlap >= CORR_MARGIN) return gap;               // Korridore überlappen genug: kein Höhenwechsel nötig
  shift = CORR_MARGIN - overlap;
  if (shift > 120) shift = 120;
  down = ((int)lo + hi) > ((int)prev_lo + prev_hi);
  cols = (frames_to_shift((unsigned char)shift, down) * W->wind[3] + 127) >> 7;   // bei dem stärksten Wind der Welt
  if (cols > 30) cols = 30;
  if (cols > gap) return (unsigned char)cols;
  return gap;
}

static unsigned char barrel_ahead(void) {
  unsigned char i;
  for (i = 0; i < MAX_BARRELS; i++)
    if (barrels[i].on && (int)(barrels[i].col - dcol) > 14) return 1;
  return 0;
}

static void gen_segment(void) {
  Seg *s = &ring[ring_head];
  unsigned char k = lvl_rand8() & 7;
  unsigned char gap = 5 + (lvl_rand8() & 3);                 // 5..8 Spalten (die Korridor-Prüfung vergrößert bei Bedarf)
  unsigned char rb = lvl_rand8();
  unsigned char lo, hi, w, special = 0;
#ifdef FORCE_KIND                                               // nur zum Testen: immer dieselbe Abschnittsart
  k = FORCE_KIND;
#endif
  if (gen_end >= level_len) {                                 // Ziel der Welt
    s->bld = B_FINISH;
    s->ceil = 0;
    lo = Y_MIN;
    hi = W->bld[B_FINISH].hi;
    gap = gap_for_corridor(lo, hi, 14);
    if (gap < 14) gap = 14;
  } else {
    if (gen_end < intro_end && W->kind_ceil[k] && !W->kind_ceil[0]) k = 0;   // Anfang: einfacher Abschnitt
    s->bld = W->kind_bld[k];
    s->ceil = W->kind_ceil[k];
    if (sp_follow) {                                          // Höhepunkt, Teil 2: Wolke gleich hinter dem Monster (versetzt, nicht darüber)
      sp_follow = 0;
      s->bld = 0;
      s->ceil = W->sp_ceil[sp_done - 1];
    } else if (sp_done < 2 && W->sp_bld[sp_done] && gen_end >= (level_len / 100) * W->sp_at[sp_done]) {
      s->bld = W->sp_bld[sp_done];                            // Höhepunkt (Monster): genau einmal, mit viel Platz davor und danach
      s->ceil = 0;
      sp_follow = W->sp_ceil[sp_done] != 0;
      sp_done++;
      special = 1;
      gap += 4;
    } else if (last_special) {
      gap += 4;
    }
    if (gen_end < intro_end) gap += 2;                        // Anfang: etwas mehr Platz
    if (gen_end > mid_start) gap--;
    if (gen_end > finale_start) gap--;                        // Schluss: enger
    if (gap < 5) gap = 5;
    lo = Y_MIN;
    hi = W->bld[s->bld].hi;
    if (s->ceil) lo = W->ceil[s->ceil].lo;
    if (hi < lo + 30) {                                       // unpassierbare Kombination: Decke weglassen
      s->ceil = 0;
      lo = Y_MIN;
    }
    gap = gap_for_corridor(lo, hi, gap);
  }
  last_special = special;
  s->lo = lo;
  s->hi = hi;
  prev_lo = lo;
  prev_hi = hi;
  s->start = gen_end + gap;
  if (W->align) s->start = (s->start + W->align - 1) & (unsigned int)(~(unsigned int)(W->align - 1));   // passend zum Hintergrundmuster
  w = s->bld ? W->bld[s->bld].w : 0;
  if (s->ceil && W->ceil[s->ceil].w > w) w = W->ceil[s->ceil].w;
  s->w = w;
  if (s->bld == B_FINISH) {
    gen_end = 0xFFF0;                                         // danach entsteht nichts mehr
  } else {
    ++since_barrel;
    if (since_barrel >= 4 || !(rb & 7) || (fuel < 300 && since_barrel >= 2 && !barrel_ahead())) {
      since_barrel = 0;                                       // bei knappem Tank kommt sicher bald ein Fass
      spawn_barrel(s);
    }
    gen_end = s->start + s->w;
  }
  ring_head = (ring_head + 1) & (RING - 1);
}

// Hintergrund hinter den Hindernissen (Skyline und feste Wolken wiederholen sich alle 32 Spalten)
static unsigned int bg_tile(unsigned char m, unsigned char r) {
  return W->bg_band[(r - MAP_TOP) * 32 + m];            // r = Tile-Zeile 2..20
}

// Spalte c der Welt in colbuf aufbauen (Hindernisse über dem Hintergrund)
static void prepare_column(unsigned int c) {
  unsigned char m = c & 31, r, i, k, top, h, w;
  unsigned int t;
  Seg *s;
  while (gen_end <= c) gen_segment();
  for (r = 0; r < MAP_ROWS; r++) colbuf[r] = bg_tile(m, r + MAP_TOP);
  for (i = 0; i < RING; i++) {
    s = &ring[i];
    if (s->w && c >= s->start && c < s->start + s->w) {
      k = (unsigned char)(c - s->start);
      if (s->bld && k < W->bld[s->bld].w) {
        h = W->bld[s->bld].h;
        w = W->bld[s->bld].w;
        top = MAP_ROWS - h;
        for (r = 0; r < h; r++) {
          t = W->bld[s->bld].map[r * w + k];
          if (t) colbuf[top + r] = t;                         // Tile 0 = Himmel: Skyline dahinter bleibt sichtbar
        }
      }
      if (s->ceil && k < W->ceil[s->ceil].w) {                // hängendes Hindernis
        for (r = 0; r < W->ceil[s->ceil].h; r++) {
          t = W->ceil[s->ceil].map[r * W->ceil[s->ceil].w + k];
          top = W->ceil[s->ceil].top_row - MAP_TOP + r;
          if (t && top < MAP_ROWS) colbuf[top] = t;
        }
      }
      break;
    }
  }
}

static void upload_column(unsigned int c) {
  SMS_loadTileMapColumn(c & 31, MAP_TOP, colbuf, MAP_ROWS);
}

// ---------------------------------------------------------------- Spielzustand
static unsigned char state;
static unsigned char demo, demo_next;   // Vorführung läuft / nächste Welt der Vorführung
static unsigned int frame;
static unsigned char sub;             // 1/16 Pixel innerhalb einer Spalte (0..127)
static int y32, vy;                   // Höhe in 1/32 Pixel, Geschwindigkeit in 1/32 Pixel pro Frame
static unsigned char wind_cur, wind_tgt;
static unsigned int wind_timer;
static unsigned char dead_timer;
static unsigned char cont_count, cont_frames;   // Continue-Countdown (9..0) und Bilder bis zur nächsten Sekunde
static unsigned char pj_col, pj_w, pj_row, pj_rows;   // Auftrag: dunkle Textfläche in den Hintergrund schreiben
static unsigned char burner;
static unsigned char new_col;
static unsigned char flash, flash_on;      // Himmel-Aufblitzen (Frames), aktueller Palettenzustand
static unsigned int best;
static unsigned int cl16, st16;       // Scrollstand der Wolken- und Straßenband in 1/16 Pixel (0..4095)

// Scrollwerte der drei Bänder: *_next schreibt das Spiel, der Frame-Interrupt übernimmt sie atomar
static volatile unsigned char sc_top, sc_main, sc_street;
static volatile unsigned char band;
static unsigned char next_top, next_main, next_street;

static void frame_handler(void) {          // Beginn der Austastlücke: Bänder neu starten
  sc_top = next_top;
  sc_main = next_main;
  sc_street = next_street;
  band = 0;
  INLINE_SMS_setBGScrollX(sc_top);
}

static void line_handler(void) {           // alle 8 Zeilen; schaltet bei Zeile 16 und 168 um
  band++;
  if (band == 2) INLINE_SMS_setBGScrollX(sc_main);         // ab Zeile 16: Hindernisband
  else if (band == 21) INLINE_SMS_setBGScrollX(sc_street); // ab Zeile 168: Straße
}

// Beim Laden großer Datenmengen ins VRAM dürfen unsere Handler nicht dazwischenfunken: Sie schreiben ins
// Steuerregister des VDP und würden die laufende Adresse verstellen (SMS_VRAMmemcpy schützt nur das Setzen der Adresse).
static void irq_off(void) {
  SMS_disableLineInterrupt();
  SMS_setFrameInterruptHandler(0);
}

static void irq_on(unsigned char with_lines) {
  SMS_setFrameInterruptHandler(frame_handler);
  if (with_lines) SMS_enableLineInterrupt();
}

static void new_game(void) {
  unsigned int c;
  unsigned char i;
  rng ^= frame * 7u + 1u;
  rng_lvl = LEVEL_SEED;
#ifdef LEVEL_COLS
  level_len = LEVEL_COLS;
#else
  level_len = W->level_cols;
#endif
  cp_trigger[0] = level_len / 3;
  cp_trigger[1] = (level_len / 3) * 2;
  intro_end = level_len / 7;
  mid_start = (level_len / 5) * 2;
  finale_start = level_len - level_len / 7;
  for (i = 0; i < MAX_BALLS; i++) balls[i].on = 0;
  for (i = 0; i < MAX_SPARKS; i++) sparks[i].life = 0;
  for (i = 0; i < RING; i++) ring[i].w = 0;
  ring_head = 0;
  gen_end = 18;
  prev_lo = Y_MIN;
  prev_hi = 137;
  sp_done = 0;
  sp_follow = 0;
  last_special = 0;
  since_barrel = 2;
  barrel_head = 0;
  for (i = 0; i < MAX_BARRELS; i++) barrels[i].on = 0;
  fuel = FUEL_MAX;
  flash = 0;
  bonus = 0;
  rope = 0;
  carrying = 0;
  bird_timer = 150;
  for (i = 0; i < MAX_BIRDS; i++) birds[i].on = 0;
  dcol = 0;
  sub = 0;
  cl16 = st16 = 0;
  y32 = 90 * 32;
  vy = 0;
  if (cp_idx) {                                   // Wiedereinstieg am letzten Checkpoint: Level ist fest, also unsichtbar bis dorthin erzeugen
    unsigned int from = cp_trigger[cp_idx - 1] + 18, anchor = 0xFFFF;   // Ballon steht 18 Spalten vor dem Abschnitt, also nie vor dem Checkpoint
    unsigned char ai = 0;
    while (gen_end <= from + 40) gen_segment();
    for (i = 0; i < RING; i++)                    // erster Abschnitt ab dem Checkpoint
      if (ring[i].w && ring[i].start >= from && ring[i].start < anchor) {
        anchor = ring[i].start;
        ai = i;
      }
    if (anchor == 0xFFFF) anchor = from;
    dcol = anchor - 18;                           // Ballon steht dann mitten in der Lücke vor diesem Abschnitt
    y32 = (((int)ring[ai].lo + ring[ai].hi) / 2) * 32;
    if (y32 > 110 * 32) y32 = 110 * 32;
    bonus = saved_bonus;
  } else {
    saved_bonus = 0;
  }
  wind_cur = wind_tgt = W->wind[0];
  wind_timer = 0;
  new_col = 0;
  snd_music(1);
  irq_off();
  SMS_displayOff();
  for (c = dcol + 1; c <= dcol + 32; c++) {   // die Spalte dcol + 32 liegt in der Karten-Spalte des linken Randes
    prepare_column(c);
    upload_column(c);
  }
  next_top = next_street = 0;
  next_main = (unsigned char)(0 - ((dcol & 31) << 3));
  sc_top = sc_street = 0;
  sc_main = next_main;
  SMS_setBGScrollX(sc_main);
  SMS_displayOn();
  irq_on(1);
}

static void update_scroll_and_wind(void) {
  wind_timer++;
  if (wind_timer >= 480 && state != ST_WIN) {
    wind_timer = 0;
    wind_tgt = W->wind[rand8() & 3];
  }
  if (!(frame & 7)) {                  // Tempo weich angleichen
    if (wind_cur < wind_tgt) wind_cur++;
    else if (wind_cur > wind_tgt) wind_cur--;
  }
  sub += wind_cur;
  cl16 = (cl16 + (wind_cur >> 2)) & 0x0FFF;                    // ferne Wolken: 1/4 Tempo
  st16 = (st16 + wind_cur + (wind_cur >> 1)) & 0x0FFF;         // Straße: 1,5-faches Tempo
  if (sub >= 128) {
    sub -= 128;
    dcol++;
    prepare_column(dcol + 32);
    new_col = 1;
  }
}

static void update_balloon(unsigned int keys) {
  burner = (keys & (PORT_A_KEY_1 | PORT_A_KEY_UP)) != 0;
  if (burner) {
    if (fuel) fuel--;
    else burner = 0;                  // Tank leer
  }
  if (fuel && fuel < 150 && !(frame & 63)) snd_sfx(SFX_LOWFUEL);   // Warnton bei fast leerem Tank
  if (burner) vy -= W->up_acc;
  else vy += W->down_acc;
  if (vy < -(int)W->max_up) vy = -(int)W->max_up;
  if (vy > (int)W->max_down) vy = W->max_down;
  y32 += vy;
  if (y32 < Y_MIN * 32) {
    y32 = Y_MIN * 32;
    vy = 0;
  }
}

#define ROPE_OUT_MAX  180        // das Seil darf höchstens 3 Sekunden am Stück draußen sein (Ausfahren + Einholen) ...
#define ROPE_LOCK     60         // ... danach ist es noch 1 Sekunde gesperrt
static unsigned int rope_out;
static unsigned char rope_lock;

static void update_rope_and_barrels(unsigned int keys) {
  unsigned char i, step = carrying ? 2 : 3;
  int ypx = y32 >> 5, bx, hy1;
  Barrel *b;
  if (rope_lock) {
    rope_lock--;
    keys &= ~PORT_A_KEY_2;
  }
  if (rope) {
    if (rope_out < 65535) rope_out++;
    if (rope_out >= ROPE_OUT_MAX) {                    // zu lange draußen: einholen erzwingen und kurz sperren
      rope_lock = ROPE_LOCK;
      keys &= ~PORT_A_KEY_2;
    }
  } else {
    rope_out = 0;
  }
  if (keys & PORT_A_KEY_2) {
    if (rope < ROPE_MAX) rope += 2;
  } else if (rope >= step) {
    rope -= step;
  } else {
    rope = 0;
  }
  if (carrying) {
    if (rope < 10) {                                   // Fass ist oben am Korb angekommen
      carrying = 0;
      snd_sfx(SFX_REFUEL);
      fuel += FUEL_BARREL;
      if (fuel > FUEL_MAX) fuel = FUEL_MAX;
      bonus += 25;
    }
    return;
  }
  hy1 = ypx + 32 + rope;                               // Unterkante des Hakens
  for (i = 0; i < MAX_BARRELS; i++) {
    b = &barrels[i];
    if (!b->on) continue;
    bx = (int)(b->col - dcol) * 8 - (sub >> 4);
    if (bx < -16) {
      b->on = 0;
      continue;
    }
    if (rope && BALLOON_X + 4 < bx + 13 && BALLOON_X + 20 > bx + 3 && hy1 - 8 < b->y + 16 && hy1 > b->y + 1) {
      b->on = 0;                                       // eingehakt: das Fass hängt jetzt am Seil
      carrying = 1;
      snd_sfx(SFX_CATCH);
    }
  }
}

// Gemeinsamer Korridor aller Abschnitte, die der Vogel auf seinem Weg zum Ballon überfliegt: *lo = größte Untergrenze,
// *hi = kleinste Obergrenze (Ballonhöhe in Pixel). Ist hi - lo klein, gibt es keine gerade Strecke durch alle.
static void bird_window(int *lo, int *hi) {
  unsigned char i;
  int left;
  *lo = 0;
  *hi = 400;
  for (i = 0; i < RING; i++) {
    if (!ring[i].w) continue;
    left = (int)(ring[i].start - dcol) * 8 - (sub >> 4);
    if (left + ring[i].w * 8 > BALLOON_X - 24 && left < BALLOON_X + 200) {
      if (ring[i].lo > *lo) *lo = ring[i].lo;
      if (ring[i].hi < *hi) *hi = ring[i].hi;
    }
  }
}

static void update_birds(void) {
  int clo, chi, y;
  unsigned char try_;
  unsigned char i, spd = wind_cur + W->flyer_fast, step;   // fliegende Gegner sind etwas schneller als die Landschaft
  if (!W->flyer_w) return;
  step = (bird_sub + spd) >> 4;
  bird_sub = (bird_sub + spd) & 15;
  for (i = 0; i < MAX_BIRDS; i++) {
    if (!birds[i].on) continue;
    birds[i].x -= step;
    if (birds[i].x < -(int)(W->flyer_w * 8)) birds[i].on = 0;
  }
  if (bird_timer) {
    bird_timer--;
    return;
  }
  bird_timer = 90 + rand8();
  if (dcol > finale_start) bird_timer = 60 + (rand8() >> 1);
  if (dcol < intro_end) return;
  bird_window(&clo, &chi);
  if (chi - clo < 30) {                  // kein gemeinsamer Durchflug: später noch einmal versuchen
    bird_timer = 30;
    return;
  }
  for (i = 0; i < MAX_BIRDS && birds[i].on; i++) ;
  if (i == MAX_BIRDS) return;
  for (try_ = 0; try_ < 6; try_++) {       // Höhe so wählen, dass im gemeinsamen Korridor über oder unter dem Vogel Platz bleibt
    y = 24 + (rand8() >> 1);
    if (chi - (y + 20) >= 12 || (y - 34) - clo >= 12) {
      birds[i].on = 1;
      birds[i].x = 248;
      birds[i].y = y;
      return;
    }
  }
  bird_timer = 30;
}

// Blitzzyklus einer Gewitterwolke (128 Bilder): 64..87 Funken als Warnung, 88..99 Blitz (gefährlich)
static unsigned char cloud_phase(const Seg *s) {
  return (unsigned char)(frame + (unsigned char)(s->start * 53)) & 127;
}

static void update_lightning(void) {
  unsigned char i, t;
  int left;
  for (i = 0; i < RING; i++) {
    if (!ring[i].w || !ring[i].ceil || ring[i].bld || !W->ceil[ring[i].ceil].bolt_y) continue;
    left = (int)(ring[i].start - dcol) * 8 - (sub >> 4);
    if (left < -56 || left > 255) continue;
    t = cloud_phase(&ring[i]);
    if (t == 88 || t == 95) flash = 3;
    if (t == 88) snd_sfx(SFX_THUNDER);
    else if (t >= 64 && t < 88 && !(t & 7)) snd_sfx(SFX_SPARK);
  }
  if (flash) flash--;
}

// Kanonen von Schiff und Festung. Phase 0..127 je Objekt; ab 96 steigt Rauch auf (Warnung), bei 112 fällt der Schuss.
// Es wird nur geschossen, wenn die Mündung weit genug rechts liegt, damit genug Zeit zum Ausweichen bleibt.
static unsigned char shooter_phase(const Seg *s) {
  return (unsigned char)(frame + (unsigned char)(s->start * 41)) & 127;
}

// Schuss von (mx, y0) auf die Ballonspalte: Flugzeit T und Zielhöhe ht so wählen, dass die Kugel dort ankommt. Der
// Spieler sieht die Bahn ab der Mündung (ca. 1 s) und kann über oder unter ihr durchfliegen.
static void fire_ball(int mx, int y0, unsigned char kind) {
  unsigned char j, t;
  int ht, dx;
  for (j = 0; j < MAX_BALLS; j++) {
    if (balls[j].on) continue;
    t = 50 + (rand8() & 15);
    ht = 64 + (rand8() & 63);
    dx = (mx - 8) - 124;
    balls[j].x = (mx - 8) * 64;
    balls[j].y = y0 * 64;
    balls[j].vx = (dx * 64) / t;
    balls[j].vy = -(((y0 - ht) * 64 + (BALL_G * t * t) / 2) / t);
    balls[j].on = 1;
    balls[j].kind = kind;
    snd_sfx(SFX_CANNON);
    break;
  }
}

static void update_cannons(void) {
  unsigned char i;
  int mx;
  const Bld *b;
  for (i = 0; i < MAX_BALLS; i++) {                // Wurfparabel: seitlich konstant, senkrecht mit Schwerkraft
    if (!balls[i].on) continue;
    balls[i].x -= balls[i].vx;
    balls[i].y += balls[i].vy;
    balls[i].vy += BALL_G;
    if (balls[i].x < -8 * 64 || balls[i].y > 190 * 64) balls[i].on = 0;
  }
  for (i = 0; i < RING; i++) {
    if (!ring[i].w) continue;
    if (ring[i].bld) {
      b = &W->bld[ring[i].bld];
      if (b->shot_y) {
        mx = (int)(ring[i].start - dcol) * 8 - (sub >> 4) + b->shot_x;
        if (mx >= 200 && mx <= 248 && (shooter_phase(&ring[i]) == 112 || (b->shot_kind == 3 && shooter_phase(&ring[i]) == 122)))
          fire_ball(mx, b->shot_y - 4, b->shot_kind);
      }
    }
    if (ring[i].ceil && W->ceil[ring[i].ceil].shot_y) {     // UFO, Hubschrauber: schießt von oben schräg nach unten
      mx = (int)(ring[i].start - dcol) * 8 - (sub >> 4) + W->ceil[ring[i].ceil].shot_x;
      if (mx >= 190 && mx <= 248 && cloud_phase(&ring[i]) == 116) fire_ball(mx, W->ceil[ring[i].ceil].shot_y, 1);
    }
  }
}

// Steht gerade ein Hindernis mit dieser Animation (1-basiert) im Bild?
static unsigned int anim_seg;           // Anfangsspalte des gerade sichtbaren Hindernisses mit dieser Animation (von anim_visible)

static unsigned char anim_visible(unsigned char id) {
  unsigned char i;
  int left;
  for (i = 0; i < RING; i++) {
    if (!ring[i].w || !ring[i].bld || W->bld[ring[i].bld].anim_id != id) continue;
    left = (int)(ring[i].start - dcol) * 8 - (sub >> 4);
    if (left < 250 && left + ring[i].w * 8 > 0) {
      anim_seg = ring[i].start;
      return 1;
    }
  }
  return 0;
}

// Laut der Monster, wenn sie in die zweite Pose wechseln (Zuschlagen, Brüllen): Krake in Welt 2, Riesenaffe und Riesenechse in New York
static unsigned int roar_seg = 0xFFFF;                 // Abschnitt, in dem Riesenechse zuletzt gebrüllt hat

static unsigned char monster_sfx(unsigned char i) {
  if (world_idx == 1) return SFX_SPLASH;
  if (world_idx == 5) return SFX_KONG;                  // (Riesenechse siehe Hauptschleife)
  return SFX_NONE;
}

static unsigned char passed_finish(void) {
  unsigned char i;
  int l;
  for (i = 0; i < RING; i++) {
    if (!ring[i].w || ring[i].bld != B_FINISH) continue;
    l = (int)(ring[i].start - dcol) * 8 - (sub >> 4);
    if (W->special_finish) {
      if (l + 128 < BALLOON_X) return 1;                      // Tower Bridge: ganz durchflogen
    } else if (l < BALLOON_X + 40 || l + ring[i].w * 8 <= 252) {
      return 1;                                               // sonst: Ziel ist erreicht, sobald das Objekt im Bild steht (man kommt nicht hin)
    }
  }
  return 0;
}

// Feuerwerk nach dem Ziel: Bursts aus je 6 Funken
static unsigned char win_timer, burst_timer, burst_col;
static unsigned int win_bonus;
static const signed char burst_dx[6] = { 2, 1, -1, -2, -1, 1 };
static const signed char burst_dy[6] = { 0, 2, 2, 0, -2, -2 };
static const unsigned char spark_tile[3] = { SPARK_Y_BIG, SPARK_R_BIG, SPARK_W_BIG };

static void spawn_burst(void) {
  unsigned char i, n = 0;
  int cx = 48 + (rand8() >> 1), cy = 20 + (rand8() >> 2);
  if (++burst_col >= 3) burst_col = 0;
  for (i = 0; i < MAX_SPARKS && n < 6; i++) {
    if (sparks[i].life) continue;
    sparks[i].x = cx;
    sparks[i].y = cy;
    sparks[i].vx = burst_dx[n];
    sparks[i].vy = burst_dy[n];
    sparks[i].life = 50;
    sparks[i].col = burst_col;
    n++;
  }
  snd_sfx(SFX_POP);
}

static void update_sparks(void) {
  unsigned char i;
  for (i = 0; i < MAX_SPARKS; i++) {
    if (!sparks[i].life) continue;
    if (!(frame & 1)) {
      sparks[i].x += sparks[i].vx;
      sparks[i].y += sparks[i].vy;
    }
    sparks[i].life--;
  }
  if (burst_timer) {
    burst_timer--;
  } else {
    burst_timer = 28;
    spawn_burst();
  }
}

// Form des Ballons als fünf Streifen (Koordinaten im 24x32-Sprite). Etwas kleiner als die Grafik,
// damit knappe Berührungen nicht als Treffer zählen. Oben y = 3 und unten y = 30 passen zu den Korridoren.
static const unsigned char sl_x0[5] = { 7, 4, 3, 6, 7 };
static const unsigned char sl_x1[5] = { 17, 20, 21, 18, 17 };
static const unsigned char sl_y0[5] = { 3, 6, 10, 17, 23 };
static const unsigned char sl_y1[5] = { 6, 10, 17, 23, 30 };

// Berührt der Ballon das Rechteck [x0,x1) x [y0,y1) (Bildschirmkoordinaten)?
static unsigned char balloon_hits(int x0, int y0, int x1, int y1) {
  unsigned char i;
  int ypx = y32 >> 5;
  for (i = 0; i < 5; i++)
    if (BALLOON_X + sl_x0[i] < x1 && BALLOON_X + sl_x1[i] > x0 && ypx + sl_y0[i] < y1 && ypx + sl_y1[i] > y0)
      return 1;
  return 0;
}

// Turm der Tower Bridge (32 px breit, Oberkante y = 72) mit spitzem Dach: gestufte Streifen, etwas kleiner als die Grafik
static unsigned char tower_hit(int x) {
  int cx = x + 16;
  return balloon_hits(cx - 3, 76, cx + 3, 81) || balloon_hits(cx - 6, 81, cx + 6, 85) ||
         balloon_hits(cx - 10, 85, cx + 10, 90) || balloon_hits(x, 90, x + 32, 400);
}

// Hindernis über seine Oberkanten-Profile prüfen (je 8-px-Spalte ein eigener Wert)
static unsigned char bld_hits(const Bld *b, int left) {
  unsigned char c;
  int x0;
  for (c = 0; c < b->w; c++) {
    x0 = left + c * 8;
    if (x0 >= BALLOON_X + 24 || x0 + 8 <= BALLOON_X) continue;
    if (balloon_hits(x0, (b->anim_id && anim_state[b->anim_id - 1]) ? b->prof2[c] : b->prof[c], x0 + 8, 400)) return 1;
  }
  return 0;
}

static unsigned char crashed(void) {
  unsigned char i, t;
  int left, right;
  Seg *s;
  if ((y32 >> 5) + 30 >= GROUND_Y) return 1;
  for (i = 0; i < MAX_BALLS; i++)
    if (balls[i].on && balloon_hits((balls[i].x >> 6) + 1, (balls[i].y >> 6) + 1, (balls[i].x >> 6) + 7, (balls[i].y >> 6) + 7))
      return 1;
  for (i = 0; i < MAX_BIRDS; i++)                              // Vogel: nur der Körper zählt, nicht die Flügelspitzen
    if (birds[i].on && W->flyer_w &&
        balloon_hits(birds[i].x + W->flyer_hx0, birds[i].y + W->flyer_hy0, birds[i].x + W->flyer_hx1, birds[i].y + W->flyer_hy1))
      return 1;
  for (i = 0; i < RING; i++) {
    s = &ring[i];
    if (!s->w) continue;
    left = (int)(s->start - dcol) * 8 - (sub >> 4);
    right = left + s->w * 8;
    if (left >= BALLOON_X + 24 || right <= BALLOON_X) continue;
    if (s->bld == B_FINISH && !W->special_finish) continue;     // Regenbogen, Höhlenausgang ...: nur Kulisse, keine Kollision
    if (s->bld == B_FINISH && W->special_finish) {             // London: Tower Bridge mit spitzen Türmen und Laufsteg
      if (tower_hit(left) || tower_hit(left + 96)) return 1;
      if (balloon_hits(left + 32, 96, left + 96, 400)) return 1;
      continue;
    }
    if (s->bld && bld_hits(&W->bld[s->bld], left)) return 1;
    if (s->ceil) {
      const Ceil *cl = &W->ceil[s->ceil];
      unsigned char c;
      int x0;
      for (c = 0; c < cl->w; c++) {                            // hängendes Hindernis: Unterkante je Spalte
        x0 = left + c * 8;
        if (x0 >= BALLOON_X + 24 || x0 + 8 <= BALLOON_X) continue;
        if (balloon_hits(x0, 0, x0 + 8, cl->prof[c])) return 1;
      }
      t = cloud_phase(s);
      if (cl->bolt_y && !s->bld && t >= 88 && t < 100 &&
          balloon_hits(left + cl->bolt_x + 5, cl->bolt_y, left + cl->bolt_x + 12, cl->bolt_y + 24))
        return 1;                                             // Blitz bzw. Strahl trifft den Ballon
    }
  }
  return 0;
}

// ---------------------------------------------------------------- Grafik
static void bg_obj(unsigned char x, unsigned char y, const unsigned int *map, unsigned char w, unsigned char h) {
  unsigned char dx, dy;
  for (dy = 0; dy < h; dy++)
    for (dx = 0; dx < w; dx++)
      SMS_setTileatXY(x + dx, y + dy, map[dy * w + dx]);
}

// ---------------------------------------------------------------- Sprites
static void spr_obj(unsigned char x, unsigned char y, unsigned char tile, unsigned char w, unsigned char h) {
  unsigned char dx, dy;
  for (dy = 0; dy < h; dy++)
    for (dx = 0; dx < w; dx++)
      SMS_addSprite(x + dx * 8, y + dy * 8, tile + dy * w + dx);
}

// Sprite-y ab 208 beendet die Sprite-Tabelle: Teile unter dem Bild gar nicht erst anlegen
static void spr(int x, int y, unsigned char tile) {
  if (x >= 0 && x <= 248 && y >= 0 && y <= 184) SMS_addSprite(x, y, tile);
}

static void draw_barrels(void) {
  unsigned char i, dx, dy;
  int x;
  for (i = 0; i < MAX_BARRELS; i++) {
    if (!barrels[i].on) continue;
    x = (int)(barrels[i].col - dcol) * 8 - (sub >> 4);
    for (dy = 0; dy < BARREL_H; dy++)
      for (dx = 0; dx < BARREL_W; dx++)
        spr(x + dx * 8, barrels[i].y + dy * 8, BARREL + dy * BARREL_W + dx);
  }
}

static void draw_bolts(void) {
  unsigned char i, t, dx, dy, tile;
  int x, y0;
  for (i = 0; i < RING; i++) {
    if (!ring[i].w || !ring[i].ceil || ring[i].bld) continue;   // Blitz nur, wenn darunter frei ist
    if (!W->ceil[ring[i].ceil].bolt_y) continue;
    x = (int)(ring[i].start - dcol) * 8 - (sub >> 4) + W->ceil[ring[i].ceil].bolt_x;
    y0 = W->ceil[ring[i].ceil].bolt_y;
    if (x < -16 || x > 255) continue;
    t = cloud_phase(&ring[i]);
    if (t >= 88 && t < 100) {                                 // Blitz
      tile = BOLT_A;
      if (frame & 4) tile = BOLT_B;
      for (dy = 0; dy < 3; dy++)
        for (dx = 0; dx < 2; dx++)
          spr(x + dx * 8, y0 + dy * 8, tile + dy * 2 + dx);
    } else if (t >= 64 && t < 88 && (frame & 4)) {            // Funken als Vorwarnung
      spr(x, y0, BOLT_A);
      spr(x + 8, y0, BOLT_A + 1);
    }
  }
}

static void draw_cannons(void) {
  unsigned char i;
  int mx;
  const Bld *b;
  for (i = 0; i < MAX_BALLS; i++)
    if (balls[i].on) {
      if (balls[i].kind == 1 || balls[i].kind == 3) spr(balls[i].x >> 6, balls[i].y >> 6, FIREBALL_A + ((frame >> 2) & 1));
      else if (balls[i].kind == 2) spr(balls[i].x >> 6, balls[i].y >> 6, BOULDER);
      else spr(balls[i].x >> 6, balls[i].y >> 6, CANNONBALL);
    }
  for (i = 0; i < RING; i++) {                    // Rauch an der Mündung als Vorwarnung
    if (!ring[i].w || !ring[i].bld) continue;
    b = &W->bld[ring[i].bld];
    if (!b->shot_y) continue;
    mx = (int)(ring[i].start - dcol) * 8 - (sub >> 4) + b->shot_x;
    if (mx >= 200 && mx <= 248 && shooter_phase(&ring[i]) >= 96 && shooter_phase(&ring[i]) < 120 && (frame & 4))
      spr(mx - 8, b->shot_y - 4, CANNON_PUFF);
  }
  for (i = 0; i < RING; i++) {                    // UFO / Hubschrauber: Funken an der Mündung als Vorwarnung
    if (!ring[i].w || !ring[i].ceil || !W->ceil[ring[i].ceil].shot_y) continue;
    mx = (int)(ring[i].start - dcol) * 8 - (sub >> 4) + W->ceil[ring[i].ceil].shot_x;
    if (mx >= 190 && mx <= 248 && cloud_phase(&ring[i]) >= 100 && cloud_phase(&ring[i]) < 120 && (frame & 4))
      spr(mx - 8, W->ceil[ring[i].ceil].shot_y - 4, BOLT_A);
  }
}

static void draw_rope(unsigned char y) {
  unsigned char i, n;
  int hy = y + 32 + rope - 14;                         // Oberkante des Hakens (Haken ist 14 Pixel hoch)
  if (!rope) return;
  spr(BALLOON_X + 8, hy, HOOK);
  spr(BALLOON_X + 8, hy + 8, HOOK + 1);
  if (carrying) {                                      // Fass hängt mit dem Ring im Haken
    spr(BALLOON_X + 4, hy + 8, BARREL);
    spr(BALLOON_X + 12, hy + 8, BARREL + 1);
    spr(BALLOON_X + 4, hy + 16, BARREL + 2);
    spr(BALLOON_X + 12, hy + 16, BARREL + 3);
  }
  n = (rope >> 3) + 1;
  for (i = 1; i <= n && hy >= 8 * i; i++) spr(BALLOON_X + 8, hy - 8 * i, ROPE);
}

static void draw_fuel(void) {
  unsigned char lvl, i, base;
  int c;
  lvl = (unsigned char)(fuel / 25);                    // 0..24 Pixel Balkenlänge
  base = FUEL_BAR;
  if (fuel < 150 && (frame & 16)) base = FUEL_BAR_RED; // fast leer: rot blinkend (kein ?: , SDCC lässt es weg)
  SMS_addSprite(8, 11, SPR_FONT_START + 5);            // 'F'
  for (i = 0; i < 3; i++) {
    c = (int)lvl - 8 * i;
    if (c < 0) c = 0;
    if (c > 8) c = 8;
    SMS_addSprite(16 + 8 * i, 11, base + c);
  }
  SMS_addSprite(40, 11, FUEL_CAP);
}

// Dunkle Fläche hinter Texten (Bildschirm-Kachelspalten c0..c1, Zeilen r0..r1, Zeilen 2..20). Der Hintergrund scrollt in
// diesen Zuständen nicht; Bildschirmspalte k liegt in Kartenspalte (dcol + k) & 31. Geschrieben wird in der Austastlücke.
static void draw_panel(unsigned char c0, unsigned char r0, unsigned char c1, unsigned char r1) {
  pj_col = (unsigned char)(dcol + c0) & 31;
  pj_w = c1 - c0 + 1;
  pj_row = r0;
  pj_rows = r1 - r0 + 1;
}

static const unsigned int panel_words[16] = {         // eine Zeile Flächenkacheln (Sprite-Palette, Attribut Bit 11)
  PANEL | 0x0800, PANEL | 0x0800, PANEL | 0x0800, PANEL | 0x0800, PANEL | 0x0800, PANEL | 0x0800, PANEL | 0x0800, PANEL | 0x0800,
  PANEL | 0x0800, PANEL | 0x0800, PANEL | 0x0800, PANEL | 0x0800, PANEL | 0x0800, PANEL | 0x0800, PANEL | 0x0800, PANEL | 0x0800
};

// Gleich am Anfang der Austastlücke, jede Zeile am Stück, höchstens 3 Zeilen je Bild: Wird zu viel geschrieben, läuft es ins
// sichtbare Bild, und der VDP verliert dort schnelle Schreibzugriffe (Löcher in der Fläche).
static void panel_step(void) {
  unsigned char n = 3, first;
  while (pj_rows && n) {
    first = 32 - pj_col;                                // Kartenspalten bis zum rechten Rand der Tilemap
    if (first > pj_w) first = pj_w;
    SMS_loadTileMap(pj_col, pj_row, panel_words, first * 2);
    if (first < pj_w) SMS_loadTileMap(0, pj_row, panel_words, (pj_w - first) * 2);   // Umbruch auf die linke Seite
    pj_row++;
    pj_rows--;
    n--;
  }
}

static void draw_lives(void) {                         // einzeln statt Schleife: SMS_addSprite_f rettet Schleifenregister nicht zuverlässig
  if (lives > 0) SMS_addSprite(8, 21, LIFE);
  if (lives > 1) SMS_addSprite(17, 21, LIFE);
  if (lives > 2) SMS_addSprite(26, 21, LIFE);
}

static void draw_birds(void) {
  unsigned char i, dx, dy, tile;
  int x;
  if (!W->flyer_w) return;
  tile = W->flyer_tile;
  if (!(frame & 8)) tile += W->flyer_w * W->flyer_h;            // zweites Bild des Flügelschlags
  for (i = 0; i < MAX_BIRDS; i++) {
    if (!birds[i].on) continue;
    for (dy = 0; dy < W->flyer_h; dy++)
      for (dx = 0; dx < W->flyer_w; dx++) {
        x = birds[i].x + dx * 8;
        if (x >= 0 && x <= 248) SMS_addSprite(x, birds[i].y + dy * 8, tile + dy * W->flyer_w + dx);
      }
  }
}

static void text(unsigned char x, unsigned char y, const char *s) {
  for (; *s; s++, x += 8) {
    if (*s >= 'A' && *s <= 'Z')      SMS_addSprite(x, y, SPR_FONT_START + (*s - 'A'));
    else if (*s >= '0' && *s <= '9') SMS_addSprite(x, y, SPR_FONT_START + 26 + (*s - '0'));
  }
}

static void number(unsigned char x, unsigned char y, unsigned int v) {
  static const unsigned int pow10[5] = { 10000, 1000, 100, 10, 1 };
  unsigned char i, d;
  for (i = 0; i < 5; i++) {
    d = 0;
    while (v >= pow10[i]) {
      v -= pow10[i];
      d++;
    }
    SMS_addSprite(x, y, SPR_FONT_START + 26 + d);
    x += 8;
  }
}

static void draw_sparks(void) {
  unsigned char i, tile;
  for (i = 0; i < MAX_SPARKS; i++) {
    if (!sparks[i].life) continue;
    if (sparks[i].life < 10 && (sparks[i].life & 2)) continue;       // zum Ende hin flackern
    tile = spark_tile[sparks[i].col];
    if (sparks[i].life <= 25) tile++;                                 // kleinere Variante
    spr(sparks[i].x - 4, sparks[i].y - 4, tile);
  }
}

static void draw_sprites(void) {
  unsigned char y = (unsigned char)(y32 >> 5);
  SMS_initSprites();
  if (state == ST_TITLE) return;                      // Titelbild: keine Sprites
  if (state == ST_WIN && win_timer >= 30) {
    if (world_idx + 1 < NUM_WORLDS) {               // geschafft, weiter geht es in die nächste Welt
      text(108, 108, "LEVEL");
      text(96, 118, "COMPLETE");
      text(108, 132, "BONUS");
      number(108, 142, win_bonus);
      if (win_timer >= 120) text(104, 156, "PUSH 1");
    } else {                                        // letzte Welt: Schluss des Spiels
      text(100, 104, "THE END");
      text(104, 114, "BALLOON");
      text(108, 124, "MASTER");
      text(108, 138, "BONUS");
      number(108, 148, win_bonus);
      if (win_timer >= 120) text(104, 160, "PUSH 1");
    }
  }
  if (state == ST_DEAD && dead_timer >= 30) {         // Texte zuerst: Sprites mit niedrigerer Nummer liegen vorn
    if (lives) {
      text(104, 98, "PUSH 1");                        // noch Leben übrig: weiter ab Checkpoint
    } else {
      text(112, 44, "GAME");
      text(112, 54, "OVER");
      text(112, 70, "BEST");
      number(108, 80, best);
      text(100, 96, "CONTINUE");
      SMS_addSprite(124, 106, SPR_FONT_START + 26 + cont_count);   // Ziffer 9..0
      text(104, 120, "PUSH 1");
    }
  }
  if (state != ST_DEAD || (dead_timer < 30 && !(dead_timer & 4)))   // nach dem Absturz blinkt der Ballon kurz, dann ist er weg
    spr_obj(BALLOON_X, y, burner ? BALLOON_BURN : BALLOON_IDLE, BALLOON_IDLE_W, BALLOON_IDLE_H);
  if (cp_msg && state == ST_PLAY) {
    text(108, 40, "CHECK");
    text(112, 50, "POINT");
  }
  draw_sparks();
  draw_birds();
  draw_barrels();
  draw_bolts();
  draw_cannons();
  if (state == ST_PLAY) draw_rope(y);
  number(8, 2, dcol + bonus);
  draw_fuel();
  draw_lives();
  if (demo && (frame & 32)) text(112, 40, "DEMO");
}

// ---------------------------------------------------------------- Start
static unsigned char title_timer;
static unsigned int idle_timer;                 // Frames ohne Tastendruck im Titel; danach startet die Vorführung
static unsigned int demo_timer;
#define IDLE_FRAMES 600                          // 10 s bis zur Vorführung
#define DEMO_FRAMES 1500                         // 25 s je Welt
static unsigned char start_sel = START_WORLD;   // auf dem Titelbild mit links/rechts wählbar (zum Testen)
static unsigned char sel_dirty;

// Zeile 23 des Titelbilds: "< WORLD n >" (Zeichen aus bank2, ROM-Bank 2 muss eingeblendet sein)
static void draw_world_select(void) {
  unsigned int row[32];
  unsigned char i, k = 10;
  static const unsigned char idx[11] = { 11, 255, 0, 1, 2, 3, 4, 255, 5, 255, 12 };   // < _ W O R L D _ n _ >
  for (i = 0; i < 32; i++) row[i] = 0;
  for (i = 0; i < 11; i++) {
    if (idx[i] == 255) continue;
    row[k + i] = title_glyph[idx[i]];
  }
  row[k + 8] = title_glyph[5 + start_sel];
  SMS_loadTileMap(0, TITLE_TEXT_ROW + 1, row, 64);
}
#ifdef TEST_DIE_AT
static unsigned char test_died;
#endif

// Kacheln, Paletten und feste Bereiche des Spiels (Straße, ferne Wolken) ins VRAM laden
static void init_game_vram(void) {
  unsigned char x;
  irq_off();
  SMS_displayOff();
  SMS_VRAMmemsetW(0, 0, 16384);          // Tilemap = Tile 0 = leerer Himmel
  SMS_loadTiles(sprite_tiles, 0, SPRITE_TILE_BYTES);
  SMS_loadTiles(W->bg_tiles, BG_TILE_BASE, W->bg_bytes);
  SMS_loadBGPalette(W->bg_pal);
  SMS_loadSpritePalette(sprite_palette);
  SMS_setSpritePaletteColor(SKY_BACKDROP, W->sky);   // Platz 14 der Sprite-Palette ist die Himmelfarbe (auch Rahmenfarbe)
  SMS_setBackdropColor(SKY_BACKDROP);
  SMS_useFirstHalfTilesforSprites(1);
  SMS_VDPturnOnFeature(VDPFEATURE_LEFTCOLBLANK);   // linke Spalte aus: verdeckt den Wrap-Rand beim Scrollen
  for (x = 0; x < 32; x++) {                       // Straße: Strich 2 Tiles lang, 2 Tiles Lücke (Muster wiederholt sich alle 4 Tiles)
    SMS_setTileatXY(x, 21, W->ground[0][x & 3]);
    SMS_setTileatXY(x, 22, W->ground[1][x & 3]);
    SMS_setTileatXY(x, 23, W->ground[2][x & 3]);
  }
  for (x = 0; x < 3; x++) { anim_state[x] = 0; anim_pos[x] = 255; }
  for (x = 2; x < 32; x += 10)                     // ferne Wolken im langsamen Band (Tile-Zeilen 0..1)
    bg_obj(x, 0, W->far_cloud, CLOUD_W, CLOUD_H);
}

// Titelbild aus ROM-Bank 2: eigene Kacheln, zwei Paletten (BG + Sprite-Palette, pro Kachel wählbar), kein Scrollen
static void show_title(void) {
  cp_idx = 0;
  snd_track(0);
  irq_off();                                       // auch die Zeileninterrupts bleiben im Titel aus
  SMS_displayOff();
  SMS_VRAMmemsetW(0, 0, 16384);
  SMS_mapROMBank(2);
  SMS_loadTiles(title_tiles, 0, TITLE_TILE_BYTES);
  SMS_loadTileMap(0, 0, title_map, 32 * 24 * 2);
  SMS_loadTileMap(0, TITLE_TEXT_ROW, title_text_map, 64);
#ifndef NO_LEVEL_SELECT
  draw_world_select();
#endif
  SMS_loadBGPalette(title_pal0);
  SMS_loadSpritePalette(title_pal1);
  SMS_setBackdropColor(0);
  SMS_VDPturnOffFeature(VDPFEATURE_LEFTCOLBLANK);
  next_top = next_main = next_street = 0;
  sc_top = sc_main = sc_street = 0;
  SMS_setBGScrollX(0);
  flash = 0;
  flash_on = 0;
  title_timer = 0;
  idle_timer = 0;
  state = ST_TITLE;
#ifdef SFX_DEMO
  snd_music(0);
#else
  snd_music(1);
#endif
  SMS_displayOn();
  irq_on(0);
}

// Autopilot (Demo und Test): fliegt in die Mitte des Korridors der nächsten Hindernisse und weicht Vögeln aus
static unsigned int autopilot(unsigned int keys) {
  int tgt = 80, lo_max = 0, hi_min = 400, l;
  unsigned char k;
  for (k = 0; k < RING; k++) {
    if (!ring[k].w) continue;
    l = (int)(ring[k].start - dcol) * 8 - (sub >> 4);
    if (l < BALLOON_X + 70 && l + ring[k].w * 8 > BALLOON_X - 24) {
      if (ring[k].lo > lo_max) lo_max = ring[k].lo;
      if (ring[k].hi < hi_min) hi_min = ring[k].hi;
    }
  }
  if (hi_min < 400) tgt = (lo_max < hi_min) ? (lo_max + hi_min) / 2 : hi_min - 6;
  for (k = 0; k < MAX_BIRDS; k++) {                 // Vögeln ausweichen: über oder unter ihnen fliegen, wo der Korridor es erlaubt
    if (!birds[k].on || birds[k].x < BALLOON_X - 20 || birds[k].x > BALLOON_X + 110) continue;
    l = birds[k].y;
    if (tgt + 15 > l - 22 && tgt + 15 < l + 34) {
      if (l - 28 >= lo_max && l - 28 < hi_min) tgt = l - 28;
      else if (l + 12 < hi_min) tgt = l + 12;
    }
  }
  if ((y32 >> 5) + (vy >> 3) > tgt) keys |= PORT_A_KEY_1;
  return keys;
}

// Vorspann: Logo von Retro Computer Dresden (ROM-Bank 9), blendet ein und aus, jede Taste überspringt es
static void fade_logo(unsigned char lv) {                // lv 0 = schwarz ... 3 = volle Farben
  unsigned char i, b, r, g, bl;
  for (i = 0; i < 5; i++) {
    b = logo_pal[i];
    r = (unsigned char)(((b & 3) * lv) / 3);
    g = (unsigned char)((((b >> 2) & 3) * lv) / 3);
    bl = (unsigned char)((((b >> 4) & 3) * lv) / 3);
    SMS_setBGPaletteColor(i, r | (g << 2) | (bl << 4));
  }
}

static void show_logo(void) {
  unsigned char f, lv;
  irq_off();
  SMS_displayOff();
  SMS_VRAMmemsetW(0, 0, 16384);
  SMS_mapROMBank(9);
  SMS_loadTiles(logo_tiles, 0, LOGO_TILE_BYTES);
  SMS_loadTileMap(0, 0, logo_map, 32 * 24 * 2);
  fade_logo(0);
  SMS_loadSpritePalette(logo_pal);
  SMS_setBackdropColor(0);
  SMS_VDPturnOffFeature(VDPFEATURE_LEFTCOLBLANK);
  next_top = next_main = next_street = 0;
  sc_top = sc_main = sc_street = 0;
  SMS_setBGScrollX(0);
  SMS_displayOn();
  irq_on(0);
  for (f = 0; f < 150; f++) {                           // 2,5 Sekunden
    SMS_waitForVBlank();
    SMS_getKeysStatus();
    if (SMS_getKeysPressed()) break;
    lv = 3;
    if (f < 12) lv = f / 4;
    else if (f >= 138) lv = (150 - f) / 4;
    fade_logo(lv);
  }
}

void main(void) {
  unsigned int keys, pressed;
  unsigned char i;

  snd_init();
  rng = 12345;
  SMS_setLineInterruptHandler(line_handler);
  SMS_setFrameInterruptHandler(frame_handler);
  SMS_setLineCounter(LINE_STEP - 1);
#ifndef AUTOPLAY                                       // Tests überspringen den Vorspann
  show_logo();
#endif
  show_title();

  for (;;) {
    keys = SMS_getKeysStatus();
    pressed = SMS_getKeysPressed();
    new_col = 0;
#ifdef AUTOPLAY                                       // nur zum Testen: Titel überspringen und selbst fliegen
    if (state == ST_TITLE && title_timer > 90) pressed |= PORT_A_KEY_1;
    if (state == ST_DEAD && dead_timer >= 40 && lives) pressed |= PORT_A_KEY_1;   // bei Game Over wartet der Test auf den Countdown
    if (state == ST_WIN && win_timer >= 130) pressed |= PORT_A_KEY_1;
    if (state == ST_PLAY) keys = autopilot(keys);
#endif

    if (demo) {
      if ((pressed & (PORT_A_KEY_1 | PORT_A_KEY_2)) || demo_timer >= DEMO_FRAMES || state != ST_PLAY) {
        demo = 0;                                  // Taste oder Ende: zurück zum Titel
        show_title();
        pressed = 0;
      } else {
        keys = autopilot(0);
        fuel = FUEL_MAX;
        demo_timer++;
      }
    }
    if (state == ST_TITLE) {
      burner = 0;
      title_timer++;
#ifdef SFX_DEMO                                          // nur zum Testen: ohne Musik, Effekt SFX_DEMO immer wieder
      if (!title_timer) snd_sfx(SFX_DEMO);
      idle_timer = 0;
#endif
      idle_timer++;
      if (pressed) idle_timer = 0;
      if (idle_timer >= IDLE_FRAMES) {               // Vorführung: selbstfliegend, unverwundbar, jedes Mal eine andere Welt
        demo = 1;
        demo_timer = 0;
        select_world(demo_next);
        demo_next++;
        if (demo_next >= NUM_WORLDS) demo_next = 0;
        init_game_vram();
        new_game();
        state = ST_PLAY;
      }
#ifndef NO_LEVEL_SELECT                                // Beta-Version: immer ab Welt 1
      if ((pressed & PORT_A_KEY_RIGHT) && start_sel + 1 < NUM_WORLDS) { start_sel++; sel_dirty = 1; }
      if ((pressed & PORT_A_KEY_LEFT) && start_sel > 0) { start_sel--; sel_dirty = 1; }
#endif
      if (pressed & PORT_A_KEY_1) {
        lives = START_LIVES;
        select_world(start_sel);
        init_game_vram();
        new_game();
        state = ST_PLAY;
      }
    } else if (state == ST_PLAY) {
#ifdef MONSTER_TEST
      fuel = FUEL_MAX;
#endif
      update_scroll_and_wind();
      update_balloon(keys);
      update_rope_and_barrels(keys);
      update_birds();
      update_lightning();
      update_cannons();
      if (cp_idx < 2 && dcol >= cp_trigger[cp_idx]) {   // Checkpoint erreicht: hier geht es nach einem Absturz mit vollem Tank weiter
        cp_idx++;                                       // kein Auftanken: das gibt es erst beim Neustart ab hier
        saved_bonus = bonus;
        cp_msg = 100;
        snd_sfx(SFX_CATCH);
      }
      if (cp_msg) cp_msg--;
#ifdef TEST_DIE_AT                                             // nur zum Testen: einmaliger Absturz in dieser Spalte
#ifdef TEST_DIE_REPEAT                                         // Absturz in dieser Spalte jedes Mal (Leben/Continue testen)
      if (dcol == TEST_DIE_AT) {
#else
      if (dcol == TEST_DIE_AT && !test_died) {
#endif
        test_died = 1;
#elif defined(GODMODE)                                         // nur zum Testen: unverwundbar
      if (0) {
#else
      if (!demo && crashed()) {
#endif
        if (dcol + bonus > best) best = dcol + bonus;
        if (lives) lives--;
        cont_count = 9;
        cont_frames = 0;
        rope = 0;
        carrying = 0;
        state = ST_DEAD;
        snd_music(0);
        snd_sfx(SFX_CRASH);
        dead_timer = 0;
        burner = 0;
      } else if (passed_finish()) {                   // Tower Bridge geschafft
        state = ST_WIN;
        win_timer = 0;
        burst_timer = 20;
        win_bonus = fuel / 5;                        // übriger Treibstoff gibt Bonuspunkte
        bonus += win_bonus;
        if (dcol + bonus > best) best = dcol + bonus;
        rope = 0;
        carrying = 0;
        burner = 0;
        wind_tgt = 0;
        for (i = 0; i < MAX_SPARKS; i++) sparks[i].life = 0;
        snd_fanfare();
      }
    } else if (state == ST_WIN) {
      if (win_timer < 255) win_timer++;
      if (W->special_finish && win_timer < 30) update_scroll_and_wind();   // ohne Brücke bleibt die Landschaft stehen (Ziel nur sichtbar), mit Brücke ab dem Text
      if (win_timer == 30) draw_panel(10, 12, 22, 20);                     // Textfläche hinter LEVEL COMPLETE / THE END
      update_sparks();
      if ((y32 >> 5) < 70) y32 += 16;                 // Ballon sanft auf Höhe 70 schweben lassen
      else if ((y32 >> 5) > 70) y32 -= 16;
      if (win_timer >= 120 && (pressed & PORT_A_KEY_1)) {
        if (world_idx + 1 < NUM_WORLDS) {               // weiter in die nächste Welt
          select_world(NEXT_WORLD(world_idx));
          init_game_vram();
          new_game();
          state = ST_PLAY;
        } else {
          show_title();                                 // alle Welten geschafft: zurück zum Titelbild
        }
      }
    } else {
      if (dead_timer < 255) dead_timer++;
      if (dead_timer == 30) {                           // Textfläche hinter GAME OVER bzw. PUSH 1
        if (lives) draw_panel(11, 11, 20, 13);
        else draw_panel(10, 4, 22, 16);
      }
      if (dead_timer >= 30 && (pressed & PORT_A_KEY_1)) {
        if (!lives) {                                   // Continue: wieder drei Leben, Level von vorn
          lives = START_LIVES;
          cp_idx = 0;
        }
        new_game();
        state = ST_PLAY;
      } else if (!lives && dead_timer >= 30) {          // Arcade-Countdown: 9 Sekunden, dann Spielende
        cont_frames++;
        if (cont_frames >= 60) {
          cont_frames = 0;
          if (cont_count) cont_count--;
          else show_title();
        }
      }
    }

    if (state != ST_TITLE) {
      next_top = (unsigned char)(0 - (cl16 >> 4));
      next_main = (unsigned char)(0 - (((dcol & 31) << 3) + (sub >> 4)));
      next_street = (unsigned char)(0 - (st16 >> 4));
    }

    draw_sprites();
    frame++;
    SMS_waitForVBlank();
    if (pj_rows) panel_step();                          // zuerst, solange die Austastlücke ganz frei ist
    SMS_copySpritestoSAT();
    if (new_col) upload_column(dcol + 32);
    if (state == ST_TITLE && sel_dirty) {
      sel_dirty = 0;
      draw_world_select();
    }
    if (state == ST_TITLE && !(title_timer & 31))      // "PUSH 1 TO START" blinkt (Zeile 22 abwechselnd Text / leer)
      SMS_loadTileMap(0, TITLE_TEXT_ROW, (title_timer & 32) ? title_map + TITLE_TEXT_ROW * 32 : title_text_map, 64);
    if ((flash != 0) != flash_on) {                     // Himmel aufblitzen lassen
      flash_on = flash != 0;
      SMS_setBGPaletteColor(0, flash_on ? W->flash : W->sky);
      SMS_setSpritePaletteColor(SKY_BACKDROP, flash_on ? W->flash : W->sky);
    }
    if (state == ST_PLAY || state == ST_WIN) {           // Animationen: Kachelblöcke zwischen Bild A und B umschalten
      for (i = 0; i < 3; i++) {
        if (!W->anim[i].count) continue;
        if (anim_pos[i] == 255 && (((unsigned char)frame + i * 5) & 31) == 0) {
          anim_state[i] ^= 1;
          anim_pos[i] = 0;
          if (anim_state[i] && anim_visible(i + 1)) {
            if (world_idx == 5 && i == 1) {                 // Riesenechse brüllt nur einmal je Auftritt (das Brüllen dauert fast 3 Sekunden)
              if (anim_seg != roar_seg) {
                roar_seg = anim_seg;
                snd_sfx(SFX_GODZILLA);
              }
            } else {
              snd_sfx(monster_sfx(i));
            }
          }
        }
        if (anim_pos[i] != 255) {                      // höchstens 6 Kacheln je Bild, sonst reicht der Vertikalrücklauf nicht
          unsigned char n = W->anim[i].count - anim_pos[i];
          if (n > 6) n = 6;
          SMS_loadTiles((anim_state[i] ? W->anim[i].frame_b : W->bg_tiles + (W->anim[i].tile - BG_TILE_BASE) * 32) + anim_pos[i] * 32,
                        W->anim[i].tile + anim_pos[i], n * 32);
          anim_pos[i] += n;
          if (anim_pos[i] >= W->anim[i].count) anim_pos[i] = 255;
        }
      }
    }
    snd_burner(burner && state == ST_PLAY);
    snd_update();
  }
}

SMS_EMBED_SEGA_ROM_HEADER(9999, 0);
SMS_EMBED_SDSC_HEADER_AUTO_DATE(0, 1, "Balloon Master", "Master System Game", "RCD");
