#ifndef SOUND_H
#define SOUND_H

// Eigene kleine Klang-Engine für den SN76489 (PSG): Kanal 0 = Melodie, Kanal 1 = Bass,
// Kanal 2 + Rauschen = Effekte (und das Brenner-Rauschen). Einmal pro Bild snd_update() aufrufen.

enum { SFX_NONE, SFX_CATCH, SFX_REFUEL, SFX_CRASH, SFX_THUNDER, SFX_SPARK, SFX_LOWFUEL, SFX_POP, SFX_CANNON, SFX_SPLASH };

void snd_init(void);
void snd_update(void);                 // einmal pro Bild
void snd_track(unsigned char t);       // Musikstück wählen: 0 = London, 1 = Piratenbucht (wirkt beim nächsten snd_music(1))
void snd_music(unsigned char on);      // 1 = von vorn starten, 0 = aus
void snd_fanfare(void);                // Siegesfanfare auf den Musikkanälen, einmalig
void snd_sfx(unsigned char id);        // Effekt starten (höhere Priorität unterbricht niedrigere)
void snd_burner(unsigned char on);     // Brenner-Rauschen an/aus (jedes Bild setzen)

#endif
