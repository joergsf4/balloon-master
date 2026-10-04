"""Welt 4: Höhle. Stalagmiten vom Boden, Stalaktiten von der Decke (Flappy-Bird-Lücken), Fledermäuse, Lava im Vordergrund.
Ziel ist der Höhlenausgang mit Tageslicht."""
import math
import random

from canvas import Canvas

CAVE_PAL = "kEeSbBgGtAroywaD"          # Platz 0 = dunkle Höhlenluft


def cave_bg(y):
    return 'k' if y < 140 else 'B'


def band():
    return [cave_bg(104 + y) * 256 for y in range(64)]


def lava():
    """Vordergrund 32x24, zwei Kacheln wiederholt: Felskante, Gestein mit Adern, glühende Lava."""
    cv = Canvas(32, 24)
    rnd = random.Random(21)
    for y in range(24):
        for x in range(32):
            cv.put(x, y, 'E' if y < 8 else ('B' if y < 16 else 'r'))
    for x in range(32):
        cv.put(x, 0, 'e')
    for tx in range(2):
        for k in range(2):                                    # glühende Risse im Fels
            n = rnd.randint(2, 4)
            x = tx * 8 + rnd.randint(0, 8 - n)
            for i in range(n):
                cv.put(x + i, 3 + 2 * k, 'o')
        for k in range(2):
            n = rnd.randint(3, 5)
            x = tx * 8 + rnd.randint(0, 8 - n)
            for i in range(n):
                cv.put(x + i, 10 + 3 * k, 'r')
        for k in range(2):                                    # Lavawellen
            n = rnd.randint(3, 6)
            x = tx * 8 + rnd.randint(0, 8 - n)
            for i in range(n):
                cv.put(x + i, 18 + 3 * k, 'o' if k == 0 else 'y')
    for y in range(24):
        for x in range(16):
            cv.put(16 + x, y, cv.g[y][x])
    return cv.rows()


def _spikes_down(cv, spikes, top_slab):
    """Stalaktiten: (Mitte x, halbe Breite, Länge); oben sitzt eine Felsplatte."""
    for x in range(cv.w):
        for y in range(top_slab):
            cv.put(x, y, 'E' if y < top_slab - 2 else 'D')
    for cx, hw, ln in spikes:
        for y in range(top_slab - 2, top_slab + ln):
            t = (y - (top_slab - 2)) / (ln + 2)
            half = hw * (1 - t)
            for x in range(int(cx - half), int(cx + half) + 1):
                lit = x < cx - half * 0.15
                cv.put(x, y, 'e' if lit else 'E')
        for y in range(top_slab + 6, top_slab + ln - 2, 14):   # Schichtlinien
            half = hw * (1 - (y - (top_slab - 2)) / (ln + 2))
            for x in range(int(cx - half) + 1, int(cx + half)):
                if (x + y) % 3:
                    cv.put(x, y, 'S' if x < cx else 'D')
        cv.put(cx, top_slab + ln - 1, 'w')                    # Tropfen glänzt an der Spitze


def _spikes_up(cv, spikes):
    """Stalagmiten: (Mitte x, halbe Breite, Höhe) vom unteren Rand aus."""
    H = cv.h
    for cx, hw, h in spikes:
        for y in range(H - h, H):
            t = (H - y) / h
            half = hw * (1 - t) + 0.5
            for x in range(int(cx - half), int(cx + half) + 1):
                lit = x < cx - half * 0.15
                cv.put(x, y, 'e' if lit else 'E')
        for y in range(H - h + 10, H - 2, 14):
            half = hw * (1 - (H - y) / h)
            for x in range(int(cx - half) + 1, int(cx + half)):
                if (x + y) % 3:
                    cv.put(x, y, 'S' if x < cx else 'D')
    for x in range(cv.w):                                    # Geröll am Fuß
        for y in range(H - 3, H):
            if cv.g[y][x] == '.' and (x * 7 + y) % 5 != 0:
                cv.put(x, y, 'D' if x % 2 else 'E')


def vent():
    """Lavakrater: Felskegel mit glühendem Schlund, an den Flanken läuft Lava herab; schießt Lavabomben."""
    cv = Canvas(48, 40)
    cv.poly([(0, 40), (48, 40), (36, 18), (12, 18)], 'E')
    cv.poly([(0, 40), (10, 40), (15, 18), (12, 18)], 'e')              # Licht von links
    for y in range(22, 40, 9):                                          # Gesteinsschichten
        for x in range(8, 40):
            if cv.g[y][x] == 'E' and (x + y) % 3:
                cv.put(x, y, 'D')
    cv.poly([(21, 18), (26, 18), (22, 40), (14, 40)], 'r')            # Lavastrom links
    cv.poly([(28, 18), (32, 18), (40, 40), (33, 40)], 'r')            # Lavastrom rechts
    cv.line(22, 20, 17, 38, 'o', 1)
    cv.line(30, 20, 36, 38, 'o', 1)
    for x in range(11, 38):
        for y in range(11, 22):
            if ((x - 24) / 12.5) ** 2 + ((y - 17) / 4.5) ** 2 <= 1:
                cv.put(x, y, 'o' if y > 15 else 'y')
    cv.rect(19, 15, 29, 17, 'w')
    for x, y in ((12, 8), (36, 7), (18, 3), (30, 2)):                 # Funken über dem Schlund
        cv.put(x, y, 'y')
    return cv.rows()


