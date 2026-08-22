---
class: immutable
type: adr
tier: canonical
id: "0001"
title: Adopt the documentation-governance model
date: "{{DATE}}"
status: accepted
superseded_by: none
owner: "{{OWNER}}"
---

# ADR-0001 — Adopt the documentation-governance model

## Context

Docs in this repo drift without anyone noticing. Three failure modes recur:

- **Competing registries** — more than one hand-kept index of "what docs exist,"
  each maintained by a different person, silently disagreeing.
- **Silent staleness** — a doc describes code that has since changed; nothing flags
  it, so agents and humans cite it as current truth long after it stopped being true.
- **Un-propagated decisions** — a decision is ratified (in a PR, a chat, an ADR) but
  never folded into the durable reference docs, so the codebase and its docs diverge.

We need trust in a doc to be **computable from front matter alone**, not inferred by
reading the body or by asking who wrote it.

## Decision

Adopt the portable documentation-governance model, pinned at
`model_version {{MODEL_VERSION}}` (`0.2.0`):

- **Three maintenance classes** — `immutable` (never edit, supersede) · `living` (keep
  fresh against `covers[]` code) · `transient` (edit until `status` resolves).
- **A derived citeability `tier`** — `canonical` (cite) · `source` (raw evidence, inform
  only) · `archive` (history). Derived from class + type-rawness + terminality, never
  hand-set.
- **A repo-local `type`** enum in [`docs/_types.yml`](../_types.yml), each type declaring
  its default class and required fields.
- **One generated index** (this repo's index file, e.g. `MAIN.md`) — hand-kept registries are banned.
- **A blocking CI gate** validating front matter, tier correctness, `covers[]` existence,
  the retire-on-ship rule, and a shrink-only `.doc-todo` grandfather list.

The normative spec is the master at
`~/.dotfiles/project-management/docs-governance/spec/model.md`; the in-repo summary is
[`docs/governance.md`](../governance.md).

## Consequences

- Every governed `.md` must carry conformant front matter; the 5-doc minimum set exists.
- Trust becomes a front-matter computation (`CITABLE`), removing "ask the author" and
  "read the whole doc" from the loop.
- **Enforcement is manual for now** — the `docgov` CLI (index generation + validator + CI
  gate) is deferred; until it is pin-installed, authors uphold the schema by hand.
- Superseding this model means a new ADR that sets this one's `superseded_by`; this file
  is never edited in place.
