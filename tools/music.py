#!/usr/bin/env python3
"""Musik der Welten 2 bis 6 (eigene Kompositionen, angelehnt an Stile) -> src/music_data.h.

Jedes Stück besteht aus Melodie (Kanal 0) und Bass (Kanal 1). Einträge sind (Frequenz in Hz, Dauer in Bildern bei
60 Hz; 0 = Pause). Melodie und Bass müssen gleich lang sein, sonst läuft die Schleife auseinander. Tiefer als etwa
110 Hz geht auf dem PSG nicht. Stück 0 (London Bridge) steht direkt in src/sound.c.

Je Stück: Grundlautstärke und Obergrenze der Dämpfung (0 = laut ... 15 = still) für Melodie und Bass sowie die
Ausklingzeit (Bilder pro Dämpfungsstufe: klein = gezupft, groß = klingt lange) und der Lücke am Ende jeder Note (Staccato).
"""
import os

R = 0


def hz(name):
    """'A4', 'C#5', 'Bb3' -> Frequenz in Hz (gleichstufig)."""
    base = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
    n, i = base[name[0]], 1
    if name[i] == '#':
        n, i = n + 1, i + 1
    elif name[i] == 'b':
        n, i = n - 1, i + 1
    midi = 12 * (int(name[i:]) + 1) + n
    f = round(440 * 2 ** ((midi - 69) / 12))
    assert 110 <= f <= 4000, f"{name}: {f} Hz außerhalb des Bereichs"
    return f


def seq(items, unit=1, stac=0.0):
    """items: (Notenname oder 'R', Länge in Einheiten). stac: Anteil der Note, der als Pause hinten drangehängt wird."""
    out = []
    for name, ln in items:
        frames = int(round(ln * unit))
        if name == 'R':
            out.append((R, frames))
        elif stac and frames >= 6:
            gap = max(1, int(round(frames * stac)))
            out += [(hz(name), frames - gap), (R, gap)]
        else:
            out.append((hz(name), frames))
    return out


TRACKS = {}      # Nummer -> (Melodie, Bass, (mbase, mcap, bbase, bcap, rate))

# ---- 1: Piratenbucht. Shanty in d-Dorisch, stampfend und flott (Achtel = 7 Bilder), Oom-Pah-Bass
U = 7
A = [[('D5', 1), ('D5', 1), ('D5', 1), ('A4', 1), ('D5', 1), ('D5', 1), ('F5', 1), ('D5', 1)],
     [('E5', 1), ('E5', 1), ('E5', 1), ('A4', 1), ('E5', 1), ('E5', 1), ('G5', 1), ('E5', 1)],
     [('F5', 1), ('F5', 1), ('F5', 1), ('C5', 1), ('F5', 1), ('F5', 1), ('A5', 1), ('F5', 1)],
     [('E5', 1), ('D5', 1), ('C5', 1), ('B4', 1), ('A4', 3), ('R', 1)]]
B = [[('A5', 1), ('A5', 1), ('A5', 1), ('F5', 1), ('A5', 1), ('A5', 1), ('C6', 1), ('A5', 1)],
     [('G5', 1), ('G5', 1), ('G5', 1), ('E5', 1), ('G5', 1), ('G5', 1), ('B5', 1), ('G5', 1)],
     [('F5', 1), ('E5', 1), ('D5', 1), ('C5', 1), ('D5', 1), ('E5', 1), ('F5', 1), ('G5', 1)],
     [('A5', 3), ('R', 1), ('A4', 1), ('D5', 1), ('F5', 1), ('A5', 1)]]
END = [[('A5', 1), ('F5', 1), ('D5', 1), ('A4', 1), ('D5', 3), ('R', 1)]]
mel = []
for bar in A + B + A + B[:3] + END:
    mel += seq(bar, U)
chords = {'Dm': ('D3', 'A3'), 'Am': ('A3', 'E4'), 'F': ('F3', 'C4'), 'C': ('C3', 'G3'), 'Gm': ('G3', 'D4'), 'A': ('A3', 'E4')}
prog = ['Dm', 'Am', 'F', 'Am', 'F', 'C', 'Gm', 'A', 'Dm', 'Am', 'F', 'Am', 'F', 'C', 'Gm', 'Dm']
bas = []
for ch in prog:
    r_, f_ = chords[ch]
    bas += seq([(r_, 1), (f_, 1)] * 4, U)
