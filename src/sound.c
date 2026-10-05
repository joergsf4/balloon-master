#include "SMSlib.h"
#include "sound.h"

__sfr __at 0x7f PSGPort;               // SN76489: Tonperiode 10 Bit, Lautstärke 0 = laut ... 15 = still

#define P(f) ((unsigned int)(111861UL / (f)))   // 3579545 / (32 * f), zur Übersetzungszeit

// Noten (Hz). Tiefer als etwa 110 Hz geht auf dem PSG nicht.
#define R  0
#define C3 P(131)
#define D3 P(147)
#define G3 P(196)
#define C4 P(262)
#define D4 P(294)
#define E4 P(330)
#define F4 P(349)
#define G4 P(392)
#define A4 P(440)
#define B3 P(247)
#define E3 P(165)
#define A3 P(220)
#define D4B P(294)
#define E4B P(330)
#define Gs4 P(415)
#define Fs4 P(370)
#define B4B P(494)
#define F5 P(698)
#define D5 P(587)
#define C5 P(523)
#define E5 P(659)
#define G5 P(784)
#define C6 P(1047)
#define E6 P(1319)

// ---------------------------------------------------------------- Musik: "London Bridge Is Falling Down" (gemeinfrei)
// 8 Takte à 8 Achtel, Achtel = 12 Bilder (ca. 150 BPM als Viertel), dazu Bass im Oom-Pah.
static const unsigned int mel_p[] = {
  G4, A4, G4, F4,   E4, F4, G4,   D4, E4, F4,   E4, F4, G4,
  G4, A4, G4, F4,   E4, F4, G4,   D4, G4, E4, C4,   C4, R
};
static const unsigned char mel_d[] = {
  36, 12, 24, 24,   24, 24, 48,   24, 24, 48,   24, 24, 48,
  36, 12, 24, 24,   24, 24, 48,   24, 24, 24, 24,   72, 24
};
static const unsigned int bas_p[] = {
  C3, G3, C3, G3,   C3, G3, C3, G3,   G3, D3, G3, D3,   C3, G3, C3, G3,
  C3, G3, C3, G3,   C3, G3, C3, G3,   G3, D3, C3, G3,   C3, G3, C3, R
};
static const unsigned char bas_d[] = {
  24, 24, 24, 24,   24, 24, 24, 24,   24, 24, 24, 24,   24, 24, 24, 24,
  24, 24, 24, 24,   24, 24, 24, 24,   24, 24, 24, 24,   24, 24, 24, 24
};

// Eigene Stücke der Welten 3 bis 6: tools/music.py erzeugt music_data.h
typedef struct {
  const unsigned int *mp;
  const unsigned char *md;
  unsigned int mlen;
  const unsigned int *bp;
  const unsigned char *bd;
  unsigned int blen;
  unsigned char mbase, mcap, bbase, bcap, rate, mgap, bgap;   // Lautstärke, Ausklingen, Lücke am Notenende (siehe tools/music.py)
} Track;
#include "music_data.h"

// Siegesfanfare (einmalig): Melodie + Bass, je 112 Bilder
static const unsigned int fan_mel_p[] = { C5, E5, G5, C6, G5, C6, E6 };
static const unsigned char fan_mel_d[] = { 8, 8, 8, 24, 8, 8, 48 };
static const unsigned int fan_bas_p[] = { C3, G3, C3, G3, C3 };
static const unsigned char fan_bas_d[] = { 16, 16, 16, 16, 48 };

typedef struct {
  const unsigned int *per;
  const unsigned char *dur;
  unsigned int len, pos;
  unsigned char timer, att, sub, base, cap, ch, loop, rate, gap;
} MChan;

static MChan mel = { mel_p, mel_d, sizeof(mel_d), 0, 0, 0, 0, 4, 9, 0, 1, 6, 0 };
static unsigned char cur_track;
static MChan bas = { bas_p, bas_d, sizeof(bas_d), 0, 0, 0, 0, 7, 11, 1, 1, 6, 0 };
static unsigned char music_on;

