---
class: living
type: guide
tier: canonical
title: AUTHORING — Front-matter cookbook
covers:
  - spec/front-matter.md
  - payload/docs/_types.yml
last_verified: 2026-08-22
description: >
  A worked v0.2.1 front-matter block per class and common type (adr, transcript,
  reference, domain-doc, runbook, brief, spec) with when-to-use, plus the golden
  rules: tier is derived, covers[] is required for living, last_verified without
  covers[] is rejected, a spec needs a ships: link, supersede-not-delete.
---

# AUTHORING — Front-matter cookbook

Copy the block for the kind of doc you are writing, fill it in, done. Field-by-field meaning is
in [`spec/front-matter.md`](../spec/front-matter.md); this is the practical cookbook.

## Golden rules (read once, apply always)

- **`tier` is DERIVED — never hand-set it to something it isn't.** It follows from `class` +
  the type's `raw` flag + terminality. The payload docs carry the correct value; if you write it,
  write the value that *derives*, and CI will reject any disagreement.
- **`covers[]` is required for every `living` doc.** It is the freshness anchor — the code/doc
  paths whose change means "re-verify me".
- **A `last_verified` with no `covers[]` is REJECTED.** A freshness promise with nothing to check
  is the undead field. If you have `last_verified`, you must have `covers[]` (and thus be living).
- **A `spec` needs a `ships:` link** (required per `_types.yml`; a `pitch`/`brief` may not have a PR
  yet). The `#PR`/`#issue` that retires it — so a spec's resolution is *derived* from the merge, not a
  hand-set status that drifts.
- **Supersede, never delete.** An immutable record is retired by writing a *new* doc and setting
  `superseded_by:`; the old one stays and derives to `tier: archive`. Never delete history.
- **`last_verified` is a steward attestation, not a machine check.** A human sets it when
  they have re-confirmed the doc against `covers[]`. An agent may run the check and *propose*
  a value, but never writes today's date on its own judgment — a clean automated scan means
  "no conflict found," not "vouched for." (Symmetric to `stale`, set only by the nightly sweep.)
- **Backfilling a pre-existing living doc: adopted ≠ verified.** Set `last_verified` to the date
  the content was last genuinely confirmed (in practice the git author-date of its last
  substantive edit), **not** today — see [DIRTY-REPO-PLAYBOOK](DIRTY-REPO-PLAYBOOK.md) §4.
- **Required core is just `class`, `type`, `title`** (v0.2.1) + the class's date-of-record (`date`
  for immutable/source · `last_verified` for living · `status`/`ships` for transient). `status` is
  authored only on `transient`; `owner` defaults from `.docgov/manifest.yml`; there is no `updated`
  (read git for content-last-changed) and no `audience`/`granularity`.

---

## immutable

### `adr` — an architecture decision record (canonical — cite it)
Use when a **non-obvious choice is ratified**. Frozen once accepted; supersede to change.

```yaml
---
class: immutable
type: adr
title: ADR-0007 — Use PostGIS for spatial queries
date: 2026-08-20            # the moment it is true as of
superseded_by: none         # a path to the doc that supersedes this one (→ status: superseded, tier: archive)
tier: canonical             # derived: immutable + not-raw + not-superseded
description: >
  Why PostGIS over app-side geo. One line; feeds the index.
---
```
Heading must be `# ADR-0007 — …` (number matches filename). To retire: write ADR-00NN, set this
one's `superseded_by: docs/decisions/00NN-….md` (a **path**, so any immutable — not just an ADR — can be
superseded the same way) and `status: superseded` (it derives to `archive`).

### `transcript` — a raw meeting/call record (source — never cite)
Use for verbatim evidence. `raw: true` in `_types.yml` derives **`tier: source`** — inform only.

```yaml
---
class: immutable
type: transcript
title: BOM/pricing architecture meeting
event_date: 2026-08-19      # required for raw types; relevance decays from here
source_of: docs/decisions/0007-postgis.md   # once distilled — what it fed
tier: source                # derived: raw type ⇒ source (⇒ immutable)
description: >
  Raw notes from the 2026-08-19 call. Evidence, not current truth.
---
```

---

## living  (every living doc needs `covers[]` + `last_verified`)

### `reference` — durable "what is true" (canonical — the default living doc)
Use for the present-tense truth about a subsystem. **TTL 180d.**

```yaml
---
class: living
type: reference
title: Order lifecycle
covers:                     # the code paths this doc describes; drift = stale
  - app/domains/orders/
  - app/models/order.rb
last_verified: 2026-08-20   # steward attestation — bump only when YOU re-confirm against covers[]
tier: canonical             # status derives to active; omit until stale/archived
description: >
  The states an order moves through and who owns each transition.
---
```

### `domain-doc` — subsystem/domain knowledge (canonical)
Use for deeper "how this domain works" than a reference. Same required shape as `reference`.

```yaml
---
class: living
type: domain-doc
title: BOM domain — units, items, cost rollup
covers:
  - app/domains/bom/
last_verified: 2026-08-20   # steward attestation
tier: canonical
domain: bom                 # attribute, not a type
description: Bom::Unit / Bom::Item model and cost-rollup design.
---
```

### `gitops-runbook` — deploy/operate procedure (canonical, shorter TTL)
Use for how to deploy/debug/back up. **TTL 90d** — operational drift bites fast.

```yaml
---
class: living
type: gitops-runbook
title: hriste-ops — deploy & restore
covers:
  - artifacts/gitops.md
  - .github/workflows/deploy.yml
last_verified: 2026-08-20   # steward attestation
tier: canonical
description: Deploy / debug / backup / topology for hriste-ops.
---
```

---

## transient  (every transient needs a terminal `status`; a `spec` also needs a `ships:` link)

### `brief` — early proposal (canonical *as plan* while active)
Use for a proposal in `phase: pitch|brief`. Retires by status flip.

```yaml
---
class: transient
type: brief
title: External customer portal — pitch
status: active              # AUTHORED on transient — draft | active | shipped | superseded | archived | killed | stale
phase: brief                # transient-only attribute
ships: "#412"               # the PR/issue that will retire this
tier: canonical             # derived: transient, active, not terminal — cite as INTENT
description: >
  Proposal for an external portal. Plan, not current system state.
---
```

### `spec` — detailed plan (canonical *as plan*; retires on ship/kill → archive)
Use for the committed, detailed `phase: spec`. **`ships:` is required.** On ship it must yield a
`living(reference)` (retire-on-ship gate); the spec then derives to `tier: archive`.

```yaml
---
class: transient
type: spec
title: External customer portal — spec
status: active              # AUTHORED on transient
phase: spec
ships: "#412"               # CI archives this transient when #412 merges
promoted_to: docs/reference/external-portal.md   # set on ship (the living doc it becomes)
tier: canonical
description: The detailed build plan for the external portal.
---
```
On ship: add/patch the `living(reference)` it promotes to, set `promoted_to:`, flip `status:` to
a terminal value — it derives to `tier: archive`. On kill: `status: killed` (also archive).
