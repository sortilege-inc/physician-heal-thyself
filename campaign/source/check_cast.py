#!/usr/bin/env python3
"""Check the cast layer against the export, sharing no code with convert_cast.py.

    python3 campaign/source/check_cast.py

Parses campaign/dsl/pht-0.5-cast.ttrpg with the VTT's own DSL parser (build/parse_dsl.py) and
re-derives every value from the Notion export by a different road:

  Maggie Molyneux   Attributes and Skills from her page's two sub-tables (the CSVs Notion exports
                    beside the page, laid out in another order), the rest from her page's text
  Fatima            every value from the root page, read cell by cell with an HTML parser

Checks: every Attribute; every Skill the source rates above 0 is written with that rating, and
none rated 0 is written; each Discipline and its dots; Clan, Generation, Blood Potency, Predator;
Health and Willpower as the sums of the printed terms; nothing written that the source lacks.
Prints the number of checks; exits 1 naming each mismatch.
"""
import csv, re, sys
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(REPO / 'build'))
from parse_dsl import parse_path  # noqa: E402

NOTION = HERE / 'notion' / 'Physician, Heal Thyself'
LAYER = HERE.parent / 'dsl' / 'pht-0.5-cast.ttrpg'
ATTR = {'Strength', 'Dexterity', 'Stamina', 'Charisma', 'Manipulation', 'Composure', 'Intelligence', 'Wits', 'Resolve'}


class Cells(HTMLParser):
    """The page's text as a list of lines, one per block element."""
    BLOCK = {'p', 'div', 'li', 'tr', 'td', 'th', 'h1', 'h2', 'h3', 'summary', 'br'}

    def __init__(self):
        super().__init__(convert_charrefs=True); self.lines = ['']

    def handle_starttag(self, tag, a):
        if tag in self.BLOCK: self.lines.append('')

    def handle_endtag(self, tag):
        if tag in self.BLOCK: self.lines.append('')

    def handle_data(self, d):
        self.lines[-1] += d


def lines(path):
    c = Cells(); c.feed(path.read_text(encoding='utf-8'))
    return [' '.join(x.split()) for x in c.lines if x.strip()]


def pairs(s):
    return [(a.strip(), int(b)) for a, b in re.findall(r'([A-Za-z][A-Za-z ]*?)\s*\((\d)\)', s)]


def from_lines(ls):
    """A stat block's lines → {label: value}, the rated traits, and the discipline list."""
    out, rated = {}, {}
    for l in ls:
        for k in ('CLAN', 'GENERATION', 'BLOOD POTENCY', 'PREDATOR TYPE', 'DISCIPLINES'):
            m = re.search(k + r':\s*(.*?)(?=\s+[A-Z]{4,}[A-Z ]*:|$)', l)
            if m: out[k] = m.group(1)
        for k in ('HEALTH', 'WILLPOWER'):
            m = re.search(k + r':\s*(\d+)\s*\+\s*(\d+)', l)
            if m: out[k] = int(m.group(1)) + int(m.group(2))
        if 'DISCIPLINES' not in l:
            rated.update(dict(pairs(l)))
    out['DISCIPLINES'] = pairs(out['DISCIPLINES'])
    return out, rated


def expected():
    exp = {}
    (mp,) = (NOTION / 'VtM NPCs').glob('Maggie Molyneux *.html')
    ls = lines(mp)
    info, _ = from_lines(ls[ls.index('Stats'):])
    rated = {}
    for t in sorted((mp.parent / mp.stem.rsplit(' ', 1)[0]).glob('*.csv')):
        for row in csv.reader(open(t, encoding='utf-8-sig')):
            for cell in row:
                rated.update(dict(pairs(cell)))
    exp['Maggie Molyneux'] = (info, rated)
    (rp,) = NOTION.parent.glob('Physician, Heal Thyself *.html')
    ls = lines(rp)
    i = next(k for k, l in enumerate(ls) if l.startswith('Fatima ('))
    j = ls.index('Game Lore Notes', i)
    block = ls[i:j]
    info, rated = from_lines(block)
    info['CLAN'] = re.search(r'CLAN:\s*(\w+)', ' '.join(block)).group(1)
    exp['Fatima'] = (info, rated)
    return exp


def written():
    got = {}
    tree = parse_path(str(LAYER))

    def walk(n):
        if isinstance(n, dict):
            if n.get('n') == 'entity':
                props = {}
                for b in n.get('body', []):
                    if isinstance(b, dict) and b.get('n') == 'prop':
                        props[b.get('name')] = b.get('value')
                got[n['name']] = props
            for v in n.values():
                walk(v)
        elif isinstance(n, list):
            for v in n:
                walk(v)
    walk(tree)
    return got


def main():
    exp, got = expected(), written()
    bad, n = [], 0

    def eq(who, what, want, have):
        nonlocal n
        n += 1
        if str(want) != str(have):
            bad.append(f'{who} · {what}: source {want!r}, written {have!r}')

    if set(exp) != set(got):
        bad.append(f'people: source {sorted(exp)}, written {sorted(got)}')
    for who, (info, rated) in exp.items():
        g = got.get(who, {})
        eq(who, 'Clan', info['CLAN'], g.get('Clan'))
        eq(who, 'Generation', info['GENERATION'], g.get('Generation'))
        eq(who, 'Blood Potency', re.match(r'\d+', info['BLOOD POTENCY']).group(0), g.get('Blood Potency'))
        eq(who, 'Predator', re.sub(r'\s*\(.*', '', info['PREDATOR TYPE']), g.get('Predator'))
        eq(who, 'Secondary Attributes', f"Health {info['HEALTH']}, Willpower {info['WILLPOWER']}", g.get('Secondary Attributes'))
        wa = dict(pairs(re.sub(r'(\w+) (\d)', r'\1 (\2)', g.get('Attributes', ''))))
        ws = dict(pairs(re.sub(r'([A-Za-z ]+?) (\d)', r'\1 (\2)', g.get('Skills', ''))))
        wd = pairs(re.sub(r'([A-Za-z ]+?) (\d)', r'\1 (\2)', g.get('Disciplines', '')))
        for a in sorted(ATTR):
            eq(who, a, rated.get(a), wa.get(a))
        skills = {k: v for k, v in rated.items() if k not in ATTR}
        for k, v in sorted(skills.items()):
            eq(who, k, v if v > 0 else None, ws.get(k))
        for k in set(ws) - set(skills):
            bad.append(f'{who} · {k}: written {ws[k]}, not in the source')
        eq(who, 'Disciplines', info['DISCIPLINES'], wd)
    if bad:
        print('\n'.join('MISMATCH ' + b for b in bad)); print(f'check_cast: {len(bad)} mismatch(es) in {n} checks'); sys.exit(1)
    print(f'check_cast: {n} checks, all match')


if __name__ == '__main__':
    main()