// ---------------------------------------------------------------- Effekte
typedef struct {
  unsigned char frames;      // 0 = Ende
  unsigned int period;       // 0 = kein Ton
  unsigned char vol;
  unsigned char nmode;       // Rauschen: Bit 2 = weiß, Bit 0..1 = Rate; 255 = kein Rauschen
  unsigned char nvol;
} Step;

static const Step s_catch[] = {
  { 3, P(660), 2, 255, 15 }, { 3, P(880), 2, 255, 15 }, { 4, P(1100), 3, 255, 15 }, { 0, 0, 0, 0, 0 }
};
static const Step s_refuel[] = {
  { 4, P(523), 2, 255, 15 }, { 4, P(659), 2, 255, 15 }, { 4, P(784), 2, 255, 15 }, { 10, P(1047), 3, 255, 15 },
  { 0, 0, 0, 0, 0 }
};
static const Step s_crash[] = {
  { 3, P(600), 2, 6, 0 }, { 3, P(480), 2, 6, 0 }, { 3, P(380), 3, 6, 1 }, { 3, P(300), 3, 6, 2 },
  { 3, P(240), 4, 6, 3 }, { 3, P(190), 4, 6, 4 }, { 4, P(150), 5, 6, 6 }, { 4, 0, 15, 6, 8 },
  { 4, 0, 15, 6, 10 }, { 6, 0, 15, 6, 12 }, { 8, 0, 15, 6, 14 }, { 0, 0, 0, 0, 0 }
};
static const Step s_thunder[] = {
  { 2, 0, 15, 6, 0 }, { 3, 0, 15, 6, 1 }, { 3, 0, 15, 6, 2 }, { 4, 0, 15, 6, 3 }, { 4, 0, 15, 6, 4 },
  { 5, 0, 15, 6, 6 }, { 6, 0, 15, 6, 8 }, { 8, 0, 15, 6, 10 }, { 10, 0, 15, 6, 12 }, { 12, 0, 15, 6, 14 },
  { 0, 0, 0, 0, 0 }
};
static const Step s_spark[] = { { 2, 0, 15, 4, 7 }, { 0, 0, 0, 0, 0 } };
static const Step s_cannon[] = {
  { 2, P(180), 2, 6, 0 }, { 3, P(130), 3, 6, 1 }, { 4, 0, 15, 6, 3 }, { 6, 0, 15, 6, 7 }, { 8, 0, 15, 6, 11 },
  { 0, 0, 0, 0, 0 }
};
static const Step s_splash[] = {                  // Platsch: Rauschstoß, dann blubbernder Ton
  { 2, 0, 15, 4, 0 }, { 2, 0, 15, 4, 2 }, { 3, P(420), 4, 4, 5 }, { 3, P(300), 5, 4, 8 }, { 4, 0, 15, 4, 11 },
  { 0, 0, 0, 0, 0 }
};
static const Step s_kong[] = {                      // Kong: tiefes Brüllen, dann zwei Schläge auf die Brust
  { 3, P(190), 2, 5, 3 }, { 3, P(160), 2, 5, 2 }, { 4, P(135), 3, 5, 2 }, { 4, P(120), 3, 5, 3 }, { 5, P(110), 4, 5, 4 },
  { 5, P(125), 4, 5, 5 }, { 6, P(110), 5, 5, 7 }, { 3, 0, 15, 255, 15 },
  { 2, 0, 15, 6, 0 }, { 3, 0, 15, 6, 5 }, { 3, 0, 15, 255, 15 }, { 2, 0, 15, 6, 0 }, { 4, 0, 15, 6, 6 },
  { 0, 0, 0, 0, 0 }
};
static const Step s_godzilla[] = {                  // Godzilla: tiefes, rauhes Brüllen (nach dem Original: Einsatz ~310 Hz, sinkt auf ~216 Hz,
  // ~7 Hz Pulsieren; Rauschen an die Tonhöhe gekoppelt = Knurren)
  { 4, P(312), 1, 7, 0 }, { 4, P(312), 4, 5, 3 },
  { 4, P(306), 1, 7, 0 }, { 4, P(306), 4, 5, 3 },
  { 4, P(300), 2, 7, 1 }, { 4, P(300), 5, 5, 4 },
  { 4, P(296), 2, 7, 1 }, { 4, P(296), 5, 5, 4 },
  { 4, P(290), 2, 7, 1 }, { 4, P(290), 5, 5, 4 },
  { 4, P(284), 2, 7, 1 }, { 4, P(284), 5, 5, 4 },
  { 4, P(280), 2, 7, 1 }, { 4, P(280), 5, 5, 4 },
  { 4, P(284), 2, 7, 1 }, { 4, P(284), 5, 5, 4 },
  { 4, P(276), 2, 7, 1 }, { 4, P(276), 5, 5, 4 },
  { 4, P(268), 2, 7, 1 }, { 4, P(268), 5, 5, 4 },
  { 4, P(258), 2, 7, 1 }, { 4, P(258), 5, 5, 4 },
  { 4, P(248), 2, 7, 1 }, { 4, P(248), 5, 5, 4 },
  { 4, P(238), 2, 7, 1 }, { 4, P(238), 5, 5, 4 },
  { 4, P(230), 2, 7, 1 }, { 4, P(230), 5, 5, 4 },
  { 4, P(224), 2, 7, 1 }, { 4, P(224), 5, 5, 4 },
  { 4, P(218), 2, 7, 1 }, { 4, P(218), 5, 5, 4 },
  { 4, P(216), 3, 7, 2 }, { 4, P(216), 6, 5, 5 },
  { 4, P(216), 4, 7, 4 }, { 4, P(216), 5, 7, 7 },
  { 4, P(218), 6, 7, 6 }, { 4, P(218), 9, 5, 9 },
  { 4, P(216), 9, 7, 9 }, { 4, P(216), 12, 5, 12 },
  { 0, 0, 0, 0, 0 }
};
static const Step s_pop[] = { { 2, P(1500), 3, 4, 3 }, { 3, 0, 15, 4, 8 }, { 0, 0, 0, 0, 0 } };
static const Step s_lowfuel[] = {
  { 4, P(880), 4, 255, 15 }, { 4, 0, 15, 255, 15 }, { 4, P(880), 4, 255, 15 }, { 0, 0, 0, 0, 0 }
};

