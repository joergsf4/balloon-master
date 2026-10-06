#!/usr/bin/env python3
"""Vorschau einer Welt als Szene: python3 tools/art/preview.py <Modul>   -> out/preview_<id>.png (3-fach)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
from palette import COLORS, SPRITE_PAL, rgb8  # noqa: E402
from pixelart import write_png  # noqa: E402


def main(mod):
    spec = __import__(mod).SPEC
    bg = spec["bg"]

    def col(v):
        return rgb8(COLORS[v])
    floors = [f["rows"]() for f in spec["floors"]] + ([spec["finish"]["rows"]()] if spec.get("finish") else [])
    ceils = [spec["ceil%d" % n]["rows"]() for n in range(1, 8) if spec.get("ceil%d" % n)]
    W = sum(len(f[0]) for f in floors) + 10 * len(floors) + 20
    W = max(W, sum(len(c[0]) for c in ceils) + 10 * len(ceils) + 20)
    img = [[col(bg(y)) for _ in range(W)] for y in range(168)]
    ground = spec["ground"]()
    for y, r in enumerate(ground):
        img.append([col(r[x % len(r)]) for x in range(W)])
    far = spec["far_cloud"]()
    for y, r in enumerate(far):
        for x, c in enumerate(r):
            if c != '.':
                img[y][8 + x] = col(c)
    x = 6
    for rows in ceils:
        for y, r in enumerate(rows):
            for xx, c in enumerate(r):
                if c != '.' and 16 + y < 168:
                    img[16 + y][x + xx] = col(c)
        x += len(rows[0]) + 10
    x = 6
    for rows in floors:
        h = len(rows)
        for y, r in enumerate(rows):
            for xx, c in enumerate(r):
                if c != '.':
                    img[168 - h + y][x + xx] = col(c)
        x += len(rows[0]) + 10
    # Welt-Sprites (Gegner) unten links einblenden
    sx = W - 20
    for name, rows in reversed(spec.get("sprites", [])):
        sx -= len(rows[0]) + 4
        for y, r in enumerate(rows):
            for xx, c in enumerate(r):
                if c != '.' and c in COLORS:
                    img[100 + y][sx + xx] = col(c)
    big = [[px for px in row for _ in range(3)] for row in img for _ in range(3)]
    out = os.path.join(HERE, "..", "..", "out", "preview_%s.png" % spec["id"])
    write_png(out, len(big[0]), len(big), big)
    print(out)


if __name__ == "__main__":
    main(sys.argv[1])
