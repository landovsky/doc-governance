---
class: living
type: model-spec
tier: canonical
title: Front-Matter Schema Reference
covers:
  - spec/model.md
last_verified: 2026-08-22
description: >
  Normative front-matter schema — every key, its meaning, which class requires it,
  the closed enums, the tier-derivation rule, and the CITABLE predicate. Organized
  from model.md §4–6.
---

# Front-Matter Schema Reference

Every governed `.md` declares YAML front matter. **Trust is computed from front matter
alone** — an agent never reads a body to decide whether it may cite a doc. This is the
field-by-field reference; the model and its rationale live in [`model.md`](model.md).

> **Two rules for optional fields.** **(1) Validated only when present** — an optional field is checked
> *only if it appears*, because the tooling leans on it: a `superseded_by`, if present, must be a path to an
> existing immutable; a malformed one fails `docgov check`, an absent one is fine. **(2) Additive growth** —
> adding an optional field is **not** breaking and needs no migration (only removing / renaming / retyping /
> tightening one does). Several optional fields today (`superseded_by`, `promoted_to`, `source_of`, `ships`)
> are effectively **future requirements**: reserved in intent, may be promoted to required as the tooling grows.

## 1. Core keys — always required

| key | meaning |
|---|---|
| `class` | maintenance class (closed enum, below) — the primary axis: how/whether to keep it fresh |
| `type` | repo-local semantic label from `docs/_types.yml`; declares its default `class` |
| `title` | human title |

These three are the **entire** universal core (v0.2.1). `status`, `owner`, and `updated` are no longer
universal: `status` is authored only on `transient` (derived elsewhere — §3), `owner` defaults from the
manifest (§4), and `updated` is **gone** — read "content last changed" from git (`git log -1`). Each
class then adds a **date-of-record**: `date` (the moment it is true as of) for **non-raw** `immutable`
(ADR, record); `event_date` for raw / `source`-tier docs (transcript, audit, …); `last_verified`
(a steward attestation) for `living`; a `transient` is dated by its `status` / `ships`, not a date field.

## 2. Conditional keys — by class

| when `class` is… | also required |
|---|---|
| `immutable` (non-raw) | `date` — the moment it is true as of (its date-of-record). A **raw** immutable doc uses `event_date` instead — see the raw-types row. |
| `living` | `covers[]` **and** `last_verified` — a `last_verified` with no `covers[]` is **rejected** (a freshness promise with nothing to check). `last_verified` is a **steward attestation** (§4). |
| `transient` | `status` from the enum (**must** include a terminal done-state) — this is the only *class-level* requirement. (A repo may additionally require `ships:` on a specific transient **type** via `_types.yml`; see the note below.) |
| raw types (→ `source` tier) | `event_date`; plus `source_of:` once distilled |
| `entry` (living) | `covers[]` lists the **docs/config** the entry indexes or mirrors (not code); still carries `last_verified` |

> **Model layer vs repo layer.** This table is the *portable model* requirement. A repo can make any
> further key mandatory **per-type** in `docs/_types.yml` (`requires: […]`) — e.g. this package declares
> `spec: requires: [status, ships]`, so a `spec` must carry `ships:` **here**. That is a **repo-layer**
> rule, not a model one; at the model level `ships` stays an **optional attribute** (§4), its role being
> the retire-on-ship link.

## 3. Derived keys — never hand-set

| key | rule |
|---|---|
| `tier` | computed from `class` + type-rawness + terminality (see §6). CI fails if a hand-set `tier` disagrees with its computed value. |
| `status` (living / immutable) | not authored on these classes — see the `status(doc)` rule in §6: `living` derives `active \| stale \| archived`; non-raw `immutable` derives `accepted \| superseded` (from `superseded_by`); a raw / `source`-tier doc has **no meaningful status** (leave it off — `tier: source` already blocks citation). Author `status` only on `transient`; on a living/immutable doc write it **only when non-default**, so a bare `grep status:` surfaces exactly the stale/archived/superseded docs. |

## 4. Optional attributes

| key | enum / form | notes |
|---|---|---|
| `owner` | `@handle` | **per-doc override** of the manifest's default steward; omit unless this doc has a different owner |
| `phase` | `pitch \| brief \| spec` | **transient only** |
| `genre` | `transcript \| audit \| research \| experiment` | raw types |
| `domain` | free | attribute, never a type |
| `language` | `cs \| en` | |
| `description` | text | drives the generated index line |
| `registry` | `always \| decide \| none` | index inclusion hint |
| `covers[]` | list of repo paths | freshness anchors (required for living) |
| `last_verified` | ISO date | date a **steward** last confirmed the doc against `covers[]` (living). **Human-set attestation — an agent may run the check and propose a value but never stamps today's date itself** (symmetric to `stale`, set only by the sweep). |
| `event_date` | ISO date | when raw evidence was captured (source) |
| `source_of` | ref | what a raw doc was distilled into |
| `promoted_to` / `superseded_by` | **path** / `none` | transformation links — a repo path to the target doc, checked to exist (`superseded_by` → an **immutable**, `promoted_to` → a **living**). Generic across all immutables, not ADR-only. |
| `ships` | `#PR`/`#issue` | the work that retires a transient |

## 5. Closed enums

```
class    : immutable | living | transient          # model layer, portable
tier     : canonical | source | archive            # DERIVED
status   : draft | active | shipped | superseded | archived | killed | stale
           # plus for immutable/ADR docs: accepted, generated
           # AUTHORED only on transient; DERIVED for living/immutable (§3)
           # `stale` is set by the nightly sweep, never by hand
phase    : pitch | brief | spec                     # transient only
genre    : transcript | audit | research | experiment
language : cs | en
registry : always | decide | none
```

## 6. Derivation rules — `tier` and `status` (never hand-set)

```
tier(doc) :=
  archive    if terminal:  transient resolved-&-unpromoted
                        OR immutable superseded
                        OR living archived   (status: archived — set when all covers[] paths cease to exist)
  source     else if doc.type is declared raw:true in docs/_types.yml
                        (transcript · audit · research · experiment)
  canonical  else        (class ∈ {immutable, living}, not raw, not terminal)
```

`status` is likewise derived on `living` / `immutable` (authored only on `transient`). CITABLE (§7)
reads `status(doc)`, **never a bare `doc.status`** — a conformant living/immutable doc may omit the key:

```
status(doc) :=
  doc.status              if present   (always on transient; a non-default value on living/immutable)
  else, by class:
    living     → active                                              # derived default (sweep may set `stale`; all covers[] gone → mark `archived`)
    immutable  → superseded   if superseded_by is set
                 accepted     else if type is not raw                # ADR / record default
                 n/a          else                                   # raw / source-tier: status is not a meaningful axis
```

Two invariants fall out:

- **`source ⟹ immutable`** — raw evidence is always frozen.
- `tier` replaces v0.1's `trust: current|historical`: `canonical` ≈ current-and-citable,
  `archive` ≈ historical, `source` is the case that binary could not express.

## 7. The CITABLE predicate — the one thing an agent runs

```
CITABLE(doc) :=
      doc.tier == canonical
  AND status(doc) ∈ {active, accepted, generated}      # status(doc) DERIVED (§6) — never a bare doc.status
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

> **Who moves `last_verified` forward.** This predicate trusts `last_verified` as a
> human sign-off. Setting it to today resets the TTL clock *and* clears the drift check
> (`no covers[] path has a commit newer than last_verified`) in one write — so it may be
> bumped **only by a steward who re-confirmed the doc**, never by an agent stamping today
> because an automated pass looked clean. See `model.md` §5.
