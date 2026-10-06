"""Welt 3: Gewitter (kurz). Dunkler Himmel, Gewitterwolken als Türme von unten, hängende Wolken mit Blitzen,
unruhiges Meer darunter; Ziel ist ein Regenbogen mit durchbrechender Sonne."""
import math
import random

from canvas import Canvas

STORM_PAL = "kEeDqwnATtyrogaY"          # Platz 0 = dunkler Himmel


def storm_bg(y):
    if y < 144:
        return 'k'
    return 'e'                                # grauer Dunst hinter den unteren Wolken (Grau der Wolken)

def band():
    return [storm_bg(104 + y) * 256 for y in range(64)]


def water():
    """Untere Wolkenebene (Parallax statt Meer), 32x24, zwei Kacheln wiederholt: dunkle Wolken mit runden Kuppen."""
    cv = Canvas(32, 24)
    puffs = [(7, 12, 9), (22, 11, 11), (31, 13, 7)]

    def inside(x, y):
        if y >= 14:
            return True
        return any((x - cx - k) ** 2 + (y - cy) ** 2 <= r * r for cx, cy, r in puffs for k in (-32, 0, 32))
    for y in range(24):
        for x in range(32):
            cv.put(x, y, ('w' if (y == 0 or not inside(x, y - 1)) else 'E') if inside(x, y) else 'e')
    return cv.rows()


def no_cloud():
    return ['.' * 48] * 16                      # keine Standardwolken am oberen Rand


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
H = 64                                   # Höhe eines Moduls (8 Kachelzeilen)
PAD = 12                                 # Rand zum Rechnen (nur für die Schattierung an den Nähten), wird abgeschnitten
SLAB_TOP, SLAB_BOT = 12, 12              # Dicke der durchgehenden Schicht an Decke bzw. Wasserlinie (px)
EDGE_R, EDGE_D = 18, 22                  # Randpuff: Radius und Tiefe (Unterkante bzw. Höhe der Oberkante über dem Boden)

# Puffs: (Mitte x, Radius, Tiefe). Tiefe = wie weit die Unterkante unter der Decke (bzw. die Oberkante über dem Boden) liegt.
# Ceil: 1,2 ruhig; 3,4,5 schwer; 6 = Anfangskappe (links offen, wächst), 7 = Endkappe (rechts offen, läuft aus).
# Floor: 1,2 ruhig; 3,4 schwer; 5 = Anfangskappe, 6 = Endkappe. Dritte Angabe: 0 normal, 1 links offen, 2 rechts offen.
TOP_MODULES = [
    ([(16, 12, 30), (40, 10, 24), (56, 8, 28)], False, 0),
    ([(10, 8, 26), (30, 14, 34), (52, 10, 28)], True, 0),
    ([(14, 9, 40), (34, 13, 50), (54, 9, 34)], False, 0),
    ([(12, 12, 46), (32, 10, 30), (50, 14, 52)], True, 0),
    ([(12, 9, 52), (30, 9, 36), (48, 13, 46)], True, 0),
    ([(7, 7, 15), (20, 10, 20), (34, 12, 20), (48, 10, 30), (58, 8, 24)], False, 1),
    ([(57, 7, 15), (44, 10, 20), (30, 12, 20), (16, 10, 30), (6, 8, 24)], False, 2),
]
BOTTOM_MODULES = [
    ([(14, 12, 26), (38, 14, 34), (56, 8, 24)], False, 0),
    ([(10, 8, 30), (30, 10, 22), (50, 14, 32)], False, 0),
    ([(14, 10, 34), (34, 14, 48), (54, 9, 40)], False, 0),
    ([(10, 8, 36), (28, 12, 46), (48, 12, 50)], False, 0),
    ([(7, 7, 15), (20, 10, 22), (34, 13, 28), (48, 10, 34), (58, 8, 26)], False, 1),
    ([(57, 7, 15), (44, 10, 22), (30, 13, 28), (16, 10, 34), (6, 8, 26)], False, 2),
]


def _tail(cx, op):
    """Offene Kappen: die äußeren Puffs sind ganze Kreise (kein Turm bis zum Rand), damit das Ende rund ausläuft."""
    return not ((op == 1 and cx < 28) or (op == 2 and cx > 36))


def _slab_x(x, op):
    return (op != 1 or x >= 30) and (op != 2 or x <= 34)


def _edges(op):
    return [] if op else [(0, EDGE_R, EDGE_D), (64, EDGE_R, EDGE_D)]


def _inside_top(x, y, puffs, op=0):
    if y < SLAB_TOP and _slab_x(x, op):
        return True
    for cx, r, d in puffs + (_edges(op) if op == 0 else []):
        cy = d - r
        if (x - cx) ** 2 + (y - cy) ** 2 <= r * r or (_tail(cx, op) and y <= cy and abs(x - cx) <= r + (cy - y) * 0.25):
            return True
    return False


def _inside_bottom(x, y, puffs, op=0):
    if y >= H - SLAB_BOT and _slab_x(x, op):
        return True
    for cx, r, d in puffs + (_edges(op) if op == 0 else []):
        cy = H - d + r
        if (x - cx) ** 2 + (y - cy) ** 2 <= r * r or (_tail(cx, op) and y >= cy and abs(x - cx) <= r + (y - cy) * 0.25):
            return True
    return False


