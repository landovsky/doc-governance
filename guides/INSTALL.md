---
class: living
type: guide
tier: canonical              # derived: living + not-drifted + not-terminal
title: INSTALL — Adopt a repo (manual)
status: active
owner: "@landovsky"
updated: 2026-08-20
covers:
  - payload/.docgov/manifest.yml
  - payload/docs/governance.md
  - spec/model.md
last_verified: 2026-08-20
description: >
  Adopt the documentation-governance model (v0.2) in a fresh repo, by hand:
  the exact copy-set from payload/, where each file lands, how to fill
  placeholders, tailor docs/_types.yml, hand-write MAIN.md, seed .doc-todo,
  and pin the manifest model_version. Worked example: ~/git/hriste-ops.
---

# INSTALL — Adopt a repo (manual)

This is the **manual** adoption procedure. Distribution today is: **copy `payload/` into the
target repo, pin `model_version` in `.docgov/manifest.yml`.** A pin-installed `docgov` CLI
(`docgov adopt`, index generation, lint) is **DEFERRED** — every step below is done by hand for
now, and each place the CLI will eventually slot in is marked **TODO (tooling, later)**.

> **Worked example throughout:** we adopt **`~/git/hriste-ops`** as the first target repo.
> `<REPO>` = `hriste-ops`. `$MASTER` = `/Users/tomas/.dotfiles/project-management/docs-governance`.

---

## 1. What lands where (the copy-set)

Copy from `$MASTER/payload/` into the **root of the target repo**, preserving relative paths:

| From (`payload/…`) | To (repo root) | What it is |
|---|---|---|
| `docs/_types.yml` | `docs/_types.yml` | repo-local type enum (the OPEN layer) |
| `docs/governance.md` | `docs/governance.md` | in-repo, citable model entry point |
| `docs/decisions/0001-adopt-doc-governance.md` | `docs/decisions/0001-adopt-doc-governance.md` | ADR-0001 = "adopt this model" |
| `.docgov/manifest.yml` | `.docgov/manifest.yml` | per-repo config; pins `model_version` |
| `.docgov/.doc-todo` | `.docgov/.doc-todo` | shrink-only grandfather list (empty on install) |
| `.github/workflows/docs.yml` | `.github/workflows/docs.yml` | CI gate (a **stub** until `docgov` ships) |

Rule of thumb: `payload/docs/*` → `docs/`, `payload/.docgov/*` → `.docgov/`,
`payload/.github/workflows/docs.yml` → `.github/workflows/`.

---

## 2. Order of operations

Do these **in order** — later steps depend on earlier ones.

1. **Copy the payload** (the table above). One paste, nothing filled in yet.
   ```
   cd ~/git/hriste-ops
   mkdir -p docs/decisions .docgov .github/workflows
   cp $MASTER/payload/docs/_types.yml                              docs/_types.yml
   cp $MASTER/payload/docs/governance.md                           docs/governance.md
   cp $MASTER/payload/docs/decisions/0001-adopt-doc-governance.md  docs/decisions/0001-adopt-doc-governance.md
   cp $MASTER/payload/.docgov/manifest.yml                         .docgov/manifest.yml
   cp $MASTER/payload/.docgov/.doc-todo                            .docgov/.doc-todo
   cp $MASTER/payload/.github/workflows/docs.yml                   .github/workflows/docs.yml
   ```
2. **Pin the manifest** (`.docgov/manifest.yml`): confirm `model_version: 0.2.0` (must equal
   `$MASTER/VERSION`), set `adopted_at:` to today, set `owner:`. Adjust `paths:` only if this
   repo's layout differs from the defaults (`docs/`, `MAIN.md`, `docs/decisions/`). Leave
   `options.tooling/index/ci` as `manual`/`stub` — the CLI isn't here yet.
3. **Fill placeholders** (step 3 below).
4. **Tailor `docs/_types.yml`** to this repo's real doc kinds (step 4).
5. **Bring the 5 minimum-set docs into being** (step 5) — these come **first**, before any
   backfill of the rest of the corpus.
6. **Hand-write `MAIN.md`** — the generated index, by hand for now (step 6).
7. **Seed `.doc-todo`** if the repo already has non-conformant markdown — but that is the
   [DIRTY-REPO-PLAYBOOK](DIRTY-REPO-PLAYBOOK.md); a fresh repo leaves `.doc-todo` empty.
8. **Commit** the whole adoption in one PR (payload + MAIN.md + filled docs). ADR-0001 records
   the adoption; the deletion of any hand-kept registries belongs in this same PR.

---

## 3. Filling the `{{PLACEHOLDER}}`s

Grep the freshly-copied files for blanks and replace every one:

```
grep -rnE '<REPO>|<YYYY-MM-DD>|@landovsky|\{\{[A-Z_]+\}\}' docs .docgov
```

