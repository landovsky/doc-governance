---
class: immutable
type: record          # a point-in-time provenance record — supersede, don't edit
tier: canonical
title: How we arrived at the v0.2 documentation-governance model
status: accepted
date: 2026-08-20
owner: "@landovsky"
description: >
  The design history of the portable documentation-governance model — the evidence,
  the synthesis, the objections that reshaped it, and the decisions taken — so a future
  reader understands not just the model but why it has this shape.
---

# How we arrived at v0.2

> This is a **record**, not a living doc. If the model changes again, write a new record;
> don't rewrite this one. The normative model is [`spec/model.md`](spec/model.md); the
> teaching artifact is [`spec/deck.html`](spec/deck.html); the working handoff (state +
> open items) lives external to this package.

## The problem we started from

Two failure modes, both observed live in real repos, motivated the whole thing:

1. **Competing sources of truth.** Pharmacy had *three* disagreeing brief registries
   (`briefs-data.js` = 23, `briefs.json` = 21, a README table = 21); a skill file claimed
   one was auto-generated when it wasn't. hriste had `MAIN.md` + `registry.json` both
   pointing at a file that had been renamed.
2. **Silent staleness / un-propagated decisions.** Pharmacy: a "Resolved Questions"
   section ratified a `Website` model that was never built (schema table present, no model,
   a stub comment "will move in Phase 6"); a brief handed to an external developer described
   five routes when `routes.rb` had two, written present-tense as fact; a *foreign repo's*
   audit doc was carried in and read as binding agent instructions.

The goal became one **portable** model — a front-matter grammar + a generated index + a CI
gate — so anyone (human first, agent second) opening any repo can answer per document, in
seconds: *What is this? Must I keep it fresh? Can I trust it as current? Where does it go?*

## The path

**v0.1 (parallel session `4b81b5`).** Produced the skeleton that survived: three maintenance
**classes** — `immutable` / `living` / `transient` — a two-layer split of a closed **model
layer** and an open per-repo **`docs/_types.yml`** type enum, a **generated** index, and the
intent to enforce via CI. Trust was a derived `current | historical` binary.

**Evidence base — two read-only inventories.** We censused every markdown file in **hriste
(376)** and **pharmacy (127)**. They surfaced the failure modes above and one load-bearing
insight: naming each file's type in 2–4 words produced **~70 distinct "types" for 127 files**,
which collapsed to ~15 because the "types" were really **attributes** — audience, lifecycle
phase, granularity, domain. That is why the model separates a small set of classes/types from
orthogonal attributes.

**Synthesis.** A three-architect panel (few-primitives×attributes / lifecycle-state-machine /
agent-minimum-context) was merged into one opinion. The critique found the single real bug in
v0.1: **`immutable` collapsed two opposite things** — a citeable ADR and a never-cite
transcript. Same edit rule ("never edit"), opposite answer to "can I trust it as current?".

**The AI-Jam (Phase 3 presentation).** Presenting v0.1 to the group produced three objection
clusters — which turned out to be a live eval that pinpointed exactly that seam:

- **(a) Radek & David — "an ADR is `immutable`, but it's really *historical*."** An ADR and a
  finished spec both feel like a decision valid at a date that may no longer hold — so why is
  one `immutable` and the other `transient`/archived? The seam: `immutable` was answering two
  questions at once.
- **(b) David — "a `transient` has only a hand-set `status`; that can drift."** `living` has a
  drift trip-wire (`last_verified`); `transient` had only a status someone must remember to flip.
- **(c) The archive/portability objection.** On supersede (e.g. Postgres→MySQL), is the old doc
  deleted or archived? And "isn't the class assignment subjective per project?"

## What the objections changed (v0.1 → v0.2)

- **Derived citeability `tier` (canonical / source / archive)** — the headline change. It
  splits "do I edit it?" (`class`) from "may I cite it?" (`tier`). Now `immutable × canonical`
  = ADR (cite), `immutable × source` = transcript (never cite), and a superseded ADR derives
  to `archive` — that "historical decision" the room was reaching for. **Answers (a).**
  - **Decision (b over a): keep 3 classes + a derived `tier`, rather than add a 4th `source`
    class.** Both fix the bug; the tier axis was chosen so the class set stays at three and
    citeability becomes a computed property, never hand-set.
- **`ships:` link + retire-on-ship gate** — a `transient` names the PR/issue that closes it and
  CI archives it on merge, so resolution is derived, not a status that can itself drift.
  **Answers (b).**
- **Supersede-not-delete + the model/repo two-layer split** — immutable records are never
  deleted (set `superseded_by`, derive to `archive`); portability is real because the classes
  are fixed while types are per-repo in `_types.yml`. **Answers (c).**
- Plus: `owner` + `updated` in the required core (the steward loop needs an assignee; `updated`
  ≠ `last_verified`); the **`ADR → reference` propagation** edge and a check that a merged ADR's
  `covers[]` docs were touched (the un-propagated-decision failure); and the **`covers[]`
  -existence** check (kills cross-repo contamination in one rule).

## The cautionary tale we designed against

hriste already *had* a governance layer — `MAIN.md`, `governance.md`, `registry.json`, ADRs —
and it still rotted: its front-matter validator covered ~21 of 376 files and was **not wired
into CI**; ADR 0008/0009 headings were off-by-one (a rule the governance doc itself said "don't
repeat"); and ADR-0011 ("generate the registry from front matter") was ratified and never built.
**Lesson: the taxonomy survived; the lack of enforcement is what killed it.** So in v0.2,
enforcement (a blocking CI gate, one generated index, a shrink-only `.doc-todo` grandfather
ratchet) ships *with* the model, not as a follow-up.

## Provenance

- **`4b81b5`** (CC session, `hriste/Doc-governance model design`) — v0.1 + the slide deck.
- **`6d3a29`** (CC session, `hriste/Docs-governance synthesis for pharmacy repo`) — the two
  inventories, the synthesis, the critique, and this master.
- On-disk artifacts: [`spec/model.md`](spec/model.md), [`spec/deck.html`](spec/deck.html),
  and the working handoff (state + the remaining open decisions D-2…D-9), which lives external
  to this package. D-1 — the `source` fix — was resolved here as option (b).