def s2():
    cv = Canvas(64, 56)
    _spikes_up(cv, [(12, 8, 34), (30, 12, 56), (50, 10, 44)])
    return cv.rows()


def s3():
    cv = Canvas(56, 88)
    _spikes_up(cv, [(16, 11, 88), (40, 10, 66)])
    return cv.rows()


def _ceil_shift(rows):
    """Die erste Pixelzeile eines hängenden Hindernisses bleibt leer: Der Zeileninterrupt schaltet bei Zeile 16 etwas
    zu spät auf das schnellere Band um, die erste Zeile würde sonst mit dem falschen Scrollwert gezeichnet."""
    return ['.' * len(rows[0])] + rows[:-1]


def c1():
    cv = Canvas(48, 48)
    _spikes_down(cv, [(10, 8, 30), (24, 10, 36), (38, 8, 26)], 8)
    return _ceil_shift(cv.rows())


def c2():
    cv = Canvas(56, 72)
    _spikes_down(cv, [(10, 8, 44), (27, 11, 60), (45, 9, 38)], 8)
    return _ceil_shift(cv.rows())


def far_cloud():
    cv = Canvas(48, 16)
    _spikes_down(cv, [(8, 6, 8), (22, 8, 13), (36, 7, 9), (45, 4, 6)], 3)
    return cv.rows()


def exit_cave():
    """Höhlenausgang: Felsmasse mit hellem Torbogen, dahinter Tageslicht (128x96)."""
    cv = Canvas(128, 96)
    rnd = random.Random(8)
    for x in range(128):
        t = (x - 64) / 64
        top = 8 + int(40 * t * t * t * t) + int(3 * math.sin(x / 5.0))
        for y in range(max(0, top), 96):
            cv.put(x, y, 'S' if (x * 7 + y * 3) % 37 == 0 else 'E')
    for x in range(128):                                     # Beleuchtung links oben
        t = (x - 64) / 64
        top = 8 + int(40 * t * t * t * t) + int(3 * math.sin(x / 5.0))
        for y in range(max(0, top), top + 3):
            cv.put(x, y, 'e')
    for y in range(96):                                      # rechte Seite im Schatten
        for x in range(108, 128):
            if cv.g[y][x] != '.' and (x + y) % 2 == 0:
                cv.put(x, y, 'D')
    # Torbogen mit Tageslicht
    for y in range(34, 96):
        for x in range(36, 92):
            dx = (x - 64) / 28
            arch_top = 34 + 16 * (dx * dx)
            if y >= arch_top:
                cv.put(x, y, 'a' if y < 74 else 'g')
    cv.disc(70, 52, 7, 'y')                                  # Sonne
    cv.disc(70, 52, 4, 'w')
    for x in range(36, 92):                                  # Wolke im Licht
        if 44 < (x % 27) + 40 < 70:
            cv.put(x, 46, 'w')
    for x in range(40, 88, 6):                               # Gras
        cv.put(x, 73, 'G')
        cv.put(x + 1, 72, 'G')
    return cv.rows()


def bat(up):
    cv = Canvas(14, 14)
    cv.disc(7, 8, 2.5, 'E')                                  # Körper
    cv.put(5, 5, 'E')
    cv.put(9, 5, 'E')                                        # Ohren
    cv.put(6, 7, 'r')
    cv.put(8, 7, 'r')                                        # rote Augen
    if up:
        cv.poly([(5, 8), (0, 1), (2, 5), (3, 3), (4, 7)], 'E')
        cv.poly([(9, 8), (14, 1), (12, 5), (11, 3), (10, 7)], 'E')
    else:
        cv.poly([(5, 8), (0, 12), (2, 9), (3, 11), (4, 9)], 'E')
        cv.poly([(9, 8), (14, 12), (12, 9), (11, 11), (10, 9)], 'E')
    return cv.rows()


def _sprites():
    from pixelart import outlined
    return [("bat_a", outlined(bat(True))), ("bat_b", outlined(bat(False)))]


SPEC = {
    "id": "cave", "title": "Höhle", "bank": 5, "pal": CAVE_PAL,
    "bg": cave_bg, "ground": lava, "far_cloud": far_cloud,
    "floors": [{"name": "vent", "rows": vent, "shot": (24, 168 - 40 + 12), "shot_kind": 1}, {"name": "s2", "rows": s2}, {"name": "s3", "rows": s3}],
    "finish": {"name": "exit", "rows": exit_cave},
    "ceil1": {"name": "c1", "rows": c1, "top_row": 2},
    "ceil2": {"name": "c2", "rows": c2, "top_row": 2},
    "kind_bld": [2, 0, 3, 1, 0, 2, 1, 3], "kind_ceil": [1, 2, 1, 1, 0, 2, 0, 2],
    "sky": "k", "flash": 0x3F,
    "sprites": _sprites(),
    "phys": (1, 3, 24, 32), "wind": (8, 10, 12, 16), "level_cols": 333,
    "flyer": {"sprite": "bat_a", "w": 2, "h": 2, "hit": (3, 5, 13, 11), "fast": 12},
    "music": 3,
}
