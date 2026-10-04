// GENERIERT von tools/make_title.py - nicht von Hand ändern.
#ifndef BANK2_H
#define BANK2_H

#define TITLE_TILE_COUNT 356
#define TITLE_TILE_BYTES 11392
#define TITLE_TEXT_ROW 22

extern const unsigned char title_pal0[16];    // BG-Palette
extern const unsigned char title_pal1[16];    // Sprite-Palette (Tiles wählen sie per Attribut)
extern const unsigned int title_map[32 * 24];
extern const unsigned int title_text_map[32]; // Zeile 22 mit Text; ohne Text: Zeile 22 aus title_map
extern const unsigned int title_glyph[13];  // Zeichen "WORLD123456<>" (Tilemap-Wörter) für die Weltauswahl
extern const unsigned char title_tiles[11392];

#endif
