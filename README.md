# Physician, Heal Thyself

A **Vampire: The Masquerade 5th Edition** chronicle in Quebec City (2021), served as an
**instance** of [sortilege-vtt-vtm5e](https://github.com/sortilege-inc/sortilege-vtt-vtm5e) —
its only dependency.

The VTT owns the root: the site at `/`, the Storyteller's table at `/gm/`, the engine, the
VtM5e system module, and the books generated from the Titterpig corpus. The campaign owns
`campaign/`; `campaign/PLAN.md` holds the decisions, the milestones and their proof.

## The fork

`upstream` is the VTT. Engine and system updates arrive by

```bash
git fetch upstream && git merge upstream/main
```

Upstream-owned files are never edited here. The instance's own root files (`engine/config.js`,
`worker/wrangler.jsonc`, `README.md`, `CNAME`, `.gitignore`, `.claude/launch.json`,
`.gitattributes`) are marked `merge=ours`. That needs a driver git does not store; run once per
clone:

```bash
git config merge.ours.driver true
```

`merge=ours` keeps the instance's *whole* `engine/config.js`, so after each pull read
`git diff <last pulled>..upstream/main -- engine/config.js` and carry what applies.

## Local

Launch entries `physician` (site, 8748) and `physician-worker` (sessions, 8798).

## Rights

*Vampire: The Masquerade* is © Paradox Interactive / World of Darkness. This is an unofficial
play aid for the owner's table, not a redistribution of the books.
