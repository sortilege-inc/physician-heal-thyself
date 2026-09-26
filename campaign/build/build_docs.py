#!/usr/bin/env python3
"""The chronicle's pages, taken from the owner's Notion export as they are.

    python3 campaign/build/build_docs.py

Reads campaign/source/notion/ (import_notion.py) and writes campaign/data/docs.js
(window.PHT_DOCS) and the page images under campaign/assets/pages/. Nothing is rewritten: each
page's HTML is reduced to plain structure (paragraphs, headings, lists, emphasis, quotes, toggles,
tables, images) and kept word for word, except what is dropped for a stated reason:

  nav         Notion's table-of-contents column and the page's property table
  gm          a Coterie page's "GM To-Do" section — the Storyteller's, not the player's
  book        a paragraph, list item or toggle that is the books' own text, found in the VTT's
              data/ (32-letter runs, half of them shared) — the books stay off the public site; a
              sentence of the player's own inside one (none of its runs in the books) is kept
  checkbox    Notion's to-do checkbox controls (the item's text is kept)

The gate, independent of the reducer: every page's words, read straight from the raw HTML with
the tags stripped, must equal the published words plus the dropped words, as multisets. The run
fails naming the page and the difference.
"""
import hashlib, html, json, re, sys, urllib.parse, zlib
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parent
NOTION = HERE / 'source' / 'notion' / 'Physician, Heal Thyself'
PAGES = HERE / 'assets' / 'pages'
OUT = HERE / 'data' / 'docs.js'
sys.path.insert(0, str(HERE / 'build'))
from build_portraits import slug  # noqa: E402

VOID = {'img', 'br', 'hr', 'input', 'meta', 'link', 'col'}
KEEP = {'p', 'h1', 'h2', 'h3', 'h4', 'ul', 'ol', 'li', 'strong', 'b', 'em', 'i', 'u', 's', 'mark', 'blockquote',
        'hr', 'br', 'figure', 'figcaption', 'img', 'details', 'summary', 'table', 'thead', 'tbody', 'tr', 'th',
        'td', 'code', 'a'}


# ── a small tree ──────────────────────────────────────────────────────
class Node:
    def __init__(self, tag, attrs, parent=None):
        self.tag, self.attrs, self.kids, self.parent = tag, dict(attrs), [], parent

    def text(self):
        return ''.join(k if isinstance(k, str) else k.text() for k in self.kids)

    def spaced(self):
        """The text with a break at every tag, as the raw count reads it."""
        return ' '.join(k if isinstance(k, str) else k.spaced() for k in self.kids)

    def cls(self):
        return self.attrs.get('class') or ''


class Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = self.cur = Node('#root', {})

    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs, self.cur)
        self.cur.kids.append(n)
        if tag not in VOID:
            self.cur = n

    def handle_startendtag(self, tag, attrs):
        self.cur.kids.append(Node(tag, attrs, self.cur))

    def handle_endtag(self, tag):
        n = self.cur
        while n is not self.root and n.tag != tag:
            n = n.parent
        if n is not self.root:
            self.cur = n.parent

    def handle_data(self, data):
        self.cur.kids.append(data)


def parse(path):
    t = Tree(); t.feed(path.read_text(encoding='utf-8')); return t.root


def find(n, pred):
    if isinstance(n, Node):
        if pred(n):
            return n
        for k in n.kids:
            r = find(k, pred)
            if r:
                return r


def words(s):
    return re.findall(r"[\w’'\-]+", html.unescape(s).lower())


# ── the books, as letter runs ─────────────────────────────────────────
# Letters only, lower case: Notion's copy of a book page often lost the space at a line break
# ("throughoutany"), which a word match would miss. A 32-letter window is sampled where its hash
# falls on 0 mod 8, on both sides alike, so the index stays small and the samples line up.
WIN, MOD = 32, 8


def alpha(s):
    return re.sub(r'[^a-z]', '', html.unescape(s).lower())


def samples(s):
    t = alpha(s)
    return [h for h in (zlib.crc32(t[i:i + WIN].encode()) for i in range(len(t) - WIN + 1)) if h % MOD == 0]


BLOB = ''


def corpus_shingles():
    global BLOB
    sh, blob = set(), []
    for f in sorted((REPO / 'data').glob('*.js')):
        for m in re.finditer(r'"((?:[^"\\]|\\.){40,})"', f.read_text(encoding='utf-8')):
            try:
                t = json.loads('"' + m.group(1) + '"')
                sh.update(samples(t)); blob.append(alpha(t))
            except ValueError:
                continue
    BLOB = '|'.join(blob)
    return sh


