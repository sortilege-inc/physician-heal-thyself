// campaign/site/site.js — Physician, Heal Thyself's own tabs on the VTT's site, ahead of the system's
// (engine/instance.js, stage `site`). Everything drawn comes from campaign/data/docs.js
// (window.PHT_DOCS, built by campaign/build/build_docs.py from the owner's Notion export).
(function () {
  const DOCS = window.PHT_DOCS;
  const tabs = window.VttSiteTabs;
  if (!DOCS || !Array.isArray(tabs)) return;
  const { el } = window.VttRender;
  const D = window.VtmData;
  const Art = () => window.VtmArt || { clans: {}, sects: {} };
  const artUrl = (src) => (D && D.artUrl ? D.artUrl(src) : src);

  // ── a person's mark: their clan, else their sect, else AURORA's ──
  function markSrc(p) {
    const clans = Art().clans, sects = Art().sects;
    const c = p.clan;
    if (c && clans[c]) return artUrl(clans[c].src);
    if (p.faction && sects[p.faction]) return artUrl(sects[p.faction].src);
    if (p.faction === 'AURORA') return artUrl('campaign/assets/marks/second-inquisition.webp');
    return null;
  }
  const markTitle = (p) => p.clan || p.faction || '';

  function portrait(p, cls) {
    const src = markSrc(p);
    return el('figure', { class: 'pht-portrait' + (cls ? ' ' + cls : '') }, [
      p.portrait ? el('img', { src: p.portrait, alt: p.name, loading: 'lazy' }) : el('div', { class: 'pht-portrait-none' }),
      src ? el('span', { class: 'pht-mark', title: markTitle(p) }, [el('span', { class: 'mark', style: '--mark:url("' + src + '")', role: 'img', 'aria-label': markTitle(p) })]) : null,
    ]);
  }

  const prose = (h, cls) => { const d = el('div', { class: 'pht-prose' + (cls ? ' ' + cls : '') }); d.innerHTML = h; return d; };
  const reader = (kids) => el('div', { class: 'site-reader solo pht-reader' }, kids);
  const page = (container) => { const p = el('div', { class: 'page pht-page' }); container.appendChild(p); return p; };
  const facts = (rows) => el('table', { class: 'pht-facts' }, [el('tbody', {}, rows.filter((r) => r[1]).map((r) => el('tr', {}, [el('th', {}, [r[0]]), el('td', {}, [r[1]])])))]);
  const crumbs = (ctx, id, label, here) => el('div', { class: 'crumbs pht-crumbs' }, [el('a', { href: ctx.href(id) }, [label]), here ? ' › ' + here : '']);
  const nightTitle = (slug) => { const c = DOCS.chronicle.find((x) => x.slug === slug) || {}; return c.written ? c.title + ' \u00b7 ' + c.part : c.title || slug; };

  // ── Home ──
  function renderHome(container, path, ctx) {
    const p = page(container);
    p.appendChild(el('div', { class: 'pht-hero' }, [
      el('h1', { class: 'pht-title' }, [(window.VttConfig || {}).title || '']),
      el('p', { class: 'pht-sub' }, ['Quebec City, June 2021 · a chronicle for Vampire: The Masquerade']),
    ]));
    const cards = [
      ['coterie', 'The Coterie', DOCS.coterie.length + ' who answered Baruch’s letters'],
      ['chronicle', 'The Story So Far', DOCS.chronicle.filter((c) => c.title !== 'Epilogue').length + ' nights and an epilogue'],
      ['personae', 'Dramatis Personae', DOCS.personae.length + ' met in the city'],
      ['letters', 'The Letters', 'from Baruch Espinosa'],
    ];
    p.appendChild(el('div', { class: 'pht-cards' }, cards.map((c) => el('a', { class: 'shelf-book pht-card', href: ctx.href(c[0]) }, [el('div', { class: 'pht-card-t' }, [c[1]]), el('div', { class: 'pht-card-s' }, [c[2]])]))));
    p.appendChild(reader([prose(DOCS.home.tenets, 'pht-tenets'), el('h2', { class: 'chapter-h' }, ['Game Lore Notes']), prose(DOCS.home.lore)]));
  }

  // ── The Coterie ──
  function personCard(ctx, id, x, sub) {
    return el('a', { class: 'pht-person', href: ctx.href(id, [x.slug]) }, [portrait(x, 'small'), el('div', { class: 'pht-person-n' }, [x.name]), el('div', { class: 'pht-person-s' }, [sub])]);
  }
  function renderCoterie(container, path, ctx) {
    const p = page(container);
    const x = path[0] && DOCS.coterie.find((c) => c.slug === path[0]);
    if (!x) {
      p.appendChild(el('h2', { class: 'chapter-h' }, ['The Coterie']));
      p.appendChild(el('div', { class: 'pht-people' }, DOCS.coterie.map((c) => personCard(ctx, 'coterie', c, [c.clan, c.concept].filter(Boolean).join(' · ')))));
      return;
    }
    p.appendChild(reader([
      crumbs(ctx, 'coterie', 'The Coterie', x.name),
      el('div', { class: 'pht-person-page' }, [
        portrait(x, 'large'),
        el('h2', { class: 'chapter-h' }, [x.name]),
        facts([['Concept', x.concept], ['Clan', x.clan], ['Generation', x.generation], ['Blood Potency', x.bloodPotency], ['Humanity', x.humanity], ['Faction', x.faction]]),
        prose(x.html),
      ]),
    ]));
  }

  // ── Dramatis Personae, by faction ──
  const ORDER = ['Camarilla', 'Anarch', 'Sabbat', 'Unaffiliated', 'AURORA', 'Society of St. Leopold'];
  function renderPersonae(container, path, ctx) {
    const p = page(container);
    const x = path[0] && DOCS.personae.find((c) => c.slug === path[0]);
    if (!x) {
      p.appendChild(el('h2', { class: 'chapter-h' }, ['Dramatis Personae']));
      p.appendChild(el('p', { class: 'pht-note' }, ['Those the coterie has met, by faction.']));
      const groups = {};
      DOCS.personae.forEach((c) => (groups[c.faction || 'Unaffiliated'] = groups[c.faction || 'Unaffiliated'] || []).push(c));
      Object.keys(groups).sort((a, b) => (ORDER.indexOf(a) + 99) % 99 - (ORDER.indexOf(b) + 99) % 99).forEach((g) => {
        p.appendChild(el('h4', { class: 'pht-group' }, [g]));
        p.appendChild(el('div', { class: 'pht-people' }, groups[g].map((c) => personCard(ctx, 'personae', c, [c.title, c.clan].filter(Boolean).join(' · ')))));
      });
      return;
    }
    p.appendChild(reader([
      crumbs(ctx, 'personae', 'Dramatis Personae', x.name),
      el('div', { class: 'pht-person-page' }, [
        portrait(x, 'large'),
        el('h2', { class: 'chapter-h' }, [x.name]),
        facts([['Title', x.title], ['Clan', x.clan], ['Faction', x.faction], ['Generation', x.generation]]),
        el('h4', {}, ['In the chronicle']),
        el('ul', { class: 'pht-nights' }, x.nights.map((n) => el('li', {}, [el('a', { href: ctx.href('chronicle', [n]) }, [nightTitle(n)])]))),
      ]),
    ]));
  }

  // ── The Story So Far: one page, a rail of the nights ──
  // #chronicle/<night> opens the page at that night. A click on the rail scrolls there and
  // rewrites the address without a hashchange (history.replaceState), so the page is not redrawn.
  // a written chapter's rail entry is its title over its night; a night still in notes, the night over its session
  const railLabel = (c) => (c.written ? c.title : c.title.replace(/^Night of /, '').replace(/, \d{4}$/, ''));
  const sessionOf = (c) => (c.written ? c.part.replace(/,? \d{4}$/, '') : ((c.html.match(/Session:\s*([^<]+)/) || [])[1] || '').trim());
  function renderChronicle(container, path, ctx) {
    const p = page(container);
    const head = document.querySelector('.site-head');
    // how much of the top the band holds while scrolling: its height where it sticks, none where it scrolls away (phones)
    const bandH = () => (head && /sticky|fixed/.test(getComputedStyle(head).position) ? head.offsetHeight : 0);
    p.style.setProperty('--pht-head', bandH() + 'px');
    const links = {};
    const rail = el('nav', { class: 'pht-rail', 'aria-label': 'Nights' }, [
      el('div', { class: 'pht-rail-h' }, ['The Story So Far']),
      el('ol', {}, DOCS.chronicle.map((c) => el('li', {}, [links[c.slug] = el('a', {
        href: ctx.href('chronicle', [c.slug]),
        onclick: (ev) => { ev.preventDefault(); go(c.slug, true); },
      }, [el('span', { class: 'pht-rail-n' }, [railLabel(c)]), sessionOf(c) ? el('span', { class: 'pht-rail-s' }, [sessionOf(c)]) : null])]))),
    ]);
    const sections = DOCS.chronicle.map((c) => el('section', { class: 'pht-night', id: 'night-' + c.slug, 'data-slug': c.slug }, [
      c.written ? el('div', { class: 'pht-part' }, [c.part]) : null,
      el('h2', { class: 'chapter-h' }, [c.title]), prose(c.html, c.written ? 'pht-chapter' : 'pht-notes'),
    ]));
    p.appendChild(el('div', { class: 'pht-chronicle' }, [rail, reader(sections)]));

    function mark(slug) {
      Object.keys(links).forEach((k) => links[k].classList.toggle('on', k === slug));
      const a = links[slug];
      if (a && rail.scrollWidth > rail.clientWidth) a.scrollIntoView({ block: 'nearest', inline: 'center' });
    }
    function go(slug, smooth) {
      const sec = document.getElementById('night-' + slug);
      if (!sec) return;
      sec.scrollIntoView({ behavior: smooth ? 'smooth' : 'auto', block: 'start' });
      history.replaceState(null, '', ctx.href('chronicle', [slug]));
      mark(slug);
    }
    // the night being read: the last one whose top has passed under the band
    const onScroll = () => {
      if (!document.body.contains(p)) { window.removeEventListener('scroll', onScroll); return; }
      // on a phone the rail is a bar under the band, and the page reads from below it
      const bar = getComputedStyle(rail).overflowY === 'hidden';
      const top = (bar ? rail.getBoundingClientRect().bottom : bandH()) + 40;
      let cur = sections[0].dataset.slug;
      sections.forEach((s) => { if (s.getBoundingClientRect().top <= top) cur = s.dataset.slug; });
      // at the foot of the page the last night (the short Epilogue) cannot reach the top: it is the one being read
      if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 2) cur = sections[sections.length - 1].dataset.slug;
      mark(cur);
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    mark(DOCS.chronicle[0].slug);
    // opened at a night: jump there now, and again once the fonts have settled the page's height
    if (path[0] && DOCS.chronicle.some((c) => c.slug === path[0])) {
      setTimeout(() => go(path[0], false), 0);
      if (document.fonts && document.fonts.ready) document.fonts.ready.then(() => { if (document.body.contains(p)) go(path[0], false); });
    }
  }

  // ── The Letters ──
  function renderLetters(container) {
    page(container).appendChild(reader([el('h2', { class: 'chapter-h' }, ['Letters from Baruch Espinosa']), prose(DOCS.letters, 'pht-letters')]));
  }

  const G = 'chronicle';
  tabs.unshift(
    { id: 'home', label: 'Home', render: renderHome, group: G },
    { id: 'coterie', label: 'The Coterie', render: renderCoterie, group: G },
    { id: 'chronicle', label: 'The Story So Far', render: renderChronicle, group: G },
    { id: 'personae', label: 'Dramatis Personae', render: renderPersonae, group: G },
    { id: 'letters', label: 'The Letters', render: renderLetters, group: G },
  );
})();
