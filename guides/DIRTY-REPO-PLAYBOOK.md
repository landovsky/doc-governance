---
class: living
type: guide
tier: canonical
title: DIRTY-REPO-PLAYBOOK — Gradually migrate a messy repo to green
status: active
owner: "@landovsky"
updated: 2026-08-20
covers:
  - payload/.docgov/.doc-todo
  - spec/model.md
last_verified: 2026-08-20
description: >
  Gradually bring a messy repo to green: inventory the corpus with the reusable
  byte-reproducible census scripts, seed .doc-todo with every non-conformant
  markdown path, then drain it under the shrink-only ratchet — minimum set first,
  high-leverage types next, long tail last — while CI stays green.
---

# DIRTY-REPO-PLAYBOOK — Gradually migrate a messy repo to green

Adopting the model in a repo that already has dozens or hundreds of markdown files does **not**
mean reclassifying everything before you can merge. You freeze the mess behind a grandfather
list and drain it over time. CI stays green throughout because it only ever checks
**clean + newly-touched** files — the grandfathered backlog is exempt until you reach it.

> Run [INSTALL](INSTALL.md) first (copy `payload/`, pin the manifest). This playbook is the
> extra work for a repo that already has legacy docs.

---

## Step 1 — Inventory the corpus (census)

You need a per-file census: does each `.md` have front matter, is it an orphan (unreachable from
the index), does it have dead internal links, is it coupled to code, etc. **Automation for this
(`docgov doctor`) is DEFERRED — TODO (tooling, later).** For now, reuse the byte-reproducible
census scripts already written on the pharmacy inventory branch:

```
PHARM=~/git/pharmacy
# Read the reusable runner straight off the branch (it is not on main):
git -C "$PHARM" show origin/chore/docs-governance-inventory:docs/docs-governance-inventory/scripts/run-all.sh
```

That `run-all.sh` bundles the Phase-1 git-fact + dead-link scripts. Fetch the whole `scripts/`
tree out of the branch into a scratch dir and run it against the **target** repo:

```
mkdir -p /tmp/docgov-census && cd /tmp/docgov-census
git -C "$PHARM" archive origin/chore/docs-governance-inventory \
    docs/docs-governance-inventory/scripts | tar -x --strip-components=3
bash run-all.sh ~/git/<REPO>      # emits a CSV row per md file
```

Output is a **CSV of every markdown file** with columns for: front-matter present?, class/type
declared?, orphan?, dead internal links, coupled-to-code?, last-touched, etc. (Same shape as the
pharmacy `docs-inventory.csv`, 127×24, and the hriste one, 376×25.) This CSV is your worklist —
it is raw evidence, so treat it as `tier: source`, not a governed doc.

## Step 2 — Seed `.doc-todo`

Take every row from the census that is **non-conformant** (missing/invalid front matter, orphan,
dead links) and write its repo-relative path, one per line, into `.docgov/.doc-todo`:

```
# .docgov/.doc-todo  (seeded from census — every currently non-conformant md path)
docs/old/legacy-notes.md
docs/briefs/websites.md
...
```

This is the grandfather list. It makes the lint gate **ignore** these files so CI can go green
on day one without reclassifying anything.

## Step 3 — The ratchet rule (the whole point)

- `.doc-todo` may **only ever SHRINK**. You remove a path when you clean that file; you never add
  a path to widen the exemption.
- Any **new** markdown file, or any **touched** existing file, must be **clean** (full v0.2 front
  matter, no dead links) — regardless of whether it was on the list. Touching a grandfathered
  file means cleaning it and deleting its line.
- CI enforces exactly this: clean the world you touch, freeze the world you don't, and the frozen
  set can only get smaller. **TODO (tooling, later):** `docgov lint` will diff `.doc-todo` between
  base and head and fail any PR that grows it.

## Step 4 — Prioritized backfill (drain the list)

Work the list highest-leverage first, not alphabetically:

1. **The 5 minimum-set docs** (model §8): `README.md`, `MAIN.md`, `CLAUDE.md`/`AGENTS.md`,
   `docs/governance.md`, `docs/decisions/ADR-0001`. These orient everything else — do them first.
2. **Highest-leverage types next** — the docs most read or most dangerous when stale: living
   `reference`/`domain-doc`/`gitops-runbook` (the "what is true" docs agents cite), then active
   `transient` specs/briefs (kill the competing-registry problem by generating the index from
   these). Retire shipped/killed transients to `tier: archive` as you go.
3. **The long tail** — everything else, as time allows. Each cleaned file drops off `.doc-todo`.

For each file: add/repair front matter (see [AUTHORING](AUTHORING.md)), fix dead links, make it
reachable from `MAIN.md`, then delete its line from `.doc-todo`.

## Step 5 — Done

Done = **`.doc-todo` is empty.** At that point every markdown file in the repo is governed and
clean, the grandfather exemption is gone, and the lint gate applies to the entire corpus.
