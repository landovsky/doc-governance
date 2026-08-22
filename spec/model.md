---
class: living
tier: canonical              # derived: living + not-drifted + not-terminal
type: model-spec             # repo-local type (_types.yml)
title: Documentation Governance Model — v0.2.1
covers:
  - spec/learn.html       # the teaching page must stay in sync with this spec
last_verified: 2026-08-22
description: >
  Portable documentation-governance model — three maintenance classes × a derived
  citeability tier × a repo-local type — with code-coupled freshness, a generated
  index, and a CI gate. The normative model; the teaching artifact is spec/learn.html.
---

# Documentation Governance Model — v0.2.1

> **Portable model, not a hriste doc.** It is meant to be identical across every repo.
> This is the **normative spec** (the model itself); the teaching artifact is
> [`spec/learn.html`](learn.html). The working handoff (state + open items) is external
> to this package. The v0.2 change over v0.1 is the **citeability `tier`** (§4); v0.1 had none.

## 1. Thesis

Every markdown file declares, in YAML front matter, a maintenance **`class`** (the primary axis —
what an agent actually acts on), a derived **`tier`** (may I cite it as current truth?), and a
repo-local **`type`** (a semantic label, not a behaviour). Audience / phase / granularity / domain
are **attributes**, never types. **Trust is computed from front matter alone** — an agent never
reads a body to decide whether it may cite a doc. There is **one index, generated from front
matter** (hand-kept registries are banned), and a **blocking CI gate ships in the same PR as the
model**, adopting via a shrink-only grandfather list.

## 2. The axes (all orthogonal)

```
class   (model layer, CLOSED)      — maintenance: how / whether to keep it fresh
tier    (DERIVED, never hand-set)  — citeability: canonical | source | archive
type    (repo layer, OPEN)         — semantic label in docs/_types.yml; declares its default class
attributes (per document)          — phase | domain | language
```

`class ⊥ tier ⊥ type`. This is the v0.1→v0.2 fix: v0.1's `immutable` answered two questions at once
("do I edit it?" **and** "can I trust it now?"), so a transcript and an ADR — same edit rule,
opposite citeability — collapsed together. Splitting `tier` out separates them.

## 3. Classes — 3 maintenance classes (closed, model layer)

| class | keep fresh? | edit rule | "stale" when… | lifecycle |
|---|---|---|---|---|
| **immutable** | never | never edit — supersede with a new doc | never — true as of its `date` | born → (`superseded_by`) |
| **living** | continuously | edit freely | a `covers[]` path has a commit newer than `last_verified`, or a `covers[]` path stops existing | born/promoted → re-verified → retired when the code goes |
| **transient** | until it resolves | edit until resolved | its `status` reaches a terminal value | status → resolved → drops from current view |

`class` is closed and portable. `type` is repo-local (`docs/_types.yml`) and **declares** its
default class — that is where product-specific needs live (`seo-audit`, `gitops-runbook`, `transcript`).

## 4. Tier — citeability (derived, never hand-set)  ← the v0.2 addition

| tier | may an agent cite it as current truth? | how it's derived |
|---|---|---|
| **canonical** | yes — trust it as what its `type` says it is | class ∈ {immutable, living}, type not raw, not terminal |
| **source** | **no** — inform only, weight by `event_date` | the `type` is declared *raw* in `_types.yml` (`transcript`, `audit`, `research`, `experiment`) |
| **archive** | no — history only | terminal: transient resolved-&-unpromoted · immutable superseded · living archived (covers[] gone) |

### The `class × tier` grid (what the split buys)

|              | canonical — *cite* | source — *never cite* | archive — *history* |
|--------------|--------------------|-----------------------|---------------------|
| **immutable**| **ADR**            | **transcript · audit**| superseded ADR      |
| **living**   | reference · domain-doc · runbook · index | — | archived reference |
| **transient**| active brief / spec *(as plan)* | — | shipped / dropped spec |

`immutable` no longer means one thing: **immutable × canonical = ADR** (cite it),
**immutable × source = transcript** (never cite). Two invariants fall out:

- **`source ⟹ immutable`** — raw evidence is always frozen; the `source` column only has immutable rows.
- **`tier` replaces v0.1's `trust: current|historical`** — `canonical` ≈ current-and-citable,
  `archive` ≈ historical, and `source` is the case that binary could not express.

## 5. Front-matter schema

