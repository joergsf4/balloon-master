#!/usr/bin/env python3
"""Titelbild im Stil der Spielgrafik (256x176, Buchstaben-Farben aus palette.py) -> res/gfx/title_art.png.

    python3 tools/art/title_art.py   # danach: TITLE_SRC=res/gfx/title_art.png python3 tools/make_title.py
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from artdefs import BIG_BEN, FONT, TOWER_BRIDGE  # noqa: E402
from canvas import Canvas  # noqa: E402
from ny import godzilla_b  # noqa: E402
from palette import COLORS, rgb8  # noqa: E402
from pixelart import write_png  # noqa: E402

W, H = 256, 176
HORIZON = 132
# Abendhimmel von oben nach unten (Farbe, Höhe); an den Übergängen schachbrettartig gemischt
SKY = [('D', 14), ('v', 16), ('m', 18), ('r', 18), ('o', 16), ('y', 20), ('Y', 30)]


def sky(cv):
    y = 0
    bands = []
    for c, h in SKY:
        bands.append((c, y, y + h))
        y += h
    for i, (c, y0, y1) in enumerate(bands):
        cv.rect(0, y0, W, y1, c)
        if i + 1 < len(bands):
            nxt = bands[i + 1][0]
            for yy in (y1 - 2, y1 - 1):
                for x in range(W):
                    if (x + yy) % 2 == 0:
                        cv.put(x, yy, nxt)
    for yy in range(H):
        pass


def sun(cv):
    cv.disc(196, 120, 17, 'w')
    cv.disc(196, 120, 13, 'Y')
    cv.disc(196, 120, 9, 'w')


def cloud(cv, x, y, w):
    sub = Canvas(w, 12)
    sub.blob([(w * 0.3, 7, 5), (w * 0.5, 5, 6), (w * 0.72, 7, 5), (w * 0.5, 8, 4)], ('m', 'm', 'r', 'r'), (2, 4, 6))
    for yy in range(sub.h):
        for xx in range(sub.w):
            c = sub.g[yy][xx]
            if c != '.':
                cv.put(x + xx, y + yy, c)


def stamp(cv, rows, x0, y0, recolor=None):
    for yy, r in enumerate(rows):
        for xx, c in enumerate(r):
            if c != '.':
                cv.put(x0 + xx, y0 + yy, recolor.get(c, c) if recolor else c)


def water(cv):
    cv.rect(0, HORIZON, W, H, 'A')
    for y in range(HORIZON, H):
        d = y - HORIZON
        c = 'A' if d < 14 else ('T' if d < 30 else 'n')
        cv.rect(0, y, W, y + 1, c)
    for x in range(W):                                           # Übergang
        if x % 2 == 0:
            cv.put(x, HORIZON + 13, 'T')
            cv.put(x, HORIZON + 29, 'n')
    for i, (y, w) in enumerate(((HORIZON + 2, 30), (HORIZON + 5, 22), (HORIZON + 8, 14), (HORIZON + 12, 8))):
        cv.rect(196 - w, y, 196 + w, y + 1, 'y')                 # Sonnenspiegelung
    for i in range(18):                                           # Wellenstriche
        x = (i * 53) % 240
        y = HORIZON + 5 + (i * 7) % 38
        cv.rect(x, y, x + 6 + i % 5, y + 1, 'w' if i % 3 == 0 else 'A')


def skyline(cv):
    # Häuser links, Big Ben, Tower Bridge hinten, Riesenechse rechts (alles abends, deshalb leicht dunkler abgesetzt)
    for x0, w, h, c in ((0, 14, 22, 'E'), (46, 16, 18, 'E'), (60, 12, 28, 'E')):
        cv.rect(x0, HORIZON - h, x0 + w, HORIZON, c)
        for wy in range(HORIZON - h + 4, HORIZON - 3, 6):
            for wx in range(x0 + 3, x0 + w - 3, 5):
                cv.rect(wx, wy, wx + 2, wy + 3, 'y')
    stamp(cv, TOWER_BRIDGE, 72, HORIZON - 96 + 4)
    stamp(cv, BIG_BEN, 16, HORIZON - 96 + 2)
    stamp(cv, godzilla_b(), 172, HORIZON - 112 + 18)
    cv.rect(160, HORIZON - 2, W, HORIZON + 1, 'E')


def balloon(cv, cx, top):
    """Großer Ballon mit Korb, Pilot und Brennerflamme. cx = Mitte, top = Oberkante."""
    R = 30
    cy = top + R + 2
    for y in range(top, cy + 34):
        t = y - cy
        if t <= 0:
            half = math.sqrt(max(0, R * R - t * t))
        else:
            half = R * (1 - t / 34.0) ** 0.8 * 0.95 + 10 * (t / 34.0)
            half = max(half, 12 * (1 - t / 34.0) + 10)
        for x in range(int(cx - half), int(cx + half) + 1):
            u = (x - (cx - half)) / max(1.0, 2 * half)
            seg = int((x - cx + 40) // 8) % 2
            col = 'y' if seg == 0 else 'r'
            if u > 0.78:
                col = 'o' if seg == 0 else 'R'
            if u < 0.12:
                col = 'w' if seg == 0 else 'm'
            cv.put(x, y, col)
        cv.put(cx - half, y, 'k')
        cv.put(cx + half, y, 'k')
    for x in range(int(cx - R), int(cx + R) + 1):                 # Umriss oben
        yy = cy - math.sqrt(max(0, R * R - (x - cx) ** 2))
        cv.put(x, yy, 'k')
        cv.put(x, yy - 1, 'k')
    by = cy + 44
    cv.line(cx - 12, cy + 33, cx - 9, by, 'k', 1)                 # Seile
    cv.line(cx + 12, cy + 33, cx + 9, by, 'k', 1)
    cv.line(cx - 12, cy + 33, cx - 8, by, 'e', 1)
    cv.line(cx + 12, cy + 33, cx + 8, by, 'e', 1)
    cv.rect(cx - 14, by, cx + 14, by + 16, 'k')                   # Korb
    cv.rect(cx - 13, by + 1, cx + 13, by + 15, 'b')
    for x in range(cx - 13, cx + 13):
        for y in range(by + 3, by + 15, 3):
            cv.put(x, y, 'B')
    for y in range(by + 1, by + 15):
        for x in range(cx - 13, cx + 13, 4):
            cv.put(x, y, 'B')
    cv.rect(cx - 14, by - 1, cx + 14, by + 2, 'y')
    cv.rect(cx - 14, by - 1, cx + 14, by, 'k')
    cv.disc(cx - 4, by - 6, 5, 'k')                               # Pilot: Kopf mit Mütze, Schal
    cv.disc(cx - 4, by - 6, 4, 'c')
    cv.rect(cx - 8, by - 11, cx, by - 8, 'r')
    cv.rect(cx - 9, by - 8, cx + 1, by - 7, 'k')
    cv.put(cx - 6, by - 6, 'k')
    cv.put(cx - 2, by - 6, 'k')
    cv.rect(cx - 6, by - 1, cx + 0, by + 1, 'w')


def lettering(cv, text, y, scale=3, gap=1):
    cw = 5 * scale + gap * scale
    total = len(text) * cw - gap * scale
    x0 = (W - total) // 2
    for i, ch in enumerate(text):
        if ch == ' ':
            continue
        gx = x0 + i * cw
        for r, row in enumerate(FONT[ch]):
            for c, v in enumerate(row):
                if v != '1':
                    continue
                for dy in range(scale):
                    for dx in range(scale):
                        px, py = gx + c * scale + dx, y + r * scale + dy
                        cv.put(px + 1, py + 2, 'k')               # Schatten
                        cv.put(px, py, 'R' if r >= 4 else 'o')
    # Umriss
    snap = [row[:] for row in cv.g]
    for yy in range(max(0, y - 2), min(H, y + 7 * scale + 3)):
        for xx in range(W):
            if snap[yy][xx] in ('o', 'R'):
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny_ = xx + dx, yy + dy
                if 0 <= nx < W and 0 <= ny_ < H and snap[ny_][nx] in ('o', 'R'):
                    cv.put(xx, yy, 'k')
                    break
    for r, row in enumerate(FONT[text[0]]):
        pass


def main():
    cv = Canvas(W, H)
    sky(cv)
    sun(cv)
    cloud(cv, 8, 62, 44)
    cloud(cv, 200, 56, 40)
    cloud(cv, 120, 76, 34)
    skyline(cv)
    water(cv)
    balloon(cv, 118, 54)
    lettering(cv, "BALLOON", 6)
    lettering(cv, "MASTER", 31)
    px = [[rgb8(COLORS[c]) if c != '.' else rgb8(COLORS['a']) for c in row] for row in cv.rows()]
    out = os.path.join(HERE, "..", "..", "res", "gfx", "title_art.png")
    write_png(out, W, H, px)
    print(out)


if __name__ == "__main__":
    main()
