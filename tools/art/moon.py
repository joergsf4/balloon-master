"""Welt 5: Mond. Schwarzer Himmel mit Sternen, Krater, Felsen, Mondlandefähre; UFOs mit Zap-Strahl hängen im Weg.
Geringe Schwerkraft. Ziel ist die Mondbasis mit Flagge."""
import math
import random

from canvas import Canvas

MOON_PAL = "kEeSDwYAgnrayotb"          # Platz 0 = schwarzer Weltraum


def moon_bg(y):
    if y < 132:
        return 'k'
    if y < 152:
        return 'D'
    return 'E'


def band():
    return [moon_bg(104 + y) * 256 for y in range(64)]


def regolith():
    """Vordergrund 32x24, zwei Kacheln wiederholt: Mondstaub mit Kratern."""
    cv = Canvas(32, 24)
    rnd = random.Random(31)
    for y in range(24):
        for x in range(32):
            cv.put(x, y, 'e' if y < 8 else ('E' if y < 16 else 'D'))
    for x in range(32):
        cv.put(x, 0, 'w')
    for tx in range(2):
        for row, (dark) in enumerate(('E', 'E', 'D')):
            for k in range(2):
                n = rnd.randint(2, 4)
                x = tx * 8 + rnd.randint(0, 8 - n)
                for i in range(n):
                    cv.put(x + i, row * 8 + 3 + 3 * k, dark)
    for y in range(24):
        for x in range(16):
            cv.put(16 + x, y, cv.g[y][x])
    return cv.rows()


def far_cloud():
    """Sterne, 48x16."""
    cv = Canvas(48, 16)
    rnd = random.Random(5)
    for _ in range(11):
        x, y = rnd.randint(1, 46), rnd.randint(1, 14)
        cv.put(x, y, 'w' if rnd.random() < 0.7 else 'y')
    for x, y in ((12, 8), (36, 5)):
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            cv.put(x + dx, y + dy, 'w')
    return cv.rows()


def _edge(rows):
    """Obere, linke und rechte Randpixel schwarz umranden, damit der Fels sich vom Boden dahinter abhebt."""
    h, w = len(rows), len(rows[0])
    out = [list(r) for r in rows]
    for y in range(h):
        for x in range(w):
            if rows[y][x] == '.':
                continue
            for dx, dy in ((-1, 0), (1, 0), (0, -1)):
                nx, ny = x + dx, y + dy
                if nx < 0 or nx >= w or ny < 0 or rows[ny][nx] == '.':
                    out[y][x] = 'k'
                    break
    return [''.join(r) for r in out]


def crater():
    cv = Canvas(72, 32)
    for x in range(72):
        t = (x - 36) / 36
        top = 30 - int(26 * (1 - t * t) ** 0.7)
        for y in range(max(0, top), 32):
            cv.put(x, y, 'e' if x < 36 else 'E')
    for x in range(14, 58):                                   # Kraterschüssel
        t = (x - 36) / 22
        dip = int(7 * (1 - t * t) ** 0.8)
        for y in range(10, 10 + dip):
            cv.put(x, y, 'E' if x < 36 else 'D')
    for x in range(72):
        cv.put(x, 31, 'E')
    return _edge(cv.rows())


def crater2():
    """Großer Krater: breiter Wall links und rechts, dazwischen eine tiefe Schüssel."""
    cv = Canvas(96, 48)
    for x in range(96):
        u = (x - 47.5) / 48.0
        h = (12 + 32 * u * u) * math.sqrt(max(0.0, 1 - u ** 8))
        top = 48 - int(h)
        for y in range(top, 48):
            if abs(u) < 0.62 and y < top + 5:
                c = 'D'                                          # Schüssel liegt im Schatten
            elif u < 0:
                c = 'w' if y == top else 'e'
            else:
                c = 'E'
            cv.put(x, y, c)
    for x in range(22, 76, 12):                                  # Brocken am Grund
        cv.rect(x, 44, x + 4, 46, 'e')
    return _edge(cv.rows())


def rocks():
    cv = Canvas(80, 64)
    cv.poly([(2, 64), (10, 34), (28, 20), (44, 30), (50, 64)], 'e')
    cv.poly([(28, 20), (44, 30), (50, 64), (30, 64)], 'E')
    cv.poly([(40, 64), (48, 40), (62, 8), (74, 28), (78, 64)], 'e')
    cv.poly([(62, 8), (74, 28), (78, 64), (64, 64)], 'E')
    cv.poly([(26, 64), (30, 50), (40, 46), (46, 64)], 'D')
    cv.poly([(10, 34), (28, 20), (24, 34)], 'w')
    cv.poly([(48, 40), (62, 8), (58, 30)], 'w')
    return cv.rows()


