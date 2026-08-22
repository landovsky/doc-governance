---
class: living
tier: canonical              # derived: living + not-drifted + not-terminal
type: model-spec             # repo-local type (_types.yml)
title: Documentation Governance Model — v0.2
status: active
owner: "@landovsky"
updated: 2026-08-20
covers:
  - spec/deck.html        # the slide deck must stay in sync with this spec
last_verified: 2026-08-20
audience: both
description: >
  Portable documentation-governance model — three maintenance classes × a derived
  citeability tier × a repo-local type — with code-coupled freshness, a generated
  index, and a CI gate. The normative model; the teaching artifact is spec/deck.html.
---

# Documentation Governance Model — v0.2

> **Portable model, not a hriste doc.** It is meant to be identical across every repo.
> This is the **normative spec** (the model itself); the teaching artifact is
> [`spec/deck.html`](deck.html). The working handoff (state + open items) is external
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
attributes (per document)          — audience | phase | granularity | domain | language
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
| **archive** | no — history only | terminal: transient resolved-&-unpromoted · immutable superseded · living retired |

### The `class × tier` grid (what the split buys)

|              | canonical — *cite* | source — *never cite* | archive — *history* |
|--------------|--------------------|-----------------------|---------------------|
| **immutable**| **ADR**            | **transcript · audit**| superseded ADR      |
| **living**   | reference · domain-doc · runbook · index | — | retired reference |
| **transient**| active brief / spec *(as plan)* | — | shipped / dropped spec |

`immutable` no longer means one thing: **immutable × canonical = ADR** (cite it),
**immutable × source = transcript** (never cite). Two invariants fall out:

- **`source ⟹ immutable`** — raw evidence is always frozen; the `source` column only has immutable rows.
- **`tier` replaces v0.1's `trust: current|historical`** — `canonical` ≈ current-and-citable,
  `archive` ≈ historical, and `source` is the case that binary could not express.

## 5. Front-matter schema

**Always required (core):** `class`, `type`, `title`, `status`, `owner` — **plus a date-of-record**:
`updated` (content last changed) for `living` and `transient`; `date` (moment it is true as of) for
`immutable` and `source`. Immutable & source carry `date` + `status`, **not** `updated`.
**Conditional by class:**
- `immutable` → `date` (its date-of-record; no `updated`)
- `living` → `covers[]` **and** `last_verified` *(a `last_verified` with no `covers[]` is rejected — a freshness promise with nothing to check is the undead field both repos already carry)*
- `transient` → `status` from a closed enum **with a terminal done-state** (`draft | active | shipped | superseded | archived | killed | stale`; `stale` is set by the nightly sweep, not by hand)
- raw types (`source` tier) → `event_date`, and `source_of:` once distilled
- **`entry`-type living docs** → `covers[]` lists the docs/config the entry indexes or mirrors (not code); they still carry `last_verified`.
**Derived (never hand-set):** `tier`.
**Optional attributes:** `audience` (human|agent|both), `phase` (pitch|brief|spec — transient only),
`genre` (transcript|audit|research|experiment — raw types), `granularity`, `domain`,
`language` (cs|en), `description` (drives the index line), `registry` (always|decide|none),
`promoted_to` / `superseded_by`, `ships` (#PR/issue that retires a transient).

## 6. The freshness contract (the one predicate an agent runs)

```
CITABLE(doc) :=
      doc.tier == canonical
  AND doc.status ∈ {active, accepted, generated}
  AND ( doc.class == immutable                         # cite as of its date
        OR ( doc.class == living
             AND now ≤ last_verified + TTL(type)
             AND every path in covers[] exists in THIS repo
             AND no covers[] path has a commit newer than last_verified ))
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
| `docs/decisions/` + `ADR-0001` | immutable / decision | rationale is the one thing code can't encode; ADR-0001 = "adopt this model" |

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
