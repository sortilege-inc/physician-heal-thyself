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

## Owner decisions — PROPOSED

**P1 — Visibility.** The GitHub repo is **PUBLIC and empty**. The first push carries upstream's
`data/` — the books verbatim. Recommend public, Pages from `main`, `.nojekyll`, but **nothing is pushed until the
owner says so**.

**P2 — Who the coterie is.** The Coterie table has seven rows. Recommend **six PCs** — Claire,
Nico, Richart, Kamal, Calliope, Susanna — and **Baruch Espinosa as an NPC** (the GM's own row,
empty page; the letter-writer found dead on night one). Calliope plays night one only; Susanna
joins partway through night two (the notes' own *PCs:* lines).

**P3 — The Chronicle.** No transcripts exist; the GM's session notes are the record. Recommend
one chapter per night (six), written as prose from the notes alone, every
event traceable to a line in them, no dice or rules named, no player names. Pilot night one for
approval before the other five. (Alternative: publish the notes nearly as they are.)

**P4 — Portraits.** 28 of the 30 portraits are photographs of real people — actors (Jennifer
Connelly, Mads Mikkelsen, Tom Ellis…), public figures (Sartre for Nico, a Mitterrand-era photo
for Comte Cioran), stock and press photos; the other two are third-party illustrations (Calliope;
Richart, credited to sikuriina on DeviantArt). Recommend **none
on the public site**: each person is shown by their clan or sect mark, which the VTT already
ships.

**P5 — The site's sections.** Recommend: **Home · The Coterie · Dramatis Personae · The
Chronicle · The City** (Quebec by night — the Camarilla court, the Anarch barons, the Sabbat
packs and the Opposition, only what the coterie knows) · **The Letters** (Baruch's five letters,
verbatim).

**P6 — The cast as a DSL layer.** The six PCs and the NPCs are written by a
converter from the export kept in `campaign/source/`, checked field by field by an independent
checker. **Recommend it carries only what the export records**: the PCs have no Attributes or
Skills, so their VTT sheets start partial (the GM or player fills them in on the sheet). Only
Maggie Molyneux and Fatima have stat blocks.

## Decided without asking (decision log)

| When | Kind | Decision | Why |
|---|---|---|---|
| 2026-09-25 | autonomous, method | **`main` is upstream's `main` (9bd4598) plus the instance commit**, not a move-and-merge | The repo was empty: nothing to move, so no unrelated histories. `git merge upstream/main` works from here on |
| 2026-09-25 | autonomous, tool | Per-repo identity Jordan Peacock <jordan@sortilege.online>; `merge.ours.driver true`; `.gitattributes` (`merge=ours` on the instance-owned root files), `.gitignore`, `.nojekyll` | Upstream's instance boundary |
| 2026-09-25 | autonomous, tool | Title *Physician, Heal Thyself*; `storagePrefix`/`channel` `pht-vtt`; Worker `physician-heal-thyself`; launch entries `physician` (8748) and `physician-worker` (8798), both unused ports | Per-instance values; own storage so no other VtM site's campaign is ever read |
| 2026-09-25 | autonomous, look | **The silver tint is `campaign/site/campaign.css` only**: the VTT's tokens redefined (blue-black night, silver-grey bone and paper, silver rules, a slightly cooler blood), the warm plum hex the VTT hard-codes on borders overridden to silver-greys, the brand and chapter titles in a silver gradient, a silver hairline under the band | An instance never edits upstream files; `instance.styles` loads after `vtm5e.css`, so the tokens win |
| 2026-09-25 | autonomous, privacy | **The consent checklists never enter the repo**, nor do the players' names (the Notion *Player* column) | Personal data about real people, not campaign material |
| 2026-09-25 | **owner** | **Depend on `sortilege-vtt-vtm5e` only** — no reference to or dependence on the Blood & Other Drugs repo. Checked: `grep` over every instance-owned file and `campaign/` for its name, path, storage prefix → 0 | Owner instruction |
