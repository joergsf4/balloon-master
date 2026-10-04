#!/usr/bin/env python3
"""Titelbild: Artwork -> Master System -> src/bank2.c / src/bank2.h (ROM-Bank 2).

    python3 tools/make_title.py            # braucht numpy und Pillow (nur für dieses Werkzeug)

Das Bild (res/gfx/title_artwork.png) wird auf 256x176 verkleinert (22 Tile-Zeilen), darunter bleiben 2 Zeilen
für "PUSH 1 TO START". Der VDP kann pro Tile zwischen der BG- und der Sprite-Palette wählen: 2 x 16 Farben aus
64. Die Paletten und die Tile-Zuordnung werden automatisch optimiert, ähnliche Tiles werden (auch gespiegelt)
zusammengelegt, bis es höchstens LIMIT_IMG eindeutige Tiles sind (das VRAM fasst 448 Tiles).

Das Ergebnis ist eingecheckt, normale Builds brauchen weder dieses Skript noch numpy.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "art"))
from artdefs import FONT  # noqa: E402

SRC = os.path.join(ROOT, os.environ.get("TITLE_SRC", os.path.join("res", "gfx", "title_art.png")))
OUT_C = os.path.join(ROOT, "src", "bank2.c")
OUT_H = os.path.join(ROOT, "src", "bank2.h")
PREVIEW = os.path.join(ROOT, "out", "title_preview.png")

IMG_W, IMG_H = 256, 176
LIMIT_IMG = int(os.environ.get("LIMIT_IMG", 415))   # eindeutige Bild-Tiles (ohne Text)
SPREAD = float(os.environ.get("SPREAD", 26))       # Stärke des geordneten Rasters (Dithering)
COLOR = float(os.environ.get("COLOR", 1.25))
CONTRAST = float(os.environ.get("CONTRAST", 1.12))
BRIGHT = float(os.environ.get("BRIGHT", 1.18))
SHARP = float(os.environ.get("SHARP", 1.4))
TEXT = "PUSH 1 TO START"

LEVELS = np.array([0, 85, 170, 255], float)
C64 = np.array([(r, g, b) for b in LEVELS for g in LEVELS for r in LEVELS])      # Index = r + 4g + 16b
WRGB = np.array([2.0, 4.0, 3.0])                                                  # Farbabstand: Grün zählt mehr
D64 = (((C64[:, None, :] - C64[None, :, :]) ** 2) * WRGB).sum(-1)
NAVY, WHITE = 16, 63                                                              # (0,0,1) und (3,3,3)
BAYER = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) + 0.5) / 16 - 0.5


def load_image():
    im = Image.open(SRC).convert("RGB")
    if im.size != (IMG_W, IMG_H):
        im = im.resize((IMG_W, IMG_H), Image.LANCZOS)
    im = ImageEnhance.Color(im).enhance(COLOR)
    im = ImageEnhance.Contrast(im).enhance(CONTRAST)
    im = ImageEnhance.Brightness(im).enhance(BRIGHT)
    im = ImageEnhance.Sharpness(im).enhance(SHARP)
    return np.asarray(im, float)


def tiles_of(arr):
    h, w = arr.shape[:2]
    t = arr.reshape(h // 8, 8, w // 8, 8, -1).transpose(0, 2, 1, 3, 4)
    return t.reshape(-1, 64, arr.shape[2])


def nearest64(px):
    d = (((px[..., None, :] - C64) ** 2) * WRGB).sum(-1)
    return d.argmin(-1)


def best_palette(hist_sum, forced):
    def cost(p):
        return float((hist_sum * D64[:, p].min(axis=1)).sum())
    chosen = list(forced)
    while len(chosen) < 16:
        best = min((cost(chosen + [c]), c) for c in range(64) if c not in chosen)
        chosen.append(best[1])
    improved = True
    while improved:
        improved = False
        for i in range(len(forced), 16):
            cur = cost(chosen)
            for c in range(64):
                if c in chosen:
                    continue
                trial = chosen.copy()
                trial[i] = c
                cc = cost(trial)
                if cc < cur - 1e-9:
                    chosen, cur, improved = trial, cc, True
    return chosen


def optimise_palettes(tiles_rgb):
    px64 = nearest64(tiles_rgb)                       # (T, 64)
    hist = np.zeros((len(px64), 64))
    for t, row in enumerate(px64):
        hist[t] = np.bincount(row, minlength=64)
    lum = (tiles_rgb.mean(1) * np.array([0.3, 0.59, 0.11])).sum(1)
    assign = (lum > np.median(lum)).astype(int)
    forced = [NAVY, WHITE]
    pals = None
    for it in range(14):
        pals = []
        for g in (0, 1):
            sel = hist[assign == g].sum(0) if (assign == g).any() else hist.sum(0)
            pals.append(best_palette(sel, forced))
        errs = [(hist * D64[:, p].min(axis=1)).sum(1) for p in pals]
        new = (errs[1] < errs[0]).astype(int)
        print(f"  Palettenrunde {it}: Fehler {errs[0][new == 0].sum() + errs[1][new == 1].sum():.0f}, "
              f"Gruppen {np.bincount(new, minlength=2)}")
        if (new == assign).all():
            break
        assign = new
    return pals, assign


def map_to_palette(tiles_rgb, pals, assign):
    idx = np.zeros((len(tiles_rgb), 64), np.uint8)
    off = np.tile(BAYER.reshape(-1), 4)[:, None] if False else None
    dither = np.zeros(64)
    for py in range(8):
        for px in range(8):
            dither[py * 8 + px] = BAYER[py % 4, px % 4] * SPREAD
    for t, tile in enumerate(tiles_rgb):
        pc = C64[pals[assign[t]]]
        p = tile + dither[:, None]
        d = (((p[:, None, :] - pc[None]) ** 2) * WRGB).sum(-1)
        idx[t] = d.argmin(-1)
    return idx


def orientations(a8):
    return [a8, a8[:, ::-1], a8[::-1, :], a8[::-1, ::-1]]       # Bit 0 = hflip, Bit 1 = vflip


def planar(idx64):
    out = bytearray()
    a = idx64.reshape(8, 8)
    for y in range(8):
        for plane in range(4):
            b = 0
            for x in range(8):
                b |= ((int(a[y, x]) >> plane) & 1) << (7 - x)
            out.append(b)
    return bytes(out)


def main():
    arr = load_image()                                             # (176, 256, 3)
    tiles_rgb = tiles_of(arr)                                      # (704, 64, 3)
    print("Paletten optimieren ...")
    pals, assign = optimise_palettes(tiles_rgb)
    idx = map_to_palette(tiles_rgb, pals, assign)
    n = len(idx)

    # --- exakt zusammenlegen (mit Spiegelungen)
    uniq, ukey, place = [], {}, []                                 # place[t] = (u, flags)
    solid = np.zeros(64, np.uint8)                                 # Tile 0: einfarbig dunkel (Index 0 = Navy)
    uniq.append((0, solid))
    ukey[(0, solid.tobytes())] = 0
    counts = [10 ** 6]
    for t in range(n):
        pid, a = int(assign[t]), idx[t]
        found = None
        for o, v in enumerate(orientations(a.reshape(8, 8))):
            k = (pid, np.ascontiguousarray(v).reshape(64).tobytes())
            if k in ukey:
                found = (ukey[k], o)
                break
        if found is None:
            ukey[(pid, a.tobytes())] = len(uniq)
            found = (len(uniq), 0)
            uniq.append((pid, a))
            counts.append(0)
        counts[found[0]] += 1
        place.append(found)
    U = len(uniq)
    print(f"{n} Kacheln, davon {U} eindeutig (mit Spiegelung)")

    # --- zu viele? Ähnlichste zusammenlegen
    cnt = np.array(counts, float)
    alive = np.ones(U, bool)
    redirect = {}                                                  # u -> (b, flags)
    if U > LIMIT_IMG + 1:
        pid = np.array([p for p, _ in uniq])
        rgb = np.array([C64[pals[p]][a] for p, a in uniq]) * np.sqrt(WRGB)   # (U, 64, 3) gewichtet
        D = np.full((U, U), np.inf)
        O = np.zeros((U, U), np.uint8)
        A = rgb.reshape(U, -1)
        a2 = (A ** 2).sum(1)
        for o in range(4):
            V = np.array([orientations(r.reshape(8, 8, 3).transpose(2, 0, 1)[0])[0] for r in rgb[:0]]) if False else None
            vv = rgb.reshape(U, 8, 8, 3)
            if o & 1:
                vv = vv[:, :, ::-1, :]
            if o & 2:
                vv = vv[:, ::-1, :, :]
            B = np.ascontiguousarray(vv).reshape(U, -1)
            Do = a2[:, None] + (B ** 2).sum(1)[None, :] - 2 * np.einsum('ik,jk->ij', A, B, optimize=False)
            better = Do < D
            D[better] = Do[better]
            O[better] = o
        D[pid[:, None] != pid[None, :]] = np.inf
        np.fill_diagonal(D, np.inf)
        D[0, :] = np.inf                                           # Tile 0 bleibt
        remaining = U
        while remaining > LIMIT_IMG + 1:
            nn = D.argmin(1)
            nd = D[np.arange(U), nn]
            cost = np.where(alive, cnt * nd, np.inf)
            cost[0] = np.inf
            a = int(cost.argmin())
            b = int(nn[a])
            redirect[a] = (b, int(O[a, b]))
            cnt[b] += cnt[a]
            alive[a] = False
            D[a, :] = np.inf
            D[:, a] = np.inf
            remaining -= 1
        print(f"  zusammengelegt auf {int(alive.sum())} Kacheln")

    def resolve(u, flags):
        while u in redirect:
            u, f = redirect[u]
            flags ^= f
        return u, flags

    # --- endgültige Tile-Nummern (Tile 0 = Navy-Fläche)
    final, newid = [], {}
    for u in range(U):
        if alive[u]:
            newid[u] = len(final)
            final.append(uniq[u])
    pal_of_final = [p for p, _ in final]

    words = np.zeros(32 * 24, np.uint16)
    for t in range(n):
        u, fl = resolve(*place[t])
        words[t] = newid[u] | ((fl & 1) << 9) | ((fl >> 1 & 1) << 10) | (pal_of_final[newid[u]] << 11)
    # untere zwei Zeilen = Tile 0 (Navy), Palette 0 -> Wort 0

    # --- Text in Zeile 22 und Zeichen für die Weltauswahl (Zeile 23)
    ARROWS = {"<": ["00010", "00100", "01000", "00100", "00010", "00000", "00000"],
              ">": ["01000", "00100", "00010", "00100", "01000", "00000", "00000"]}

    def glyph_word(ch):
        g = np.zeros((8, 8), np.uint8)
        for r, row in enumerate(ARROWS.get(ch) or FONT[ch]):
            for c, v in enumerate(row):
                if v == "1":
                    g[r + 1, c] = 1                                 # Palettenplatz 1 = Weiß
        tid = None
        for o, v in enumerate(orientations(g)):
            k = np.ascontiguousarray(v).reshape(64).tobytes()
            for fi, (p, a) in enumerate(final):
                if p == 0 and a.tobytes() == k:
                    tid = (fi, o)
                    break
            if tid:
                break
        if tid is None:
            final.append((0, g.reshape(64).astype(np.uint8)))
            tid = (len(final) - 1, 0)
        fi, o = tid
        return fi | ((o & 1) << 9) | ((o >> 1 & 1) << 10)

    text_words = np.zeros(32, np.uint16)
    x0 = (32 - len(TEXT)) // 2
    pal0 = pals[0]
    for i, ch in enumerate(TEXT):
        if ch != " ":
            text_words[x0 + i] = glyph_word(ch)
    GLYPHS = "WORLD123456<>"
    glyph_words = [glyph_word(ch) for ch in GLYPHS]
    nt = len(final)
    print(f"Tiles gesamt (VRAM): {nt} von 448, Bank-2-Größe ca. {nt * 32 + 32 * 24 * 2 + 64 + 32} Byte von 16384")
    assert nt <= 440, "zu viele Tiles"
    assert nt * 32 + 32 * 24 * 2 + 64 + 32 <= 16384, "passt nicht in eine ROM-Bank"

    # --- C-Dateien
    def carr(name, data, typ, per=16, fmt="0x%02X"):
        s = f"const {typ} {name}[{len(data)}] = {{\n"
        for i in range(0, len(data), per):
            s += "  " + ", ".join(fmt % v for v in data[i:i + per]) + ",\n"
        return s + "};\n\n"

    tile_bytes = b"".join(planar(a) for _, a in final)
    with open(OUT_C, "w") as f:
        f.write("// GENERIERT von tools/make_title.py - nicht von Hand ändern.\n"
                "// Wird mit --constseg BANK2 übersetzt und liegt in ROM-Bank 2 (vor dem Zugriff SMS_mapROMBank(2)).\n"
                '#include "bank2.h"\n\n')
        f.write(carr("title_pal0", pals[0], "unsigned char"))
        f.write(carr("title_pal1", pals[1], "unsigned char"))
        f.write(carr("title_map", [int(w) for w in words], "unsigned int", 12, "0x%04X"))
        f.write(carr("title_text_map", [int(w) for w in text_words], "unsigned int", 12, "0x%04X"))
        f.write(carr("title_glyph", glyph_words, "unsigned int", 13, "0x%04X"))
        f.write(carr("title_tiles", list(tile_bytes), "unsigned char"))
    with open(OUT_H, "w") as f:
        f.write("// GENERIERT von tools/make_title.py - nicht von Hand ändern.\n#ifndef BANK2_H\n#define BANK2_H\n\n"
                f"#define TITLE_TILE_COUNT {nt}\n#define TITLE_TILE_BYTES {nt * 32}\n"
                "#define TITLE_TEXT_ROW 22\n\n"
                "extern const unsigned char title_pal0[16];    // BG-Palette\n"
                "extern const unsigned char title_pal1[16];    // Sprite-Palette (Tiles wählen sie per Attribut)\n"
                "extern const unsigned int title_map[32 * 24];\n"
                "extern const unsigned int title_text_map[32]; // Zeile 22 mit Text; ohne Text: Zeile 22 aus title_map\n"
                f"extern const unsigned int title_glyph[{len(GLYPHS)}];  // Zeichen \"{GLYPHS}\" (Tilemap-Wörter) für die Weltauswahl\n"
                f"extern const unsigned char title_tiles[{nt * 32}];\n\n#endif\n")

    # --- Vorschau
    out = np.zeros((192, 256, 3), np.uint8)
    for ty in range(24):
        for tx in range(32):
            w = int(words[ty * 32 + tx])
            if ty == 22:
                w = int(text_words[tx])
            ti, hf, vf, pl = w & 0x1FF, (w >> 9) & 1, (w >> 10) & 1, (w >> 11) & 1
            p, a = final[ti]
            tile = a.reshape(8, 8)
            if hf:
                tile = tile[:, ::-1]
            if vf:
                tile = tile[::-1, :]
            out[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8] = C64[pals[pl if ty < 22 else 0]][tile].astype(np.uint8)
    os.makedirs(os.path.dirname(PREVIEW), exist_ok=True)
    Image.fromarray(out).resize((768, 576), Image.NEAREST).save(PREVIEW)
    print("Vorschau:", PREVIEW)


if __name__ == "__main__":
    main()