BOOK = None


def book_ratio(text):
    got = samples(text)
    return (sum(h in BOOK for h in got) / len(got)) if got else None


def is_book(text):
    """A long block: half its sampled runs are the books'. A short one (20-59 letters): the whole
    of it, letters only, is in the books."""
    t = alpha(text)
    if len(t) < 20:
        return False
    if len(t) < 60:
        return t in BLOB
    return book_ratio(text) >= 0.5


def is_mine(sentence):
    """A sentence of the player's own: 12 letters or more, and not found in the books."""
    t = alpha(sentence)
    r = book_ratio(sentence)
    return len(t) >= 12 and t not in BLOB and (r is None or r < 0.3)


SENT = re.compile(r'(?<=[.!?:;])\s+|\s+(?=[-\u2013\u2014]\s)')


def sentences(text):
    return [x for x in SENT.split(text) if x.strip()]


# ── reduce a subtree to plain HTML, recording what is dropped ─────────
class Page:
    def __init__(self, name, public=True):
        self.name, self.dropped, self.images, self.public = name, Counter(), [], public

    def drop(self, why, n):
        t = n if isinstance(n, str) else n.spaced()
        self.dropped[why] += len(words(t))
        self.__dict__.setdefault('dropped_words', Counter()).update(words(t))

    def image(self, src, base):
        rel = urllib.parse.unquote(src)
        path = (base / rel).resolve()
        if not path.is_file():
            return None
        data = path.read_bytes()
        name = hashlib.sha256(data).hexdigest()[:16] + ('.pdf' if path.suffix.lower() == '.pdf' else '.webp')
        PAGES.mkdir(parents=True, exist_ok=True)
        dest = PAGES / name
        if not dest.exists():
            if path.suffix.lower() == '.pdf':
                dest.write_bytes(data)
            else:
                im = Image.open(path)
                im = im.convert('RGBA' if im.mode in ('P', 'LA', 'RGBA') else 'RGB')
                im.thumbnail((1000, 1400))
                im.save(dest, 'WEBP', quality=82, method=6)
        self.images.append(name)
        return 'campaign/assets/pages/' + name

    def render(self, n, base, book_filter=False):
        if isinstance(n, str):
            return html.escape(n, quote=False)
        tag = n.tag
        if tag == 'nav' or 'table_of_contents' in n.cls():
            self.drop('nav', n); return ''
        if tag == 'input':
            return ''
        if tag == 'style' or tag == 'script':
            return ''
        blocky = tag == 'li' and find(n, lambda x: x is not n and x.tag in ('details', 'p', 'ul', 'ol', 'h1', 'h2', 'h3', 'h4'))
        if book_filter and tag in ('p', 'li', 'details', 'blockquote') and not blocky and is_book(n.text()):
            # a player's own sentence inside the book's paragraph is kept, as plain text
            parts = sentences(n.spaced()) if tag != 'details' else []
            verdicts = [(x, None) for x in parts]
            mine = [x for x in parts if is_mine(x)]
            if not mine:
                self.drop('book', n); return ''
            kept = [x for x, r in verdicts if x in mine]
            for x, r in verdicts:
                if x not in mine:
                    self.drop('book', x)
            return f'<{tag} class="own">' + html.escape(' '.join(' '.join(k.split()) for k in kept), quote=False) + f'</{tag}>'
        inner = ''.join(self.render(k, base, book_filter) for k in n.kids)
        if tag == 'img':
            src = n.attrs.get('src', '')
            if src.startswith('http'):
                return ''                                    # Notion's own property icons
            url = self.image(src, base)
            return f'<img src="{html.escape(url)}" alt="" loading="lazy">' if url else ''
        if tag == 'a':
            href = html.unescape(n.attrs.get('href', ''))
            if re.match(r'https?://', href) and 'notion.' not in href:
                return f'<a href="{html.escape(href)}" rel="noopener" target="_blank">{inner}</a>'
            if href.lower().endswith('.pdf') and self.public:
                return inner                                 # a book's pages (Susanna's Salubri.pdf): the text, not the file
            if href.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.pdf')):
                url = self.image(href, base)
                return f'<a href="{html.escape(url)}" target="_blank">{inner}</a>' if url else inner
            return inner
        if tag == 'mark':
            c = re.search(r'highlight-(\w+)', n.cls())
            return f'<mark class="hl-{c.group(1)}">{inner}</mark>' if c else f'<mark>{inner}</mark>'
        if tag == 'li' and 'to-do-list' in (n.parent.cls() if n.parent else ''):
            done = find(n, lambda x: x.tag == 'input' and 'checked' in x.attrs) is not None
            return f'<li class="todo{" done" if done else ""}">{inner}</li>'
        if tag in KEEP:
            if tag in VOID:
                return f'<{tag}>'
            attrs = ' open' if tag == 'details' and 'open' in n.attrs else ''
            return f'<{tag}{attrs}>{inner}</{tag}>' if inner.strip() or tag in ('td', 'th') else ''
        return inner                                         # div, span, article…: their content only


