"""Alle Grafiken des Spiels als ASCII bzw. kleine Formfunktionen. '.' = durchsichtig (Sprites) bzw. Himmel (Hintergrund).

Ansicht: nah dran. Ballon 24x32, Bäume 32x48, Häuser 48x48, Big Ben 32x96 (Bildschirm: 256x192).

Stilregeln:
- Sprites: dunkler 1-px-Umriss (automatisch, 'k'), Maße inkl. Umriss ein Vielfaches von 8.
- Hintergrund: kein Umriss, Form über helle/dunkle Töne derselben Farbe (Licht von links oben).
- Farben nur aus palette.py; Großbuchstabe = Schatten zur Kleinbuchstaben-Farbe.
"""
import math

from pixelart import ctr, outlined


def put(row, text):
    """Text mittig in eine Zeile setzen (überschreibt)."""
    s = (len(row) - len(text)) // 2
    return row[:s] + text + row[s + len(text):]


def ell_widths(w, h):
    """Breiten (gerade) einer Ellipse w x h, zeilenweise."""
    out = []
    for y in range(h):
        t = (y + 0.5 - h / 2) / (h / 2)
        out.append(max(2, 2 * round(w / 2 * math.sqrt(max(0.0, 1 - t * t)) / 2 * 1.0 * 1)))
    return out


# ---------------------------------------------------------------- Sprites (mit Umriss)

_ENV_W = [8, 12, 16, 18, 20, 22, 22, 22, 22, 22, 22, 20, 20, 18, 16, 14, 12, 10]


def _env_row(w):
    cells = []
    for x in range(w):
        col = (22 - w) // 2 + x
        if abs(col - 10.5) < 2.5:
            cells.append('y')
        elif x >= w - 3:
            cells.append('R')
        else:
            cells.append('r')
    return ''.join(cells).center(22, '.')


_ENVELOPE = [_env_row(w) for w in _ENV_W]
_ROPE = '.' * 6 + 'e' + '.' * 8 + 'e' + '.' * 6
_ROPES = [_ROPE] * 5
_FLAME = ["yy", "yy", "oyyo", "oooo", "oo"]
_BURNER = [put(_ROPE, f) for f in _FLAME]
_BASKET = [
    "." * 5 + "y" * 12 + "." * 5,
    "." * 5 + "bBbBbBbBbBbB" + "." * 5,
    "." * 5 + "BbBbBbBbBbBb" + "." * 5,
    "." * 5 + "bBbBbBbBbBbB" + "." * 5,
    "." * 5 + "BbBbBbBbBbBb" + "." * 5,
    "." * 5 + "bBbBbBbBbBbB" + "." * 5,
    "." * 6 + "B" * 10 + "." * 6,
]

BALLOON_IDLE = outlined(_ENVELOPE + _ROPES + _BASKET)   # 24x32
BALLOON_BURN = outlined(_ENVELOPE + _BURNER + _BASKET)
assert len(BALLOON_IDLE) == 32 and len(BALLOON_IDLE[0]) == 24

_BIRD_BODY_UP = [
    "ee..........ee",
    "eee........eee",
    ".eee......eee.",
    "..eee....eee..",
    "...eewwwwee...",
    "....wwwwwwkw..",
    "....wwwwwwwwoo",
    ".....wwwwwww..",
    "......wwww....",
]
_BIRD_BODY_DOWN = [
    "....wwwwwwkw..",
    "..eewwwwwwwwoo",
    ".eeewwwwwwww..",
    "eee.wwwwwww...",
    "ee...wwww.....",
    "e.............",
]


def _bird(rows):
    """Möwe, die nach links fliegt (Schnabel links): Zeilen sind rechtsblickend gezeichnet und werden gespiegelt."""
    rows = [r[::-1] for r in rows]
    pad = 14 - len(rows)
    return outlined(["." * 14] * 2 + rows + ["." * 14] * (pad - 2))


BIRD_UP = _bird(_BIRD_BODY_UP)      # 16x16
BIRD_DOWN = _bird(_BIRD_BODY_DOWN)

# ---- Treibstoff: Fässer mit F, Seil mit Haken, Tankanzeige

