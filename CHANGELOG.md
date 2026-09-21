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

## [0.3.1] — 2026-09-21

### Added
- **`**Proof:**` takes a bullet list.** A list opening on the line right under the marker is
  read as one citation with several paths, each checked and reported at its own line. The
  first repo to write the marker at scale produced a stack of one-line `**Proof:**`
  paragraphs whenever a claim rested on more than one spec; that is now one block. A list
  starting further down the paragraph is still not chased.

## [0.3.0] — 2026-09-19

The index stops being a promise. Until now the model's central claim — *front matter **is**
the index* — was unfalsifiable, because nothing compared the map to the front matter; the
first repo to adopt at scale had **29 of 44** `registry: always|decide` docs missing from its
hand-kept `MAIN.md`. This release generates the map and gates it. It also gives adopters who
pin the tool a supported way to add their own rules, which pinning had quietly taken away.
Rationale: [`docs/decisions/0001-v0-3-0-generated-index-extension-hooks-proof-marker.md`](docs/decisions/0001-v0-3-0-generated-index-extension-hooks-proof-marker.md).
Migration: [`migrations/0.2.1-to-0.3.0.md`](migrations/0.2.1-to-0.3.0.md).

### Fixed
- **`paths.index` resolved to the string `manual` in the shipped payload template.** The
  manifest parser matched keys line-wise with no path context, so `paths.index` and
  `options.index` were one key to it and the last one won. The parser is now nesting-aware,
  and `options.index` is renamed to **`options.index_mode`** so the two can never collide
  again. **Breaking** for `.docgov/manifest.yml`; step 1 of the migration.
- **A folded `description: >` was captured as the bare fold indicator**, dropping the
  sentence. Nothing consumed `description` before the generator, so no result changes.
- **`**Proof:**` inside a fenced block is no longer chased** — a guide that documents the
  convention must not fail on the example it shows.

### Added
- **`docgov index [--write|--check]`** — the map emitted from `registry` + `type` +
  `description`, between `<!-- docgov:index -->` markers so hand-written prose survives.
  Sections are one per `type`, in `_types.yml` declaration order, headed by that type's
  `description`: the enum is already the outline, so the order lives in one place.
  `--check` fails CI when the block is stale (model §9.2, no longer deferred).
- **Repo-local checks in `.docgov/checks/*.py`** — `check(root, doc, fields)` runs after the
  built-ins, findings merged into the same output and exit code; `sources(root, doc, fields)`
  adds drift anchors to the sweep. `fields` carries `.covers`, `.text`, `.types`, `.manifest`,
  `.tier` and `.derived_status` so a rule never re-parses a file docgov has already read.
  A hook that raises, or fails to import, is a finding — a broken rule must not read as a pass.
- **The `**Proof:**` claim→evidence edge** — a backtick-quoted repo path on a `**Proof:**`
  line must resolve; the one check priced per paragraph rather than per document. Inert in a
  repo that never writes the marker. It fails *open* on a path with no extension.
- **`docgov adr next` / `docgov adr audit`** — the next free ADR number across every ref the
  checkout already has, and a report of slug/number disagreements. Neither fetches.
- **A duplicate ADR number within one working tree is a finding** — the state a rebase
  actually leaves behind. Cross-*branch* disagreement is a **warning on stderr, outside the
  exit code**: `check` runs on a depth-1 single-branch CI checkout, where the honest answer
  is "I cannot see the other branches", not "they agree".
- **`.doc-todo` entries may name one check** — `path  # check:<name>`. A bare line still
  exempts the whole document; naming a check keeps a grandfather entry from silently widening
  into a blanket one as checks are added (the §9.6 ratchet only shrinks if an entry cannot
  grow on its own).

### Changed
- **`registry: decide` has semantics.** It was an "index inclusion hint" with three values and
  no rule anywhere in the spec; a generator forced the question. `always` → always listed,
  `none` → never, `decide`/absent → listed iff `tier: canonical` and a non-terminal status.
- **One manifest spelling** across master, payload, tests and the CLI: `paths.index`,
  `paths.types`, `paths.decisions`, `paths.doc_todo`. The long forms still read.

### Not in this release
- **Sub-document drift.** Re-attestation is priced per document, so a 22-doc backlog re-reads
  22 whole documents. The cheaper experiment — surfacing drift as a PR comment on the touched
  docs rather than a nightly list nobody opens — should run before paragraph-level anchors
  are built.

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
