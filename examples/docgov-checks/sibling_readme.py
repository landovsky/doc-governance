"""A `sources()` hook: sweep a path the doc does not list in covers[].

A domain doc's covers[] names the code it describes. This repo also keeps a technical
README next to that code, and the domain doc goes stale when *either* moves — but the
README is an implementation detail nobody wants repeated in every doc's front matter.

Returning it from `sources()` makes the sweep watch it exactly as if it were a covers[]
entry, without putting it in the front matter. `check()` is not required; a module may
export either hook or both.
"""
import os


def sources(root, doc, fields):
    out = []
    for covered in fields.covers:
        readme = os.path.join(os.path.dirname(covered), "README.md")
        if os.path.exists(os.path.join(root, readme)):
            out.append(readme)
    return out