def _barrel():
    """Kleines rotes Fass (10x11) mit Tragering oben, weißem F und grauen Reifen.
    Sprite 16x16, Fass unten bündig (steht auf dem Boden), mittig, Ring zum Einhängen des Hakens."""
    widths = [8, 10, 10, 10, 10, 10, 10, 10, 10, 10, 8]
    body = []
    for y, w in enumerate(widths):
        row = ''.join('R' if x >= w - 2 else 'r' for x in range(w)).center(10, '.')
        if y in (0, 10):
            row = ''.join('E' if c != '.' else '.' for c in row)
        body.append(list(row))
    f = ["11111", "10000", "10000", "1111", "10000", "10000", "10000"]
    for fy, fr in enumerate(f):
        for fx, c in enumerate(fr):
            if c == '1':
                body[2 + fy][2 + fx] = 'w'
    rows = ctr(["eeee", "e..e"], 10) + [''.join(r) for r in body]
    rows = outlined(rows)                                   # 12x15
    rows = [r.center(16, '.') for r in rows]
    return ['.' * 16] + rows                                # 16x16


BARREL = _barrel()

ROPE = ["...eE..."] * 8

_HOOK = [
    ".eeee.",
    ".e..e.",
    ".eeee.",
    "..ee..",
    "..ee..",
    "..ee..",
    "..ee..",
    "..ee..",
    "..eE..",
    "..eE..",
    "e.eE..",
    "eeeE..",
]
HOOK = outlined(_HOOK) + ['.' * 8] * 2         # 8x16, Seil sitzt auf den Spalten 3-4


def _fuel_bar(fill):
    """9 Tiles nebeneinander: Balkenstück mit 0..8 gefüllten Pixeln (oben/unten Rahmen k, leer E, gefüllt = fill)."""
    rows = [''] * 8
    for px in range(9):
        for y in range(8):
            if y in (0, 7):
                rows[y] += '.' * 8
            elif y in (1, 6):
                rows[y] += 'k' * 8
            else:
                rows[y] += fill * px + 'E' * (8 - px)
    return rows


FUEL_BAR = _fuel_bar('y')           # 72x8
FUEL_BAR_RED = _fuel_bar('r')
FUEL_CAP = ['.' * 8, 'k' + '.' * 7] + ['k' + '.' * 7] * 4 + ['k' + '.' * 7, '.' * 8]    # rechter Abschluss

def _bolt(flip):
    """Zickzack-Blitz 16x24: gelber Rand, weißer Kern, ohne Umriss (leuchtet)."""
    pts = [(10, 0), (6, 8), (11, 10), (5, 18), (9, 20), (7, 23)]
    g = [['.'] * 16 for _ in range(24)]

    def line(a, b, ch, wid):
        (x0, y0), (x1, y1) = a, b
        n = max(abs(x1 - x0), abs(y1 - y0))
        for i in range(n + 1):
            x = round(x0 + (x1 - x0) * i / n)
            y = round(y0 + (y1 - y0) * i / n)
            for dx in range(-wid, wid + 1):
                if 0 <= x + dx < 16:
                    if ch == 'w' or g[y][x + dx] == '.':
                        g[y][x + dx] = ch
    for a, b in zip(pts, pts[1:]):
        line(a, b, 'y', 1)
    for a, b in zip(pts, pts[1:]):
        line(a, b, 'w', 0)
    rows = [''.join(r) for r in g]
    return [r[::-1] for r in rows] if flip else rows


BOLT_A = _bolt(False)
BOLT_B = _bolt(True)

def _spark(size, c1, c2):
    """Feuerwerksfunken 8x8: Kreuz mit hellem Kern (size 3 oder 1)."""
    g = [['.'] * 8 for _ in range(8)]
    for d in range(-size, size + 1):
        g[3][3 + d] = c1
        g[4][3 + d] = c1
        g[3 + d][3] = c1
        g[3 + d][4] = c1
    for y in (3, 4):
        for x in (3, 4):
            g[y][x] = c2
    return [''.join(r) for r in g]


