"""ASCII-Zeilen -> Pixelraster -> SMS-Tiles (4bpp planar), dazu Umriss und PNG-Vorschau (nur stdlib)."""
import struct
import zlib

from palette import COLORS, rgb8


def check(rows, name):
    w = len(rows[0])
    for i, r in enumerate(rows):
        assert len(r) == w, f"{name}: Zeile {i} hat {len(r)} statt {w} Zeichen"
    return w, len(rows)


def ctr(rows, width):
    """Zeilen mittig auf die Breite bringen (nur sichtbarer Bereich zeichnen)."""
    out = []
    for r in rows:
        assert (width - len(r)) % 2 == 0, f"ctr: '{r}' passt nicht symmetrisch in {width}"
        out.append(r.center(width, '.'))
    return out


def outlined(rows, ch='k'):
    """1 px Umriss (4er-Nachbarschaft) um alle sichtbaren Pixel; Raster wächst je Seite um 1 px."""
    w, h = check(rows, "outlined")
    grid = [['.'] * (w + 2) for _ in range(h + 2)]
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            grid[y + 1][x + 1] = c
    out = [row[:] for row in grid]
    for y in range(h + 2):
        for x in range(w + 2):
            if grid[y][x] != '.':
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w + 2 and 0 <= ny < h + 2 and grid[ny][nx] != '.':
                    out[y][x] = ch
                    break
    return [''.join(r) for r in out]


def to_tiles(rows, pal, name):
    """Raster (Vielfaches von 8) -> (Bytes, Breite in Tiles, Höhe in Tiles), Tiles zeilenweise."""
    w, h = check(rows, name)
    assert w % 8 == 0 and h % 8 == 0, f"{name}: {w}x{h} ist kein Vielfaches von 8"
    data = bytearray()
    for ty in range(h // 8):
        for tx in range(w // 8):
            for y in range(8):
                line = rows[ty * 8 + y][tx * 8:tx * 8 + 8]
                idx = []
                for c in line:
                    if c == '.':
                        idx.append(0)
                    elif c in pal:
                        idx.append(pal.index(c))
                    else:
                        raise ValueError(f"{name}: Farbe '{c}' fehlt in der Palette '{pal}'")
                for plane in range(4):
                    b = 0
                    for x, i in enumerate(idx):
                        b |= ((i >> plane) & 1) << (7 - x)
                    data.append(b)
    return bytes(data), w // 8, h // 8


def write_png(path, width, height, pixels):
    """pixels: Liste von Zeilen, je Zeile Liste von (r, g, b)."""
    raw = b''.join(b'\x00' + bytes(v for px in row for v in px) for row in pixels)

    def chunk(tag, body):
        return struct.pack('>I', len(body)) + tag + body + struct.pack('>I', zlib.crc32(tag + body) & 0xffffffff)

    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(raw, 9))
    png += chunk(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(png)


def blit(canvas, rows, x0, y0, sky):
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c != '.':
                canvas[y0 + y][x0 + x] = rgb8(COLORS[c])


def scale(canvas, k):
    out = []
    for row in canvas:
        wide = [px for px in row for _ in range(k)]
        out.extend([wide] * k)
    return out


def profile(rows, bottom=168, min_px=4):
    """Oberkante je 8-px-Spalte für die Kollision: erste Zeile, in der mindestens min_px der 8 Pixel gefüllt sind
    (dünne Masten und Antennen zählen nicht). Unten bündig auf `bottom` (Bildschirm-y)."""
    w, h = check(rows, "profile")
    top = bottom - h
    out = []
    for c in range(w // 8):
        y_hit = h
        for y in range(h):
            if sum(1 for x in range(c * 8, c * 8 + 8) if rows[y][x] != '.') >= min_px:
                y_hit = y
                break
        out.append(top + y_hit)
    return out


def profile_bottom(rows, top, min_px=4):
    """Unterkante je 8-px-Spalte für hängende Hindernisse: letzte Zeile mit mindestens min_px gefüllten Pixeln.
    `top` ist die Bildschirm-y der Oberkante des Objekts."""
    w, h = check(rows, "profile_bottom")
    out = []
    for c in range(w // 8):
        y_hit = 0
        for y in range(h - 1, -1, -1):
            if sum(1 for x in range(c * 8, c * 8 + 8) if rows[y][x] != '.') >= min_px:
                y_hit = y + 1
                break
        out.append(top + y_hit)
    return out