def raw_words(path, cut_nav=True):
    """The independent count: the page body's words, straight from the raw HTML."""
    s = path.read_text(encoding='utf-8')
    s = s[s.find('<div class="page-body"'):] if '<div class="page-body"' in s else s[s.find('<body'):]
    s = re.sub(r'<style.*?</style>', '', s, flags=re.S)
    return Counter(words(re.sub(r'<[^>]+>', ' ', s)))


def check(page, path, html_out):
    raw = raw_words(path)
    got = Counter(words(re.sub(r'<[^>]+>', ' ', html_out))) + page.__dict__.get('dropped_words', Counter())
    if raw != got:
        miss, extra = raw - got, got - raw
        sys.exit(f'{page.name}: words differ — missing {dict(list(miss.items())[:12])} extra {dict(list(extra.items())[:12])}')


def body(path):
    return find(parse(path), lambda n: 'page-body' in n.cls())


def split_sections(root_nodes, level_tag):
    """Top-level blocks → [(heading text, [nodes])] at each <level_tag>."""
    out = []
    for n in root_nodes:
        if isinstance(n, Node) and n.tag == level_tag:
            out.append((n.text().strip(), [n]))
        elif out:
            out[-1][1].append(n)
        else:
            out.append(('', [n]))
    return out


def flat_blocks(n):
    """The page body's blocks in order, with Notion's column wrappers opened up."""
    out = []
    for k in n.kids:
        if isinstance(k, Node) and ('column' in k.cls().split() or 'column-list' in k.cls().split()):
            out.extend(flat_blocks(k))
        else:
            out.append(k)
    return out


# ── the pages ─────────────────────────────────────────────────────────
CHAPTERS = HERE / 'docs' / 'chronicle'


def md(text):
    """The chapters' small Markdown: paragraphs, `---` breaks, `> ` quotes, *italic*, **bold**."""
    def inline(t):
        t = html.escape(t, quote=False)
        t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
        return re.sub(r'\*(.+?)\*', r'<em>\1</em>', t)
    out = []
    for blk in re.split(r'\n\s*\n', text.strip()):
        lines = blk.split('\n')
        if blk.strip() == '---':
            out.append('<hr>')
        elif all(l.startswith('>') for l in lines):
            inner = '\n'.join(l[1:].lstrip() for l in lines)
            out.append('<blockquote>' + ''.join('<p>' + inline(' '.join(q.split())) + '</p>' for q in re.split(r'\n\s*\n', inner) if q.strip()) + '</blockquote>')
        else:
            out.append('<p>' + inline(' '.join(blk.split())) + '</p>')
    return ''.join(out)


def front(path):
    t = path.read_text(encoding='utf-8')
    m = re.match(r'---\n(.*?)\n---\n', t, re.S)
    if not m:
        sys.exit(f'{path.name}: no front matter')
    meta = dict(l.split(': ', 1) for l in m.group(1).splitlines())
    for k in ('title', 'part'):
        if k not in meta:
            sys.exit(f'{path.name}: front matter has no {k}')
    return meta, t[m.end():]


