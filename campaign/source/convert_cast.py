#!/usr/bin/env python3
"""The cast's stat blocks, from the Notion export into the campaign's DSL layer.

    python3 campaign/source/convert_cast.py

Writes campaign/dsl/pht-0.5-cast.ttrpg. Only the people the export gives a full stat block
(owner, 2026-09-25): Maggie Molyneux (her NPC page's *Stats*) and Fatima (the root page's
*Relationship Map*). Each is written in the corpus's own Storyteller-character labels (Clan,
Generation, Blood Potency, Predator, Attributes, Secondary Attributes, Skills, Disciplines), so the
VTT reads them as characters. Values are the page's; two are sums of what the page prints:
HEALTH "3 + 3" is written Health 6, WILLPOWER "3 + 1" Willpower 4. A Skill the page rates 0 is
left out, as the books leave it out. The page reference ("(pg.216)", "(Core pg.177)") is dropped.
Never edit the .ttrpg by hand; change this and rerun. check_cast.py checks the result.
"""
import hashlib, html, re, string, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTION = HERE / 'notion' / 'Physician, Heal Thyself'
OUT = HERE.parent / 'dsl' / 'pht-0.5-cast.ttrpg'
CAST_VERSION = '0.1.0'

ATTRS = [['Strength', 'Dexterity', 'Stamina'], ['Charisma', 'Manipulation', 'Composure'], ['Intelligence', 'Wits', 'Resolve']]


def page_text(path):
    s = path.read_text(encoding='utf-8')
    s = re.sub(r'<style.*?</style>', '', s, flags=re.S)
    s = re.sub(r'<(br|/p|/h\d|/li|/tr|/div|/td|/th|/summary)[^>]*>', '\n', s)
    return html.unescape(re.sub(r'<[^>]+>', ' ', s))


def block(text, start, end):
    i = text.index(start)
    j = text.index(end, i) if end else len(text)
    return text[i:j]


def stat_block(text):
    """The printed block → its values, exactly as printed."""
    one = lambda label: re.search(label + r':\s*([^\n]+?)\s*(?:\n|$|[A-Z]{4,}:)', text).group(1).strip()
    traits = {m.group(1): int(m.group(2)) for m in re.finditer(r'([A-Z][a-z]+(?: [A-Z][a-z]+)?) \((\d)\)', text)}
    h = re.search(r'HEALTH:\s*(\d+)\s*\+\s*(\d+)', text)
    w = re.search(r'WILLPOWER:\s*(\d+)\s*\+\s*(\d+)', text)
    disc = re.search(r'DISCIPLINES:\s*([^\n]+)', text).group(1)
    return {
        'Clan': one('CLAN'),
        'Generation': one('GENERATION'),
        'Blood Potency': re.search(r'BLOOD POTENCY:\s*(\d+)', text).group(1),
        'Predator': re.search(r'PREDATOR TYPE:\s*([^(\n]+?)\s*\(', text).group(1),
        'traits': traits,
        'health': int(h.group(1)) + int(h.group(2)),
        'willpower': int(w.group(1)) + int(w.group(2)),
        'disciplines': [(m.group(1), int(m.group(2))) for m in re.finditer(r'([A-Z][\w ]+?) \((\d)\)', disc)],
    }


def hash_id(name):
    digest = int(hashlib.sha256(('pht-cast/' + name).encode()).hexdigest(), 16)
    alpha = string.digits + string.ascii_letters
    out = ''
    while len(out) < 16:
        digest, r = divmod(digest, 62); out += alpha[r]
    return '#pht' + out


def q(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


def entity(name, desc, source, v):
    t = v['traits']
    attrs = '; '.join(', '.join(f'{a} {t[a]}' for a in group) for group in ATTRS)
    discs = {d for d, _ in v['disciplines']}
    secondary = f"Health {v['health']}, Willpower {v['willpower']}"
    skills = sorted((k, n) for k, n in t.items() if k not in sum(ATTRS, []) and k not in discs and n > 0)
    lines = [
        f'    {hash_id(name)} ^{q(name)} DEF {{',
        f'        DESCRIPTION {q(desc)}',
        f'        # source: {source}',
        f'        ^"Clan" STRING {q(v["Clan"])}',
        f'        ^"Generation" STRING {q(v["Generation"])}',
        f'        ^"Blood Potency" STRING {q(v["Blood Potency"])}',
        f'        ^"Predator" STRING {q(v["Predator"])}',
        f'        ^"Attributes" STRING {q(attrs)}',
        f'        ^"Secondary Attributes" STRING {q(secondary)}',
        f'        ^"Skills" STRING {q(", ".join(f"{k} {n}" for k, n in skills))}',
        f'        ^"Disciplines" STRING {q(", ".join(f"{d} {n}" for d, n in v["disciplines"]))}',
        '    }',
    ]
    return '\n'.join(lines)


def cast():
    (maggie,) = (NOTION / 'VtM NPCs').glob('Maggie Molyneux *.html')
    (root,) = NOTION.parent.glob('Physician, Heal Thyself *.html')
    mt = page_text(maggie)
    rt = page_text(root)
    fat = block(rt, 'Fatima (', 'Game Lore Notes')
    head = re.match(r'Fatima \(([^)]*)\):\s*(\w+)', fat)
    import csv
    (table,) = NOTION.glob('VtM NPCs *.csv')
    title = next(r['Title'] for r in csv.DictReader(open(table, encoding='utf-8-sig')) if r['Name'] == 'Maggie Molyneux')
    return [
        ('Maggie Molyneux', title, f'VtM NPCs/{maggie.name}, Stats', stat_block(block(mt, 'Stats', None))),
        ('Fatima', head.group(2), f'{root.name}, Relationship Map', stat_block(fat)),
    ]


def main():
    ents = [entity(*c) for c in cast()]
    text = '\n'.join([
        'EXTENSION "pht-cast" EXTENDS "vtm5e" {',
        '    NAME "Physician, Heal Thyself - the cast"',
        f'    VERSION "{CAST_VERSION}"',
        '    SPEC_VERSION "0.5"',
        '    RELEASE_DATE "2026-09-25"',
        '',
        '    # Generated by campaign/source/convert_cast.py from campaign/source/notion — do not edit by hand.',
        '    # The two people the Notion export gives a full stat block (owner, 2026-09-25).',
        '',
        '\n\n'.join(ents),
        '}',
        '',
    ])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding='utf-8')
    print(f'cast: {len(ents)} characters → {OUT.relative_to(HERE.parent.parent)} (CAST_VERSION {CAST_VERSION})')


if __name__ == '__main__':
    main()