static const Step *const sfx_tab[12] = { 0, s_catch, s_refuel, s_crash, s_thunder, s_spark, s_lowfuel, s_pop, s_cannon, s_splash, s_kong, s_godzilla };
static const unsigned char sfx_prio_tab[12] = { 0, 3, 3, 5, 4, 1, 2, 1, 3, 3, 3, 4 };

static const Step *sfx_next;           // nächster Schritt, 0 = kein Effekt aktiv
static unsigned char sfx_timer, sfx_prio, sfx_nmode, sfx_nvol;
static unsigned char burner_on, cur_nmode;

// ---------------------------------------------------------------- PSG
static void tone(unsigned char ch, unsigned int p) {
  PSGPort = 0x80 | (ch << 5) | (p & 15);
  PSGPort = (p >> 4) & 63;
}

static void vol(unsigned char ch, unsigned char att) {
  PSGPort = 0x90 | (ch << 5) | (att & 15);
}

static void set_noise(unsigned char mode, unsigned char att) {
  if (mode != cur_nmode) {             // Schreiben des Rauschmodus setzt den Zufallsgenerator zurück
    PSGPort = 0xE0 | mode;
    cur_nmode = mode;
  }
  PSGPort = 0xF0 | (att & 15);
}

void snd_init(void) {
  unsigned char ch;
  for (ch = 0; ch < 3; ch++) vol(ch, 15);
  cur_nmode = 255;
  set_noise(5, 15);
  music_on = 0;
  sfx_next = 0;
  sfx_prio = 0;
}

static void mchan_start(MChan *m) {
  m->pos = 0xFFFF;
  m->timer = 0;
}

