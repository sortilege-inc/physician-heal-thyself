# Physician, Heal Thyself × sortilege-vtt-vtm5e — plan and decision log

A **Vampire: The Masquerade 5th Edition** chronicle in Quebec City, played in 2021: a coterie
drawn together by letters from the Nosferatu Baruch Espinosa, who is found dead in his own haven
on the first night. Six nights of play (in-game 9–14 June 2021). Built as an **instance**
of `sortilege-vtt-vtm5e` (its `PLAN.md`, *Instances*), with a silver tint of its own.

**This repo depends on `sortilege-vtt-vtm5e` only** (owner, 2026-09-25). Nothing here reads,
links to, imports or copies at build time from any other campaign repo; every script under
`campaign/` is this repo's own.

Status words: **PROPOSED** (awaiting the owner), **(owner)** decided, **landed** built and proven.

- **here** — `sortilege-inc/physician-heal-thyself` (**PUBLIC, empty on GitHub; nothing pushed**, see P1).
- **upstream** — `sortilege-inc/sortilege-vtt-vtm5e`. Everything generic is built there and pulled.

## What is on disk (read 2026-09-25)

**The only source is the owner's Notion export**, at
`~/Downloads/5583ee56-…_ExportBlock-…/Private & Shared/Physician, Heal Thyself`. 158 files,
31 MB. No Foundry world, transcripts or other store was found on disk.

