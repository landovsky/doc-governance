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

## Enforcement

`docgov` runs the gate. CI fetches the version pinned in `.github/workflows/docs.yml`, so
what blocks a merge is a tagged upstream, not whatever happens to sit in `bin/`.

| Command | When | Blocking |
|---|---|---|
| `docgov check` | every PR | **yes** — front matter, tiers, `covers[]` existence, dead links, ADR numbering, `**Proof:**` citations, repo-local rules |
| `docgov index --check` | every PR | **yes** — fails when the generated map is stale |
| `docgov index --write` | after any front-matter edit; nightly | — regenerates the map |
| `docgov sweep` | nightly | no — advisory freshness drift |
| `docgov adr next` | before writing an ADR | no — the next number free on every visible branch |

The index file (e.g. `MAIN.md`) is an **artifact**, never a hand-kept registry: the region
between `<!-- docgov:index -->` markers is generated from front matter and an edit to it is
lost on the next run. Prose outside the markers is yours and survives.

### Repo-local rules

A house rule belongs in `.docgov/checks/<name>.py`, **not** in a patch to `bin/docgov` —
CI fetches the pinned upstream, so a patched CLI never runs in CI and is overwritten by the
next version bump.

```python
def check(root, doc, fields):
    """Return [(message, front_matter_key | None), …]. Findings gate like any built-in."""
    return [] if fields.get("domain") else [("house rule: domain required", "title")]
```

`fields` is the front-matter dict and also carries `.covers`, `.text`, `.types`,
`.manifest`, `.tier` and `.derived_status`. A module may export
`sources(root, doc, fields) -> [path, …]` to add drift anchors beyond `covers[]`. Modules
named `_*.py` are helpers. A rule that raises, or fails to import, is a finding.

To grandfather a doc against **one** check rather than all of them, name it in
`.docgov/.doc-todo`:

```
docs/legacy/old-thing.md  # check:house_rule — grandfathered for the house rule only
```
