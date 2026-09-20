# `.docgov/checks/` — repo-local rules, worked examples

Copy one of these into your repo's `.docgov/checks/` and adapt it. They are **examples,
not payload**: nothing here is installed by adopting the model.

Why here and not in `bin/docgov`: under `options.tooling: pinned`, CI fetches the tagged
upstream CLI, so a rule added by editing that file never runs in CI and is overwritten by
the next `DOCGOV_VERSION` bump. A rule in `.docgov/checks/` runs inside the pinned gate and
survives upgrades.

## The contract

```python
def check(root, doc, fields):
    """root: repo root · doc: absolute path · fields: the front-matter dict.
    Returns [(message, front_matter_key | None), …] — a key makes the finding clickable."""

def sources(root, doc, fields):
    """Extra drift anchors for `docgov sweep`, beyond the doc's own covers[]."""
```

`fields` is a plain dict of the front matter, and also carries what the built-ins already
parsed — `.covers`, `.text`, `.types`, `.manifest`, `.tier`, `.derived_status` — so a rule
never re-reads or re-parses a file docgov has just read.

- A module named `_*.py` is a helper and is not run as a rule.
- A rule that raises, or fails to import, is reported and **fails the gate**. A broken rule
  must not read as a pass.
- `.docgov/.doc-todo` can exempt a doc from one named rule: `path  # check:<module_name>`.

## Files

| Example | What it shows |
|---|---|
| `domain_required.py` | the minimal shape — one front-matter rule, clickable finding |
| `runbook_freshness.py` | reading `.tier` / `.derived_status` instead of re-deriving them |
| `sibling_readme.py` | a `sources()` hook — sweep a path the doc does not list in `covers[]` |
