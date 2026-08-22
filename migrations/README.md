---
class: living
type: guide
tier: canonical
title: migrations/ — how model-version migrations work
status: active
owner: "@landovsky"
updated: 2026-08-20
covers:
  - VERSION
  - payload/.docgov/manifest.yml
last_verified: 2026-08-20
description: >
  How doc-governance migrations work: one guide per version hop named
  <from>-to-<to>.md, applied transitively, driven by manifest.model_version;
  and how to author a new hop guide. The .py codemod per hop is a later phase.
---

# migrations/ — how model-version migrations work

When the **model** changes version, adopted repos don't jump automatically. Each repo pins a
`model_version` in `.docgov/manifest.yml`; migrating it means applying the migration guide(s)
between its pinned version and the master `VERSION`. This directory holds those guides.

To migrate an actual repo, follow [`../guides/MIGRATING.md`](../guides/MIGRATING.md); this file
explains how the migration *files* themselves are organised and authored.

## Filename convention

```
migrations/<from>-to-<to>.md        e.g. migrations/0.1.0-to-0.2.0.md
```

- `<from>` and `<to>` are **consecutive** released model versions (as in `VERSION` /
  `CHANGELOG.md`).
- **One guide per single hop.** There is no combined "skip" file for multi-version jumps.
- The guide is a plain-Markdown, human-followable set of **manual** steps.

## Applied transitively

A repo several versions behind is walked forward **one hop at a time**, lowest to highest —
`0.1.0-to-0.2.0.md`, then `0.2.0-to-0.3.0.md`, and so on — bumping `manifest.model_version`
after each. The chain to apply is derived by comparing `manifest.model_version` to `VERSION`.

## Driven by `manifest.model_version`

The pinned version in `.docgov/manifest.yml` is the single source of truth for *where a repo
stands*. Migration is: read that field, find the ordered hop chain up to `VERSION`, apply each
guide, bump the field. Nothing else tracks a repo's model version.

## Authoring a new hop guide

When you cut a new model version, add `migrations/<prev>-to-<new>.md` in the **same change** that
bumps `VERSION` and `CHANGELOG.md`. Structure it as:

1. **Front matter** — dogfood it: `class: immutable`, `type: migration`, `date:` (the release
   date; a migration guide is frozen once its hop is released — supersede, don't rewrite),
   `title`, `status: accepted`, `owner`, `updated`. `tier` derives to `canonical`.
2. **What changed** — the schema/layout deltas a repo must absorb, tied to the `CHANGELOG.md`
   entry for `<new>`.
3. **Per-file manual steps** — an ordered, mechanical checklist an operator can apply by hand
   (key renames, new required keys, moved files, deleted fields), each with a before/after.
4. **Verification** — how to confirm the repo now satisfies `<new>`.
5. **Bump** — set `manifest.model_version: <new>`.

## Tooling status

Everything here is **manual**. A per-hop Python codemod (`docgov migrate`, one `<from>-to-<to>.py`
alongside each `.md`) is a **LATER phase — DEFERRED**. Until it ships, the `.md` guide is the
whole migration; the future `.py` will automate exactly the per-file steps the `.md` spells out.
