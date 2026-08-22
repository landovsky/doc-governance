---
class: living
type: guide
tier: canonical
title: MIGRATING — Move a repo between model versions
status: active
owner: "@landovsky"
updated: 2026-08-20
covers:
  - payload/.docgov/manifest.yml
  - migrations/README.md
  - VERSION
last_verified: 2026-08-20
description: >
  Move an adopted repo between model versions: read its .docgov/manifest.yml
  model_version, compare to the master VERSION, apply migrations/<from>-to-<to>.md
  in sequence (transitively), then bump the manifest. Worked example: 0.1.0 → 0.2.0.
---

# MIGRATING — Move a repo between model versions

The **model** evolves; each adopted repo pins the version it tracks in
`.docgov/manifest.yml:model_version`. Migrating means walking the repo forward, **one version
hop at a time**, from the version in its manifest up to the master `VERSION`. Each hop has a
written guide at `migrations/<from>-to-<to>.md`. Every step is **manual** today; a per-hop
codemod (`docgov migrate`) is **DEFERRED** — **TODO (tooling, later)**.

---

## 1. Find where the repo stands

```
grep model_version ~/git/<REPO>/.docgov/manifest.yml     # e.g. 0.1.0
cat $MASTER/VERSION                                       # e.g. 0.2.0
```

If they match, there is nothing to do. If the manifest is **behind** `VERSION`, you have one or
more hops to apply.

## 2. The filename convention

Migration guides live in `migrations/` and are named for the exact version pair they bridge:

```
migrations/<from>-to-<to>.md          e.g. migrations/0.1.0-to-0.2.0.md
```

`<from>` and `<to>` are consecutive released model versions. There is **one** guide per hop.
There is no "0.1.0-to-0.3.0" shortcut file — multi-version jumps are done by composing the
single-hop guides in order (next section). See `migrations/README.md` for authoring rules.

## 3. Apply hops in order, transitively

To go from the manifest version to `VERSION`, apply each intervening hop **in sequence**,
lowest to highest. Example — a repo at `0.1.0` when master is `0.3.0`:

```
migrations/0.1.0-to-0.2.0.md      # apply fully first
migrations/0.2.0-to-0.3.0.md      # then this one
```

For each hop:

1. Open `migrations/<from>-to-<to>.md`.
2. Work its **manual steps top-to-bottom** (front-matter key renames, new required keys, moved
   files, etc.). Do not skip ahead — a later hop assumes the earlier hop already ran.
3. Verify the repo against the new version's model (spec/front-matter checks) before starting
   the next hop.
4. **Bump the manifest** after each hop:
   ```
   # .docgov/manifest.yml
   model_version: 0.2.0     # was 0.1.0
   ```
   Bumping per-hop (not once at the end) keeps the manifest honest if you have to stop midway.

## 4. Commit

Commit each hop (or the whole transitive walk) as its own PR, with the `model_version` bump in
the same diff as the front-matter changes it justifies. The CI gate then validates the repo
against the new version.

**TODO (tooling, later):** `docgov migrate` will read `manifest.model_version`, discover the
hop chain up to `VERSION`, run each hop's codemod, and bump the manifest automatically. Until
then this walk is manual and each hop guide spells out the by-hand procedure.
