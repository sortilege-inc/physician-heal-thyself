#!/usr/bin/env python3
"""The Storyteller's material: every page of the Notion export, into the GM tabs' pack.

    python3 campaign/build/build_seed.py

Writes campaign/pack/seed.json — a campaign pack (engine/state.js seed) whose `gm` key fills the
GM tabs the first time the Storyteller opens /gm/ (and fills only what they have never had: a
section they edit or remove stays theirs). All of it, word for word, in the tabs' own small
Markdown (engine/gm-text.js):

  gm.overview  the chronicle's root page (the sects, the GM's to-dos, tools and notes, the rules
               crib, the lore, the names) and *The Story Coming Up*; a heading starts a section,
               a toggle is a subsection
  gm.people    every page of the VtM NPCs table (Baruch Espinosa's too), its table fields first
  gm.pc        every Coterie page, whole — the GM To-Do sections included

The public site (build_docs.py) shows the players' part; nothing here is sent to players (the gm
key's ops are local, engine/gm-text.js). The gate is build_docs.py's: each page's words, read from
the raw HTML, must equal the words written here, as multisets.
"""
import csv, hashlib, html, json, re, sys, urllib.parse
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_docs as B  # noqa: E402
from build_docs import Node, find, words, body, flat_blocks, NOTION  # noqa: E402

OUT = B.HERE / 'pack' / 'seed.json'
IMG = '↗ image'                   # an image's link text, not counted as the page's words
# the cast layer's records (campaign/dsl), so a person's GM notes show on their record in the Inspector
CAST = re.findall(r'^\s*(#pht\w+) \^"([^"]+)" DEF', (B.HERE / 'dsl' / 'pht-0.5-cast.ttrpg').read_text(encoding='utf-8'), re.M)


def sid(*parts):
    return 'pht-' + hashlib.sha256('/'.join(parts).encode()).hexdigest()[:12]


class MD:
    """A subtree → the GM tabs' Markdown: paragraphs, `- ` lists, `> ` quotes, **bold**, *italic*, links."""

    def __init__(self, page, base):
        self.page, self.base = page, base

    def inline(self, n):
        if isinstance(n, str):
            return re.sub(r'\s+', ' ', n)
        t = n.tag
        if t in ('style', 'script', 'input'):
            return ''
        if t == 'br':
            return '\n'
        if t == 'img':
            src = n.attrs.get('src', '')
            if src.startswith('http'):
                return ''
            url = self.page.image(src, self.base)
            return f' [{IMG}]({url}) ' if url else ''
        inner = ''.join(self.inline(k) for k in n.kids)
        if t in ('strong', 'b') and inner.strip():
            return f' **{inner.strip()}** '
        if t in ('em', 'i') and inner.strip():
            return f' *{inner.strip()}* '
        if t == 'a':
            href = html.unescape(n.attrs.get('href', ''))
            if re.match(r'https?://', href) and 'notion.' not in href:
                return f'[{inner.strip() or href}]({href})'
            if href.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.pdf')):
                url = self.page.image(href, self.base)
                return f'[{inner.strip()}]({url})' if url else inner
        if t in ('div', 'p', 'li', 'ul', 'ol', 'h1', 'h2', 'h3', 'h4', 'figure', 'blockquote', 'tr', 'td', 'th', 'summary', 'details', 'figcaption'):
            return f' {inner} '
        return inner

    def blocks(self, n, out):
        """Append the subtree's paragraphs (strings) to out."""
        if isinstance(n, str):
            if n.strip():
                out.append(n.strip())
            return
        t = n.tag
        if t in ('style', 'script') or t == 'nav' or 'table_of_contents' in n.cls():
            return
        if t in ('p', 'h1', 'h2', 'h3', 'h4', 'figcaption'):
            s = self.inline(n).strip()
            if s:
                out.append(f'**{s}**' if t.startswith('h') else s)
            return
        if t in ('ul', 'ol'):
            items = []
            for li in n.kids:
                if isinstance(li, Node) and li.tag == 'li':
                    head = ''.join(self.inline(k) for k in li.kids if not (isinstance(k, Node) and k.tag in ('ul', 'ol', 'details', 'p')))
                    mark = '[x] ' if find(li, lambda x: x.tag == 'input' and 'checked' in x.attrs) else ''
                    items.append('- ' + mark + ' '.join(head.split()))
                    rest = []
                    for k in li.kids:
                        if isinstance(k, Node) and k.tag in ('ul', 'ol', 'details', 'p'):
                            self.blocks(k, rest)
                    items.extend('- ' + ' '.join(r.replace('- ', '', 1).split()) if not r.startswith('- ') else r for r in rest)
            if items:
                out.append('\n'.join(items))
            return
        if t == 'blockquote':
            sub = []
            for k in n.kids:
                self.blocks(k, sub) if isinstance(k, Node) and k.tag in ('p', 'ul', 'ol') else sub.append(self.inline(k))
            s = '\n'.join(x.strip() for x in sub if x.strip())
            if s:
                out.append('\n'.join('> ' + l for l in s.split('\n')))
            return
        if t == 'details':
            summ = find(n, lambda x: x.tag == 'summary')
            if summ:
                s = self.inline(summ).strip()
                if s:
                    out.append(f'**{s}**')
            for k in n.kids:
                if k is not summ:
                    self.blocks(k, out)
            return
        if t == 'table':
            rows = []
            for tr in [x for x in iter_nodes(n) if x.tag == 'tr']:
                cells = [' '.join(self.inline(c).split()) for c in tr.kids if isinstance(c, Node) and c.tag in ('td', 'th')]
                if any(cells):
                    rows.append('- ' + ' · '.join(c for c in cells if c))
            if rows:
                out.append('\n'.join(rows))
            return
        if t == 'figure':
            s = ' '.join(self.inline(n).split())
            if s:
                out.append(s)
            return
        for k in n.kids:
            self.blocks(k, out)


