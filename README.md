---
class: living
type: entry
tier: canonical
title: Docs-Governance System
status: active
owner: "@landovsky"
updated: 2026-08-20
covers: [spec/model.md, VERSION]
last_verified: 2026-08-20
description: Master entry for the portable documentation-governance system (model v0.2.0) — the class × tier × type model, its payload, guides, and current adoption status.
---

# Docs-Governance System

A portable documentation-governance system you drop into any repo. It classifies
every doc along three axes and enforces the rules with a generated index, a CI
gate, and a grandfather ratchet:

- **class** (maintenance rule, immutable) — `immutable` / `living` / `transient`
- **tier** (citeability, *derived* from class + placement) — `canonical` / `source` / `archive`
- **type** (repo-local vocabulary) — e.g. `entry`, `adr`, `reference`, `runbook`

Current model version: **0.2.0** (see [`VERSION`](VERSION)).

## Directory map

- **`spec/`** — the normative model: `model.md` (spec), `front-matter.md` (field reference), `deck.html` (explainer).
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

> ## STATUS — tooling deferred
> The `docgov` Python CLI and its pinned install (`pipx install docgov==0.2.0`
> in CI) are **deferred to a later phase**. For now, **adoption, indexing, and
> checks are MANUAL** — the shipped CI workflow is a placeholder stub. The model
> spec, front matter, and config templates are stable and usable today.
