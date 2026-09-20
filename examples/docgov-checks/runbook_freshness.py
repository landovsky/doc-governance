"""Use what docgov already derived, rather than re-deriving it.

A runbook someone may act on today must cite at least one covered path — a runbook with no
anchor cannot drift, which sounds good and means nobody is ever told it went stale.

`fields.tier` and `fields.derived_status` are the model's DERIVED values (spec/model.md §6),
not whatever the doc happens to have typed; reading them here keeps the rule agreeing with
the built-ins instead of quietly inventing a second derivation.
"""


def check(root, doc, fields):
    if fields.get("type") != "runbook":
        return []
    if fields.tier != "canonical" or fields.derived_status != "active":
        return []                      # retired or stale runbooks are history, not instructions
    if fields.covers:
        return []
    return [("an actionable runbook must anchor to at least one covers[] path", "type")]