def iter_nodes(n):
    if isinstance(n, Node):
        yield n
        for k in n.kids:
            yield from iter_nodes(k)


def sectioned(nodes, md, key):
    """Blocks → sections: h1/h2 start a section; a top-level toggle or an h3 is a subsection."""
    secs, cur, sub = [], None, None

    def new(title):
        nonlocal cur, sub
        cur = {'id': sid(key, str(len(secs)), title), 'title': title, 'text': '', 'sections': []}
        secs.append(cur); sub = None

    def add(paras):
        tgt = sub if sub is not None else cur
        tgt['text'] = '\n\n'.join(x for x in [tgt['text']] + paras if x)

    for n in nodes:
        if isinstance(n, Node) and n.tag in ('h1', 'h2'):
            new(' '.join(md.inline(n).replace('**', ' ').split()).rstrip(':') or 'Notes'); continue
        if cur is None:
            new(key.split('/')[-1]); cur['synthetic'] = True
        if isinstance(n, Node) and (n.tag == 'h3' or (n.tag == 'details')):
            summ = n if n.tag == 'h3' else find(n, lambda x: x.tag == 'summary')
            title = ' '.join(md.inline(summ).replace('**', ' ').split()) if summ else 'Notes'
            sub = {'id': sid(key, str(len(secs)), str(len(cur['sections'])), title), 'title': title, 'text': ''}
            cur['sections'].append(sub)
            if n.tag == 'details':
                paras = []
                for k in n.kids:
                    if k is not summ:
                        md.blocks(k, paras)
                add(paras)
            continue
        paras = []
        md.blocks(n, paras)
        add(paras)
    for s in secs:
        if not s['sections']:
            del s['sections']
    return secs


def counted(secs):
    """The words the tabs will show: titles and text, link targets and image labels left out."""
    c = Counter()
    for s in secs:
        for part in [s['title'] if not s.get('synthetic') else '', s.get('text', '')] + [x for ss in s.get('sections', []) for x in (ss['title'], ss['text'])]:
            part = re.sub(r'\[' + IMG + r'\]\([^)]*\)', ' ', part).replace('[x] ', '')
            part = re.sub(r'^(?:- |> )+', '', part, flags=re.M)
            part = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', part)
            c.update(words(part.replace('**', ' ').replace('*', ' ')))
    return c


def check(name, path, secs, extra=Counter()):
    has_body = '<div class="page-body"' in path.read_text(encoding='utf-8')
    raw, got = (B.raw_words(path) if has_body else Counter()), counted(secs)
    nav = Counter(w for n in iter_nodes(B.parse(path)) if n.tag == 'nav' for w in words(n.spaced()))
    raw = raw - nav
    if raw + extra != got:
        miss, more = (raw + extra) - got, got - (raw + extra)
        sys.exit(f'{name}: words differ — missing {dict(list(miss.items())[:12])} extra {dict(list(more.items())[:12])}')


