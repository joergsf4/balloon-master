"""Festes Farbschema des Spiels. Jede Farbe ist ein Buchstabe, RGB je 0..3 (SMS: 2 Bit pro Kanal).

Das ist der Stilanker: Sprites und Hintergrund greifen nur auf diese Buchstaben zu. Jede der beiden
Hardware-Paletten hat genau 16 Plätze; die Reihenfolge der Buchstaben ist der Palettenindex.
"""

COLORS = {
    'a': (1, 2, 3),  # Himmelblau
    'q': (2, 2, 3),  # Wolkenschatten
    'w': (3, 3, 3),  # Weiß
    'e': (2, 2, 2),  # Hellgrau
    'E': (1, 1, 1),  # Dunkelgrau
    'k': (0, 0, 1),  # Umriss / Schwarz
    'r': (3, 1, 1),  # Koralle (Markenfarbe)
    'R': (2, 0, 0),  # Dunkelrot
    'o': (3, 2, 0),  # Orange
    'y': (3, 3, 1),  # Gelb
    'Y': (3, 3, 2),  # Hellgelb / Stein
    'S': (2, 2, 1),  # Steinschatten
    'c': (3, 2, 1),  # Haut
    'b': (2, 1, 0),  # Braun
    'B': (1, 0, 0),  # Dunkelbraun
    'g': (1, 2, 0),  # Grün
    'G': (0, 1, 0),  # Dunkelgrün
    't': (0, 2, 2),  # Teal (Markenfarbe)
    'n': (0, 0, 2),  # Dachblau
    'A': (0, 1, 2),  # Meer, mittleres Blau
    'D': (1, 1, 2),  # Schiefer (dunkler Gewitterhimmel)
    'v': (2, 0, 2),  # Violett
    'm': (3, 1, 2),  # Rosa
    'T': (0, 1, 1),  # Meer, tiefes Blaugrün
}

# Index = Position. '.' steht an Platz 0 und heißt "durchsichtig" (Sprites) bzw. Himmel (Hintergrund).
SPRITE_PAL = ".kweErRoyYcbBgat"
BG_PAL = "akwqeErRByYSbgGn"

assert len(SPRITE_PAL) == 16 and len(BG_PAL) == 16
assert len(set(SPRITE_PAL)) == 16 and len(set(BG_PAL)) == 16


def sms_byte(rgb):
    r, g, b = rgb
    return r | (g << 2) | (b << 4)


def rgb8(rgb):
    return tuple(v * 85 for v in rgb)