static void load_tracks(unsigned char fan) {
  const Track *t;
  if (fan) {
    mel.per = fan_mel_p; mel.dur = fan_mel_d; mel.len = sizeof(fan_mel_d); mel.loop = 0;
    bas.per = fan_bas_p; bas.dur = fan_bas_d; bas.len = sizeof(fan_bas_d); bas.loop = 0;
    mel.base = 3; mel.cap = 8; bas.base = 6; bas.cap = 10; mel.rate = bas.rate = 6; mel.gap = bas.gap = 0;
  } else if (cur_track >= 1) {
    t = &ext_tracks[cur_track - 1];
    mel.per = t->mp; mel.dur = t->md; mel.len = t->mlen; mel.loop = 1;
    bas.per = t->bp; bas.dur = t->bd; bas.len = t->blen; bas.loop = 1;
    mel.base = t->mbase; mel.cap = t->mcap; bas.base = t->bbase; bas.cap = t->bcap; mel.rate = bas.rate = t->rate; mel.gap = t->mgap; bas.gap = t->bgap;
  } else {
    mel.per = mel_p; mel.dur = mel_d; mel.len = sizeof(mel_d); mel.loop = 1;
    bas.per = bas_p; bas.dur = bas_d; bas.len = sizeof(bas_d); bas.loop = 1;
    mel.base = 4; mel.cap = 9; bas.base = 7; bas.cap = 11; mel.rate = bas.rate = 6; mel.gap = bas.gap = 0;
  }
}

void snd_track(unsigned char t) {
  cur_track = t;
}

void snd_fanfare(void) {
  load_tracks(1);
  music_on = 1;
  mchan_start(&mel);
  mchan_start(&bas);
}

void snd_music(unsigned char on) {
  music_on = on;
  load_tracks(0);
  if (on) {
    mchan_start(&mel);
    mchan_start(&bas);
  } else {
    vol(0, 15);
    vol(1, 15);
  }
}

static void mchan_update(MChan *m) {
  unsigned int p;
  if (m->timer == 0) {
    m->pos++;
    if (m->pos >= m->len) {
      if (!m->loop) {                           // einmaliges Stück ist zu Ende
        music_on = 0;
        vol(0, 15);
        vol(1, 15);
        return;
      }
      m->pos = 0;
    }
    p = m->per[m->pos];
    m->timer = m->dur[m->pos];
    m->att = m->base;
    m->sub = 0;
    if (p) tone(m->ch, p);
    else m->att = 15;
  }
  m->timer--;
  if (m->att < m->cap && ++m->sub >= m->rate) {   // gezupfter Klang: Lautstärke klingt langsam ab
    m->sub = 0;
    m->att++;
  }
  if (m->gap && m->timer < m->gap && m->dur[m->pos] >= m->gap + 5)
    vol(m->ch, 15);                                  // Lücke am Notenende: abgesetzter (staccato) Klang
  else
    vol(m->ch, m->att);
}

void snd_sfx(unsigned char id) {
  if (id == SFX_NONE || id > SFX_GODZILLA) return;
  if (sfx_next && sfx_prio_tab[id] < sfx_prio) return;
  sfx_next = sfx_tab[id];
  sfx_prio = sfx_prio_tab[id];
  sfx_timer = 0;
}

void snd_burner(unsigned char on) {
  burner_on = on;
}

void snd_update(void) {
  const Step *st;
  if (music_on) {
    mchan_update(&mel);
    mchan_update(&bas);
  }
  sfx_nmode = 255;
  if (sfx_next) {
    if (sfx_timer == 0) {
      st = sfx_next;
      if (st->frames == 0) {                  // Ende des Effekts
        sfx_next = 0;
        sfx_prio = 0;
        vol(2, 15);
      } else {
        if (st->period) {
          tone(2, st->period);
          vol(2, st->vol);
        } else {
          vol(2, 15);
        }
        sfx_nmode = st->nmode;
        sfx_nvol = st->nvol;
        sfx_timer = st->frames;
        sfx_next = st + 1;
      }
    }
    if (sfx_next) {
      if (sfx_timer) sfx_timer--;
      st = sfx_next - 1;                        // Schritt, der gerade klingt
      sfx_nmode = st->nmode;
      sfx_nvol = st->nvol;
    }
  }
  if (sfx_nmode != 255) set_noise(sfx_nmode, sfx_nvol);
  else if (burner_on) set_noise(5, 3);          // Brenner: weißes Rauschen, deutlich hörbar
  else set_noise(cur_nmode, 15);                // still (Modus bleibt, damit der Zufallsgenerator nicht zurückgesetzt wird)
}