def page_sections(path, key, lead=None):
    page = B.Page(key, public=False)
    md = MD(page, path.parent)
    b = body(path)
    secs = sectioned(flat_blocks(b), md, key) if b else []
    if not secs:
        secs = [{'id': sid(key, '0'), 'title': key.split('/')[-1], 'text': '', 'synthetic': True}]
    if lead:
        secs[0]['text'] = '\n'.join(lead) + ('\n\n' + secs[0]['text'] if secs[0]['text'] else '')
    return secs, page


def table_rows(pat):
    (p,) = NOTION.glob(pat)
    return list(csv.DictReader(open(p, encoding='utf-8-sig')))


def fields(r, skip=('Name', 'Portrait')):
    """A table row's fields as `- **Field:** value` lines; Notion's relation links left out."""
    out = []
    for k, v in r.items():
        if k in skip or not v or 'notion.com' in v:
            continue
        out.append(f'- **{k}:** {v}')
    return out


def main():
    B.BOOK = B.corpus_shingles()
    overview, people, pcs = [], [], []
    (root,) = NOTION.parent.glob('Physician, Heal Thyself *.html')
    secs, _ = page_sections(root, 'Physician, Heal Thyself')
    check('the root page', root, secs); overview += secs
    (up,) = NOTION.glob('The Story Coming Up *.html')
    secs, _ = page_sections(up, 'The Story Coming Up')
    check('The Story Coming Up', up, secs)
    overview.append({'id': sid('The Story Coming Up'), 'title': 'The Story Coming Up', 'text': '',
                     'sections': [s2 for s in secs for s2 in ([{'id': s['id'], 'title': s['title'], 'text': s['text']}] if s['text'] else []) + s.get('sections', [])]})
    npc_rows = {r['Name']: r for r in table_rows('VtM NPCs *.csv')}
    cot_rows = {r['Name']: r for r in table_rows('Coterie *.csv')}
    for name, r in list(npc_rows.items()) + [('Baruch Espinosa', cot_rows['Baruch Espinosa'])]:
        folder = 'Coterie' if name == 'Baruch Espinosa' else 'VtM NPCs'
        (path,) = (NOTION / folder).glob(B.glob_escape(name.replace('"', '')) + ' *.html')
        lead = fields(r)
        secs, _ = page_sections(path, f'people/{name}', lead)
        check(name, path, secs, Counter(words(' '.join(l[2:] for l in lead).replace('**', ' '))))
        entry = {'id': sid('people', name), 'title': name, 'text': '\n\n'.join(s['text'] for s in secs[:1]),
                 'sections': [x for s in secs for x in ([{'id': s['id'], 'title': s['title'], 'text': s['text']}] if s is not secs[0] else []) + s.get('sections', [])],
                 'about': [h for h, nm in CAST if nm == name]}
        # the NPC's own sub-tables (Maggie Molyneux's Attributes and Skills)
        sub = path.parent / path.stem.rsplit(' ', 1)[0]
        for tcsv in sorted(sub.glob('*.csv')) if sub.is_dir() else []:
            rows = list(csv.reader(open(tcsv, encoding='utf-8-sig')))
            head = rows[0][-1].rstrip(':').title()
            entry['sections'].append({'id': sid('people', name, tcsv.name), 'title': head,
                                      'text': '\n'.join('- ' + ' · '.join(c for c in row if c) for row in rows[1:])})
        if not entry['sections']:
            del entry['sections']
        people.append(entry)
    for name, r in cot_rows.items():
        if name == 'Baruch Espinosa':
            continue
        (path,) = (NOTION / 'Coterie').glob(B.glob_escape(name) + ' *.html')
        lead = fields(r)
        secs, _ = page_sections(path, f'pc/{name}', lead)
        check(name, path, secs, Counter(words(' '.join(l[2:] for l in lead).replace('**', ' '))))
        pcs.append({'id': sid('pc', name), 'title': name, 'text': secs[0]['text'],
                    'sections': [x for s in secs for x in ([{'id': s['id'], 'title': s['title'], 'text': s['text']}] if s is not secs[0] else []) + s.get('sections', [])],
                    'about': [name]})
    pack = {'kind': 'sortilege-vtt-campaign', 'version': 1,
            'gm': {'overview': overview, 'people': people, 'pc': pcs}}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(pack, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    n = lambda l: sum(1 + len(x.get('sections', [])) for x in l)
    print(f'seed: overview {len(overview)} sections ({n(overview)} with subsections) · people {len(people)} · '
          f'pc {len(pcs)} · every page word for word → {OUT.relative_to(B.REPO)}')


if __name__ == '__main__':
    main()
