#!/usr/bin/env python3
"""The portraits: each reference image in the Notion export, cut to a 4:5 card with torn edges.

    python3 campaign/build/build_portraits.py

Reads the Coterie and VtM NPCs tables in campaign/source/notion/, takes each row's Portrait, crops
it to 4:5 (centred across, a little above centre down, where faces sit), and tears the edges: a
ragged outer edge, then a band of pale paper fibre, then the image. The tear is seeded by the
person's name, so a rebuild is byte-identical. Writes campaign/assets/portraits/<slug>.webp (alpha)
and fails if a row names a portrait that is not in the export, or a slug is taken twice. The
clan mark that overlaps the corner is drawn by the page (campaign/site/campaign.css), not baked in.
"""
import csv, hashlib, math, random, re, sys, unicodedata, urllib.parse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parents[1]
NOTION = HERE / 'source' / 'notion'
OUT = HERE / 'assets' / 'portraits'
W, H = 480, 600
PAPER = (236, 238, 240)
MARKS = {'second-inquisition': 'Physician, Heal Thyself/VtM NPCs/Patricia Cornell/SymbolSecondInquisition.png'}


def slug(name):
    s = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')


def tables():
    for pat in ('Coterie *.csv', 'VtM NPCs *.csv'):
        (path,) = (NOTION / 'Physician, Heal Thyself').glob(pat)
        yield from csv.DictReader(open(path, encoding='utf-8-sig'))


def wander(rng, n, big, small):
    """n offsets along one edge: a slow wander (a few long waves) plus fine fibre, all >= 0."""
    waves = [(rng.uniform(0.6, 2.6), rng.uniform(0, 6.283), rng.uniform(0.3, 1.0)) for _ in range(4)]
    out, fib = [], 0.0
    for i in range(n):
        t = i / n
        slow = sum(a * math.sin(6.283 * f * t + ph) for f, ph, a in waves) / 2.2   # about -1..1
        fib = 0.55 * fib + rng.uniform(-1, 1)                                        # rough, correlated grain
        out.append(max(0.0, big * (0.5 + 0.5 * slow) + small * (0.5 + 0.5 * fib)))
    return out


def ragged(rng, inset, big, small, step=3):
    """A closed outline `inset` px inside the card, each side torn along its own wander."""
    pts = []
    sides = [((inset, inset), (W - inset, inset), (0, 1)), ((W - inset, inset), (W - inset, H - inset), (-1, 0)),
             ((W - inset, H - inset), (inset, H - inset), (0, -1)), ((inset, H - inset), (inset, inset), (1, 0))]
    for (x0, y0), (x1, y1), (nx, ny) in sides:
        n = max(2, int(max(abs(x1 - x0), abs(y1 - y0)) / step))
        for i, d in enumerate(wander(rng, n, big * rng.uniform(0.5, 1.3), small)):
            t = i / n
            pts.append((x0 + (x1 - x0) * t + nx * d, y0 + (y1 - y0) * t + ny * d))
    return pts


def tear(img, name):
    rng = random.Random(hashlib.sha256(name.encode()).hexdigest())
    outer, inner = Image.new('L', (W, H), 0), Image.new('L', (W, H), 0)
    ImageDraw.Draw(outer).polygon(ragged(rng, 2, 14, 4), fill=255)
    ImageDraw.Draw(inner).polygon(ragged(rng, 10, 16, 5), fill=255)
    outer = outer.filter(ImageFilter.GaussianBlur(0.8))
    inner = inner.filter(ImageFilter.GaussianBlur(0.6))
    card = Image.new('RGBA', (W, H), PAPER + (0,))
    card.paste(Image.new('RGBA', (W, H), PAPER + (255,)), (0, 0), outer)
    card.paste(img.convert('RGBA'), (0, 0), inner)
    card.putalpha(outer)
    return card


def crop45(img):
    w, h = img.size
    if w / h > W / H:                      # too wide: centre across
        nw = round(h * W / H); x = (w - nw) // 2
        box = (x, 0, x + nw, h)
    else:                                  # too tall: keep the upper part, where faces sit
        nh = round(w * H / W); y = round((h - nh) * 0.3)
        box = (0, y, w, y + nh)
    return img.crop(box).resize((W, H), Image.LANCZOS)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    seen, made = {}, []
    for row in tables():
        name, rel = row['Name'], row['Portrait']
        if not rel:
            continue
        src = NOTION / urllib.parse.unquote(rel)
        if not src.is_file():
            sys.exit(f'{name}: portrait {src} is not in the export')
        s = slug(name)
        if s in seen:
            sys.exit(f'{name}: slug {s!r} already taken by {seen[s]}')
        seen[s] = name
        img = Image.open(src)
        img = img.convert('RGBA') if img.mode in ('P', 'LA', 'RGBA') else img.convert('RGB')
        if img.mode == 'RGBA':             # transparent source art sits on the paper
            bg = Image.new('RGB', img.size, PAPER); bg.paste(img, (0, 0), img); img = bg
        tear(crop45(img), name).save(OUT / f'{s}.webp', 'WEBP', quality=82, method=6)
        made.append(s)
    stale = [p.name for p in OUT.glob('*.webp') if p.stem not in seen]
    if stale:
        sys.exit(f'portraits no table row names: {stale}')
    # the one mark the VTT's art does not carry: AURORA's (the Second Inquisition's), from the export
    marks = HERE / 'assets' / 'marks'
    marks.mkdir(parents=True, exist_ok=True)
    for name, rel in MARKS.items():
        Image.open(NOTION / rel).convert('RGBA').save(marks / f'{name}.webp', 'WEBP', lossless=True)
    print(f'portraits: {len(made)} written to {OUT.relative_to(HERE.parent)}; marks: {len(MARKS)}')


if __name__ == '__main__':
    main()