| Page | What it is | Words |
|---|---|---|
| *Physician, Heal Thyself* (the root) | Coterie and NPC tables; the setting — Camarilla (Traditions, the Convention of Prague), Sabbat, Anarch, the Opposition (AURORA/CSIS, the Society of St. Leopold); Comte Cioran's mausoleum; rules crib pasted from the core; GM to-dos, GM notes, a stat block (Fatima) | 9,116 |
| *The Story So Far* | The GM's session notes — six nights, one per session (Apr 3 → May 29, 2021), scene by scene with PCs/NPCs present, some dice | 8,524 |
| *The Story Coming Up* | GM prep: NPC relationships, the three-way bidding war for Susanna, scene plans | 1,243 |
| *Letters from Baruch Espinosa* | The five letters that open the chronicle, player-facing | 356 |
| *Coterie* (7 pages + CSV) | Claire Breguet, Nico, Richart Cartier, Kamaludeen Hussein, Susanna, Calliope — clan, generation, BP, Humanity, Predator type, Disciplines and powers, some rituals, ambitions, touchstones, haven/domain; **no Attributes or Skills**. Much of each page is core-rulebook text pasted in. Baruch Espinosa's page is empty (player: Jordan) | ~21k |
| *VtM NPCs* (24 pages + CSV) | Clan, faction, generation, title, one-line description; tarot-drawn traits for a few; one stat block (Maggie Molyneux's Attributes/Skills) | ~1k |
| *Consent Checklists* | Four players' filled-in consent forms (PDF) and a screenshot | — |
| Images | 78 PNG + 23 JPG: portraits, clan marks, rules screenshots | — |

## Owner decisions (2026-09-25)

**P1 — Public (owner).** The repo stays public; Pages from `main` when pushed. **Not pushed yet.**

**P2 — Six PCs; Baruch Espinosa is an NPC (owner).** Claire, Nico, Richart, Kamal, Calliope,
Susanna. Baruch is in Dramatis Personae and the GM's People.

**P3 — The Chronicle is the notes as they are (owner).** *The Story So Far*, split at each
"Night of …" heading and the Epilogue — seven pages, word for word.

**P4 — The portraits are used (owner)**: they are the reference images. Each is cut to a 4:5 card
with torn edges, and the clan mark (else the sect's; AURORA's Second Inquisition mark from the
export) sits over its bottom-right corner, half off the card.

**P5 — The site's tabs** (proposed, not objected to; one change, below): Home · The Coterie ·
The Story So Far · Dramatis Personae · The Letters.

**Owner, mid-build: every GM note is in the GM section.** The whole export is in the pack
(`campaign/pack/seed.json`, `build_seed.py`), word for word.

**P6 — The cast layer: Maggie Molyneux and Fatima (owner, 2026-09-25)**; the six PCs are filled in
on the VTT's sheets when their numbers exist. The finding that led to it: Finding: the VTT counts an entity as a
*character* only by its stat shape (`build_data.py`: *Standard Dice Pools*, or *Secondary
Attributes*, or *Attributes* and *Skills*). The export carries a full stat block for two people
(Maggie Molyneux's Attributes and Skills; Fatima's on the root page); the six PCs have clan,
generation, Blood Potency, Humanity, Predator type and Disciplines but **no Attributes, Skills,
Health or Willpower**, and the NPCs only table fields. A layer from it would hold two characters;
writing the rest would invent numbers.

## Milestones

| # | What | Proof |
|---|---|---|
| **M1** | The fork | landed 2026-09-25 (`58d8292`, boundary `f05000c`) |
| **M2** | The export in the repo — `campaign/source/import_notion.py` → `campaign/source/notion/` | landed 2026-09-25: *158 files — copied 144, redacted 8, excluded 6; players redacted: 6; 0 names remain*. The name check **proven by planting a fault** (redaction disabled → *a player name survives in:* six Coterie pages, exit 1) |
| **M3** | The public site — `build_portraits.py`, `build_docs.py` → `campaign/data/docs.js`; `campaign/site/site.js` | landed 2026-09-25: 30 portraits (byte-identical on rebuild); 7 chronicle pages, the letters, 6 coterie, 21 dramatis personae; every page **word-checked both ways** (raw words = published + dropped by reason). Browser on 8748: all five tabs, every character page, 0 console errors, 0 missing assets (35 referenced), no horizontal scroll at 375px |
| **M4** | The GM's material — `build_seed.py` → `campaign/pack/seed.json`, `defaultCampaign.seed` | landed 2026-09-25: overview 10 sections (47 with subsections), people 25, pc 6, every page word for word; the gate **proven by planting a fault** (one name dropped → *the root page: words differ — missing {'sybille': 1}*). In `/gm/` after the gate: Overview, People and Coterie notes populated from the seed (`seeded` 271 ids), 0 console errors |
| **M5** | The cast layer — `campaign/source/convert_cast.py` → `campaign/dsl/pht-0.5-cast.ttrpg`, `build/build_layer.sh`, `campaign/source/check_cast.py` | landed 2026-09-25: 2 characters in the books' Storyteller-character labels; upstream's layer gate *28 strings (37 occurrences) — 0 uncovered · 0 short · 0 unsourced; ids 2, none the corpus's; every reference resolves*; check_cast (the VTT's parser on the layer, the export re-read another way — Maggie's Attributes and Skills from her sub-tables) **84 checks, all match**, **proven by planting four faults** (a changed Skill, a dropped Skill, a 0-rated Skill written, a changed Willpower) → 4 mismatches, exit 1. Browser: *Storyteller characters* 805 (803 + 2), Maggie's stat block drawn; the shelf leads with *Physician, Heal Thyself*; her GM notes carry her record's id (`about`) |
| **M6** | Deploy — push, Pages, the Worker | **owner, 2026-09-25: "push and deploy"**. `main` pushed (public repo); Pages on from `main` (`.nojekyll` in place) → https://sortilege-inc.github.io/physician-heal-thyself/; Worker `physician-heal-thyself` → https://physician-heal-thyself.sortilege.workers.dev (version 6a89abe7), `ALLOWED_ORIGIN` the github.io origin: `GET /session/ABCD` from it → `{"exists":false}` 200, from a foreign origin → 403; `engine/config.js` names it |

## Decided without asking (decision log)

| When | Kind | Decision | Why |
|---|---|---|---|
| 2026-09-25 | autonomous, method | **`main` is upstream's `main` (9bd4598) plus the instance commit**, not a move-and-merge | The repo was empty: nothing to move, so no unrelated histories. `git merge upstream/main` works from here on |
| 2026-09-25 | autonomous, tool | Per-repo identity Jordan Peacock <jordan@sortilege.online>; `merge.ours.driver true`; `.gitattributes` (`merge=ours` on the instance-owned root files), `.gitignore`, `.nojekyll` | Upstream's instance boundary |
| 2026-09-25 | autonomous, tool | Title *Physician, Heal Thyself*; `storagePrefix`/`channel` `pht-vtt`; Worker `physician-heal-thyself`; launch entries `physician` (8748) and `physician-worker` (8798), both unused ports | Per-instance values; own storage so no other VtM site's campaign is ever read |
| 2026-09-25 | autonomous, look | **The silver tint is `campaign/site/campaign.css` only**: the VTT's tokens redefined (blue-black night, silver-grey bone and paper, silver rules, a slightly cooler blood), the warm plum hex the VTT hard-codes on borders overridden to silver-greys, the brand and chapter titles in a silver gradient, a silver hairline under the band | An instance never edits upstream files; `instance.styles` loads after `vtm5e.css`, so the tokens win |
| 2026-09-25 | autonomous, privacy | **The consent checklists never enter the repo**, nor do the players' names (the Notion *Player* column) | Personal data about real people, not campaign material |
| 2026-09-25 | **owner** | **Depend on `sortilege-vtt-vtm5e` only** — no reference to or dependence on the Blood & Other Drugs repo. Checked: `grep` over every instance-owned file and `campaign/` for its name, path, storage prefix → 0 | Owner instruction |
| 2026-09-25 | proof | **The fork boundary, proven by making it fail** in a throwaway clone: a fake upstream commit editing `engine/config.js` and `index.html`. Without the driver → `CONFLICT (content): Merge conflict in engine/config.js`; with it → merged clean, the title stayed *Physician, Heal Thyself*, `index.html` took upstream's edit. In the browser on 8748: title *Physician, Heal Thyself*, `campaign.css` loaded after `vtm5e.css`, `--night` `#0c0e11`, 0 console errors | The playbook's boundary check |
| 2026-09-25 | autonomous, method | **Public pages keep only the players' part of each Coterie page**: the GM To-Do section goes to the GM tabs, and any paragraph that is the books' own text is left out (found in the VTT's `data/` by 32-letter runs, or exactly for short lines; a player's own sentence inside one is kept). 2.3–3.1k words a page left out as book text | The books stay off the public site (§4b.4); Notion's copies had lost spaces at line breaks, so a word match missed them |
| 2026-09-25 | autonomous, scope | **Dramatis Personae = the NPCs the notes name** (21 of 25, matched by name or first name, aliases listed in `build_docs.py`); each shows title, clan, faction, generation and the nights they appear in. Their NPC pages (descriptions, tarot traits, stat blocks) are in the GM's People | The public site holds what the table saw; the GM's notes on a person are the GM's |
| 2026-09-25 | autonomous, scope | **No separate City tab**: the root page's two player-facing blocks — the *Chronicle Tenets* and *Game Lore Notes* (Comte Cioran's mausoleum) — are on Home; the rest of the setting (the sects, the Opposition) is GM material | There was no gazetteer to publish; a City tab would have been two paragraphs |
| 2026-09-25 | autonomous, fidelity | **Susanna's `Salubri.pdf` is not linked or copied on the public site** (its name stays as the notes show it); the GM's copy links it | It is a published book's chapter |
| 2026-09-25 | autonomous, tool | The GM page opens on **Overview · People · Chronicle** (`defaultSlots`) | The notes are what the owner asked to have at hand |
| 2026-09-25 | autonomous, fidelity | **Health and Willpower are the sums of the printed terms** ("HEALTH: 3 + 3" → Health 6); **0-rated Skills are left out**, as the books leave them out; the page references ("(pg.216)") dropped | The corpus's Storyteller-character shape; nothing added that the page does not print |
| 2026-09-25 | **owner** | **The Story So Far is one page with a rail of the nights** (sticky beside the text; a scrolling bar of chips on a phone): a click scrolls to the night and rewrites the address without a redraw; the night being read is lit as you scroll (the last at the foot of the page); `#chronicle/<night>` — the Dramatis Personae links — opens the page at that night, again after the fonts settle. Headless Playwright at 1280 and 375: deep link lands on June 13th, a rail click on June 11th, the foot lights the Epilogue, 0 errors, no sideways scroll | Owner instruction |
| 2026-09-25 | **owner, replaces P3** | **The Story So Far is rewritten as prose chapters, in the style of Fall of London and Blood & Other Drugs**: one chapter per night (`campaign/docs/chronicle/NN-*.md`, front matter *title* and *part* = the night), written from that night's notes only; prose only (no dice, no Hunger, no power names as mechanics, no player names, none of the GM's meta-notes); the letters quoted verbatim. **Pilot: night one (*Letters*, Wednesday 9 June 2021), for the owner's read before the rest.** Until a night has a chapter, the site shows that night's notes. The notes themselves move into the GM tabs (*The Story So Far (the notes)*, word-gated). `build_docs.py` fails on any proper name in a chapter the export never uses (proven: a planted *Marguerite* → exit 1) | Owner instruction; Fall of London's O3 and its pilot pattern |
| 2026-09-25 | **owner: "continue with the rest"** | **The Chronicle is seven written chapters** — *Letters* (Wed 9 June), *The Bank*, *The Wight*, *Elysium*, *Follow the Boots*, *The Fairmont* (Mon 14 June), *Epilogue* — ~8472 words, each from its night's notes only. Build: names check passes on all seven; a scan for dice, Hunger, rules and power names finds only quoted dialogue. Headless: the rail lists the seven with their nights, a deep link lands on its chapter, 0 errors | The owner's go on the pilot |
| 2026-09-25 | autonomous, fidelity | **Names as the table and the map spell them, not the notes' typing**: *Mohammed* → Mohamed (Mkerref), *Giselle* → Gisele, *Mathieu* → Matthieu, *Lefebre* → Lefebvre, *Bar la Sacrilege* → Bar le Sacrilège, *Saint-Foy* → Sainte-Foy. The notes' `[?]` gaps are left as gaps (Sybille's lines are given as the notes give them, one after another); *Session:* dates and the GM's recording note are not in the chapters | Fall of London's rule; the notes mark their own gaps |
| 2026-09-25 | autonomous, fidelity | **"Nice sends a text message to a number he knows Gisele monitors"** is written without naming the sender (*A text went to a number Gisele was known to watch*). The notes' *Nice* is most likely Nico, but the text contradicts the coordinates he gave, so the chapter does not decide it. **For the owner:** say who sent it and the line gets a name | Ambiguous in the source; not the chapter's to settle |
| 2026-09-25 | autonomous, method | **Dramatis Personae's "In the chronicle" is still read from the notes**, and links to the chapters: a chapter may describe someone without naming them (Linh, Stefan and the Councillor are named only in the notes' *NPCs:* lines). 21 people, as before | The notes are the authority for who was there |
| 2026-09-27 | owner input | **Session transcripts** (`~/Downloads/2021 VtM - Physician Heal Thyself/transcripts`, from the recordings): 2021-04-03 *First Blood* → night of 9 June; 04-17 *Twice Shy* → 10 June; 05-08 → **both** 11 June (the wight, the blood walk) and 12 June (Elysium) — the notes' "Session: March 8th" on 11 June is a typo for 8 May; 04-19 is the GM's spoken recap of the first two sessions. No transcript for 13 June, 14 June or the Epilogue. **They stay outside the repo** (players' names, the table's talk) | The owner's new source |
| 2026-09-27 | autonomous, fidelity | **Chapters 1–4 rewritten from the transcripts, B&OD's rule: where transcript and notes both speak, the transcript wins; the notes fill what it lost.** Corrections to the notes: Claire found **her own** and Kamal's files whole, Richart's and Calliope's on the floor, none for Nico (the notes: Kamal's and Richart's whole); Claire was *quite certain* the melted mask was Baruch's and it was Calliope who doubted it; the medic's answer on consent is *"As a formality, yes. That is for my superiors to decide."*; Richart's "four-screen shirt" is a **forest green** shirt (a mishearing); Kamal wore **no tie** at the Elysium (the notes: a bow tie); Richart answered the Prince *"I will try to withstand my devastation."*; Javier also asked that Susanna be brought to the Elysium. The chapters now carry the dialogue and detail the recordings kept (the tunnel, the pager, the silencer, the three knocks, Nico's blade and the break-glass stake, the blood-drive bags, Mohamed's diplomatic protection, the Prince's lines as spoken). Chapters 5–7 are unchanged | The transcripts are the record; the notes were written from memory |
| 2026-09-27 | autonomous, scope | **Left out, though the recordings have it:** the GM's out-of-character statement that Baruch had bound Susanna to Glaurung without her knowledge (no character learns it); table talk, rules, dice and players' names; Richart's player leaving after 8 May | The chapters tell what the characters did and learned |
| 2026-09-27 | autonomous, gate | **The names check admits transcript words by declaration** (`NAME_OK` in `build_docs.py`, each with the session it comes from): *Catholic, Canadian, Danish, Final, Malkavians*; plural possessives (*Anarchs'*) and the pronoun's contractions (*I'd*) are no longer read as names; a quotation starts a sentence | The transcripts are outside the repo, so the build cannot read them |
| 2026-09-27 | **owner** | **The Baruch bond detail goes in the GM notes only**: `GM_ADDITIONS` in `build_seed.py` adds one subsection, *The bond Kamal found (from the 8 May 2021 recording)*, to Susanna's character notes and to Baruch Espinosa's People entry, with the Storyteller's words from the recording quoted and tagged SOURCE / NOTE. Not in any chapter or public page (`grep` over `campaign/data/docs.js` → 0). The seed adds it by id, so a GM page that was already seeded gains it too | Owner instruction |