SPRITES = [
    ("balloon_idle", BALLOON_IDLE),
    ("balloon_burn", BALLOON_BURN),
    ("bird_up", BIRD_UP),
    ("bird_down", BIRD_DOWN),
    ("barrel", BARREL),
    ("rope", ROPE),
    ("rain", ["......a.", ".....a..", ".....a..", "....a...", "....a...", "...a....", "...a....", "........"]),
    ("hook", HOOK),
    ("fuel_bar", FUEL_BAR),
    ("fuel_bar_red", FUEL_BAR_RED),
    ("fuel_cap", FUEL_CAP),
    ("bolt_a", BOLT_A),
    ("bolt_b", BOLT_B),
    ("cannonball", outlined([".EEEE.", "EweEEE", "EeEEEE", "EEEEEE", "EEEEEE", ".EEEE."])),
    ("fireball_a", ["........", "..oo....", ".oyyoor.", "oyywyyor", "oyyyyyo.", ".oyyoo.r", "..oo....", "........"]),
    ("fireball_b", ["........", "...oo...", ".ooyyo..", "oyywyyo.", "oyyyyyor", ".oyyyo..", "..ooor..", "........"]),
    ("boulder", outlined([".bbbb.", "bbBbbb", "bbbbbB", "bBbbbb", "bbbbBB", ".bBBb."])),
    ("cannon_puff", ["...ee...", "..eewe..", ".eewwee.", ".ewwwwe.", ".eewwee.", "..eeee..", "........", "........"]),
    ("spark_y_big", _spark(3, 'y', 'w')),
    ("spark_y_small", _spark(1, 'y', 'w')),
    ("spark_r_big", _spark(3, 'r', 'y')),
    ("spark_r_small", _spark(1, 'r', 'y')),
    ("spark_w_big", _spark(3, 'w', 'e')),
    ("spark_w_small", _spark(1, 'w', 'e')),
    ("panel", ["kkkkkkkk"] * 8),
    ("life", ["..kkkk..", ".krryrk.", "krryyrrk", "krryyrrk", ".krryrk.", "..k..k..", "..kbbk..", "...kk..."]),
]

# ---------------------------------------------------------------- Hintergrund (ohne Umriss)


def _tree():
    w, h = 32, 32
    widths = [4, 10, 14, 18, 20, 22, 24, 26, 28, 28, 30, 30, 32, 32, 32, 32,
              32, 32, 32, 32, 30, 30, 30, 28, 28, 26, 24, 22, 20, 16, 12, 8]
    rows = []
    for y, rw in enumerate(widths):
        x0 = (w - rw) // 2
        cells = []
        for x in range(rw):
            gx, gy = x0 + x, y
            d = ((gx - 13) * 0.5 + (gy - 12) * 0.7) / 16
            if d > 0.42 or (d > 0.34 and (gx + gy) % 2 == 0):
                cells.append('G')
            elif (gx * 7 + gy * 13) % 29 == 0:
                cells.append('G')
            else:
                cells.append('g')
        rows.append(''.join(cells).center(w, '.'))
    trunk = ["bbbbbBBB"] * 14 + ["bbbbbbBBBB", "bbbbbbbBBBBB"]
    return rows + ctr(trunk, w)


TREE = _tree()      # 32x48


