---
class: living
type: entry
tier: canonical
title: MAIN — Docs-Governance master index
status: active
owner: "@landovsky"
updated: 2026-08-20
covers: [_types.yml]
last_verified: 2026-08-20
description: >
  The generated-style navigation index for the docs-governance master package —
  every governed doc grouped by role (Entry, Spec, Guides, Migrations, Records),
  what is deliberately NOT governed here, and where the governance rules live.
  Hand-written for now; the generator that derives this from front matter is deferred.
---

# MAIN — Docs-Governance master index

> **Generated-style, hand-written for now.** The model mandates one index generated
> from front matter (`spec/model.md` §8–9); the generator is deferred, so this table is
> maintained by hand until it lands. This is the master package governing **itself** —
> the ultimate dogfood.

## Governed docs

### Entry

| Doc | Type | Description |
|---|---|---|
| [`README.md`](README.md) | entry | Master entry — what the system is, its payload, guides, adoption status. |
| [`MAIN.md`](MAIN.md) | entry | This index — the one navigation surface over the governed docs. |

### Spec (the governance rules themselves)

| Doc | Type | Description |
|---|---|---|
| [`spec/model.md`](spec/model.md) | model-spec | The normative model — 3 classes × derived tier × repo-local type. |
| [`spec/front-matter.md`](spec/front-matter.md) | model-spec | The front-matter schema: every key, the enums, tier derivation, CITABLE. |

### Guides

| Doc | Type | Description |
|---|---|---|
| [`guides/INSTALL.md`](guides/INSTALL.md) | guide | Adopt the model in a fresh repo, by hand. |
| [`guides/AUTHORING.md`](guides/AUTHORING.md) | guide | Front-matter cookbook — a worked block per class/type. |
| [`guides/MIGRATING.md`](guides/MIGRATING.md) | guide | Move an adopted repo between model versions. |
| [`guides/DIRTY-REPO-PLAYBOOK.md`](guides/DIRTY-REPO-PLAYBOOK.md) | guide | Bring a messy repo to green under the shrink-only ratchet. |
| [`migrations/README.md`](migrations/README.md) | guide | How version-hop migrations work and how to author one. |

### Migrations

| Doc | Type | Description |
|---|---|---|
| [`migrations/0.1.0-to-0.2.0.md`](migrations/0.1.0-to-0.2.0.md) | migration-guide | The v0.1 → v0.2 upgrade (add derived tier, owner/updated, ships:). |

### Records

| Doc | Type | Description |
|---|---|---|
| [`PROVENANCE.md`](PROVENANCE.md) | record | How we arrived at v0.2 — evidence, synthesis, decisions (immutable). |
| [`CHANGELOG.md`](CHANGELOG.md) | changelog | Model-version history (covers `VERSION`). |

The type enum for all of the above is [`_types.yml`](_types.yml).

## Not governed here

- **`payload/**`** and **`examples/**`** — distributable templates and example artifacts.
  They are validated when **instantiated** in a target repo, not as files sitting in the master.
- **`spec/deck.html`** — an HTML teaching artifact with no YAML front matter; it is a
  **companion** of [`spec/model.md`](spec/model.md), tracked via that spec's `covers:` list.
- **`VERSION`** — data, not a document.

## Where the governance rules live

This master has **no separate `docs/governance.md`**. Its governance rules **are**
[`spec/model.md`](spec/model.md) + [`spec/front-matter.md`](spec/front-matter.md) — this
package *is* the model. The per-repo wiring is in [`.docgov/manifest.yml`](.docgov/manifest.yml).