TRACKS[1] = (mel, bas, (3, 8, 6, 10, 5, 1, 3))

# ---- 2: Gewitter. Anfang nach dem Motiv der Toccata in d-Moll (Bach, gemeinfrei), dann dunkle Läufe und Donnergrollen
f = lambda names: names
toccata_hi = [(880, 6), (784, 6), (880, 40), (R, 12), (784, 6), (698, 6), (659, 6), (587, 6), (554, 6), (587, 44), (R, 20)]
toccata_lo = [(440, 6), (392, 6), (440, 40), (R, 12), (392, 6), (349, 6), (330, 6), (294, 6), (277, 6), (294, 44), (R, 20)]
arp = [(294, 12), (349, 12), (440, 12), (587, 12), (440, 12), (349, 12)] * 2
rumble = [(587, 6), (554, 6)] * 5
end_hi = [(880, 6), (784, 6), (880, 60), (R, 20)]
down = [(698, 12), (659, 12), (587, 12), (554, 12), (587, 60), (R, 60)]
coda = [(440, 30), (392, 30), (349, 30), (330, 30), (294, 60)]
mel = toccata_hi + toccata_lo + arp + rumble + end_hi + down + coda
bas = [(147, 158), (147, 158), (147, 72), (175, 72), (165, 30), (165, 30), (147, 92),
       (147, 56), (139, 56), (131, 56), (147, 60), (196, 60), (147, 60)]
TRACKS[2] = (mel, bas, (4, 9, 7, 11, 6, 0, 0))

# ---- 3: Höhle, esoterisch. Glockentöne in d-Pentatonik über einem langen Bordun (d - a), sehr langsam
U = 20
mel = seq([('D5', 6), ('R', 2), ('A5', 4), ('G5', 2), ('E5', 6), ('R', 2), ('B5', 4), ('A5', 2), ('G5', 4), ('E5', 4),
           ('D5', 6), ('R', 2), ('A4', 4)], U)
bas = seq([('D3', 24), ('A3', 12), ('D3', 12)], U)
TRACKS[3] = (mel, bas, (4, 9, 8, 10, 14, 0, 0))

# ---- 4: Mond. Raketenstart, danach schwebende Linien über Arpeggien (angelehnt an den Stil von "Rocket Man")
U = 10
launch = [('C4', 1), ('E4', 1), ('G4', 1), ('C5', 1), ('E5', 1), ('G5', 1), ('C6', 1), ('E6', 1)]
bars = [launch,
        [('G5', 3), ('E5', 1), ('D5', 2), ('C5', 2)],
        [('A5', 3), ('G5', 1), ('E5', 2), ('D5', 2)],
        [('G5', 4), ('R', 2), ('E5', 1), ('G5', 1)],
        [('C6', 3), ('G5', 1), ('E5', 2), ('G5', 2)],
        [('A5', 3), ('F5', 1), ('A5', 2), ('C6', 2)],
        [('B5', 3), ('G5', 1), ('D5', 2), ('G5', 2)],
        [('C6', 6), ('R', 2)],
        [('E6', 3), ('C6', 1), ('G5', 2), ('C6', 2)],
        [('D6', 3), ('B5', 1), ('G5', 2), ('B5', 2)],
        [('C6', 2), ('A5', 2), ('F5', 2), ('A5', 2)],
        [('G5', 4), ('E5', 2), ('D5', 2)]]
mel = []
for b in bars:
    mel += seq(b, U)
arps = {'C': ('C3', 'G3', 'C4', 'G3'), 'Am': ('A3', 'E4', 'A4', 'E4'), 'F': ('F3', 'C4', 'F4', 'C4'),
        'G': ('G3', 'D4', 'G4', 'D4')}
bas = seq([('C3', 8)], U)
for ch in ['C', 'Am', 'F', 'C', 'F', 'G', 'C', 'C', 'G', 'F', 'G']:
    bas += seq([(n, 1) for n in arps[ch]] * 2, U)
TRACKS[4] = (mel, bas, (4, 9, 7, 11, 5, 2, 3))

# ---- 5: New York. Swing mit Fanfare und Walking Bass (angelehnt an den Stil der großen Show-Nummern)
Q = 20


def sw(a, b):
    return [(a, 13), (b, 7)]


def seqf(items):
    out = []
    for name, fr in items:
        out.append((R if name == 'R' else hz(name), fr))
    return out


