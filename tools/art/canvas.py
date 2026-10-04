"""Zeichenhilfen für prozedurale Pixelgrafik (Buchstaben als Farben, '.' = durchsichtig)."""
import math
import random


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.g = [['.'] * w for _ in range(h)]

    def put(self, x, y, c):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            self.g[y][x] = c

    def rect(self, x0, y0, x1, y1, c):
        for y in range(int(y0), int(y1)):
            for x in range(int(x0), int(x1)):
                self.put(x, y, c)

    def line(self, x0, y0, x1, y1, c, thick=1):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) or 1
        for i in range(n + 1):
            x = x0 + (x1 - x0) * i / n
            y = y0 + (y1 - y0) * i / n
            for dx in range(thick):
                self.put(x + dx, y, c)

    def poly(self, pts, c):
        """Gefülltes Vieleck (Scanline)."""
        ys = [p[1] for p in pts]
        for y in range(int(min(ys)), int(max(ys)) + 1):
            xs = []
            for i in range(len(pts)):
                (xa, ya), (xb, yb) = pts[i], pts[(i + 1) % len(pts)]
                if (ya <= y < yb) or (yb <= y < ya):
                    xs.append(xa + (y - ya) * (xb - xa) / (yb - ya))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                for x in range(int(round(xs[i])), int(round(xs[i + 1]))):
                    self.put(x, y, c)

    def rows(self):
        return [''.join(r) for r in self.g]


    def disc(self, cx, cy, r, c):
        for y in range(int(cy - r), int(cy + r) + 1):
            for x in range(int(cx - r), int(cx + r) + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    self.put(x, y, c)

    def blob(self, circles, tones, steps=(3, 7, 13)):
        """Wolke/Fels aus Kreisen (cx, cy, r). Beleuchtet von links oben: der Ton hängt davon ab, wie weit ein Pixel
        (diagonal nach links oben gemessen) von der Kante der gesamten Form entfernt ist; an den Stufen wird
        schachbrettartig gemischt. tones = (hell, mittel, dunkel, am dunkelsten)."""
        mask = [[any((x - cx) ** 2 + (y - cy) ** 2 <= r * r for cx, cy, r in circles) for x in range(self.w)]
                for y in range(self.h)]
        depth = [[0] * self.w for _ in range(self.h)]
        for y in range(self.h):
            for x in range(self.w):
                if not mask[y][x]:
                    continue
                inside_prev = x > 0 and y > 0 and mask[y - 1][x - 1]
                depth[y][x] = depth[y - 1][x - 1] + 1 if inside_prev else 0
                d = depth[y][x]
                chk = (x + y) % 2 == 0
                if d < steps[0] - (0 if chk else 1):
                    t = tones[0]
                elif d < steps[1] - (0 if chk else 1):
                    t = tones[1]
                elif d < steps[2] - (0 if chk else 1):
                    t = tones[2]
                else:
                    t = tones[3]
                self.put(x, y, t)
