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
  const nightTitle = (slug) => (DOCS.chronicle.find((c) => c.slug === slug) || {}).title || slug;

  // ── Home ──
  function renderHome(container, path, ctx) {
    const p = page(container);
    p.appendChild(el('div', { class: 'pht-hero' }, [
      el('h1', { class: 'pht-title' }, [(window.VttConfig || {}).title || '']),
      el('p', { class: 'pht-sub' }, ['Quebec City, June 2021 · a chronicle for Vampire: The Masquerade']),
    ]));
    const cards = [
      ['coterie', 'The Coterie', DOCS.coterie.length + ' who answered Baruch’s letters'],
      ['chronicle', 'The Story So Far', DOCS.chronicle.filter((c) => /^Night of/.test(c.title)).length + ' nights and an epilogue, as they were written down'],
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

  // ── The Story So Far ──
  function renderChronicle(container, path, ctx) {
    const p = page(container);
    const i = DOCS.chronicle.findIndex((c) => c.slug === path[0]);
    if (i === -1) {
      p.appendChild(reader([
        el('h2', { class: 'chapter-h' }, ['The Story So Far']),
        el('ol', { class: 'pht-toc' }, DOCS.chronicle.map((c) => el('li', {}, [el('a', { href: ctx.href('chronicle', [c.slug]) }, [c.title])]))),
      ]));
      return;
    }
    const c = DOCS.chronicle[i], prev = DOCS.chronicle[i - 1], next = DOCS.chronicle[i + 1];
    const paging = () => el('div', { class: 'pht-paging' }, [
      prev ? el('a', { href: ctx.href('chronicle', [prev.slug]) }, ['← ' + prev.title]) : el('span'),
      next ? el('a', { href: ctx.href('chronicle', [next.slug]) }, [next.title + ' →']) : el('span'),
    ]);
    p.appendChild(reader([crumbs(ctx, 'chronicle', 'The Story So Far', c.title), el('h2', { class: 'chapter-h' }, [c.title]), prose(c.html, 'pht-notes'), paging()]));
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