**Always required (core):** `class`, `type`, `title`. Nothing else is universal — everything below
is conditional on class, derived, or optional. (v0.2.1 removed `status`, `owner`, and `updated` from
the universal core; see §12.)
**Conditional by class:**
- `immutable` (non-raw) → `date` (the moment it is true as of); a **raw** immutable doc uses `event_date` (below), not `date`
- `living` → `covers[]` **and** `last_verified` *(a `last_verified` with no `covers[]` is rejected — a freshness promise with nothing to check is the undead field both repos already carry)*. **`last_verified` is a steward attestation, not a machine check result:** a human sets it when they have re-confirmed the doc against its `covers[]`. An agent may run the check and *propose* a value, but **never stamps today's date on its own judgment** — symmetric to `stale`, which only the nightly sweep sets. (A clean automated scan means "no conflict found," not "a steward vouches for this"; only the latter may bump the field that `CITABLE` trusts.)
- `transient` → `status` from a closed enum **with a terminal done-state** (`draft | active | shipped | superseded | archived | killed | stale`; `stale` is set by the nightly sweep, not by hand). *This `status` is the only class-level requirement.* `ships:` (the #PR/issue that retires it) is a model-layer **optional** attribute (its role is the retire-on-ship link); a repo can make it **required** on a specific transient *type* via `_types.yml` (§10) — this package does on `spec`, so a `spec` must carry `ships` here, while a `pitch`/`brief` need not.
- raw types (`source` tier) → `event_date`, and `source_of:` once distilled
- **`entry`-type living docs** → `covers[]` lists the docs/config the entry indexes or mirrors (not code); they still carry `last_verified`.

**`status` is authored only on `transient`.** For `living` it **derives** to `active | stale | archived`
(the sweep sets `stale` when covered code drifts; a living doc whose `covers[]` paths all cease to exist is
terminal → mark `status: archived`, which derives `tier: archive`); for `immutable` to `accepted | superseded`
(from `superseded_by`). Write it on a `living`/`immutable` doc **only when non-default** — so a bare
`grep -r 'status:'` returns exactly the drifted / archived / superseded docs. Absent `status` means the
derived default via `status(doc)` (§6): `active` for living, `accepted` for non-raw immutable; a raw /
`source`-tier doc has **no meaningful status** (leave it off — `tier: source` already blocks citation).
**`owner` is a repo-level default** in `.docgov/manifest.yml`; a per-doc `owner:` is an **optional
override** for a doc with a different steward. The sweep notifies the doc's owner, or the manifest
default when none is set.
**There is no `updated` field.** Content-last-changed is read from git (`git log -1`); front matter keeps
only the temporal anchors git cannot derive — `date`, `event_date`, `last_verified`.
**Derived (never hand-set):** `tier` (§4); and `status` for `living` / `immutable` (above).
**Optional attributes:** `phase` (pitch|brief|spec — transient only), `genre`
(transcript|audit|research|experiment — raw types), `domain`, `language` (cs|en),
`description` (drives the index line), `registry` (always|decide|none),
`promoted_to` / `superseded_by`, `ships` (#PR/issue that retires a transient), `owner` (per-doc override).

## 6. The freshness contract (the one predicate an agent runs)

```
CITABLE(doc) :=
      doc.tier == canonical
  AND status(doc) ∈ {active, accepted, generated}      # DERIVED (below) — never a bare doc.status
  AND ( doc.class == immutable                         # cite as of its date
        OR ( doc.class == living
             AND now ≤ last_verified + TTL(type)
             AND every path in covers[] exists in THIS repo
             AND no covers[] path has a commit newer than last_verified ))
# status(doc) := doc.status if present (always on transient; a non-default value on living/immutable)
#             else living    → active                            # derived default
#             else immutable → superseded  if superseded_by set
#                              accepted     else if type not raw  # ADR / record default
#                              n/a          else                  # raw/source: status not a meaningful axis
# tier == source            → never citeable (inform only, weight by event_date)
# transient (active)        → citeable as intent, NOT as current system state
# tier == archive / terminal → history only
TTL defaults: reference 180d · playbook 90d · immutable ∞ · index 0 (regenerate)
              transient = event-driven (ship/kill, not time) · source = n/a
```

## 7. Transformation DAG (`from → to : trigger`; ★ = the edges both repos failed)

```
source(transcript)          → transient(pitch|brief) : a meeting becomes a proposal
source(research|audit|exp)  → transient(spec)        : evidence folded into a plan
source(audit, recurring)    → living(playbook)       : a repeated audit becomes a procedure
transient(pitch→brief→spec)                          : phase advances (accepted → committed → detailed)
transient(spec) → immutable(ADR)                     : ON SHIP, iff a non-obvious choice is ratified
transient(spec) → living(reference)   ★ MANDATORY    : ON SHIP, "what we want" becomes "what is true"
transient(spec) → living(playbook)                   : ON SHIP, iff it changes deploy/operate
transient(spec) → archive             ★ MANDATORY    : ON SHIP or KILL (status terminal)
immutable(ADR)  → living(reference)   ★              : a ratified decision PROPAGATES into durable docs
immutable(ADR)  → immutable(ADR)                     : supersession (old stays, derives to tier:archive)
living → living'                                     : a covers[] path changed → update + bump last_verified
```

Rules: promotion sets `promoted_to:` and flips the upstream transient to `tier: archive`; a transient
links to the work that closes it via `ships: #PR`, and CI archives it automatically on merge (drift
solved by a link, not a hand-set status); shipping without promotion leaves the spec as historical
intent (kept, dropped from the current view); the transcript stays `source` forever. Not every promotion
needs an ADR — only ratified non-obvious choices. Default: `brief` and `spec` are the **same** transient
type with an advancing `phase` (avoids proliferation).

## 8. Minimum required set (5 — every repo carries these)

| Member | class / type | Why non-negotiable |
|---|---|---|
| `README.md` | living / entry (overview) | bootstrap: what the repo is, how to run/test |
| `MAIN.md` | living / entry (**generated** index) | the one navigation surface; generated so it can't fork into disagreeing copies |
| `CLAUDE.md` = `AGENTS.md` | living / entry (agent) | conventions; without it agents import foreign process |
| `docs/governance.md` | living / entry | this grammar, in-repo & citable (may fold into `MAIN.md` for small repos) |
| an *adopt-this-model* ADR | immutable / adr | rationale is the one thing code can't encode. Lives in the repo's ADR home (`.docgov/manifest.yml:paths.decisions`), per its numbering/format — not a fixed path. |

The generated index (`registry.json`) is an **artifact**, not a sixth hand-kept file.

## 9. Enforcement (ships WITH the model)

1. **Blocking CI job from commit #1** — red build = merge blocked (not stderr warnings on 18%).
2. **One generated index; hand-kept registries deleted in the adoption PR.** Editing the generated index fails CI.
3. **Validator on 100% of canonical docs:** required keys present; `class`/`type`/`status` in-enum & legal; `tier` matches its computed value; `covers[]` present for living; **every `covers[]` path exists in THIS repo** (kills cross-repo contamination *and* un-propagated decisions); no dead internal links; ADR heading == filename number; every governed doc reachable from the index.
4. **Retire-on-ship gate:** a PR closing an issue linked to a `transient(spec)` must add/patch a `living(reference)` (+ADR if a choice was encoded) and archive the spec, or CI fails.
5. **Nightly freshness sweep:** flips any drifted canonical doc to `status: stale`, opens an issue, comments on PRs that touch a `covers[]` path without bumping `last_verified`.
6. **Grandfather ratchet:** a `.doc-todo` list of pre-existing non-conformant files; it may **only shrink**; new/touched files must be clean.

## 10. Two-layer split

- **Model layer** (closed, portable, rare to change): the 3 classes, the tier derivation, the front-matter core, the invariants. Identical across every repo.
- **Repo layer** (open): `docs/_types.yml` declares the local type enum — each entry names its default `class`, a `raw: true` flag for `source`-tier types, and its required attributes. Adding a type = one line, no model change.
- **Guardrail:** an explicit "does NOT belong in docs" rule so the enum can't re-grow into dozens of pseudo-types — customer/bot copy → `app/i18n`/CMS; living item-lists → Issues/`bd`.

## 11. v0.1 → v0.2 changelog

- **+ citeability `tier`** (canonical/source/archive), derived — the headline change. v0.1 had only `trust: current|historical` and collapsed cite-able ADRs with never-cite transcripts under `immutable`. Decision **D-1 resolved as (b): keep 3 classes + a derived `tier`.**
- **+ `owner`, `updated`** in the required core (the steward loop needs an assignee; `updated` ≠ `last_verified`).
- **+ `immutable(ADR) → living(reference)` propagation edge** + CI check that a merged ADR's `covers[]` docs were touched.
- **+ `covers[]`-existence check** (not just drift).
- **+ `ships:` link + retire-on-ship gate** so a transient's resolution is derived, not a hand-set status that can itself drift.
- **+ out-of-scope guardrail** on the open `_types.yml`; **+ concrete minimum set**.
- **Kept from v0.1:** two-layer model/repo split; `class` primary with `type` a repo label; `.doc-todo` grandfathering.

## 12. v0.2 → v0.2.1 changelog

Readability cull — trim the front-matter surface to fields something actually *consumes*, and formalise
the trust field the `living` class hangs on.

- **− `updated`** from the required core. Nothing read it (`CITABLE`, tier derivation, and the sweep
  never did); git already shadows "content last changed" (`git log -1`). Kept the anchors git *cannot*
  derive — `date`, `event_date`, `last_verified`. Deleting an unread required field is the same
  undead-field logic that already rejects a `last_verified` with no `covers[]`.
- **− `audience`** and **− `granularity`** — descriptive attributes no rule consumes; `audience` was
  `both` most of the time, so it carried no signal. Filter on `type` instead. Re-add either with teeth
  (a real consumer) if one ever lands.
- **`status` authored only on `transient`.** For `living` / `immutable` it derives (`active|stale|archived`,
  `accepted|superseded`) and is surfaced only when non-default — which turns `grep status:` into the
  stale/archived worklist.
- **`owner` → manifest default + optional per-doc override.** A single-steward repo stops copying the
  same handle onto every file; the sweep falls back to `.docgov/manifest.yml:owner`.
- **`last_verified` is a steward attestation** (§5): an agent may propose a value or report a clean check
  but never stamps today's date on its own judgment; backfill uses the last genuine-confirmation date
  (**adopted ≠ verified**). Formalises the one field the whole `living`-class trust computation depends on.

New required core: `class`, `type`, `title` + the class's date-of-record.
Migration: [`../migrations/0.2.0-to-0.2.1.md`](../migrations/0.2.0-to-0.2.1.md).
