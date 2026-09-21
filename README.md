---
class: living
type: entry
tier: canonical
title: Docs-Governance System
covers: [spec/model.md, VERSION]
last_verified: 2026-08-22
description: Master entry for the portable documentation-governance system (model v0.3.1) — the class × tier × type model, its payload, guides, and current adoption status.
---

# Docs-Governance System

A portable documentation-governance system you drop into any repo. It classifies
every doc along three axes and enforces the rules with a generated index, a CI
gate, and a grandfather ratchet:

- **class** (maintenance rule, immutable) — `immutable` / `living` / `transient`
- **tier** (citeability, *derived* from class + placement) — `canonical` / `source` / `archive`
- **type** (repo-local vocabulary) — e.g. `entry`, `adr`, `reference`, `runbook`

Current model version: **0.3.1** (see [`VERSION`](VERSION)).

## Directory map

- **`spec/`** — the normative model: `model.md` (spec), `front-matter.md` (field reference), `learn.html` (interactive explainer).
- **`payload/`** — everything copied into an adopting repo (`.docgov/` config + `.github/` CI stub).
- **`guides/`** — human playbooks: `INSTALL`, `MIGRATING`, `DIRTY-REPO-PLAYBOOK`, `AUTHORING`.
- **`migrations/`** — version-to-version upgrade steps for the model.
- **`examples/`** — (planned) worked examples of conformant docs and repos (directory currently empty).
- **`README.md`** — this entry doc.
- **`VERSION`** — current model version string.
- **`CHANGELOG.md`** — model-version history.
- **`PROVENANCE.md`** — how and why the model reached its current shape.

## Start here

- **Adopting a repo?** → [`guides/INSTALL.md`](guides/INSTALL.md).
- **Understanding the model?** → [`spec/model.md`](spec/model.md).
- **Why is it built this way?** → [`PROVENANCE.md`](PROVENANCE.md).

> ## STATUS — the index is generated; two pieces of tooling still deferred
> **`bin/docgov` is real and the CI gate runs it:** `docgov check` (front matter,
> classes, tiers, `covers[]`, on-use field contracts, dead internal links, ADR
> numbering, `**Proof:**` citations, and repo-local rules from `.docgov/checks/`),
> `docgov index --check` (the map is generated from front matter and stale blocks
> fail CI — new in 0.3.0), `docgov sweep` (freshness drift) and `docgov adr next`
> all work today, and `.github/workflows/` runs the gate on every PR.
> Still deferred: `docgov adopt`, and the pinned `pipx install docgov==<ver>` (the
> vendored `bin/docgov` stands in until then). Model spec, front matter, and
> templates are stable and usable today.
