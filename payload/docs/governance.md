---
class: living
type: entry
tier: canonical
title: "{{REPO_NAME}} — Documentation Governance"
covers: [docs/_types.yml]
last_verified: "{{DATE}}"   # steward attestation — today is honest for this freshly-authored doc
description: >
  How this repo governs its docs: the class × tier × type model, the repo type enum,
  the 5-doc minimum set, and the (currently manual) enforcement.
---

# {{REPO_NAME}} — Documentation Governance

This repo follows the portable **documentation-governance model `{{MODEL_VERSION}}`**
(default `0.2.1`). The normative master lives at
`~/.dotfiles/project-management/docs-governance/spec/model.md` — read it for rationale;
this page is the in-repo, citable summary.

## The model in one paragraph

Every governed `.md` declares, in YAML front matter, a maintenance **`class`**
(`immutable` — never edit, supersede · `living` — keep fresh against `covers[]` code ·
`transient` — edit until its `status` resolves), a derived citeability **`tier`**
(`canonical` cite it · `source` raw evidence, inform only · `archive` history), and a
repo-local **`type`**. Trust is computed from front matter alone — see the front-matter
schema reference (canonical model: the docs-governance master in your dotfiles —
`spec/front-matter.md`, `spec/model.md`) and the `CITABLE` predicate. `tier`
is **derived, never hand-set**.

## Repo type enum

The types this repo recognizes — each declaring its default `class`, `raw:` flag, and
required fields — live in **[`docs/_types.yml`](_types.yml)**. Adding a type is one line;
it never changes the model. Attributes (phase, domain, language) are never types.

## Minimum set (this repo carries all 5)

| Member | class / type | Why |
|---|---|---|
| `README.md` | living / entry | what the repo is, how to run/test |
| `MAIN.md` | living / entry (**generated** index) | the one navigation surface |
| `CLAUDE.md` (= `AGENTS.md`) | living / entry | agent conventions |
| `docs/governance.md` | living / entry | this page — the grammar, in-repo |
| `docs/decisions/` + `ADR-0001` | immutable / adr | rationale; ADR-0001 adopts this model |

## Enforcement — manual for now

The `docgov` CLI (generated index + validator + CI gate + `.doc-todo` ratchet) is
**deferred**. Until it is pin-installed, index generation and linting are **manual**:
author front matter to the schema reference (canonical model: the docs-governance master
in your dotfiles — `spec/front-matter.md`, `spec/model.md`), and keep the generated
index (this repo's index file, e.g. `MAIN.md`) as an artifact — never a hand-kept registry.
