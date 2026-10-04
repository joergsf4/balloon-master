"""Welt 6 (Finale): New York im Abendrot, die Stadt brennt. Wolkenkratzer, Zeppelin, Flugzeuge; King Kong und Godzilla
erscheinen genau einmal als Höhepunkte und werfen Felsen bzw. spucken Feuer. Ziel ist die Freiheitsstatue."""
import math
import random

from canvas import Canvas

NY_PAL = "nvmoyEeDkwrRtgGb"          # Platz 0 = Abendhimmel oben (dunkelblau)


def ny_bg(y):
    if y < 32:
        return 'n'
    if y < 64:
        return 'v'
    if y < 96:
        return 'm'
    if y < 132:
        return 'o'
    return 'r'


def street():
    """Vordergrund 32x24, zwei Kacheln wiederholt: Gehweg, Asphalt mit gelben Strichen."""
    cv = Canvas(32, 24)
    for y in range(24):
        for x in range(32):
            cv.put(x, y, 'e' if y < 6 else ('E' if y < 8 else 'D'))
    for x in range(32):
        cv.put(x, 6, 'w')
    for x in range(0, 32, 16):
        for i in range(8):
            cv.put(x + i, 12, 'y')
            cv.put(x + i, 13, 'y')
    rnd = random.Random(2)
    for _ in range(10):
        cv.put(rnd.randint(0, 15), rnd.randint(16, 23), 'E')
    for y in range(24):
        for x in range(16):
            cv.put(16 + x, y, cv.g[y][x])
    return cv.rows()


def far_cloud():
    cv = Canvas(48, 16)
    cv.blob([(10, 10, 6), (21, 7, 8), (33, 8, 7), (41, 11, 5), (24, 11, 6)], ('m', 'v', 'v', 'D'), (3, 6, 9))
    for y in range(13, 16):
        for x in range(48):
            cv.put(x, y, '.')
    return cv.rows()


