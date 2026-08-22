---
class: living
type: model-spec
tier: canonical
title: Front-Matter Schema Reference
status: active
owner: "@landovsky"
updated: 2026-08-20
covers:
  - spec/model.md
last_verified: 2026-08-20
description: >
  Normative front-matter schema — every key, its meaning, which class requires it,
  the closed enums, the tier-derivation rule, and the CITABLE predicate. Organized
  from model.md §4–6.
---

# Front-Matter Schema Reference

Every governed `.md` declares YAML front matter. **Trust is computed from front matter
alone** — an agent never reads a body to decide whether it may cite a doc. This is the
field-by-field reference; the model and its rationale live in [`model.md`](model.md).

## 1. Core keys — always required

| key | meaning |
|---|---|
| `class` | maintenance class (closed enum, below) — the primary axis: how/whether to keep it fresh |
| `type` | repo-local semantic label from `docs/_types.yml`; declares its default `class` |
| `title` | human title |
| `status` | lifecycle state (closed enum, below) |
| `owner` | steward, `@handle` — the assignee the steward loop notifies |

**Plus a date-of-record**, which key depends on class: `updated` (ISO date content last changed,
**≠ `last_verified`**) for `living` and `transient`; `date` (the moment it is true as of) for
`immutable` and `source`. Immutable & source carry `date` + `status`, **not** `updated`.

## 2. Conditional keys — by class

| when `class` is… | also required |
|---|---|
| `immutable` | `date` — the moment it is true as of (its date-of-record; **not** `updated`) |
| `living` | `covers[]` **and** `last_verified` — a `last_verified` with no `covers[]` is **rejected** (a freshness promise with nothing to check) |
| `transient` | `status` from the enum, which **must** include a terminal done-state |
| raw types (→ `source` tier) | `event_date`; plus `source_of:` once distilled |
| `entry` (living) | `covers[]` lists the **docs/config** the entry indexes or mirrors (not code); still carries `last_verified` |

## 3. Derived key — never hand-set

| key | rule |
|---|---|
| `tier` | computed from `class` + type-rawness + terminality (see §6). CI fails if a hand-set `tier` disagrees with its computed value. |

## 4. Optional attributes

| key | enum / form | notes |
|---|---|---|
| `audience` | `human \| agent \| both` | who it is for |
| `phase` | `pitch \| brief \| spec` | **transient only** |
| `genre` | `transcript \| audit \| research \| experiment` | raw types |
| `granularity` | free | attribute, never a type |
| `domain` | free | attribute, never a type |
| `language` | `cs \| en` | |
| `description` | text | drives the generated index line |
| `registry` | `always \| decide \| none` | index inclusion hint |
| `covers[]` | list of repo paths | freshness anchors (required for living) |
| `last_verified` | ISO date | last freshness check (living) |
| `event_date` | ISO date | when raw evidence was captured (source) |
| `source_of` | ref | what a raw doc was distilled into |
| `promoted_to` / `superseded_by` | ref / `none` | transformation links |
| `ships` | `#PR`/`#issue` | the work that retires a transient |

## 5. Closed enums

```
class    : immutable | living | transient          # model layer, portable
tier     : canonical | source | archive            # DERIVED
status   : draft | active | shipped | superseded | archived | killed | stale
           # plus for immutable/ADR docs: accepted, generated
           # `stale` is set by the nightly sweep, never by hand
phase    : pitch | brief | spec                     # transient only
genre    : transcript | audit | research | experiment
audience : human | agent | both
language : cs | en
registry : always | decide | none
```

## 6. Tier-derivation rule (never hand-set)

```
tier(doc) :=
  archive    if terminal:  transient resolved-&-unpromoted
                        OR immutable superseded
                        OR living retired
  source     else if doc.type is declared raw:true in docs/_types.yml
                        (transcript · audit · research · experiment)
  canonical  else        (class ∈ {immutable, living}, not raw, not terminal)
```

Two invariants fall out:

- **`source ⟹ immutable`** — raw evidence is always frozen.
- `tier` replaces v0.1's `trust: current|historical`: `canonical` ≈ current-and-citable,
  `archive` ≈ historical, `source` is the case that binary could not express.

## 7. The CITABLE predicate — the one thing an agent runs

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
