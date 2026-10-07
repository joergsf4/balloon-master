"""Welt 2: Piratenbucht. Insel mit Palmen, Piratenschiff, Piratenfestung und Schatzinsel (Ziel), Wasser und Himmel.

Alle Objekte sind unten bündig auf dem Wasser (Bildschirm-y 168). '.' = durchsichtig; vor der Umwandlung in Kacheln
wird es mit der Hintergrundfarbe dieser Bildschirmzeile gefüllt (bake), damit es zur Szene passt: oben Himmel,
darunter Meerstreifen, die nur von der Zeile abhängen.
"""
import math
import random

from canvas import Canvas

SEA_PAL = "awtATkYSbBgGeEyr"          # Index = Position; '.' = Platz 0 = Himmel
BOTTOM = 168


def sea_bg(y):
    """Hintergrundfarbe hinter den Hindernissen in Bildschirmzeile y (Meer ab y = 112)."""
    if y < 112:
        return 'a'
    if y < 128:
        return 't'
    if y < 152:
        return 'A'
    return 'T'


def bake(rows):
    """'.' durch die Hintergrundfarbe der jeweiligen Bildschirmzeile ersetzen (Objekt unten bündig auf 168)."""
    h = len(rows)
    return [''.join(sea_bg(BOTTOM - h + y) if c == '.' else c for c in r) for y, r in enumerate(rows)]


def foam(cv, y, x0, x1, seed):
    rnd = random.Random(seed)
    x = x0
    while x < x1:
        n = rnd.randint(2, 5)
        for i in range(n):
            cv.put(x + i, y, 'w')
        x += n + rnd.randint(3, 7)


# ---------------------------------------------------------------- Palmen
def palm(cv, bx, by, tx, ty, flip=1):
    """Palme: gebogener Stamm von (bx,by) nach (tx,ty), Wedel oben."""
    n = 40
    for i in range(n + 1):
        t = i / n
        x = bx + (tx - bx) * t + math.sin(t * math.pi) * 5 * flip
        y = by + (ty - by) * t
        cv.put(x, y, 'b')
        cv.put(x + 1, y, 'b')
        cv.put(x + 2, y, 'B')
    for ang, ln in ((20, 15), (55, 15), (90, 12), (125, 15), (160, 15), (200, 13), (340, 13), (235, 9), (305, 9)):
        a = math.radians(ang)
        for s in range(ln + 1):
            x = tx + 1 + math.cos(a) * s
            y = ty - math.sin(a) * s + 0.04 * s * s
            cv.put(x, y, 'g')
            cv.put(x, y + 1, 'g')
            cv.put(x, y + 2, 'G')
    cv.put(tx, ty + 2, 'B')
    cv.put(tx + 2, ty + 3, 'B')
    cv.put(tx + 1, ty + 4, 'B')


def sand_mound(cv, x0, x1, top, base, water):
    """Sandhügel von x0..x1, Scheitel `top`, unten bis zur Wasserlinie `water`."""
    cx, hw = (x0 + x1) / 2, (x1 - x0) / 2
    for x in range(int(x0), int(x1)):
        t = (x - cx) / hw
        y_top = base - (base - top) * math.sqrt(max(0.0, 1 - t * t))
        for y in range(int(round(y_top)), int(water)):
            shade = y > water - 4 or t > 0.55
            cv.put(x, y, 'S' if shade else 'Y')


# ---------------------------------------------------------------- Objekte
def island():
    cv = Canvas(64, 64)
    sand_mound(cv, 4, 60, 42, 56, 58)
    palm(cv, 24, 46, 18, 12, 1)
    foam(cv, 58, 4, 60, 3)
    foam(cv, 59, 8, 56, 5)
    return cv.rows()


def _cannon45(cv, x0, y0, x1, y1):
    """Kanonenrohr schräg nach oben links (45 Grad): von (x0,y0) an der Lafette bis zur Mündung (x1,y1)."""
    cv.line(x0, y0, x1, y1, 'E', 4)
    cv.line(x0 + 1, y0 + 1, x1 + 1, y1 + 1, 'k', 1)
    cv.rect(x1 - 1, y1 - 1, x1 + 3, y1 + 1, 'k')            # Mündung


