---
class: immutable
type: adr
tier: canonical
id: "0001"
title: "v0.3.0: generated index, extension hooks, the Proof marker — and one manifest spelling"
date: "2026-09-19"
superseded_by: none
---

# ADR-0001 — v0.3.0: generated index, extension hooks, the Proof marker — and one manifest spelling

## Context

The first repo to adopt the model at scale (`landovsky/hriste`, 44 governed docs,
`tooling: pinned`) hit four limits at once. They are not four CLI tickets; together
they change the model's contract, which is why this is an ADR.

**The index is not generated, so it is not trusted.** `MAIN.md` is hand-written
(`options.index: manual`, deferred since 0.1.0). In hriste, **29 of 44
`registry: always|decide` docs are not linked from it** — every business-domain doc,
every task-management mechanics doc, the whole `docs/reference/catalog-*` set. The tell
is in that repo's `CLAUDE.md`, which instructs agents to `grep -rl '^registry: always'`
*instead of* reading the map. The model's central claim is that front matter **is** the
index; a hand-kept map falsifies it in practice.

**A repo-local rule cannot gate a merge.** hriste added a `dead_proof_links` check by
editing its `bin/docgov`. Under `tooling: pinned`, CI fetches the tagged master, so the
check never runs in CI — and the next `DOCGOV_VERSION` bump overwrites it. The model
told adopters to pin, then left them no supported way to extend.

**`**Source:**` was carrying two meanings.** In hriste it means "proved by this spec"
29 times and "came from this meeting" 36+ times, with nothing checking either. Their
ADR-0050 split it: `**Proof:**` cites evidence as a backtick-quoted repo path;
`**Source:**` stays free-prose provenance.

**ADR numbers collide across branches.** hriste has 40 distinct ADRs across open
branches under **up to five numbers each** (`bom-component-override` is 0008, 0013,
0018, 0024, 0026). Every rebase renumbers and rewrites inbound links. `paths.decisions`
is already in the manifest, so the master can answer "next free number" better than a
human scanning one working tree.

**The blocker under all of it: the manifest has no single spelling, and the parser is
nesting-blind.** Master uses `paths.index_file` / `paths.types_file`; payload uses
`paths.index` / `paths.types`; `manifest_scope()` matches `^\s*(?:index|index_file):`
line-wise with no path context, last match winning. Both manifests also key
`options.index`. Consequence, verified against the shipped payload:

```
matched -> 'index: MAIN.md   # generated documentation index / map'   (paths.index)
matched -> 'index: manual    # regenerate the index by hand'          (options.index)
FINAL index_file = manual
```

The template every adopter copies verbatim resolves its index to the string `manual`.
hriste dodged this by renaming its own key to `options.index_regen` — a local
workaround, documented in a comment in their manifest, not a divergence to standardise
on. A generator that reads the manifest cannot be built on top of this.

## Decision

Ship **0.3.0** — hooks, a generated index, a new manifest option and pinned-down
`registry` semantics are a contract change, not a patch — with
`migrations/0.2.1-to-0.3.0.md`.

**Fix the manifest first, inside the same bump.** One spelling across master, payload,
tests and `bin/docgov`; keys unique across the whole file so a nesting-blind parser
cannot mis-resolve; `options.index` renamed so it can never collide with `paths.index`
again. The migration guide carries the rename for adopted repos, including hriste's
`index_regen`.

**And make the manifest answerable, not just consistent.** The collision is one symptom
of a broader one: the manifest asserts things nothing checks. `options.ci: active` in
the master names `.github/workflows/docs-governance.yml`, and the master has no
`.github/` directory at all — CI has never existed in the repo that defines the model,
while its own manifest claims otherwise. (The payload's `ci: active` is honest;
`payload/.github/workflows/docs.yml` exists.) So 0.3.0 also adds a `check` rule that
`options.ci: active` implies the named workflow file resolves, and the master either
gets its own workflow or sets `ci: none`. A model repo failing its own gate is the one
inconsistency that cannot ship.

**Then, in this order** — each step unblocks the next, and the order is the release plan:

1. **`docgov index [--write|--check]`** — emit the map from `registry` + `description`
   + `type`, between `<!-- docgov:index -->` markers so hand-written prose survives.
   `--check` fails CI when the block is stale, mirroring the existing gate. Flips
   `options.index` from `manual` to `auto`.
2. **Extension hooks** — load repo-local checks from `.docgov/checks/*.py`, each
   exposing `check(root, doc, fields) -> list[tuple[str, str | None]]`, run after the
   built-ins, findings merged into the same output and exit code, `.doc-todo` honoured.
   The same idea for `sweep` (extra drift sources beyond `covers[]`).
3. **The `**Proof:**` marker** — a claim→evidence edge in the model: a backtick-quoted
   repo path that must resolve, ignoring backticked non-paths (`#method`, describe-block
   names) and markers inside code spans. Reference implementation to lift: hriste
   `bin/docgov` at commit `1d36f5c6`.
4. **`docgov adr next`** — a convenience, scanning local *and* remote branches under
   `paths.decisions`, plus a `check` warning when two branches disagree on a number for
   one slug.

## Consequences

The index becomes the model's own proof. Until 0.3.0 the claim "front matter is the
index" was unfalsifiable, because nothing compared the map to the front matter; `index
--check` makes it a gate, and hriste's 29 missing docs become a failing build rather
than a habit of grepping past the map.

Hooks change what "pinned" costs adopters. Today pinning means giving up local rules;
after 0.3.0 it means local rules live in `.docgov/checks/` and survive upgrades. This
also makes `**Proof:**` a real decision rather than a default: if it does not earn a
place in the model, it ships as the hook exemplar instead, and nothing is lost.

The new `ci` rule can fail an adopter's first 0.3.0 `check` — by design: it fails
exactly where the manifest was already lying. `ci: none` is always an honest answer and
always available.

The manifest rename touches every adopted repo, which is the cost of doing it now
rather than after a generator reads those keys. One adopter exists.

`docgov index --write` will rewrite `MAIN.md` wholesale for adopters whose map has
drifted. Adopters should land structural moves **before** generating: hriste's
`docs/business-context/` → `docs/domains/` migration rewrites ~22 inbound links, and
generating first means generating twice.

Sub-document drift (re-attestation priced per document — hriste has 22 drifted docs,
one for nine months) is **not** in 0.3.0. The cheaper experiment is surfacing drift as
a PR comment on touched docs rather than a nightly list nobody opens; run that before
building paragraph-level anchors.