def _windows(cv, x0, y0, x1, y1, seed, wall):
    """Fensterraster in 8x8-Zellen (an den Kacheln ausgerichtet), Fenster 4x4 in der Zellenmitte."""
    for cy in range((y0 // 8) * 8 + 8, y1 - 8, 8):
        for cx in range((x0 // 8) * 8, x1 - 8, 8):
            if cx < x0 + 1 or cx + 8 > x1 - 3:
                continue
            lit = (cx * 7 + cy * 13 + seed) % 5 in (0, 1)
            cv.rect(cx + 2, cy + 2, cx + 6, cy + 6, 'y' if lit else 'k')


def _block(cv, x0, x1, y0, y1, seed, wall='D', side='E'):
    cv.rect(x0, y0, x1, y1, wall)
    cv.rect(x1 - 3, y0, x1, y1, side)
    cv.rect(x0, y0, x1, y0 + 1, 'e')
    _windows(cv, x0, y0, x1, y1, seed, wall)


def empire():
    cv = Canvas(48, 112)
    _block(cv, 4, 44, 56, 112, 1)
    _block(cv, 10, 38, 30, 56, 2)
    _block(cv, 16, 32, 14, 30, 3)
    cv.rect(23, 0, 25, 14, 'w')
    cv.put(24, 0, 'r')
    return cv.rows()


def chrysler():
    cv = Canvas(40, 104)
    _block(cv, 4, 36, 46, 104, 4)
    for k in range(4):                                       # gestufte Silberkrone
        hw = 16 - 4 * k
        y1 = 46 - 8 * k
        cv.rect(20 - hw, y1 - 8, 20 + hw, y1, 'e')
        cv.rect(20 + hw - 2, y1 - 8, 20 + hw, y1, 'w')
        for x in range(20 - hw + 3, 20 + hw - 2, 5):
            cv.rect(x, y1 - 5, x + 2, y1 - 2, 'k')
    cv.rect(19, 4, 21, 14, 'w')
    return cv.rows()


def slab():
    cv = Canvas(56, 80)
    cv.rect(0, 12, 56, 80, 'R')
    cv.rect(53, 12, 56, 80, 'b')
    cv.rect(0, 12, 56, 14, 'b')
    for cy in range(16, 76, 8):
        for cx in range(4, 50, 8):
            lit = (cx * 5 + cy * 11) % 5 in (0, 2)
            cv.rect(cx + 1, cy + 2, cx + 5, cy + 6, 'y' if lit else 'k')
    cv.rect(22, 2, 36, 12, 'b')                              # Wassertank
    cv.rect(22, 2, 36, 4, 'D')
    for lx in (24, 33):
        cv.rect(lx, 12, lx + 1, 14, 'k')
    return cv.rows()


def _kong(arm_up):
    cv = Canvas(72, 104)
    fur = ('o', 'b', 'b', 'k')
    cv.blob([(46, 34, 15), (40, 12, 10), (36, 30, 10), (54, 42, 12), (46, 52, 11)], fur, (2, 12, 24))
    if arm_up:
        cv.line(34, 26, 24, 12, 'b', 6)
        cv.disc(22, 8, 4, 'o')
    else:
        cv.line(34, 28, 26, 50, 'b', 6)
        cv.disc(25, 53, 4, 'o')
    cv.poly([(33, 9), (46, 9), (44, 18), (35, 18)], 'o')   # Gesicht
    cv.rect(35, 10, 37, 12, 'w')
    cv.rect(41, 10, 43, 12, 'w')
    cv.put(36, 11, 'k')
    cv.put(42, 11, 'k')
    cv.rect(37, 14, 41, 15, 'k')
    cv.put(38, 16, 'k')
    cv.put(40, 16, 'k')
    cv.put(37, 15, 'w')
    cv.put(41, 15, 'w')
    # Gebäude, auf dem er sitzt (verdeckt die Beine)
    _block(cv, 24, 72, 54, 104, 6)
    return cv.rows()


def kong():
    return _kong(False)


def kong_b():
    return _kong(True)


def _godzilla(open_mouth):
    cv = Canvas(80, 112)
    cv.poly([(30, 40), (60, 36), (72, 70), (66, 104), (32, 108), (24, 78)], 'G')            # Rumpf
    cv.poly([(24, 38), (40, 34), (46, 52), (28, 58)], 'G')                                  # Hals
    cv.poly([(4, 24), (22, 14), (36, 26), (32, 46), (14, 42), (4, 34)], 'G')                # Kopf
    cv.poly([(60, 86), (80, 98), (80, 112), (58, 112)], 'G')                                # Schwanz
    cv.poly([(34, 98), (56, 98), (58, 112), (30, 112)], 'D')                                # Beine
    cv.line(27, 58, 17, 74, 'G', 4)                                                         # Arm
    cv.rect(14, 74, 20, 77, 'g')
    for x0, y0 in ((48, 38), (56, 44), (62, 54), (66, 66), (66, 78)):                      # Rückenplatten
        cv.poly([(x0, y0), (x0 + 8, y0 - 10), (x0 + 12, y0 + 2)], 'e')
        cv.put(x0 + 8, y0 - 10, 'w')
    for y in range(36, 106):                                                                # Licht von links
        for x in range(20, 76):
            if cv.g[y][x] == 'G' and (x < 20 or cv.g[y][x - 2] == '.'):
                cv.put(x, y, 'g')
    cv.rect(18, 20, 23, 24, 'y')                                                            # Auge
    cv.put(20, 22, 'k')
    if open_mouth:
        cv.poly([(4, 34), (30, 40), (28, 52), (6, 46)], 'G')                                # Unterkiefer
        cv.poly([(5, 34), (28, 38), (27, 46), (7, 42)], 'r')                                # Rachen
        cv.poly([(0, 30), (8, 36), (8, 44), (0, 46)], 'o')                                  # Feuer
        cv.rect(0, 33, 4, 43, 'y')
    else:
        cv.rect(5, 36, 28, 38, 'k')
        for x in range(8, 28, 4):
            cv.put(x, 35, 'w')
    return cv.rows()


def godzilla():
    return _godzilla(False)


def godzilla_b():
    return _godzilla(True)


def liberty():
    cv = Canvas(96, 112)
    for x in range(96):                                      # Insel
        t = (x - 48) / 48
        top = 96 + int(10 * t * t)
        for y in range(top, 112):
            cv.put(x, y, 'e' if y < 104 else 'E')
    cv.rect(26, 78, 70, 98, 'e')                             # Sockel
    cv.rect(62, 78, 70, 98, 'E')
    cv.rect(32, 66, 64, 78, 'e')
    cv.rect(56, 66, 64, 78, 'E')
    cv.poly([(38, 66), (58, 66), (62, 40), (50, 30), (40, 40)], 't')         # Gewand
    cv.poly([(50, 30), (62, 40), (58, 66), (52, 66)], 'g')
    cv.line(54, 34, 63, 12, 't', 5)                           # erhobener Arm
    cv.poly([(60, 4), (66, 4), (68, 10), (62, 12)], 'y')      # Fackel
    cv.poly([(62, 0), (65, 4), (60, 4)], 'o')
    cv.disc(48, 25, 6, 't')                                   # Kopf
    for ang in (-60, -30, 0, 30, 60):                         # Krone
        a = math.radians(ang - 90)
        cv.line(48, 22, 48 + 11 * math.cos(a), 22 + 11 * math.sin(a), 'g', 1)
    cv.rect(36, 44, 44, 58, 'g')                              # Tafel
    cv.rect(37, 45, 40, 57, 't')
    for x in range(0, 96, 6):
        cv.put(x, 111, 'w')
    return cv.rows()


def blimp():
    cv = Canvas(64, 32)
    cv.blob([(30, 14, 12), (16, 14, 10), (44, 14, 10)], ('e', 'e', 'E', 'D'), (3, 8, 14))
    cv.rect(6, 13, 54, 15, 'r')
    cv.poly([(52, 8), (62, 3), (62, 14), (52, 17)], 'E')
    cv.rect(24, 24, 38, 28, 'D')
    for x in (26, 36):
        cv.line(x, 24, x, 22, 'k', 1)
    return ['.' * 64] + cv.rows()[:31]


def plane(frame_b):
    cv = Canvas(22, 14)
    cv.disc(11, 8, 3.3, 'w')
    cv.rect(2, 6, 20, 10, 'w')
    cv.rect(2, 8, 20, 9, 'r')
    for x in (7, 10, 13):
        cv.put(x, 7, 'k')
    cv.poly([(17, 6), (21, 0), (21, 6)], 'r')
    cv.poly([(8, 9), (15, 9), (12, 13), (8, 13)], 'e')
    if frame_b:
        cv.rect(0, 7, 2, 8, 'k')
    else:
        cv.line(0, 4, 0, 11, 'k', 1)
    return cv.rows()


def _sprites():
    from pixelart import outlined
    return [("plane_a", outlined(plane(False))), ("plane_b", outlined(plane(True)))]


SPEC = {
    "id": "ny", "title": "New York", "bank": 7, "pal": NY_PAL,
    "bg": ny_bg, "ground": street, "far_cloud": far_cloud,
    "floors": [
        {"name": "empire", "rows": empire},
        {"name": "chrysler", "rows": chrysler},
        {"name": "slab", "rows": slab},
        {"name": "kong", "rows": kong, "anim": {"rows_b": kong_b}, "shot": (18, 168 - 104 + 6), "shot_kind": 2},
        {"name": "godzilla", "rows": godzilla, "anim": {"rows_b": godzilla_b}, "shot": (2, 168 - 112 + 38), "shot_kind": 1},
    ],
    "finish": {"name": "liberty", "rows": liberty},
    "ceil1": {"name": "blimp", "rows": blimp, "top_row": 2},
    "kind_bld": [1, 2, 3, 0, 1, 3, 2, 0], "kind_ceil": [0, 0, 0, 1, 0, 1, 0, 1],
    "setpieces": [(38, 4), (72, 5)],
    "sky": "n", "flash": 0x3F,
    "sprites": _sprites(),
    "phys": (1, 3, 24, 32), "wind": (14, 20, 26, 32), "level_cols": 433,
    "flyer": {"sprite": "plane_a", "w": 3, "h": 2, "hit": (4, 5, 22, 11), "fast": 20},
    "music": 5,
}
