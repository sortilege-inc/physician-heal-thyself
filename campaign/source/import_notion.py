#!/usr/bin/env python3
"""Take the owner's Notion export of the chronicle into campaign/source/notion/.

    python3 campaign/source/import_notion.py "<export>/Private & Shared"

Every file is copied byte for byte, except:
  - the consent checklists (the page and its folder) — players' personal data, never in the repo;
  - the players' names — the `Player` property row on each Coterie page and the `Player` column
    of the Coterie table, removed and nothing else touched.
Each file's fate is written to notion/MANIFEST.tsv (copied / redacted / excluded, with the reason),
and the run fails if a player's name survives anywhere in what was written.
"""
import csv, io, re, shutil, sys
from pathlib import Path

ROOT = 'Physician, Heal Thyself'
OUT = Path(__file__).resolve().parent / 'notion'
EXCLUDE = re.compile(r'(^|/)Consent Checklists( [0-9a-f]{32}\.html$|/)')
PLAYER_ROW = re.compile(r'<tr class="property-row property-row-text"><th>(?:(?!</th>).)*?</span>Player</th><td>([^<]*)</td></tr>')


def main(src):
    src = Path(src)
    if not (src / ROOT).is_dir():
        sys.exit(f'no {ROOT!r} under {src}')
    if OUT.exists():
        shutil.rmtree(OUT)
    rows, names = [], set()
    files = sorted(p for p in src.rglob('*') if p.is_file())
    for p in files:
        rel = p.relative_to(src).as_posix()
        if EXCLUDE.search(rel):
            rows.append((rel, 'excluded', 'consent checklist: players’ personal data'))
            continue
        dest = OUT / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if rel.startswith(ROOT + '/Coterie/') and rel.endswith('.html') and rel.count('/') == 2:
            text = p.read_text(encoding='utf-8')
            found = PLAYER_ROW.findall(text)
            if len(found) != 1:
                sys.exit(f'{rel}: expected one Player row, found {len(found)}')
            names.update(n for n in found if n)
            dest.write_text(PLAYER_ROW.sub('', text), encoding='utf-8')
            rows.append((rel, 'redacted', 'the Player property row removed'))
        elif re.fullmatch(re.escape(ROOT) + r'/Coterie [0-9a-f]{32}\.csv', rel):
            text = p.read_text(encoding='utf-8-sig')
            table = list(csv.reader(io.StringIO(text)))
            col = table[0].index('Player')
            names.update(r[col] for r in table[1:] if r[col])
            buf = io.StringIO()
            csv.writer(buf, lineterminator='\n').writerows([r[:col] + r[col + 1:] for r in table])
            dest.write_text('﻿' + buf.getvalue(), encoding='utf-8')
            rows.append((rel, 'redacted', 'the Player column removed'))
        else:
            shutil.copyfile(p, dest)
            rows.append((rel, 'copied', ''))
    with open(OUT / 'MANIFEST.tsv', 'w', encoding='utf-8') as f:
        f.write('file\tfate\treason\n')
        f.writelines('\t'.join(r) + '\n' for r in rows)
    # the proof: no player's name in anything written (the GM's own name is in the notes as he wrote them)
    players = sorted(n for n in names if n != 'Jordan')
    leak = [str(q.relative_to(OUT)) for q in OUT.rglob('*') if q.suffix in ('.html', '.csv')
            for n in players if re.search(r'\b' + re.escape(n) + r'\b', q.read_text(encoding='utf-8-sig'))]
    if leak:
        sys.exit(f'a player name survives in: {leak}')
    counts = {k: sum(1 for r in rows if r[1] == k) for k in ('copied', 'redacted', 'excluded')}
    print(f'notion: {len(files)} files — {counts}; players redacted: {len(players)}; 0 names remain')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '')
