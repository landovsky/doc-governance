---
class: living
type: changelog
title: "Documentation Governance — changelog"
covers: [VERSION]
last_verified: 2026-08-22
description: "Model version history"
---

# Changelog

Model-version history for the docs-governance system. Newest first.
Format follows [keep-a-changelog](https://keepachangelog.com/). See
[`PROVENANCE.md`](PROVENANCE.md) for the rationale behind these changes.

## [0.2.1] — 2026-08-22

Readability cull — trim the front-matter surface to fields something actually consumes,
and formalise the trust field the `living` class depends on. Migration:
[`migrations/0.2.0-to-0.2.1.md`](migrations/0.2.0-to-0.2.1.md).

### Removed
- **`updated`** — nothing consumed it; git shadows "content last changed" (`git log -1`).
  Kept the anchors git can't derive (`date`, `event_date`, `last_verified`).
- **`audience`** and **`granularity`** — descriptive attributes no rule consumed; `audience`
  was `both` most of the time (no signal). Filter on `type` instead.

### Changed
- **`status` authored only on `transient`.** Derived for `living` (`active|stale|retired`) and
  `immutable` (`accepted|superseded`), surfaced only when non-default — `grep status:` becomes
  the stale/retired worklist.
- **`owner` → manifest default + optional per-doc override.** Single-steward repos stop copying
  the handle onto every file; the sweep falls back to `.docgov/manifest.yml:owner`.
- **Required core is now `class`, `type`, `title`** + the class's date-of-record.

### Clarified
- **`last_verified` is a steward attestation** — an agent may propose a value or report a clean
  check but never stamps today's date on its own judgment; backfill uses the last
  genuine-confirmation date (**adopted ≠ verified**).

### Tooling
No model change — interim `bin/docgov` and CI distribution only (tag re-pointed while
still pre-release; hriste is the sole, un-merged adopter).
- **`docgov check`/`sweep` gain `-v`/`--verbose`** — lists every governed doc scanned (to
  stderr; stdout stays the findings channel).
- **Scope fix:** `governed_docs()` now prunes dot-directories (`.pytest_cache/`, `.venv/`, …),
  so a tool-generated `README.md` no longer trips `check`.
- **CI fetches a pinned `docgov`** instead of a vendored copy: the payload workflow curls the
  tag-pinned `payload/bin/docgov` (`env.DOCGOV_VERSION`) from the model repo — reproducible,
  no drift. `bin/docgov` is now local/dev-only.

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
