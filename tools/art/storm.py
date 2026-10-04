"""Welt 3: Gewitter (kurz). Dunkler Himmel, Gewitterwolken als Türme von unten, hängende Wolken mit Blitzen,
unruhiges Meer darunter; Ziel ist ein Regenbogen mit durchbrechender Sonne."""
import math
import random

from canvas import Canvas

STORM_PAL = "kEeDqwnATtyrogaY"          # Platz 0 = dunkler Himmel


def storm_bg(y):
    if y < 128:
        return 'k'
    if y < 152:
        return 'n'
    return 'T'


def band():
    return [storm_bg(104 + y) * 256 for y in range(64)]


def water():
    """Unruhiges Meer, 32x24, zwei Kacheln wiederholt."""
    cv = Canvas(32, 24)
    for y in range(24):
        for x in range(32):
            cv.put(x, y, 'A' if y < 8 else ('n' if y < 16 else 'k'))
    rnd = random.Random(11)
    for tx in range(2):
        for row, crest in enumerate(('q', 'A', 'n')):
            for k in range(2):
                n = rnd.randint(3, 6)
                x = tx * 8 + rnd.randint(0, 8 - n)
                y = row * 8 + (2 if k == 0 else 5)
                for i in range(n):
                    cv.put(x + i, y, crest)
    for y in range(24):
        for x in range(16):
            cv.put(16 + x, y, cv.g[y][x])
    return cv.rows()


def far_cloud():
    cv = Canvas(48, 16)
    cv.blob([(10, 10, 6), (21, 7, 8), (33, 8, 7), (41, 11, 5), (24, 11, 6)], ('e', 'E', 'E', 'D'))
    for y in range(13, 16):
        for x in range(48):
            cv.put(x, y, '.')
    return cv.rows()


def _head(w, h, circles):
    cv = Canvas(w, h)
    cv.blob(circles, ('q', 'e', 'E', 'D'), (4, 12, 26))
    return cv.rows()


def t1():
    return _head(64, 56, [(18, 40, 16), (34, 32, 20), (48, 40, 15), (32, 46, 14)])


def t2():
    return _head(72, 88, [(36, 70, 22), (24, 58, 18), (48, 54, 20), (34, 40, 18), (42, 24, 16), (30, 62, 16), (22, 76, 14)])


def t3():
    return _head(64, 112, [(32, 96, 24), (22, 78, 18), (42, 76, 20), (30, 56, 18), (38, 38, 16), (32, 20, 14), (24, 100, 14)])


def dark():
    """Große dunkle Gewitterwolke zum Aufhängen (56x48)."""
    cv = Canvas(56, 48)
    cv.blob([(12, 20, 11), (26, 14, 15), (42, 20, 12), (28, 28, 15), (14, 30, 9), (44, 31, 9)], ('e', 'e', 'E', 'D'), (4, 10, 22))
    for x in range(56):
        for y in range(43, 48):
            cv.put(x, y, '.')
    return cv.rows()


def rainbow():
    cv = Canvas(128, 80)
    cx, cy, R = 64, 76, 58
    for y in range(80):
        for x in range(128):
            d = math.hypot(x - cx, y - cy)
            if y <= cy and d < R - 12:
                cv.put(x, y, 'a')                         # Himmel bricht auf
    cv.disc(64, 44, 15, 'Y')
    cv.disc(64, 44, 9, 'w')
    cols = ['r', 'o', 'y', 'g', 'a', 'n']
    for y in range(80):
        for x in range(128):
            d = math.hypot(x - cx, y - cy)
            if y <= cy + 2 and R - 12 <= d < R:
                cv.put(x, y, cols[min(5, int((R - d) // 2))])
    for x in range(0, 128, 6):
        cv.put(x, 77, 'q')
        cv.put(x + 1, 77, 'q')
    return cv.rows()


def _storm():
    from artdefs import STORM_CLOUD
    return STORM_CLOUD


SPEC = {
    "id": "storm", "title": "Gewitter", "bank": 4, "pal": STORM_PAL,
    "bg": storm_bg, "ground": water, "far_cloud": far_cloud,
    "floors": [{"name": "t1", "rows": t1}, {"name": "t2", "rows": t2}, {"name": "t3", "rows": t3}],
    "finish": {"name": "rainbow", "rows": rainbow},
    "ceil1": {"name": "storm", "rows": _storm, "top_row": 2, "bolt": (20, 44)},
    "ceil2": {"name": "dark", "rows": dark, "top_row": 2, "bolt": (16, 58)},
    "kind_bld": [1, 2, 0, 3, 0, 1, 3, 0], "kind_ceil": [0, 0, 1, 0, 2, 1, 0, 2],
    "sky": "k", "flash": 0x3F,
    "phys": (1, 3, 24, 32), "wind": (16, 24, 32, 40), "level_cols": 217,
    "flyer": None,
    "music": 2,
}
