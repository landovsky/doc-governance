---
class: living
type: changelog
title: "Documentation Governance — changelog"
status: active
owner: "@landovsky"
updated: 2026-08-20
covers: [VERSION]
last_verified: 2026-08-20
description: "Model version history"
---

# Changelog

Model-version history for the docs-governance system. Newest first.
Format follows [keep-a-changelog](https://keepachangelog.com/). See
[`PROVENANCE.md`](PROVENANCE.md) for the rationale behind these changes.

## [0.2.0] — 2026-08-20

### Added
- **Derived citeability `tier`** (`canonical` / `source` / `archive`) — separates
  the *edit-rule* (class) from the *cite-rule* (tier); tier is derived, not authored.
- Required `owner` and `updated` front-matter fields on governed docs.
- **`ships:`** field on `transient` docs plus a **retire-on-ship** rule.
- **ADR → reference propagation** edge: an accepted ADR must propagate into the
  referenced living docs.
- **`covers[]`-existence check**: every path listed in `covers[]` must exist.

## [0.1.0]

### Added
- Initial portable model — 3 maintenance classes (`immutable` / `living` / `transient`).
- Two-layer split: a shared **model** vs. per-repo **type** vocabulary.
- Intent for a generated index and a CI gate. (From session `4b81b5`.)