def names_check(chapters, notes_text):
    """Every proper name in a written chapter is in the Notion export (the notes, the tables, the pages)."""
    export = ' '.join(p.read_text(encoding='utf-8', errors='ignore') for p in NOTION.parent.rglob('*') if p.suffix in ('.html', '.csv'))
    export = html.unescape(export)
    bad = {}
    for c in chapters:
        if not c.get('written'):
            continue
        text = re.sub(r'<[^>]+>', ' ', c['html'])
        for sent in re.split(r'(?<=[.!?"\u201d:])\s+|\n', text):
            for w in re.findall(r"(?<!^)(?<![.!?]\s)\b([A-Z][a-z\u00e0-\u00ff'\u2019]+(?:[- ][A-Z][a-z]+)*)", sent.strip())[0:]:
                for part in re.split(r"[- ]", w):
                    part = re.sub(r"['\u2019]s$", '', part)
                    if part and part not in export and part not in NAME_OK:
                        bad.setdefault(c['slug'], set()).add(part)
    if bad:
        sys.exit('names in a chapter that the export never uses: ' + '; '.join(f'{k}: {sorted(v)}' for k, v in bad.items()))


# words a chapter may capitalise that are not names from the export (declared, with the reason)
NAME_OK = {
    'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday', 'Monday', 'June',   # the nights' dates
}


def chronicle():
    """The nights: a written chapter (campaign/docs/chronicle/NN-*.md, NN the night's place) where
    there is one, the owner's notes for that night until then."""
    (path,) = NOTION.glob('The Story So Far *.html')
    page = Page('The Story So Far')
    blocks = flat_blocks(body(path))
    notes = []
    for title, nodes in split_sections(blocks, 'h1'):
        htm = ''.join(page.render(n, path.parent) for n in nodes)
        if not title:
            assert not re.sub(r'<[^>]+>', '', htm).strip(), 'text before the first night'
            continue
        htm = re.sub(r'^<h1>.*?</h1>', '', htm, count=1)
        notes.append({'slug': slug(title), 'title': title, 'part': '', 'html': htm})
    check(page, path, ''.join(f'<h1>{html.escape(c["title"])}</h1>' + c['html'] for c in notes))
    written = {int(p.name[:2]): p for p in sorted(CHAPTERS.glob('[0-9][0-9]-*.md'))} if CHAPTERS.is_dir() else {}
    if any(n < 1 or n > len(notes) for n in written):
        sys.exit(f'a chapter number outside 01-{len(notes):02d}: {sorted(written)}')
    chapters = []
    for i, c in enumerate(notes, 1):
        if i in written:
            meta, text = front(written[i])
            chapters.append({'slug': c['slug'], 'title': meta['title'], 'part': meta['part'], 'html': md(text), 'written': True})
        else:
            chapters.append(dict(c, part=c['title']))
    names_check(chapters, None)
    return chapters, page, {c['slug']: c['html'] for c in notes}


def letters():
    (path,) = NOTION.glob('Letters from Baruch Espinosa *.html')
    page = Page('Letters from Baruch Espinosa')
    htm = ''.join(page.render(n, path.parent) for n in flat_blocks(body(path)))
    check(page, path, htm)
    return htm, page


def home():
    """The root page's two player-facing notes: the Chronicle Tenets and Game Lore Notes."""
    (path,) = NOTION.parent.glob('Physician, Heal Thyself *.html')
    root = body(path)
    page = Page('home')
    out = {}
    lore = find(root, lambda n: n.tag in ('h1', 'h2', 'h3') and n.text().strip() == 'Game Lore Notes')
    if not lore:
        sys.exit('home: no "Game Lore Notes" heading')
    sibs = lore.parent.kids
    i = sibs.index(lore) + 1
    nodes = []
    while i < len(sibs) and not (isinstance(sibs[i], Node) and sibs[i].tag == lore.tag):
        nodes.append(sibs[i]); i += 1
    out['lore'] = ''.join(page.render(n, path.parent.parent) for n in nodes)
    ten = find(root, lambda n: n.tag in ('p', 'div') and n.text().strip().startswith('Chronicle Tenets:'))
    if not ten:
        sys.exit('home: no "Chronicle Tenets:" block')
    out['tenets'] = page.render(ten, path.parent.parent)
    if Counter(words(re.sub(r'<[^>]+>', ' ', out['tenets']))) != Counter(words(ten.text())):
        sys.exit('home tenets: words differ from the source block')
    got = Counter(words(re.sub(r'<[^>]+>', ' ', out['lore'])))
    want = Counter(w for n in nodes for w in words(n if isinstance(n, str) else n.text()))
    if got != want:
        sys.exit(f'home lore: words differ — {dict(want - got)} / {dict(got - want)}')
    return out, page


