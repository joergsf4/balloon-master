#!/usr/bin/env python3
"""Erzeugt res/generated/assets.h (Paletten + Tiles) und out/art_preview.png aus tools/art/.

Tile-Reihenfolge im VRAM (alles unter 256, damit Sprites und Hintergrund dieselbe Hälfte nutzen):
  0 = leeres Himmel-Tile (Hintergrund), 1.. = Sprites (erste Tile-Hälfte, wie vom VDP für Sprites gewählt),
  danach Hintergrund (Font, Objekte). Nutzbar sind nur Tiles 0..447: ab 448 liegen Tilemap und Sprite-Tabelle.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "art"))

from artdefs import BG_OBJECTS, FONT_ORDER, SPRITES, font_tile  # noqa: E402
from palette import BG_PAL, COLORS, SPRITE_PAL, rgb8, sms_byte  # noqa: E402
from pixelart import blit, profile, profile_bottom, scale, to_tiles, write_png  # noqa: E402
from artdefs import STORM_CLOUD  # noqa: E402

ROOT = os.path.join(HERE, "..")


def pal_bytes(letters):
    return [0 if c == '.' else sms_byte(COLORS[c]) for c in letters]


def c_array(name, data, typ="unsigned char"):
    out = f"static const {typ} {name}[] = {{\n"
    for i in range(0, len(data), 16):
        out += "  " + ", ".join(f"0x{b:02X}" for b in data[i:i + 16]) + ",\n"
    return out + "};\n\n"


def london_world(maps):
    """Die Welt "London" als C-Struktur (Zahlen direkt, damit sie konstante Initialisierer sind)."""
    idx = {n: i for n, _, _, i in maps}
    objrows = dict(BG_OBJECTS)
    out = ""
    names = ("arch_building", "grey_tower", "brick_tower", "tower_bridge")
    hi = {}
    for n in names:
        p = profile(objrows[n])
        hi[n] = min(p) - 30
        out += c_array("prof_" + n, p)
    hi["tower_bridge"] = 46                       # Ziel wird überflogen, Spitzen bei y = 72 (siehe tower_hit in main.c)
    cp = profile_bottom(STORM_CLOUD, 16)
    out += c_array("prof_storm_cloud", cp)

    def b(n):
        N = n.upper()
        return "{ %s_map, prof_%s, %s_W, %s_H, %d, 0, 0, 0, 0, 0 }" % (n, n, N, N, hi[n])

    def g(name):
        return idx[name][0]
    out += "static const unsigned int london_band[32 * 19] = {\n"
    out += "  " + ", ".join(["0"] * (32 * 11)) + ",\n"      # Tile-Zeilen 2..12: Himmel
    out += "  " + ", ".join(str(v) for v in idx["SKYLINE"]) + "\n};\n"
    out += "static const World world_london = {\n"
    out += "  bg_tiles, sizeof(bg_tiles), bg_palette, london_band,\n"
    out += "  { { %d, %d, %d, %d }, { %d, %d, %d, %d }, { %d, %d, %d, %d } },\n" % (
        (g("PAVEMENT"),) * 4 + (g("ROAD"),) * 4 + (g("ROAD_DASH"), g("ROAD_DASH"), g("ROAD"), g("ROAD")))
    out += "  cloud_map,\n"
    out += "  { { 0, 0, 0, 0, 137, 0, 0, 0, 0, 0 },\n    %s,\n    %s,\n    %s,\n    { 0, 0, 0, 0, 137, 0, 0, 0, 0, 0 }, { 0, 0, 0, 0, 137, 0, 0, 0, 0, 0 }, { 0, 0, 0, 0, 137, 0, 0, 0, 0, 0 },\n    %s },\n" % tuple(b(n) for n in names)
    out += "  { { 0, 0, 0, 0, 0, 0, 0, 0 },\n    { storm_cloud_map, prof_storm_cloud, STORM_CLOUD_W, STORM_CLOUD_H, 2, %d, 20, %d },\n" % (max(cp) - 3, max(cp))
    out += "    { 0, 0, 0, 0, 0, 0, 0, 0 } },\n"
    out += "  { 1, 2, 3, 0, 1, 2, 3, 1 }, { 0, 0, 0, 1, 1, 1, 0, 1 },\n"
    out += "  0x39, 0x3E, 1,\n"
    out += "  1, 3, 24, 32,\n"
    out += "  { 8, 12, 16, 24 },\n"
    out += "  433,\n"
    out += "  BIRD_UP, BIRD_UP_W, BIRD_UP_H, 3, 6, 13, 12, 8,\n"
    out += "  0,\n"
    out += "  { 0, 0 }, { 0, 0 },\n"
    out += "  { { 0, 0, 0 }, { 0, 0, 0 }, { 0, 0, 0 } }\n};\n"
    return out


class TileSet:
    """Kacheln einer Welt: gleiche Kacheln werden zusammengelegt; leere Kachel = Nummer 0 (Himmel)."""

    def __init__(self, base, pal):
        self.base, self.pal, self.tiles, self.seen = base, pal, [], {}

    def add_exclusive(self, data):
        """Kachel ohne Zusammenlegen anhängen (für Animationen), liefert die Kachelnummer."""
        self.tiles.append(bytes(data))
        return self.base + len(self.tiles) - 1

    def add(self, name, rows, skip=()):
        data, tw, th = to_tiles(rows, self.pal, name)
        idx = []
        for i in range(tw * th):
            t = bytes(data[i * 32:(i + 1) * 32])
            if i in skip:
                idx.append(-1)
                continue
            if not any(t):
                idx.append(0)
                continue
            if t not in self.seen:
                self.seen[t] = self.base + len(self.tiles)
                self.tiles.append(t)
            idx.append(self.seen[t])
        return idx, tw, th


def emit_world(spec, bg_base, shared):
    """Eine Welt -> src/bank<N>.c / .h (ROM-Bank N). spec siehe tools/art/sea.py (SPEC) als Muster.
    shared: Namen der gemeinsamen Sprites -> erste Kachel (für Gegner, die keine eigenen Sprites haben)."""
    pal = spec["pal"]
    ident = spec["id"]
    ts = TileSet(bg_base, pal)
    # Welt-Sprites (eigene Gegner) zuerst: mit der Sprite-Palette umgewandelt, nicht zusammengelegt
    wsp = {}
    for name, rows in spec.get("sprites", []):
        data, tw, th = to_tiles(rows, SPRITE_PAL, name)
        wsp[name] = bg_base + len(ts.tiles)
        for i in range(tw * th):
            ts.tiles.append(bytes(data[i * 32:(i + 1) * 32]))
    assert bg_base + len(ts.tiles) <= 256 or not wsp, "Welt-Sprites müssen unter Kachel 256 liegen"
    bg = spec["bg"]
    band = ts.add("band", spec["band"]() if spec.get("band") else [bg(16 + y) * 256 for y in range(152)])[0]
    ground = ts.add("ground", spec["ground"]())[0]
    far = ts.add("far", [r.replace('.', pal[0]) for r in spec["far_cloud"]()])[0]

    def bake(rows, top):
        return [''.join(bg(top + y) if c == '.' else c for c in r) for y, r in enumerate(rows)]

    floors = {}                                              # Bodenhindernisse und Ziel
    anims = []
    prof2s = {}
    floorspecs = [("floor%d" % (i + 1), f) for i, f in enumerate(spec["floors"])] + [("finish", spec.get("finish"))]
    for key, f in floorspecs:
        if not f:
            continue
        pre = f["rows"]()
        h = len(pre)
        baked = bake(pre, 168 - h)
        an = f.get("anim")
        skip = set()
        if an:                                             # Kacheln, die sich zwischen Bild A und B unterscheiden
            bakedb = bake(an["rows_b"](), 168 - h)
            da, tw0, _ = to_tiles(baked, pal, f["name"])
            db, _, _ = to_tiles(bakedb, pal, f["name"] + "_b")
            diff = [i for i in range(len(da) // 32) if da[i * 32:(i + 1) * 32] != db[i * 32:(i + 1) * 32]]
            skip = set(diff)
        idx, tw, th = ts.add(f["name"], baked, skip)
        if an:
            first = None
            blob = b""
            for i in sorted(skip):                         # zusammenhängender Block, Bild A im Kachelarray
                n_ = ts.add_exclusive(da[i * 32:(i + 1) * 32])
                first = n_ if first is None else first
                idx[i] = n_
                blob += bytes(db[i * 32:(i + 1) * 32])
            anims.append((f, key, first, len(skip), blob))
        prof = profile(pre)
        hi = min(prof) - 30
        if an:
            prof2 = profile(an["rows_b"]())
            hi = min(hi, min(prof2) - 30)                  # die höhere der beiden Posen bestimmt den Korridor
            prof2s[key] = (prof2, len(anims))              # Animationsnummer = Position in der Liste (1-basiert)
        floors[key] = (f, idx, tw, th, prof, f.get("hi", hi))
    ceils = {}                                               # hängende Hindernisse
    for key in ("ceil1", "ceil2"):
        c = spec.get(key)
        if not c:
            continue
        pre = c["rows"]()
        top = c.get("top_row", 2) * 8
        idx, tw, th = ts.add(c["name"], bake(pre, top))
        prof = profile_bottom(pre, top)
        ceils[key] = (c, idx, tw, th, prof)
    n = len(ts.tiles)
    total = bg_base + n
    print(f"{spec['title']}: {n} Kacheln ab {bg_base} (insgesamt {total} von 448)")
    assert total <= 448, f"zu viele Kacheln in der Welt {ident}"
    size = n * 32 + 1100 + 2 * (256 + 12 + 28 + 100)
    assert size < 16384, f"Bank von {ident} zu groß"

    def arr(name, data, typ, per=16, fmt="%d"):
        s = f"const {typ} {name}[{len(data)}] = {{\n"
        for i in range(0, len(data), per):
            s += "  " + ", ".join(fmt % v for v in data[i:i + per]) + ",\n"
        return s + "};\n\n"

    c = (f"// GENERIERT von tools/gen_assets.py (Welt {spec['title']}) - nicht von Hand ändern.\n"
         f"// Liegt dank --constseg BANK{spec['bank']} in ROM-Bank {spec['bank']} (vor dem Zugriff SMS_mapROMBank).\n"
         f'#include "bank{spec["bank"]}.h"\n\n')
    c += arr(f"{ident}_pal", pal_bytes(pal), "unsigned char", 16, "0x%02X")
    c += arr(f"{ident}_tiles", list(b"".join(ts.tiles)), "unsigned char", 16, "0x%02X")
    c += arr(f"{ident}_band_map", band, "unsigned int", 16)
    c += arr(f"{ident}_far_map", far, "unsigned int", 16)
    for key, (f, idx, tw, th, prof, hi) in floors.items():
        c += arr(f"{ident}_{key}_map", idx, "unsigned int", tw)
        c += arr(f"{ident}_{key}_prof", prof, "unsigned char", 16)
        if key in prof2s:
            c += arr(f"{ident}_{key}_prof2", prof2s[key][0], "unsigned char", 16)
    for n_, (f_, key_, first_, cnt_, blob_) in enumerate(anims):
        c += arr(f"{ident}_anim{n_}_b", list(blob_), "unsigned char", 16, "0x%02X")
    for key, (cc, idx, tw, th, prof) in ceils.items():
        c += arr(f"{ident}_{key}_map", idx, "unsigned int", tw)
        c += arr(f"{ident}_{key}_prof", prof, "unsigned char", 16)

    def bld(key):
        if key not in floors:
            return "{ 0, 0, 0, 0, 137, 0, 0, 0, 0, 0 }"
        f, idx, tw, th, prof, hi = floors[key]
        sx, sy = f.get("shot", (0, 0))
        p2 = "%s_%s_prof2" % (ident, key) if key in prof2s else "0"
        aid = prof2s[key][1] if key in prof2s else 0
        return "{ %s_%s_map, %s_%s_prof, %d, %d, %d, %d, %d, %d, %s, %d }" % (
            ident, key, ident, key, tw, th, hi, sx, sy, f.get("shot_kind", 0), p2, aid)

    def cl(key):
        if key not in ceils:
            return "{ 0, 0, 0, 0, 0, 0, 0, 0 }"
        cc, idx, tw, th, prof = ceils[key]
        bx, by = cc.get("bolt", (0, 0))
        return "{ %s_%s_map, %s_%s_prof, %d, %d, %d, %d, %d, %d }" % (
            ident, key, ident, key, tw, th, cc.get("top_row", 2), max(prof) - 3, bx, by)

    fl = spec["flyer"]
    if fl is None:
        fly = "0, 0, 0, 0, 0, 0, 0, 0"
    else:
        tile = shared[fl["shared"]] if "shared" in fl else wsp[fl["sprite"]]
        hx0, hy0, hx1, hy1 = fl["hit"]
        fly = "%d, %d, %d, %d, %d, %d, %d, %d" % (tile, fl["w"], fl["h"], hx0, hy0, hx1, hy1, fl["fast"])
    gr = ["%d, %d, %d, %d" % tuple(ground[r * 4 + k] for k in range(4)) for r in range(3)]
    c += f"const World world_{ident} = {{\n"
    c += f"  {ident}_tiles, sizeof({ident}_tiles), {ident}_pal, {ident}_band_map,\n"
    c += "  { { %s }, { %s }, { %s } },\n" % tuple(gr)
    c += f"  {ident}_far_map,\n"
    c += "  { { 0, 0, 0, 0, 137, 0, 0, 0, 0, 0 },\n    %s },\n" % ",\n    ".join(
        [bld("floor%d" % (i + 1)) for i in range(6)] + [bld("finish")])
    c += "  { { 0, 0, 0, 0, 0, 0, 0, 0 },\n    %s,\n    %s },\n" % (cl("ceil1"), cl("ceil2"))
    c += "  { %s }, { %s },\n" % (", ".join(map(str, spec["kind_bld"])), ", ".join(map(str, spec["kind_ceil"])))
    def colbyte(v):
        return v if isinstance(v, int) else sms_byte(COLORS[v])
    c += "  0x%02X, 0x%02X, %d,\n" % (colbyte(spec["sky"]), colbyte(spec["flash"]), spec.get("special_finish", 0))
    c += "  %d, %d, %d, %d,\n" % tuple(spec["phys"])
    c += "  { %s },\n" % ", ".join(map(str, spec["wind"]))
    c += "  %d,\n" % spec["level_cols"]
    c += f"  {fly},\n"
    c += "  %d,\n" % spec["music"]
    sp = spec.get("setpieces", [])                       # [(Prozent, Index des Bodenhindernisses 1..6)]
    sp = list(sp) + [(0, 0)] * (2 - len(sp))
    c += "  { %d, %d }, { %d, %d },\n" % (sp[0][1], sp[1][1], sp[0][0], sp[1][0])
    ans = []
    for n_ in range(3):
        if n_ < len(anims):
            f_, key_, first_, cnt_, blob_ = anims[n_]
            ans.append("{ %d, %d, %s_anim%d_b }" % (cnt_, first_, ident, n_))
        else:
            ans.append("{ 0, 0, 0 }")
    c += "  { %s }\n};\n" % ", ".join(ans)
    open(os.path.join(ROOT, "src", f"bank{spec['bank']}.c"), "w").write(c)
    open(os.path.join(ROOT, "src", f"bank{spec['bank']}.h"), "w").write(
        f"// GENERIERT von tools/gen_assets.py - nicht von Hand ändern.\n#ifndef BANK{spec['bank']}_H\n#define BANK{spec['bank']}_H\n\n"
        f'#include "world.h"\n\nextern const World world_{ident};   // Daten liegen in ROM-Bank {spec["bank"]}\n\n#endif\n')


WORLD_MODULES = ["sea", "storm", "cave", "moon", "ny"]             # weitere Welten (jeweils Modul in tools/art mit SPEC), Reihenfolge = Spielreihenfolge


def emit_world_table(specs):
    """src/worlds_gen.h: Tabelle aller Welten (London zuerst) und ihrer ROM-Bänke."""
    s = "// GENERIERT von tools/gen_assets.py - nicht von Hand ändern.\n#ifndef WORLDS_GEN_H\n#define WORLDS_GEN_H\n\n"
    for sp in specs:
        s += f'#include "bank{sp["bank"]}.h"\n'
    s += f"\n#define NUM_WORLDS {len(specs) + 1}\n"
    s += "static const World *const worlds[NUM_WORLDS] = { &world_london" + "".join(f", &world_{sp['id']}" for sp in specs) + " };\n"
    s += "static const unsigned char world_bank[NUM_WORLDS] = { 0" + "".join(f", {sp['bank']}" for sp in specs) + " };   // ROM-Bank der Weltdaten (0 = Hauptspeicher)\n\n#endif\n"
    open(os.path.join(ROOT, "src", "worlds_gen.h"), "w").write(s)


def main():
    spr_tiles = bytearray(32)  # Tile 0: leer
    bg_tiles = bytearray()
    defines = []
    objs = []  # fürs Preview: (rows, pal)
    spr_next = 1
    bg_next = 0

    def add_spr(name, rows):
        nonlocal spr_next
        data, tw, th = to_tiles(rows, SPRITE_PAL, name)
        defines.append((name.upper(), spr_next, tw, th))
        spr_tiles.extend(data)
        spr_next += tw * th

    seen = {}      # Dedupe: gleiche Tiles nur einmal ins VRAM
    maps = []      # (NAME, Breite, Höhe, Tile-Nummern zeilenweise)

    def add_bg(name, rows):
        nonlocal bg_next
        data, tw, th = to_tiles(rows, BG_PAL, name)
        idx = []
        for i in range(tw * th):
            t = bytes(data[i * 32:(i + 1) * 32])
            if not any(t):
                idx.append(0)          # leeres Tile = Tile 0 (Himmel)
                continue
            if t not in seen:
                seen[t] = bg_next
                bg_tiles.extend(t)
                bg_next += 1
            idx.append(seen[t])
        maps.append((name.upper(), tw, th, idx))

    for name, rows in SPRITES:
        add_spr(name, rows)
        objs.append(rows)

    spr_font_start = spr_next      # Font auch für Sprites (HUD, Texte über dem scrollenden Hintergrund)
    for ch in FONT_ORDER:
        data, _, _ = to_tiles(font_tile(ch), SPRITE_PAL, "sprite font " + ch)
        spr_tiles.extend(data)
        spr_next += 1

    bg_base = spr_next            # Hintergrund-Tiles beginnen direkt hinter den Sprite-Tiles
    bg_next = bg_base
    font_start = bg_next
    for ch in FONT_ORDER:
        data, _, _ = to_tiles(font_tile(ch), BG_PAL, "font " + ch)
        bg_tiles.extend(data)
        bg_next += 1

    for name, rows in BG_OBJECTS:
        add_bg(name, rows)
        objs.append(rows)

    assert spr_next <= 256, f"{spr_next} Sprite-Tiles: zu viele für die erste Hälfte"
    assert bg_next <= 448, f"{bg_next} Tiles: ab Tile 448 liegen Tilemap und Sprite-Tabelle im VRAM"
    with open(os.path.join(ROOT, "res", "generated", "assets.h"), "w") as f:
        f.write("// GENERIERT von tools/gen_assets.py - nicht von Hand ändern\n#pragma once\n\n#include \"world.h\"\n\n")
        f.write(f"#define FONT_TILE_START {font_start}\n#define BG_TILE_BASE {bg_base}\n#define SPR_FONT_START {spr_font_start}\n\n")
        f.write("// Objekte: erstes Tile, Breite und Höhe in Tiles (Tiles zeilenweise)\n")
        for n, start, w, h in defines:
            f.write(f"#define {n} {start}\n#define {n}_W {w}\n#define {n}_H {h}\n")
        f.write("\n// Hintergrundobjekte: Tile-Nummern zeilenweise (gleiche Tiles sind zusammengelegt)\n")
        for n, w, h, idx in maps:
            f.write(f"#define {n}_W {w}\n#define {n}_H {h}\n")
            f.write(f"static const unsigned int {n.lower()}_map[] = {{\n")
            for i in range(0, len(idx), 16):
                f.write("  " + ", ".join(str(v) for v in idx[i:i + 16]) + ",\n")
            f.write("};\n")
        f.write("\n")
        f.write(c_array("sprite_palette", pal_bytes(SPRITE_PAL)))
        f.write(c_array("bg_palette", pal_bytes(BG_PAL)))
        f.write(c_array("sprite_tiles", list(spr_tiles)))
        f.write(c_array("bg_tiles", list(bg_tiles)))
        f.write(london_world(maps))

    # Vorschau: alles auf Himmelblau, 4-fach vergrößert (Sprites mit Sprite-, Rest mit BG-Palette)
    sky = rgb8(COLORS['a'])
    W = 340
    canvas = [[sky] * W for _ in range(100)]
    x = y = 4
    rowh = 0
    for rows in objs:
        w, h = len(rows[0]), len(rows)
        if x + w > W:
            x, y, rowh = 4, y + rowh + 4, 0
        while y + h > len(canvas):
            canvas.append([sky] * W)
        blit(canvas, rows, x, y, sky)
        x += w + 4
        rowh = max(rowh, h)
    os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
    big = scale(canvas, 4)
    write_png(os.path.join(ROOT, "out", "art_preview.png"), len(big[0]), len(big), big)
    shared = {n: start for n, start, _, _ in defines}
    specs = []
    for modname in WORLD_MODULES:
        spec = __import__(modname).SPEC
        emit_world(spec, bg_base, shared)
        specs.append(spec)
    emit_world_table(specs)
    print(f"Sprites: {spr_next} Tiles, Hintergrund: {bg_next - bg_base} Tiles, insgesamt {bg_next} von 448. Vorschau: out/art_preview.png")


if __name__ == "__main__":
    main()
