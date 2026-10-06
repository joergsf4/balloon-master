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


# ---------------------------------------------------------------- Wolken-Puffs und Formationen
# Die Gewitterwolken sind Kettenmodule (64 px = 8 Spalten breit), die lückenlos aneinandergereiht werden: oben hängt eine
# Wolkenformation, unten steigt eine auf, dazwischen liegt der Kanal. Jedes Modul ist eine Vereinigung runder Puffs (Kreise
# in drei Größen) auf einer durchgehenden Wolkenschicht. An beiden Modulrändern sitzt derselbe halbe Randpuff: zwei
# Module ergeben an der Naht einen ganzen Kreis, die Formation fließt ohne Stufe. Schattiert wird wie bei den übrigen
# Wolken von links oben; eine helle Randzeile hebt die Wolken vom Himmel ab.
H = 48                                   # Höhe eines Moduls (6 Kachelzeilen)
PAD = 12                                 # Rand zum Rechnen (nur für die Schattierung an den Nähten), wird abgeschnitten
SLAB_TOP, SLAB_BOT = 12, 12              # Dicke der durchgehenden Schicht an Decke bzw. Wasserlinie (px)
EDGE_R, EDGE_D = 18, 22                  # Randpuff: Radius und Tiefe (Unterkante bzw. Höhe der Oberkante über dem Boden)

# Puffs: (Mitte x, Radius, Tiefe). Tiefe = wie weit die Unterkante unter der Decke (bzw. die Oberkante über dem Boden) liegt.
TOP_MODULES = [
    ([(16, 10, 28), (30, 13, 36), (46, 9, 30)], False),
    ([(12, 12, 32), (28, 16, 42), (50, 11, 34)], True),
    ([(20, 14, 40), (36, 9, 28), (52, 13, 38)], False),
    ([(14, 9, 30), (32, 17, 44), (48, 12, 36)], True),
    ([(10, 11, 32), (26, 12, 38), (40, 10, 42), (54, 10, 32)], False),
    ([(18, 15, 42), (34, 11, 32), (50, 15, 40)], True),
]
BOTTOM_MODULES = [
    ([(16, 10, 28), (32, 14, 36), (48, 10, 28)], False),
    ([(12, 13, 36), (30, 9, 26), (46, 15, 42)], False),
    ([(20, 12, 34), (34, 16, 44), (52, 10, 30)], False),
    ([(10, 10, 30), (26, 14, 40), (42, 11, 34), (56, 9, 28)], False),
    ([(18, 16, 44), (38, 10, 30), (52, 13, 38)], False),
    ([(14, 12, 36), (30, 10, 30), (44, 16, 44)], False),
]


def _inside_top(x, y, puffs):
    if y < SLAB_TOP:
        return True
    for cx, r, d in puffs + [(0, EDGE_R, EDGE_D), (64, EDGE_R, EDGE_D)]:
        cy = d - r
        if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
            return True
    return False


def _inside_bottom(x, y, puffs):
    if y >= H - SLAB_BOT:
        return True
    for cx, r, d in puffs + [(0, EDGE_R, EDGE_D), (64, EDGE_R, EDGE_D)]:
        cy = H - d + r
        if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
            return True
    return False


def _render(puffs, top):
    """Maske der Puffs -> Wolke. Schattiert wird nach dem Abstand zur Oberfläche (senkrecht): erst eine helle Randzeile, dann ein
    heller Saum, innen eine ruhige Füllung mit wenig Körnung. So bleiben viele Kacheln gleich und das Kachelbudget klein."""
    inside = _inside_top if top else _inside_bottom
    def ins(x, y):
        if top and y < 0:
            return True
        if not top and y >= H:
            return True
        return inside(x, y, puffs)
    rnd = random.Random(7)
    grain = [[rnd.random() for _ in range(8)] for _ in range(8)]          # Körnung: 8x8 wiederholt, damit Füllkacheln gleich werden
    out = [['.'] * 64 for _ in range(H)]
    for y in range(H):
        for x in range(64):
            if not ins(x, y):
                continue
            # senkrechter Abstand zur Oberfläche (zur Unterkante bei Deckenwolken, zur Oberkante bei Bodenwolken)
            d = 0
            step = 1 if top else -1
            yy = y
            while ins(x, yy + step) and d < 12:
                yy += step
                d += 1
            if d == 0:
                t = 'q'                                                    # Randzeile
            elif d < 4:
                t = 'e'                                                    # hellerer Saum
            else:
                t = 'D' if grain[y % 8][x % 8] < 0.12 else 'E'
            out[y][x] = t
    # seitliche Ränder der Puffs ebenfalls hell (nicht am Modulrand)
    for y in range(H):
        for x in range(64):
            if out[y][x] == '.':
                continue
            if (0 < x and out[y][x - 1] == '.') or (x < 63 and out[y][x + 1] == '.'):
                out[y][x] = 'q'
    return [''.join(r) for r in out]


def _ceil_rows(idx):
    return _render(TOP_MODULES[idx][0], True)


def _floor_rows(idx):
    return _render(BOTTOM_MODULES[idx][0], False)


def _bolt_of(idx):
    """Blitz unter dem tiefsten Puff der Deckenwolke: (x-Versatz im Modul, y der Unterkante)."""
    from pixelart import profile_bottom
    puffs, bolt = TOP_MODULES[idx]
    if not bolt:
        return (0, 0)
    prof = profile_bottom(_ceil_rows(idx), 16)
    c = max(range(8), key=lambda i: (prof[i], -abs(i - 3.5)))
    return (max(0, 8 * c - 4), prof[c] - 2)


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


SPEC = {
    "id": "storm", "title": "Gewitter", "bank": 4, "pal": STORM_PAL,
    "bg": storm_bg, "ground": water, "far_cloud": far_cloud,
    "floors": [{"name": "b%d" % (i + 1), "rows": (lambda i=i: _floor_rows(i))} for i in range(6)],
    "finish": {"name": "rainbow", "rows": rainbow},
    "chain": 6,
}
for _i in range(6):
    SPEC["ceil%d" % (_i + 1)] = {"name": "c%d" % (_i + 1), "rows": (lambda i=_i: _ceil_rows(i)), "top_row": 2, "bolt": _bolt_of(_i)}
SPEC.update({
    "kind_bld": [1, 2, 3, 4, 5, 6, 1, 2], "kind_ceil": [1, 2, 3, 4, 5, 6, 1, 2],
    "sky": "k", "flash": 0x3F,
    "phys": (1, 3, 24, 32), "wind": (24, 32, 40, 48), "level_cols": 400, "nofuel": 1,
    "flyer": None,
    "music": 2,
})