def ship():
    cv = Canvas(96, 96)

    def y_bot(x):
        if x < 22:
            return 66 + (x - 6) * 18 / 16
        if x <= 80:
            return 84
        return 84 - (x - 80) * 22 / 10

    def y_top(x):
        if x >= 70:
            return 50
        return 66 if x <= 30 else 64
    for x in range(6, 91):
        for y in range(int(y_top(x)), int(y_bot(x))):
            cv.put(x, y, 'B')
    for x in range(6, 91):                                      # Reling und Planken
        cv.put(x, int(y_top(x)), 'b')
        cv.put(x, int(y_top(x)) + 1, 'b')
        for y in range(int(y_top(x)) + 8, int(y_bot(x)), 8):
            cv.put(x, y, 'b')
    for x in range(6, 91):
        cv.put(x, int(y_bot(x)) - 1, 'k')
    for px in (14, 28, 42):                                     # Kanonenpforten
        cv.rect(px, 74, px + 5, 78, 'k')
    _cannon45(cv, 17, 65, 9, 57)                                # Bugkanone, 45 Grad
    cv.rect(14, 64, 24, 68, 'B')

    def mast(x, y0, y1):
        cv.rect(x - 1, y0, x + 2, y1, 'B')
    mast(44, 4, 66)
    mast(22, 36, 64)
    mast(78, 32, 52)

    def sail(x0, x1, y0, y1, bulge=3):
        for y in range(y0, y1):
            t = (y - y0) / max(1, (y1 - y0 - 1))
            inset = int(bulge * math.sin(t * math.pi) * 0.4)
            for x in range(x0 + (1 if y in (y0, y1 - 1) else 0), x1 - (1 if y in (y0, y1 - 1) else 0)):
                shade = x >= x1 - 3 - inset or y >= y1 - 2
                cv.put(x, y, 'e' if shade else 'w')
        for y in (y0 + (y1 - y0) // 2,):
            for x in range(x0 + 1, x1 - 1):
                cv.put(x, y, 'e')
    sail(30, 59, 26, 46)
    sail(34, 55, 8, 24)
    sail(10, 34, 36, 54)
    cv.poly([(79, 33), (79, 50), (93, 48)], 'w')
    skull = ["..kkkkk..", ".kkkkkkk.", ".k.kkk.k.", ".kkkkkkk.", "..k.k.k.."]
    for dy, row in enumerate(skull):                            # Totenkopf auf dem Großsegel
        for dx, ch in enumerate(row):
            if ch == 'k':
                cv.put(40 + dx, 30 + dy, 'k')
    cv.line(39, 36, 49, 42, 'k')
    cv.line(49, 36, 39, 42, 'k')
    cv.poly([(46, 2), (46, 8), (56, 5)], 'k')                   # Wimpel
    foam(cv, 84, 8, 90, 11)
    return cv.rows()


def fort():
    """Piratenfestung. Kachel-sparend: Holzmuster wiederholen sich alle 8 px, Details liegen auf dem 8er-Raster
    (das Spiel legt nur exakt gleiche 8x8-Kacheln zusammen; die Welt hat nur 448 Kacheln)."""
    cv = Canvas(96, 88)

    for x in range(0, 96):                                      # Felsen im Wasser (wie vorher)
        top = 64 + int(5 * math.sin(x / 7.0))
        for y in range(top, 82):
            edge = x < 4 or x > 91 or y > 78
            cv.put(x, y, 'S' if (y - top < 2 and not edge) else 'E')

    def planks(x0, y0, x1, y1):
        """Schiffsplanken: 8 px hoch, Stoss alle 8 px, jede zweite Reihe um 4 versetzt (Periode 8x16)."""
        for y in range(y0, y1):
            for x in range(x0, x1):
                dark = (y % 8 == 7) or ((x + 4 * ((y // 8) % 2)) % 8 == 0)
                if x >= x1 - 3:
                    dark = True
                cv.put(x, y, 'B' if dark else 'b')

    def logs(x0, y0, x1, y1):
        """Senkrechte Staemme, Periode 4; rechte 3 px dunkel."""
        for y in range(y0, y1):
            for x in range(x0, x1):
                cv.put(x, y, 'B' if (x % 4 == 3 or x >= x1 - 3) else 'b')

    def art(x0, y0, rows):
        """8x8-Kachel (oder Vielfaches) auf dem Raster; '.' = nichts ueberschreiben."""
        for dy, r in enumerate(rows):
            for dx, ch in enumerate(r):
                if ch != '.':
                    cv.put(x0 + dx, y0 + dy, ch)

    PLATFORM = ["bbbbbbbb"] + ["BBBBBBBB"] * 7
    RAIL = ["bbbbbbbb", "bbbbbbbb"] + ["BB......"] * 6
    STAKE = ["........", "........", ".bb.....", ".bb.....", "bbbB....", "bbbB....", "bbbB....", "bbbB...."]
    WINDOW = ["kkkkkkkk", "kyyykyyk", "kyyykyyk", "kkkkkkkk", "kyyykyyk", "kyyykyyk", "kkkkkkkk", "BBBBBBBB"]
    PORTHOLE = ["..kkkk..", ".kyyyyk.", "kyyyyyyk", "kyyyyyyk", "kyyyyyyk", "kyyyyyyk", ".kyyyyk.", "..kkkk.."]
    GUNPORT = ["BBBBBBBB", "BkkkkkkB", "BkEEEEkB", "BkEkkEkB", "BkEkkEkB", "BkEEEEkB", "BkkkkkkB", "BBBBBBBB"]
    ANCHOR = ["...EE...", "...EE...", ".EEEEEE.", "...EE...", "...EE...", "E..EE..E", "EE.EE.EE", ".EEEEEE."]
    GATE_TOP = ["BBBBBBBB", "kBkkkBkk", "kBkkkBkk", "kBkkkBkk", "BBBBBBBB", "kBkkkBkk", "kBkkkBkk", "kBkkkBkk"]
    GATE_BOT = ["kBkkkBkk", "kBkkkBkk", "kBkkkBkk", "BBBBBBBB", "kBkkkBkk", "kBkkkBkk", "kBkkkBkk", "BBBBBBBB"]
    MAST = ["BB......"] * 8

    SHINGLE = ["BbBbBbBb", "bBbBbBbB", "BbBbBbBb", "BBBBBBBB", "bBbBbBbB", "BbBbBbBb", "bBbBbBbB", "BBBBBBBB"]
    SKULLPOLE = ["..www...", ".wwwww..", ".wkwkw..", "..www...", "...B....", "...B....", "...B....", "...B...."]
    BARREL = [".kkkkkk.", "kbbbbbBk", "kyyyyyyk", "kbbbbbBk", "kbbbbbBk", "kyyyyyyk", "kbbbbbBk", ".kkkkkk."]
    CHEST = ["........", "........", ".kkkkkk.", "kbbbbbBk", "kyyyyyyk", "kbbyybBk", "kbbbbbBk", "kkkkkkkk"]
    PENNANT = ["........", "......rr", "rrrrrrrr", "rrrrrrrr", "..rrrrrr", "........", "........", "........"]

    # Mauer, Tuerme (alles auf dem 8er-Raster)
    planks(0, 24, 96, 72)
    art(24, 16, STAKE)                                          # Pfahl neben dem linken Turm
    art(24, 8, SKULLPOLE)                                       # mit Totenkopf (sitzt auf dem Pfahl)
    art(64, 16, STAKE)
    logs(0, 24, 24, 72)                                         # linker Turm: Ausguck
    for x in range(0, 24, 8):
        art(x, 16, PLATFORM)
        art(x, 8, RAIL)
    planks(72, 24, 96, 72)                                      # rechter Turm: gestrandetes Heck
    for x in range(72, 96, 8):
        art(x, 16, PLATFORM)
        art(x, 8, RAIL)
    art(80, 0, PENNANT)                                         # Wimpel am Heckmast
    art(88, 0, MAST)
    planks(32, 16, 64, 32)                                      # Wachhaus mit Schindeldach
    for x in range(32, 64, 8):
        art(x, 8, SHINGLE)
    art(40, 16, WINDOW)
    art(56, 16, WINDOW)

    art(72, 32, WINDOW)                                         # Heckfenster
    art(88, 32, WINDOW)
    art(80, 48, ANCHOR)
    art(16, 32, PORTHOLE)
    art(24, 48, GUNPORT)                                        # Kanonenpforten
    art(64, 48, GUNPORT)
    art(40, 56, GATE_TOP)                                       # Tor
    art(48, 56, GATE_TOP)
    art(40, 64, GATE_BOT)
    art(48, 64, GATE_BOT)
    for x in (32, 56, 64):                                      # Rumfaesser am Fuss
        art(x, 64, BARREL)
    art(24, 64, CHEST)

    _cannon45(cv, 12, 47, 4, 39)                                # Turmkanone, 45 Grad (Schusspunkt!)

    # Totenkopf mit Knochen ueber dem Tor (16x16, auf dem Raster)
    cv.line(42, 42, 54, 54, 'e', 2)
    cv.line(54, 42, 42, 54, 'e', 2)
    skull = ["..wwwwwwww..", ".wwwwwwwwww.", "wwwwwwwwwwww", "wwkkkwwkkkww", "wwkkkwwkkkww",
             "wwwwwkkwwwww", ".wwwwwwwwww.", "..wkwkwkww..", "..wwwwwwww.."]
    for dy, r in enumerate(skull):
        for dx, ch in enumerate(r):
            if ch != '.':
                cv.put(42 + dx, 40 + dy, ch)

    # Fahnenmast und Totenkopfflagge (wie vorher)
    art(48, 0, MAST)
    cv.poly([(50, 1), (50, 11), (64, 11), (61, 6), (64, 1)], 'k')
    for dy, row in enumerate(["wwwww", "w.w.w", "wwwww", ".w.w."]):
        for dx, ch in enumerate(row):
            if ch == 'w':
                cv.put(53 + dx, 2 + dy, 'w')

    foam(cv, 80, 0, 96, 21)
    return cv.rows()


def treasure():
    cv = Canvas(96, 72)
    sand_mound(cv, 2, 94, 28, 52, 64)
    palm(cv, 16, 40, 12, 8, 1)
    cv.rect(36, 36, 60, 48, 'b')                                # Truhe
    cv.rect(36, 36, 60, 38, 'B')
    cv.rect(36, 46, 60, 48, 'B')
    cv.rect(46, 36, 48, 48, 'B')
    cv.rect(41, 40, 44, 44, 'y')
    cv.poly([(36, 36), (60, 36), (57, 27), (39, 27)], 'b')      # offener Deckel
    cv.rect(39, 27, 57, 29, 'B')
    for x, y in ((40, 33), (46, 31), (52, 32), (56, 34)):
        cv.rect(x, y, x + 4, y + 3, 'y')
        cv.put(x + 1, y, 'w')
    for x, y in ((48, 24),):                                    # Glitzern
        for dx, dy in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
            cv.put(x + dx, y + dy, 'w')
    foam(cv, 64, 2, 94, 31)
    return cv.rows()


def _tentacle(cv, pts, w0, w1):
    """Tentakel entlang eines weichen Pfades (Catmull-Rom), Dicke von w0 nach w1, Saugnäpfe innen."""
    P = [pts[0]] + list(pts) + [pts[-1]]
    n = 0
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(24):
            t = k / 24
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t * t +
                       (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t ** 3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t * t +
                       (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t ** 3)
            frac = ((i - 1) * 24 + k) / ((len(P) - 3) * 24)
            r = w0 + (w1 - w0) * frac
            cv.disc(x, y, r, 'r')
            n += 1


def _kraken(strike):
    cv = Canvas(64, 80)
    cv.blob([(40, 54, 14), (30, 58, 10), (48, 58, 10)], ('r', 'r', 'r', 'r'), (4, 10, 17))
    for y in range(70, 80):
        for x in range(64):
            cv.put(x, y, '.')
    cv.disc(35, 49, 3, 'w')                                      # Augen
    cv.disc(46, 49, 3, 'w')
    cv.disc(34, 50, 1.5, 'k')
    cv.disc(45, 50, 1.5, 'k')
    cv.line(31, 44, 38, 47, 'k', 2)                              # böse Brauen
    cv.line(50, 44, 43, 47, 'k', 2)
    if strike:                                                   # zwei Tentakel peitschen nach links
        _tentacle(cv, [(16, 70), (8, 58), (2, 46), (4, 36)], 4.5, 2)
        _tentacle(cv, [(28, 70), (18, 56), (8, 42), (2, 36)], 4, 2)
    else:                                                        # Tentakel ragen nach oben
        _tentacle(cv, [(16, 70), (10, 54), (18, 38), (10, 22), (16, 8)], 4.5, 2)
        _tentacle(cv, [(28, 70), (24, 52), (32, 34), (26, 18), (30, 6)], 4, 2)
    _tentacle(cv, [(54, 70), (60, 52), (52, 34), (58, 18), (52, 8)], 4, 2)
    foam(cv, 70, 4, 60, 9)
    return cv.rows()


def kraken():
    return _kraken(False)


def kraken_b():
    return _kraken(True)


def far_cloud():
    circles = [(10, 10, 6), (21, 7, 8), (33, 8, 7), (41, 11, 5), (24, 11, 6)]
    rows = []
    for y in range(16):
        r = []
        for x in range(48):
            inside = y <= 12 and any((x - cx) ** 2 + (y - cy) ** 2 <= rr * rr for cx, cy, rr in circles)
            r.append(('E' if y >= 10 or x >= 44 else 'e') if inside else '.')
        rows.append(''.join(r))
    return rows


def water():
    """Vordergrund-Wasser, 32x24 (4 Kacheln breit, 3 Zeilen): Wellenkämme in vier Varianten."""
    cv = Canvas(32, 24)
    for y in range(24):
        for x in range(32):
            cv.put(x, y, 't' if y < 8 else ('A' if y < 16 else 'T'))
    rnd = random.Random(3)
    for tx in range(2):
        for row, (base, crest) in enumerate((('t', 'w'), ('A', 't'), ('T', 'A'))):
            for k in range(2):
                n = rnd.randint(3, 5)
                x = tx * 8 + rnd.randint(0, 8 - n)
                y = row * 8 + (2 if k == 0 else 5)
                for i in range(n):
                    cv.put(x + i, y, crest)
    for y in range(24):                                         # zwei Kacheln wiederholen sich (spart VRAM)
        for x in range(16):
            cv.put(16 + x, y, cv.g[y][x])
    return cv.rows()


def sea_band():
    """Hintergrund hinter den Hindernissen für Tile-Zeilen 13..20 (y 104..167): nur Himmel und Meerstreifen."""
    return [sea_bg(104 + y) * 256 for y in range(64)]


def _storm():
    from artdefs import STORM_CLOUD
    return STORM_CLOUD


SPEC = {
    "id": "sea", "title": "Piratenbucht", "bank": 3, "pal": SEA_PAL,
    "bg": sea_bg, "ground": water, "far_cloud": far_cloud,
    "floors": [{"name": "island", "rows": island},
               {"name": "ship", "rows": ship, "shot": (9, 168 - 96 + 57)},
               {"name": "fort", "rows": fort, "shot": (3, 168 - 88 + 38)},
               {"name": "kraken", "rows": kraken, "anim": {"rows_b": kraken_b}}],
    "setpieces": [(45, 4, 1), (78, 4, 1)],
    "finish": {"name": "treasure", "rows": treasure},
    "ceil1": {"name": "storm", "rows": _storm, "top_row": 2, "bolt": (20, 44)},
    "kind_bld": [1, 2, 3, 0, 1, 2, 3, 1], "kind_ceil": [0, 0, 0, 1, 1, 0, 0, 0],
    "sky": "a", "flash": 0x3E,
    "phys": (1, 3, 24, 32), "wind": (8, 12, 16, 24), "level_cols": 433,
    "flyer": {"shared": "BIRD_UP", "w": 2, "h": 2, "hit": (3, 6, 13, 12), "fast": 8},
    "music": 1,
}