def coterie_page(path, name):
    page = Page(name)
    blocks = flat_blocks(body(path))
    out, skipping = [], None
    for n in blocks:
        if isinstance(n, Node) and n.tag in ('h1', 'h2', 'h3'):
            level = int(n.tag[1])
            if skipping is not None and level <= skipping:
                skipping = None
            if n.text().strip() == 'GM To-Do':
                skipping = level
        if skipping is not None:
            page.drop('gm', n); continue
        out.append(page.render(n, path.parent, book_filter=True))
    htm = ''.join(out)
    check(page, path, htm)
    return htm, page


def rows(pat):
    import csv
    (p,) = NOTION.glob(pat)
    return list(csv.DictReader(open(p, encoding='utf-8-sig')))


def people(chapters, notes):
    """Who was met on which night is read from the notes (the authority; a chapter may describe
    someone without naming them); the links go to that night's chapter."""
    cot, npcs = rows('Coterie *.csv'), rows('VtM NPCs *.csv')
    pcs, dp, pages = [], [], []
    for r in cot:
        name = r['Name']
        entry = {'slug': slug(name), 'name': name, 'clan': r['Clan'], 'faction': r['Faction'],
                 'generation': r['Generation'], 'concept': r['Concept'], 'bloodPotency': r['Blood Potency'],
                 'humanity': r['Humanity Left'], 'portrait': f'campaign/assets/portraits/{slug(name)}.webp' if r['Portrait'] else ''}
        (path,) = (NOTION / 'Coterie').glob(f'{glob_escape(name)} *.html')
        if name == 'Baruch Espinosa':                    # an NPC (owner, 2026-09-25): the letter-writer
            npcs = npcs + [dict(r, Title='', **{'Short Description': ''})]
            continue
        entry['html'], page = coterie_page(path, name)
        pages.append(page)
        pcs.append(entry)
    for r in npcs:
        name = r['Name']
        keys = aliases(name)
        nights = [c['slug'] for c in chapters if any(re.search(r'\b' + re.escape(k) + r'\b', re.sub(r'<[^>]+>', ' ', notes[c['slug']])) for k in keys)]
        if not nights:
            continue
        dp.append({'slug': slug(name), 'name': name.replace('"', '“', 1).replace('"', '”', 1),
                   'title': r.get('Title', ''), 'clan': r['Clan'], 'faction': r['Faction'],
                   'generation': r['Generation'], 'nights': nights,
                   'portrait': f'campaign/assets/portraits/{slug(name)}.webp' if r['Portrait'] else ''})
    return pcs, dp, pages


def glob_escape(s):
    return re.sub(r'([\[\]*?])', r'[\1]', s)


# the forms the notes use for each NPC — each one checked against the chronicle by the build's report
ALIASES = {
    'Prince Beatrice Bouchard': ['Beatrice', 'Prince Bouchard'],
    'Councillor Rene Lefebvre': ['Lefebvre', 'Lefebre'],
    'Jerome "The Bank" Giovanni': ['Jerome'],
    '"The Spaniard"': ['Spaniard', 'Spanariad'],
    'Comte Cioran': ['Cioran'],
    'Estelle De León': ['Estelle'],
}


def aliases(name):
    first = re.sub(r'^(Prince|Councillor)\s+', '', name).split()[0].strip('"')
    return ALIASES.get(name, []) + [name, first]


def main():
    global BOOK
    BOOK = corpus_shingles()
    if PAGES.exists():
        for f in PAGES.iterdir():
            f.unlink()
    chapters, cp, notes = chronicle()
    letters_html, lp = letters()
    home_parts, hp = home()
    pcs, dp, pps = people(chapters, notes)
    docs = {'home': home_parts, 'chronicle': chapters, 'letters': letters_html, 'coterie': pcs, 'personae': dp}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text('/* Generated by campaign/build/build_docs.py from campaign/source/notion — do not edit by hand. */\n'
                   'window.PHT_DOCS = ' + json.dumps(docs, ensure_ascii=False, separators=(',', ':')) + ';\n', encoding='utf-8')
    for p in [cp, lp, hp] + pps:
        print(f'  {p.name}: kept, dropped {dict(p.dropped) or "nothing"}')
    print(f'docs: {len(chapters)} chapters ({sum(1 for c in chapters if c.get("written"))} written, the rest the notes) · letters · {len(pcs)} coterie · {len(dp)} dramatis personae '
          f'({", ".join(d["name"] for d in dp)}) · {len(set(sum((p.images for p in [cp, lp, hp] + pps), [])))} page images · words checked both ways')


if __name__ == '__main__':
    main()