| Placeholder | Where | Replace with |
|---|---|---|
| `<REPO>` | `docs/governance.md` (title, body) | the repo name, e.g. `hriste-ops` |
| `<YYYY-MM-DD>` | `manifest.yml:adopted_at`, `ADR-0001` `date`/`updated` | today's date |
| `@landovsky` | `owner:` everywhere | the repo's actual steward handle |
| `model_version` | `manifest.yml` | must equal `$MASTER/VERSION` (today: `0.2.0`) |

`tier:` is **derived** — leave the values that ship in the payload; never invent one.

---

## 4. Tailor `docs/_types.yml`

The payload ships portable types (`adr`, `transcript`, `reference`, `domain-doc`,
`gitops-runbook`, `brief`, `spec`) and commented examples. Keep what applies, uncomment/add
what this repo needs (one line each), delete what it doesn't. Every entry names its default
`class`; raw evidence types carry `raw: true` (→ derives `tier: source`). Respect the guardrail
comment: customer/bot copy and living item-lists are **not** doc types.

---

## 5. The 5 minimum-set docs come first

Before backfilling anything else, make sure the repo carries all five orienting docs
(model §8). Adopt these before the long tail. **Two rules resolve the create-vs-edit
question:**

- **Missing minimum-set docs → CREATE them now, conformant.** Adoption brings
  `docs/governance.md`, `MAIN.md`, `docs/decisions/0001`, and a root `CLAUDE.md`
  (= `AGENTS.md`, if absent) into being with clean v0.2 front matter. These are new and
  conformant, so they are **not** added to `.doc-todo`.
- **Existing minimum-set docs → GRANDFATHER, don't edit at adopt time.** A pre-existing
  file (typically `README.md`) is **not** rewritten during adoption. List it in `.doc-todo`
  and **backfill it FIRST**, ahead of the rest of the corpus, per the
  [DIRTY-REPO-PLAYBOOK](DIRTY-REPO-PLAYBOOK.md). Adoption never edits grandfathered content.

| Member | class / type | Action on install |
|---|---|---|
| `README.md` | living / entry | if it already exists: **grandfather** into `.doc-todo`, backfill first (do NOT edit at adopt time); if absent: create conformant |
| `MAIN.md` | living / entry (generated index) | create — hand-write it now — see step 6 |
| `CLAUDE.md` = `AGENTS.md` | living / entry | create if absent (front matter; keep `AGENTS.md` a symlink); grandfather if it pre-exists |
| `docs/governance.md` | living / entry | create — copied from payload; placeholders filled |
| `docs/decisions/` + `ADR-0001` | immutable / adr | create — copied from payload; `date` filled |

---

## 6. Create the first `MAIN.md` index BY HAND

The index is normally **generated from front matter** — hand-kept registries are banned. But
the generator is **TODO (tooling, later)** (`docgov index`). Until then you write `MAIN.md`
yourself, as a faithful reflection of the front matter that exists:

1. Front matter: `class: living`, `type: entry`, `status: active`, `owner`, `updated`,
   `covers: [docs/_types.yml]`, `last_verified`. (`tier` derives to `canonical`.)
2. Body: one navigation line per governed doc — title (link) + its `description:` — grouped by
   `class` or `type`. Pull each line straight from that doc's front matter; do not invent
   descriptions.
3. Treat this file as **provisional**: when `docgov index` ships it will regenerate `MAIN.md`,
   and from then on editing it by hand will fail CI. For now, re-hand-edit it whenever you add
   or retitle a governed doc.

---

## 7. Copy-paste adoption checklist

```
[ ] payload/ copied: docs/_types.yml, docs/governance.md, docs/decisions/0001-*, .docgov/manifest.yml, .docgov/.doc-todo, .github/workflows/docs.yml
[ ] manifest.yml: model_version == $MASTER/VERSION (0.2.0); adopted_at + owner set; paths checked
[ ] all placeholders replaced (grep '<REPO>|<YYYY-MM-DD>|{{...}}' returns nothing)
[ ] docs/_types.yml tailored to this repo's real doc kinds (raw: true on evidence types)
[ ] ADR-0001 date filled; heading number matches filename (0001)
[ ] 5 minimum-set docs present & carry v0.2 front matter (README, MAIN.md, CLAUDE.md/AGENTS.md, docs/governance.md, ADR-0001)
[ ] MAIN.md hand-written from front matter (provisional; regenerated once docgov ships)
[ ] no tier: hand-invented anywhere (tier is derived)
[ ] .doc-todo empty (fresh repo) OR seeded per DIRTY-REPO-PLAYBOOK (messy repo)
[ ] any old hand-kept registries deleted in THIS PR
[ ] committed as one adoption PR
```

**TODO (tooling, later):** `docgov adopt` will do steps 1–6 (copy, pin, fill, generate a first
`MAIN.md`, seed `.doc-todo`); `docgov lint` + `docgov index --check` will replace manual review
and flip `.github/workflows/docs.yml` from stub to blocking.