def lander():
    cv = Canvas(64, 88)
    for lx0, lx1 in ((12, 4), (52, 60), (22, 14), (42, 50)):
        cv.line(lx0, 64, lx1, 84, 'E', 2)
    for fx in (0, 10, 56, 46):
        cv.rect(fx, 84, fx + 8, 87, 'e')
    cv.rect(16, 38, 48, 64, 'y')                              # Abstiegsstufe mit goldener Folie
    for y in range(40, 64, 4):
        for x in range(16 + (y // 4 % 2) * 2, 48, 4):
            cv.put(x, y, 'o')
    cv.rect(44, 38, 48, 64, 'o')
    cv.rect(16, 62, 48, 64, 'o')
    cv.rect(22, 18, 42, 38, 'e')                              # Aufstiegsstufe
    cv.rect(38, 18, 42, 38, 'E')
    cv.rect(26, 24, 34, 30, 'k')
    cv.line(32, 18, 32, 4, 'w', 1)                            # Antenne mit Schüssel
    cv.rect(28, 3, 37, 5, 'w')
    return cv.rows()


def base():
    cv = Canvas(128, 96)
    for x in range(128):                                      # Mondstaub
        t = (x - 64) / 64
        top = 84 + int(4 * t * t)
        for y in range(top, 96):
            cv.put(x, y, 'e' if y < 90 else 'E')
    for y in range(40, 84):                                   # Kuppel
        for x in range(8, 78):
            dx, dy = (x - 43) / 35, (y - 84) / 44
            if dx * dx + dy * dy <= 1:
                cv.put(x, y, 'w' if (x - 43) < -6 and dy < -0.3 else ('e' if dx < 0.2 else 'E'))
    for y in range(52, 84):                                   # Fenster
        for x in range(26, 62):
            if (x - 43) ** 2 / 100 + (y - 84) ** 2 / 560 <= 1 and y < 80 and (x // 7) % 2 == 0:
                cv.put(x, y, 'a')
    cv.rect(78, 66, 114, 84, 'e')                             # Modul
    cv.rect(110, 66, 114, 84, 'E')
    cv.rect(84, 72, 92, 78, 'k')
    cv.rect(98, 72, 106, 78, 'k')
    cv.line(96, 66, 96, 38, 'w', 2)                           # Antennenmast
    cv.disc(97, 36, 3, 'r')
    for sx in (100, 8):                                       # Sonnenkollektoren
        pass
    cv.rect(84, 48, 120, 60, 'A')
    for gx in range(84, 120, 6):
        cv.rect(gx, 48, gx + 1, 60, 'k')
    cv.rect(84, 54, 120, 55, 'k')
    cv.rect(100, 60, 102, 66, 'w')
    cv.rect(4, 28, 6, 84, 'w')                                # Flaggenmast
    for y in range(28, 44):
        for x in range(6, 28):
            cv.put(x, y, 'r' if (y // 3) % 2 == 0 else 'w')
    cv.rect(6, 28, 15, 37, 'A')
    for sx in range(7, 15, 3):
        for sy in range(29, 37, 3):
            cv.put(sx, sy, 'w')
    return cv.rows()


def ufo(w, h, bolt_x):
    cv = Canvas(w, h)
    cx = w // 2
    cv.disc(cx, 14, 9, 'a')                                   # Kuppel
    for y in range(0, 10):
        for x in range(cx - 10, cx + 11):
            if (x - cx) ** 2 + (y - 14) ** 2 <= 81 and y < 12:
                pass
    for x in range(cx - 4, cx):
        cv.put(x, 8, 'w')
    cv.put(cx - 5, 10, 'w')
    cv.poly([(2, 18), (cx - 10, 12), (cx + 10, 12), (w - 2, 18), (w - 6, 24), (6, 24)], 'e')
    cv.poly([(2, 18), (w - 2, 18), (w - 6, 24), (6, 24)], 'E')
    for lx in range(8, w - 6, 8):                             # Lichter
        cv.rect(lx, 19, lx + 3, 21, 'y' if (lx // 8) % 2 else 'r')
    cv.poly([(cx - 8, 24), (cx + 8, 24), (cx + 5, 28), (cx - 5, 28)], 'E')
    return cv.rows()


def u1():
    return ['.' * 56] + ufo(56, 32, 20)[:31]


def u2():
    cv_rows = ufo(64, 40, 24)
    return ['.' * 64] + cv_rows[:39]


SPEC = {
    "id": "moon", "title": "Mond", "bank": 6, "pal": MOON_PAL,
    "bg": moon_bg, "ground": regolith, "far_cloud": far_cloud,
    "floors": [{"name": "crater", "rows": crater}, {"name": "rocks", "rows": rocks}, {"name": "lander", "rows": lander},
               {"name": "crater2", "rows": crater2}],
    "finish": {"name": "base", "rows": base},
    "ceil1": {"name": "u1", "rows": u1, "top_row": 2, "bolt": (20, 46), "shot": (28, 46)},
    "ceil2": {"name": "u2", "rows": u2, "top_row": 2, "bolt": (24, 54), "shot": (32, 54)},
    "kind_bld": [1, 4, 2, 3, 0, 4, 2, 3], "kind_ceil": [1, 2, 2, 0, 1, 2, 1, 2],
    "sky": "k", "flash": 0x3F,
    "phys": (1, 2, 12, 20), "wind": (6, 8, 10, 12), "level_cols": 200,
    "flyer": None,
    "music": 4,
}