def _render(puffs, top, op=0):
    """Maske der Puffs -> Wolke. Schattiert wird nach dem Abstand zur Oberfläche (senkrecht): erst eine helle Randzeile, dann ein
    heller Saum, innen eine ruhige Füllung mit wenig Körnung. So bleiben viele Kacheln gleich und das Kachelbudget klein."""
    inside = _inside_top if top else _inside_bottom
    def ins(x, y):
        if top and y < 0:
            return True
        if not top and y >= H:
            return True
        return inside(x, y, puffs, op)
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
            if d == 0 or not ins(x, y - step):
                t = 'w'                                                    # Randzeile
            else:
                t = 'e'
            out[y][x] = t
    # seitliche Ränder der Puffs ebenfalls hell (nicht am Modulrand)
    for y in range(H):
        for x in range(64):
            if out[y][x] == '.':
                continue
            if (0 < x and out[y][x - 1] == '.') or (x < 63 and out[y][x + 1] == '.'):
                out[y][x] = 'w'
    return [''.join(r) for r in out]


def _ceil_rows(idx):
    return _render(TOP_MODULES[idx][0], True, TOP_MODULES[idx][2])


def _floor_rows(idx):
    return _render(BOTTOM_MODULES[idx][0], False, BOTTOM_MODULES[idx][2])


def _bolt_of(idx):
    """Blitz unter dem tiefsten Puff der Deckenwolke: (x-Versatz im Modul, y der Unterkante)."""
    from pixelart import profile_bottom
    puffs, bolt, _op = TOP_MODULES[idx]
    if not bolt:
        return (0, 0)
    prof = profile_bottom(_ceil_rows(idx), 16)
    c = max(range(8), key=lambda i: (prof[i], -abs(i - 3.5)))
    return (max(0, 8 * c - 4), prof[c] - 2)


def _godzilla(open_mouth):
    """Echsenkopf von der Seite (schaut nach links, 30 Grad nach oben geneigt), 48x40, in zwei Bildern: Maul zu / Maul auf."""
    from pixelart import outlined
    S = 1.4
    cv = Canvas(48, 48)

    def P(*pts):
        return [(int(round(x * S)), int(round(y * S))) for x, y in pts]

    def R(x0, y0, x1, y1, c):
        cv.rect(int(round(x0 * S)), int(round(y0 * S)), int(round(x1 * S)), int(round(y1 * S)), c)

    def pt(x, y, c, w=1, h=1):
        for i in range(w):
            for j in range(h):
                cv.put(int(round(x * S)) + i, int(round(y * S)) + j, c)
    cv.poly(P((2, 12), (6, 8), (14, 6), (22, 7), (28, 12), (28, 22), (14, 22), (4, 18)), 'g')      # Schädel und Schnauze
    for k, hx in enumerate((15, 20, 25)):                                                         # Rückenplatten
        cv.poly(P((hx, 7 - k // 2), (hx + 2, 1 + k), (hx + 4, 7 - k // 2)), 'E')
    R(12, 9, 15, 11, 'y')                                                                         # Auge
    R(13, 10, 14, 11, 'k')
    R(10, 7, 17, 7, 'k')                                                                          # Braue
    pt(3, 12, 'k', 2, 2)
    if open_mouth:
        cv.poly(P((2, 16), (14, 15), (16, 20), (14, 26), (4, 24)), 'r')                           # offenes Maul mit Unterkiefer
        cv.poly(P((4, 24), (14, 26), (16, 30), (6, 28)), 'g')
        for tx in (3, 6, 9, 12):
            pt(tx, 17, 'w', 2, 3)
        for tx in (5, 9, 13):
            pt(tx, 24, 'w', 2, 3)
    else:
        for tx in (3, 6, 9, 12):
            pt(tx, 18, 'w', 2, 3)
        R(3, 20, 14, 20, 'k')
    src = cv.rows()                                                    # um 30 Grad nach oben neigen (Drehpunkt am Hals)
    px, py = 22.0 * S, 20.0 * S
    c, sn = 0.8660, 0.5
    cv2 = Canvas(48, 48)
    for y in range(48):
        for x in range(48):
            sx = int(round(px + (x - px) * c + (y - py) * sn))
            sy = int(round(py - (x - px) * sn + (y - py) * c))
            if 0 <= sx < 48 and 0 <= sy < 48 and src[sy][sx] != '.':
                cv2.put(x, y, src[sy][sx])
    nx0 = int(round(px - 8))
    cv2.rect(nx0, int(py), nx0 + 21, 47, 'g')                          # Hals (taucht in die Wolkenebene)
    cv2.rect(nx0 + 17, int(py), nx0 + 21, 47, 't')
    return outlined([r[1:47] for r in cv2.rows()[1:39]])              # 46x38 + Umriss = 48x40


def _sprites():
    return [("godz_a", _godzilla(False)), ("godz_b", _godzilla(True))]


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
    "bg": storm_bg, "ground": water, "far_cloud": no_cloud,
    "floors": [{"name": "b%d" % (i + 1), "rows": (lambda i=i: _floor_rows(i))} for i in range(6)],
    "finish": {"name": "rainbow", "rows": rainbow},
    "chain": 6,
}
for _i in range(7):
    SPEC["ceil%d" % (_i + 1)] = {"name": "c%d" % (_i + 1), "rows": (lambda i=_i: _ceil_rows(i)), "top_row": 2, "bolt": _bolt_of(_i)}
SPEC.update({
    "kind_bld": [1, 2, 3, 4, 5, 6, 1, 2], "kind_ceil": [1, 2, 3, 4, 5, 6, 1, 2],
    "sky": "k", "flash": 0x3F,
    "phys": (1, 3, 24, 32), "wind": (40, 52, 64, 76), "level_cols": 600, "nofuel": 1, "boss": "godz_a", "sprites": _sprites(),
    "flyer": {"shared": "BIRD_UP", "w": 2, "h": 2, "hit": (3, 6, 13, 12), "fast": 40},
    "music": 2,
})
