#!/usr/bin/env python3
"""Kontaktbogen der Kandidatenbilder: python3 tools/contact.py WELT INTERVALL -> out/cand/sheet_w<WELT>.png (Beschriftung = Sekunde)."""
import sys, glob
from PIL import Image, ImageDraw
w, every = sys.argv[1], float(sys.argv[2])
files = sorted(glob.glob(f"out/cand/w{w}/c*.png"))
cols, tw, th = 4, 384, 288
rows = (len(files) + cols - 1) // cols
sheet = Image.new("RGB", (cols * tw, rows * th), (30, 30, 30))
d = ImageDraw.Draw(sheet)
for i, f in enumerate(files):
    im = Image.open(f).resize((tw, th), Image.NEAREST)
    sheet.paste(im, ((i % cols) * tw, (i // cols) * th))
    d.rectangle((i % cols * tw, i // cols * th, i % cols * tw + 70, i // cols * th + 16), fill=(0, 0, 0))
    d.text((i % cols * tw + 3, i // cols * th + 2), f"{i * every:.0f}s", fill=(255, 255, 0))
sheet.save(f"out/cand/sheet_w{w}.png")
print(len(files), "Bilder")
