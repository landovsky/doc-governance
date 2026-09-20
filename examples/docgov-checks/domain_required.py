"""The minimal shape: one front-matter rule.

Every living reference must declare which domain it belongs to, so the generated index
can be read by someone who does not already know the repo.
"""


def check(root, doc, fields):
    if fields.get("class") != "living" or fields.get("type") != "reference":
        return []
    if fields.get("domain"):
        return []
    # The second element names a front-matter key, which makes the finding clickable at
    # that line. Use None when the problem is not attached to one key.
    return [("house rule: a living reference must declare `domain`", "type")]