def _brick(x, y):
    seam = (y % 4 == 3) or ((x + (4 if (y // 4) % 2 else 0)) % 8 == 7)
    return 'R' if seam else 'r'


def _window(rows, x0, y0):
    for yy in range(10):
        for xx in range(8):
            edge = yy in (0, 9) or xx in (0, 7)
            mull = xx in (3, 4) or yy == 4
            rows[y0 + yy][x0 + xx] = 'S' if (edge or mull) else 'y'


def _house():
    roof = []
    for i in range(14):
        rw = 2 * (6 + round(i * 18 / 13))
        ch = 'E' if i % 4 == 3 else 'n'
        roof.append(ch * rw)
    roof = ctr(roof, 48)
    wall = [[_brick(x, y) for x in range(44)] for y in range(34)]
    for fx in (5, 18, 31):
        _window(wall, fx, 3)
    _window(wall, 5, 17)
    _window(wall, 31, 17)
    for yy in range(17, 32):                    # Tür
        for xx in range(16, 28):
            wall[yy][xx] = 'B' if (yy == 17 or xx in (16, 27)) else 'b'
    wall[25][24] = wall[25][25] = 'y'
    for yy in (32, 33):
        wall[yy] = ['S'] * 44
    return roof + [''.join(r).center(48, '.') for r in wall]


HOUSE = _house()    # 48x48


def _bigben():
    w = 32
    spire = []
    for i in range(28):
        rw = 2 * (1 + (i * 11) // 27)
        cells = ['y' if i < 4 else 'n'] * rw
        if i >= 4:
            cells[-2:] = ['k', 'k']
        spire.append(''.join(cells))
    spire = ctr(spire, w)
    belfry = []
    for y in range(8):
        r = []
        for x in range(24):
            arch = y >= 1 and (x % 8) in (2, 3, 4, 5) and not (y == 1 and (x % 8) in (2, 5))
            r.append('k' if arch else ('S' if x >= 21 else 'Y'))
        belfry.append(''.join(r))
    clock = []
    for y in range(24):
        r = []
        for x in range(24):
            dx, dy = x - 11.5, y - 11.5
            rad = math.hypot(dx, dy)
            c = 'S' if x >= 21 else 'Y'
            if rad <= 10.5:
                c = 'y' if rad > 9 else 'w'
                if rad <= 9:
                    if (11 <= x <= 12 and 3 <= y <= 11) or (11 <= y <= 12 and 11 <= x <= 17):
                        c = 'k'
                    for tx, ty in ((11, 2), (12, 2), (21, 11), (21, 12), (11, 21), (12, 21), (2, 11), (2, 12)):
                        pass
                    if (x in (11, 12) and y in (2, 3, 20, 21)) or (y in (11, 12) and x in (2, 3, 20, 21)):
                        c = 'k'
            r.append(c)
        clock.append(''.join(r))
    shaft = []
    for y in range(36):
        r = []
        for x in range(24):
            c = 'S' if x >= 21 else 'Y'
            if y % 12 == 0:
                c = 'S'
            elif y % 12 in (3, 4, 5, 6, 7, 8) and x in (6, 7, 15, 16) and y < 34:
                c = 'k'
            r.append(c)
        shaft.append(''.join(r))
    body = belfry + clock + shaft
    return spire + [r.center(w, '.') for r in body]


BIG_BEN = _bigben()  # 32x96
assert len(BIG_BEN) == 96, len(BIG_BEN)


def _tower_bridge():
    """Tower Bridge als Ziel, die man überfliegt: zwei Türme (je 32 px), blauer Laufsteg dazwischen (128x96)."""
    W, H = 128, 96
    g = [['.'] * W for _ in range(H)]

    def put(x, y, c):
        if 0 <= x < W and 0 <= y < H:
            g[y][x] = c

    def tower(x0):
        for i in range(18):                                   # spitzes Dach
            rw = 2 * (1 + (i * 11) // 17)
            st = x0 + 16 - rw // 2
            for x in range(rw):
                put(st + x, i, 'y' if i < 3 else ('k' if x >= rw - 2 else 'n'))
        for y in range(12, H):                                 # Eckpfeiler mit kleinem Dach
            for px in (x0, x0 + 28):
                for x in range(4):
                    put(px + x, y, 'S' if x == 3 else 'Y')
        for px in (x0, x0 + 28):
            for y in range(8, 12):
                for x in range(1, 3):
                    put(px + x, y, 'n')
        for y in range(18, H):                                 # Mauerwerk
            for x in range(4, 28):
                put(x0 + x, y, 'S' if x >= 25 else 'Y')
        for by in (30, 54):                                    # Steinbänder
            for x in range(4, 28):
                put(x0 + x, by, 'S')
                put(x0 + x, by + 1, 'S')
        for wy in (36, 60):                                    # Bogenfenster
            for fx in (x0 + 8, x0 + 18):
                for yy in range(10):
                    w = 6 if yy >= 3 else (2, 4, 6)[yy]
                    for xx in range((6 - w) // 2, (6 - w) // 2 + w):
                        put(fx + xx, wy + yy, 'y' if (fx + wy) % 3 == 0 else 'k')
        for y in range(H - 6, H):
            for x in range(4, 28):
                put(x0 + x, y, 'S')

    tower(0)
    tower(96)
    for x in range(32, 96):                                    # blauer Laufsteg
        for y in range(24, 36):
            put(x, y, 'n' if y in (24, 25, 34, 35) else 'k')
    for x in range(34, 94, 8):
        for y in range(28, 32):
            for xx in range(4):
                put(x + xx, y, 'y')
    for x in range(32, 96, 16):                                # Streben
        for y in range(24, 36):
            put(x, y, 'n')
    for x in range(32, 96):                                    # Fahrbahn
        put(x, 80, 'w')
        put(x, 81, 'e')
        for y in range(82, 96):
            put(x, y, 'E' if x % 16 == 0 else 'S')
    return [''.join(r) for r in g]


TOWER_BRIDGE = _tower_bridge()          # 128x96, wird überflogen


def _cloud():
    """Flache ferne Wolke für das langsame Parallax-Band (48x16)."""
    circles = [(10, 10, 6), (21, 7, 8), (33, 8, 7), (41, 11, 5), (24, 11, 6)]
    rows = []
    for y in range(16):
        r = []
        for x in range(48):
            inside = y <= 12 and any((x - cx) ** 2 + (y - cy) ** 2 <= rr * rr for cx, cy, rr in circles)
            # grau statt weiß: die weißen Punkte-/Tankanzeigen (Sprites) liegen oft davor und müssen lesbar bleiben
            r.append(('E' if y >= 10 or x >= 44 else ('q' if y < 4 else 'e')) if inside else '.')
        rows.append(''.join(r))
    return rows


CLOUD = _cloud()    # 48x16

# ---- Rampage-artige Stadt: hohe, flache Gebäude mit Fensterraster, dunkle Skyline dahinter

def _lit(seed):
    return (seed * 7 + 3) % 5 in (0, 2)     # Pseudozufall, deterministisch: etwa 40 % beleuchtet


def _grey_tower(w, h, antenna=True):
    """Graues Hochhaus; Fenster in 16x16-Zellen (8x12 Fenster), Dach mit Antenne."""
    top = 8
    rows = [['.'] * w for _ in range(h + top)]
    for y in range(top, h + top):
        for x in range(w):
            rows[y][x] = 'E' if x >= w - 3 else 'e'
    for x in range(w):
        rows[top][x] = rows[top + 1][x] = 'E'          # Dachkante
    if antenna:
        for y in range(0, top):
            rows[y][w - 10] = rows[y][w - 9] = 'E'
        rows[0][w - 10] = rows[0][w - 9] = 'r'
    cols = (w - 8) // 16
    x0 = (w - 8 - 16 * (cols - 1)) // 2
    k = 0
    for fy in range(top + 6, h + top - 30, 16):   # unterstes Fenster endet vor der Tür
        for c in range(cols):
            lit = _lit(k)
            k += 1
            for yy in range(12):
                for xx in range(8):
                    edge = yy in (0, 11) or xx in (0, 7)
                    glass = 'y' if lit else 'n'
                    rows[fy + yy][x0 + 16 * c + xx] = 'E' if edge else (('E' if xx in (3, 4) else glass) if lit else glass)
    door_x = (w - 8) // 2
    for xx in range(door_x - 2, door_x + 10):                 # Sturz über der Tür
        rows[h + top - 20][xx] = rows[h + top - 19][xx] = 'E'
    for yy in range(h + top - 18, h + top - 2):
        for xx in range(8):
            rows[yy][door_x + xx] = 'B' if (yy == h + top - 18 or xx in (0, 7)) else 'b'
    for x in range(w):
        rows[h + top - 1][x] = rows[h + top - 2][x] = 'E'
    return [''.join(r) for r in rows]


def _arch_mask():
    widths = [4, 6, 8, 8] + [8] * 8
    return [[(8 - w) // 2 <= x < (8 - w) // 2 + w for x in range(8)] for w in widths]


def _arch_building(w=56, h=64):
    rows = [['S' if x >= w - 3 else 'Y' for x in range(w)] for _ in range(h)]
    for x in range(w):
        rows[0][x] = rows[1][x] = 'S'
        rows[2][x] = 'y'
    mask = _arch_mask()
    k = 100

    def inside(my, mx):
        return 0 <= my < 12 and 0 <= mx < 8 and mask[my][mx]

    for ci, fx in enumerate((8, 24, 40)):
        for ri, fy in enumerate((10, 26, 42)):
            if ri == 2 and ci == 1:
                continue
            lit = _lit(k)
            k += 1
            for yy in range(12):
                for xx in range(8):
                    if not mask[yy][xx]:
                        continue
                    glass = all(inside(yy + dy, xx + dx) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                    rows[fy + yy][fx + xx] = ('y' if lit else 'k') if glass else 'S'
    for yy in range(46, h - 2):
        for xx in range(24, 32):
            rows[yy][xx] = 'B' if (yy == 46 or xx in (24, 31)) else 'b'
    for x in range(w):
        rows[h - 1][x] = rows[h - 2][x] = 'S'
    return [''.join(r) for r in rows]


def _brick_tower(w=40, h=96):
    rows = [[_brick(x, y) for x in range(w)] for y in range(h)]
    for x in range(w):
        rows[0][x] = rows[1][x] = 'S'
    for fy in (8, 24, 40, 56):
        for fx in (6, 26):
            _window(rows, fx, fy)
    for yy in range(76, h - 2):
        for xx in range(16, 24):
            rows[yy][xx] = 'B' if (yy == 76 or xx in (16, 23)) else 'b'
    for x in range(w):
        rows[h - 1][x] = rows[h - 2][x] = 'S'
    return [''.join(r) for r in rows]


def _skyline(w=256, h=64):
    # (Breite, Höhe) der Blöcke von links nach rechts, dazu Antennen/Schornsteine
    blocks = [(16, 40), (24, 56), (12, 36), (20, 48), (28, 60), (16, 44), (24, 34), (20, 52),
              (16, 42), (32, 58), (20, 38), (24, 50), (28, 44)]
    spikes = {44: 6, 120: 8, 188: 5, 230: 7}
    tops, x = [], 0
    for bw, bh in blocks:
        tops += [bh] * bw
    tops += [40] * (w - len(tops))
    tops = tops[:w]
    for sx, sh in spikes.items():
        for dx in (0, 1):
            tops[sx + dx] += sh
    return [''.join('k' if h - y <= tops[x] else '.' for x in range(w)) for y in range(h)]


def _storm_cloud():
    """Grimmige Gewitterwolke mit Gesicht (56x32). Der Blitz ist ein eigener Sprite, siehe BOLT_A/BOLT_B."""
    circles = [(10, 18, 9), (22, 12, 12), (36, 12, 12), (47, 19, 8), (28, 20, 10)]
    g = [['.'] * 56 for _ in range(32)]
    for y in range(2, 28):
        for x in range(56):
            if any((x - cx) ** 2 + (y - cy) ** 2 <= rr * rr for cx, cy, rr in circles):
                v = y + x * 0.25                       # Licht von links oben
                lit = v < 21 or (v < 25 and (x + y) % 2 == 0)
                g[y][x] = 'e' if lit else 'E'

    def px(pts, c):
        for x, y in pts:
            g[y][x] = c
    for ex in (20, 32):                                  # Augen
        px([(ex + dx, 14 + dy) for dx in range(4) for dy in range(4)], 'w')
        px([(ex + 2 + dx, 15 + dy) for dx in range(2) for dy in range(2)], 'k')
    px([(19, 11), (20, 11), (21, 12), (22, 12), (23, 13)], 'k')   # böse Brauen
    px([(36, 11), (35, 11), (34, 12), (33, 12), (32, 13)], 'k')
    px([(x, 21) for x in range(25, 31)] + [(24, 22), (31, 22)], 'k')   # Mund
    return [''.join(r) for r in g]


STORM_CLOUD = _storm_cloud()            # 56x32 (hängendes Hindernis)
GREY_TOWER = _grey_tower(40, 112)       # 40x120
ARCH_BUILDING = _arch_building()        # 56x64
BRICK_TOWER = _brick_tower()            # 40x96
SKYLINE = _skyline()                    # 256x64

# Straße: glatter hellgrauer Gehweg, helle Bordsteinkante, dunkle Fahrbahn mit weißem Mittelstrich
# (keine senkrechten Fugen oder Punkte: bei der Wiederholung alle 8 px wirken sie wie Zaunpfosten)
PAVEMENT = ["eeeeeeee", "eeeeeeee", "eeeeeeee", "eeeeeeee", "eeeeeeee", "wwwwwwww", "SSSSSSSS", "kkkkkkkk"]
ROAD = ["EEEEEEEE"] * 8
ROAD_DASH = ["EEEEEEEE", "wwwwwwww", "wwwwwwww", "EEEEEEEE", "EEEEEEEE", "EEEEEEEE", "EEEEEEEE", "EEEEEEEE"]

GROUND_TOP = ["gggggggg", "gGgggGgg", "GGGGGGGG", "bbbbbbbb", "bBbbbBbb", "bbbbbbbb", "bbBbbbbb", "bbbbbbbb"]
GROUND_FILL = ["bbbbbbbb", "bBbbbBbb", "bbbbbbbb", "bbbbBbbb", "bbbbbbbb", "bBbbbbbB", "bbbbbbbb", "bbbbBbbb"]

# Reihenfolge = Tile-Reihenfolge im VRAM. Name, Zeilen. Nicht gelistet (aber definiert): TREE, HOUSE, BIG_BEN
# für spätere Welten, damit sie jetzt kein VRAM belegen.
BG_OBJECTS = [
    ("skyline", SKYLINE),
    ("storm_cloud", STORM_CLOUD),
    ("tower_bridge", TOWER_BRIDGE),
    ("grey_tower", GREY_TOWER),
    ("arch_building", ARCH_BUILDING),
    ("brick_tower", BRICK_TOWER),
    ("pavement", PAVEMENT),
    ("road", ROAD),
    ("road_dash", ROAD_DASH),
    ("ground_top", GROUND_TOP),
    ("ground_fill", GROUND_FILL),
    ("cloud", CLOUD),
]

# ---------------------------------------------------------------- Pixelfont (5x7, Farbe 'w')
FONT = {
 'A': ["01110","10001","10001","11111","10001","10001","10001"],
 'B': ["11110","10001","10001","11110","10001","10001","11110"],
 'C': ["01110","10001","10000","10000","10000","10001","01110"],
 'D': ["11110","10001","10001","10001","10001","10001","11110"],
 'E': ["11111","10000","10000","11110","10000","10000","11111"],
 'F': ["11111","10000","10000","11110","10000","10000","10000"],
 'G': ["01110","10001","10000","10111","10001","10001","01111"],
 'H': ["10001","10001","10001","11111","10001","10001","10001"],
 'I': ["01110","00100","00100","00100","00100","00100","01110"],
 'J': ["00111","00010","00010","00010","00010","10010","01100"],
 'K': ["10001","10010","10100","11000","10100","10010","10001"],
 'L': ["10000","10000","10000","10000","10000","10000","11111"],
 'M': ["10001","11011","10101","10101","10001","10001","10001"],
 'N': ["10001","11001","10101","10011","10001","10001","10001"],
 'O': ["01110","10001","10001","10001","10001","10001","01110"],
 'P': ["11110","10001","10001","11110","10000","10000","10000"],
 'Q': ["01110","10001","10001","10001","10101","10010","01101"],
 'R': ["11110","10001","10001","11110","10100","10010","10001"],
 'S': ["01111","10000","10000","01110","00001","00001","11110"],
 'T': ["11111","00100","00100","00100","00100","00100","00100"],
 'U': ["10001","10001","10001","10001","10001","10001","01110"],
 'V': ["10001","10001","10001","10001","10001","01010","00100"],
 'W': ["10001","10001","10001","10101","10101","11011","10001"],
 'X': ["10001","10001","01010","00100","01010","10001","10001"],
 'Y': ["10001","10001","01010","00100","00100","00100","00100"],
 'Z': ["11111","00001","00010","00100","01000","10000","11111"],
 '0': ["01110","10001","10011","10101","11001","10001","01110"],
 '1': ["00100","01100","00100","00100","00100","00100","01110"],
 '2': ["01110","10001","00001","00010","00100","01000","11111"],
 '3': ["11110","00001","00001","01110","00001","00001","11110"],
 '4': ["00010","00110","01010","10010","11111","00010","00010"],
 '5': ["11111","10000","11110","00001","00001","10001","01110"],
 '6': ["00110","01000","10000","11110","10001","10001","01110"],
 '7': ["11111","00001","00010","00100","01000","01000","01000"],
 '8': ["01110","10001","10001","01110","10001","10001","01110"],
 '9': ["01110","10001","10001","01111","00001","00010","01100"],
}
FONT_ORDER = [chr(c) for c in range(ord('A'), ord('Z') + 1)] + [chr(c) for c in range(ord('0'), ord('9') + 1)]


def font_tile(ch):
    rows = ['.' * 8]
    for r in FONT[ch]:
        rows.append(''.join('w' if c == '1' else '.' for c in r).ljust(8, '.'))
    return rows