bars = [
    [('C5', 20), ('E5', 20), ('G5', 20), ('C6', 20)],
    sw('B5', 'G5') + [('E5', 20), ('D5', 20), ('C5', 20)],
    sw('A5', 'F5') + [('A5', 20), ('C6', 20), ('A5', 20)],
    [('G5', 40), ('R', 20)] + sw('G5', 'F5'),
    sw('E5', 'G5') + [('C6', 20), ('B5', 20), ('G5', 20)],
    sw('A5', 'C6') + [('E6', 20), ('D6', 20), ('C6', 20)],
    sw('B5', 'D6') + [('G6', 20), ('F6', 20), ('D6', 20)],
    [('C6', 60), ('R', 20)],
    sw('C5', 'E5') + sw('G5', 'E5') + [('C6', 20), ('E5', 20)],
    sw('G5', 'B5') + [('D6', 20), ('B5', 20), ('G5', 20)],
    sw('F5', 'A5') + [('C6', 20), ('A5', 20), ('F5', 20)],
    sw('E5', 'D5') + [('C5', 20), ('G4', 20), ('R', 20)],
]
mel = []
for b in bars:
    for name, fr in b:
        mel.append((R if name == 'R' else hz(name), fr))
walk = ['C3 E3 G3 E3', 'G3 B3 D4 B3', 'F3 A3 C4 A3', 'C3 G3 E3 G3', 'C3 E3 G3 E3', 'F3 A3 C4 E4', 'G3 B3 D4 F4',
        'C3 G3 C4 G3', 'C3 E3 G3 E3', 'G3 B3 D4 B3', 'F3 A3 C4 A3', 'G3 B3 D4 G3']
bas = []
for w in walk:
    bas += seq([(n, 1) for n in w.split()], Q)
TRACKS[5] = (mel, bas, (3, 8, 6, 10, 4, 3, 5))


def carr(name, typ, vals):
    s = "static const %s %s[] = {\n" % (typ, name)
    for i in range(0, len(vals), 10):
        s += "  " + ", ".join(vals[i:i + 10]) + ",\n"
    return s + "};\n"


def main():
    out = "// GENERIERT von tools/music.py - nicht von Hand ändern.\n// Setzt das Makro P(Hz) und den Typ Track aus sound.c voraus.\n\n"
    def split(lst):                       # Dauer ist ein Byte: lange Töne in Stücke teilen
        out = []
        for h, d in lst:
            while d > 240:
                out.append((h, 240))
                d -= 240
            out.append((h, d))
        return out
    for n in list(TRACKS):
        mm, bb, par = TRACKS[n]
        TRACKS[n] = (split(mm), split(bb), par)
    for n, (m, b, _) in sorted(TRACKS.items()):
        tm, tb = sum(d for _, d in m), sum(d for _, d in b)
        assert tm == tb, f"Stück {n}: Melodie {tm} und Bass {tb} Bilder sind nicht gleich lang"
        assert all(0 < d <= 255 for _, d in m + b)
        print(f"Stück {n}: {tm} Bilder ({tm / 60:.1f} s), {len(m)} + {len(b)} Töne")
        fm = lambda h: "0" if h == 0 else "P(%d)" % h
        out += carr("t%d_mel_p" % n, "unsigned int", [fm(h) for h, _ in m])
        out += carr("t%d_mel_d" % n, "unsigned char", [str(d) for _, d in m])
        out += carr("t%d_bas_p" % n, "unsigned int", [fm(h) for h, _ in b])
        out += carr("t%d_bas_d" % n, "unsigned char", [str(d) for _, d in b])
    out += "\n// Index = Stücknummer - 1\nstatic const Track ext_tracks[%d] = {\n" % len(TRACKS)
    for n in sorted(TRACKS):
        mb, mc, bb, bc, rate, mg, bg = TRACKS[n][2]
        out += ("  { t%d_mel_p, t%d_mel_d, sizeof(t%d_mel_d), t%d_bas_p, t%d_bas_d, sizeof(t%d_bas_d), %d, %d, %d, %d, %d, %d, %d },\n"
                % ((n,) * 6 + (mb, mc, bb, bc, rate, mg, bg)))
    out += "};\n"
    here = os.path.dirname(os.path.abspath(__file__))
    open(os.path.join(here, "..", "src", "music_data.h"), "w").write(out)


if __name__ == "__main__":
    main()
