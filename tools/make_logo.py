#!/usr/bin/env python3
"""Vorspann-Logo "RCD" (Retro Computer Dresden): Buchstabenblöcke wie im Projekt master-system-game, darunter der Vereinsname.
Erzeugt res/gfx/rcd_logo.png (Vorschau) und src/bank9.c / src/bank9.h (ROM-Bank 9: Kacheln, Karte, Palette).

    python3 tools/make_logo.py        # braucht Pillow nur für das Vorschau-Bild; normale Builds brauchen das Skript nicht
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "art"))
from artdefs import FONT  # noqa: E402
from palette import COLORS, rgb8, sms_byte  # noqa: E402

W, H = 256, 192
CELL = 12
LETTERS = {                         # 5x7, wie in master-system-game (MSB = linke Spalte)
    'R': [0b11110, 0b10001, 0b10001, 0b11110, 0b10100, 0b10010, 0b10001],
    'C': [0b01111, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b01111],
    'D': [0b11110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b11110],
}
PAL = "krcte"                       # Palettenplatz: 0 Hintergrund, 1 Koralle (R), 2 Orange (C), 3 Türkis (D), 4 hellgrau (Text)
TEXT = ["RETRO COMPUTER", "DRESDEN"]


def render():
    g = [[0] * W for _ in range(H)]
    x0 = (W - (3 * 5 * CELL + 2 * CELL)) // 2
    y0 = 36
    for n, ch in enumerate("RCD"):
        for r, bits in enumerate(LETTERS[ch]):
            for c in range(5):
                if bits & (1 << (4 - c)):
                    for y in range(CELL):
                        for x in range(CELL):
                            g[y0 + r * CELL + y][x0 + n * 6 * CELL + c * CELL + x] = 1 + n
    for line, text in enumerate(TEXT):
        scale = 2
        tw = len(text) * 6 * scale - scale
        tx = (W - tw) // 2
        ty = 140 + line * 20
        for i, ch in enumerate(text):
            if ch == ' ':
                continue
            for r, row in enumerate(FONT[ch]):
                for c, v in enumerate(row):
                    if v == '1':
                        for y in range(scale):
                            for x in range(scale):
                                g[ty + r * scale + y][tx + i * 6 * scale + c * scale + x] = 4
    return g


def main():
    g = render()
    tiles, seen, tmap = [], {}, []
    for ty in range(H // 8):
        for tx in range(W // 8):
            t = tuple(g[ty * 8 + y][tx * 8 + x] for y in range(8) for x in range(8))
            if t not in seen:
                seen[t] = len(tiles)
                tiles.append(t)
            tmap.append(seen[t])
    # Tile 0 = leere Fläche (Hintergrund), damit der Rest der Karte auch nach VRAM-Löschen stimmt
    zero = tuple([0] * 64)
    order = [zero] + [t for t in tiles if t != zero]
    index = {t: i for i, t in enumerate(order)}
    tmap = [index[tiles[i]] for i in tmap]
    data = bytearray()
    for t in order:
        for y in range(8):
            planes = [0, 0, 0, 0]
            for x in range(8):
                v = t[y * 8 + x]
                for p in range(4):
                    planes[p] |= ((v >> p) & 1) << (7 - x)
            data.extend(planes)
    pal = [sms_byte(COLORS[c]) for c in PAL] + [0] * (16 - len(PAL))
    n = len(order)
    print(f"{n} Kacheln, {len(data)} Byte Kacheldaten")
    with open(os.path.join(ROOT, "src", "bank9.c"), "w") as f:
        f.write("// GENERIERT von tools/make_logo.py - nicht von Hand ändern.\n// Wird mit --constseg BANK9 übersetzt und liegt in ROM-Bank 9.\n#include \"bank9.h\"\n\n")
        f.write("const unsigned char logo_pal[16] = {\n  " + ", ".join("0x%02X" % b for b in pal) + "\n};\n\n")
        f.write("const unsigned int logo_map[32 * 24] = {\n")
        for i in range(0, len(tmap), 16):
            f.write("  " + ", ".join(str(v) for v in tmap[i:i + 16]) + ",\n")
        f.write("};\n\nconst unsigned char logo_tiles[LOGO_TILE_BYTES] = {\n")
        for i in range(0, len(data), 16):
            f.write("  " + ", ".join("0x%02X" % b for b in data[i:i + 16]) + ",\n")
        f.write("};\n")
    with open(os.path.join(ROOT, "src", "bank9.h"), "w") as f:
        f.write("// GENERIERT von tools/make_logo.py - nicht von Hand ändern.\n#ifndef BANK9_H\n#define BANK9_H\n\n")
        f.write(f"#define LOGO_TILE_BYTES {len(data)}\n\n")
        f.write("extern const unsigned char logo_pal[16];                 // BG-Palette\nextern const unsigned int logo_map[32 * 24];\n")
        f.write("extern const unsigned char logo_tiles[LOGO_TILE_BYTES];\n\n#endif\n")
    try:
        from PIL import Image
        im = Image.new("RGB", (W, H))
        im.putdata([rgb8(COLORS[PAL[v]]) for row in g for v in row])
        os.makedirs(os.path.join(ROOT, "res", "gfx"), exist_ok=True)
        im.save(os.path.join(ROOT, "res", "gfx", "rcd_logo.png"))
    except ImportError:
        print("Pillow fehlt: kein Vorschau-Bild")


if __name__ == "__main__":
    main()
