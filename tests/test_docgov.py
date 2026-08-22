#!/usr/bin/env python3
"""Stdlib-only TDD suite for bin/docgov (documentation-governance CLI).

Runnable two ways:
    python3 -m unittest tests.test_docgov
    python3 tests/test_docgov.py

The suite is TDD: some tests encode KNOWN BUGS and MUST currently FAIL
(they document the intended fix in a one-line comment). Others are
regression/guard tests that MUST currently PASS so a fix does not regress
confirmed-correct behavior.

We import docgov as a module for unit tests (no .py extension → SourceFileLoader)
and shell out to `python3 bin/docgov …` on fixture repos for end-to-end
check/sweep behavior.
"""
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from importlib.machinery import SourceFileLoader

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCGOV_PATH = os.path.join(REPO_ROOT, "bin", "docgov")
PAYLOAD_DOCGOV_PATH = os.path.join(REPO_ROOT, "payload", "bin", "docgov")

# ── import bin/docgov as a module (no .py extension) ────────────────────────
_loader = SourceFileLoader("docgov", DOCGOV_PATH)
_spec = importlib.util.spec_from_loader("docgov", _loader)
docgov = importlib.util.module_from_spec(_spec)
_loader.exec_module(docgov)


DEFAULT_TYPES = """\
reference:
  class: living
  requires: [covers, last_verified]
record:
  class: immutable
  requires: [date]
transcript:
  class: immutable
  raw: true
  requires: [event_date]
note:
  class: transient
  requires: [status]
adr:
  class: immutable
  requires: [date]
"""

MINIMAL_MANIFEST = "model_version: 0.2.1\npaths:\n  types_file: _types.yml\n"


# ── fixture helpers ──────────────────────────────────────────────────────────
class RepoMixin:
    def make_repo(self, files, types=DEFAULT_TYPES, manifest=MINIMAL_MANIFEST):
        """Create a temp repo tree with .docgov/ + _types.yml + given md/code files.

        `files` maps repo-relative path → text content.
        Returns the absolute repo root; auto-cleaned on tearDown.
        """
        root = tempfile.mkdtemp(prefix="docgov_fx_")
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        os.makedirs(os.path.join(root, ".docgov"), exist_ok=True)
        with open(os.path.join(root, ".docgov", "manifest.yml"), "w") as f:
            f.write(manifest)
        if types is not None:
            with open(os.path.join(root, "_types.yml"), "w") as f:
                f.write(types)
        for rel, content in files.items():
            full = os.path.join(root, rel)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, "w") as f:
                f.write(content)
        return root

    def lint(self, root, relpath):
        types = docgov.load_types(root)
        return docgov.lint_doc(root, os.path.join(root, relpath), types)

    def msgs(self, findings):
        return [m for m, _ in findings]

    def run_cli(self, root, *cli_args):
        env = dict(os.environ)
        return subprocess.run(
            [sys.executable, DOCGOV_PATH, *cli_args],
            cwd=root, env=env, capture_output=True, text=True,
        )

    def git(self, root, *args):
        env = dict(os.environ)
        env.update(
            GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@e",
            GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@e",
        )
        subprocess.run(["git", "-C", root, *args], check=True,
                       capture_output=True, text=True, env=env)


# ─────────────────────────────────────────────────────────────────────────────
# BUG TESTS — these MUST currently FAIL (they document the bugs).
# ─────────────────────────────────────────────────────────────────────────────
class BugTests(RepoMixin, unittest.TestCase):

    def test_bug1_sweep_exit_code_signals_drift(self):
        # FIX: add `sweep --exit-code` → sys.exit(non-zero) when any living doc's
        # covers[] target is dirty/newer than last_verified; exit 0 when clean.
        root = self.make_repo({
            "code.py": "print('v1')\n",
            "doc.md": (
                "---\nclass: living\ntype: reference\ntitle: Cover Doc\n"
                "covers: [code.py]\nlast_verified: 2099-01-01\n---\nbody\n"
            ),
        })
        self.git(root, "init", "-q")
        self.git(root, "add", "-A")
        self.git(root, "commit", "-q", "-m", "init")

        # Clean working tree → intended exit 0.
        clean = self.run_cli(root, "sweep", "--exit-code")
        self.assertEqual(clean.returncode, 0,
                         f"clean sweep --exit-code should be 0; got {clean.returncode}\n{clean.stderr}")

        # Dirty the covered file → intended non-zero.
        with open(os.path.join(root, "code.py"), "a") as f:
            f.write("print('v2')\n")
        dirty = self.run_cli(root, "sweep", "--exit-code")
        self.assertNotEqual(dirty.returncode, 0,
                            "dirty sweep --exit-code should be non-zero")

    def test_bug2_check_honors_docs_dir_ignores_vendor(self):
        # FIX: `check` should lint only docs under manifest paths.docs_dir
        # (+ named core files), not arbitrary *.md like vendor/junk.md.
        manifest = "model_version: 0.2.1\npaths:\n  docs_dir: docs\n  types_file: _types.yml\n"
        root = self.make_repo({
            "app.py": "x = 1\n",
            "docs/good.md": (
                "---\nclass: living\ntype: reference\ntitle: Good\n"
                "covers: [app.py]\nlast_verified: 2026-08-01\n---\nBody.\n"
            ),
            "vendor/junk.md": "just some vendored markdown, no front matter\n",
        }, manifest=manifest)
        res = self.run_cli(root, "check")
        self.assertEqual(res.returncode, 0,
                         f"check should ignore vendor/ and pass; stdout:\n{res.stdout}")

    def test_bug4_iso_date_rejects_impossible_dates(self):
        # FIX: validate ISO dates semantically (month 1-12, valid day),
        # not just the ^\d{4}-\d{2}-\d{2}$ shape → flag 2026-13-99.
        root = self.make_repo({
            "app.py": "x = 1\n",
            "bad.md": (
                "---\nclass: living\ntype: reference\ntitle: Bad Date\n"
                "covers: [app.py]\nlast_verified: 2026-13-99\n---\nbody\n"
            ),
        })
        findings = self.lint(root, "bad.md")
        self.assertTrue(any("2026-13-99" in m for m in self.msgs(findings)),
                        f"impossible date must be flagged; findings: {self.msgs(findings)}")

    def test_bug5_bare_scalar_covers_kept(self):
        # FIX: parse_fm must treat `covers: some/path.md` (no brackets, single
        # scalar) as one covers entry, not drop it → no false "missing covers[]".
        text = (
            "---\nclass: living\ntype: reference\ntitle: T\n"
            "covers: some/existing.md\nlast_verified: 2026-08-01\n---\nbody\n"
        )
        fields, covers = docgov.parse_fm(text)
        self.assertEqual(covers, ["some/existing.md"],
                         f"bare-scalar covers dropped; got {covers!r}")

    def test_bug6_reference_style_dead_links_detected(self):
        # FIX: dead_body_links must also resolve reference-style links
        # `[thing][ref]` via their `[ref]: ./target` definitions.
        root = self.make_repo({
            "doc.md": (
                "---\nclass: living\ntype: reference\ntitle: T\n"
                "covers: [doc.md]\nlast_verified: 2026-08-01\n---\n"
                "See [thing][ref] here.\n\n[ref]: ./does-not-exist.md\n"
            ),
        })
        findings = docgov.dead_body_links(root, os.path.join(root, "doc.md"))
        self.assertTrue(any("does-not-exist.md" in m for m, _ in findings),
                        f"reference-style dead link not detected; findings: {findings}")

    def test_bug8_adr_heading_number_matches_filename(self):
        # FIX: implement model §9.3 — an `adr` doc's H1 number must match the
        # filename number; flag docs/decisions/0007-x.md whose H1 is ADR-0009.
        root = self.make_repo({
            "docs/decisions/0007-x.md": (
                "---\nclass: immutable\ntype: adr\ntitle: Some Decision\n"
                "date: 2026-01-01\n---\n# ADR-0009 — Some Decision\n\nBody.\n"
            ),
        })
        findings = self.lint(root, "docs/decisions/0007-x.md")
        self.assertTrue(any("0009" in m for m in self.msgs(findings)),
                        f"ADR heading/filename number mismatch not flagged; findings: {self.msgs(findings)}")

    def test_bug9_mark_stale_inserts_on_missing_anchor(self):
        # FIX: mark_stale must insert `status: stale` even when there is no
        # `status:` line and no `type:` line to anchor on.
        root = self.make_repo({
            "doc.md": (
                "---\nclass: living\ntitle: No Type Doc\n"
                "covers: [doc.md]\nlast_verified: 2026-08-01\n---\nbody\n"
            ),
        })
        path = os.path.join(root, "doc.md")
        docgov.mark_stale(path)
        with open(path) as f:
            after = f.read()
        self.assertIn("status: stale", after,
                      "mark_stale silently no-op'd when no status/type anchor present")


# ─────────────────────────────────────────────────────────────────────────────
# GUARD TEST — currently PASSES (protects the future).
# ─────────────────────────────────────────────────────────────────────────────
class GuardTests(unittest.TestCase):

    def test_bug7_vendored_copy_in_sync(self):
        # Guards future drift: the two copies must stay byte-identical.
        with open(DOCGOV_PATH, "rb") as f:
            a = f.read()
        with open(PAYLOAD_DOCGOV_PATH, "rb") as f:
            b = f.read()
        self.assertEqual(a, b, "bin/docgov and payload/bin/docgov have drifted")


# ─────────────────────────────────────────────────────────────────────────────
# REGRESSION TESTS — these MUST currently PASS (fixes must not break them).
# ─────────────────────────────────────────────────────────────────────────────
class RegressionTests(RepoMixin, unittest.TestCase):

    def test_valid_living_reference_passes(self):
        root = self.make_repo({
            "target.py": "x = 1\n",
            "ref.md": (
                "---\nclass: living\ntype: reference\ntitle: Ref Doc\n"
                "covers: [target.py]\nlast_verified: 2026-08-01\n---\nBody text.\n"
            ),
        })
        self.assertEqual(self.lint(root, "ref.md"), [],
                         "a fully valid living reference must lint clean")

    def test_forbidden_removed_key_updated_flagged(self):
        root = self.make_repo({
            "target.py": "x = 1\n",
            "ref.md": (
                "---\nclass: living\ntype: reference\ntitle: Ref\n"
                "covers: [target.py]\nlast_verified: 2026-08-01\n"
                "updated: 2026-08-01\n---\nbody\n"
            ),
        })
        self.assertTrue(any("updated" in m and "forbidden" in m
                            for m in self.msgs(self.lint(root, "ref.md"))))

    def test_hand_set_tier_mismatch_flagged(self):
        root = self.make_repo({
            "target.py": "x = 1\n",
            "ref.md": (
                "---\nclass: living\ntype: reference\ntitle: Ref\n"
                "covers: [target.py]\nlast_verified: 2026-08-01\n"
                "tier: source\n---\nbody\n"
            ),
        })
        self.assertTrue(any("tier=source" in m and "canonical" in m
                            for m in self.msgs(self.lint(root, "ref.md"))))

    def test_superseded_by_living_target_flagged(self):
        root = self.make_repo({
            "living-target.md": (
                "---\nclass: living\ntype: reference\ntitle: Live\n"
                "covers: [living-target.md]\nlast_verified: 2026-08-01\n---\nx\n"
            ),
            "rec.md": (
                "---\nclass: immutable\ntype: record\ntitle: Old Record\n"
                "date: 2026-01-01\nsuperseded_by: living-target.md\n---\nbody\n"
            ),
        })
        self.assertTrue(any("superseded_by" in m
                            for m in self.msgs(self.lint(root, "rec.md"))),
                        "superseded_by → living target (expected immutable) must be flagged")

    def test_superseded_by_none_passes(self):
        root = self.make_repo({
            "rec.md": (
                "---\nclass: immutable\ntype: record\ntitle: Rec\n"
                "date: 2026-01-01\nsuperseded_by: none\n---\nbody\n"
            ),
        })
        self.assertFalse(any("superseded_by" in m
                             for m in self.msgs(self.lint(root, "rec.md"))),
                         "superseded_by: none must not be flagged")

    def test_dead_inline_link_flagged_but_external_anchor_and_fenced_skipped(self):
        body = (
            "See [live](./real.md), [dead](./nope.md), "
            "[ext](https://example.com), [anchor](#sec).\n\n"
            "```\n[hidden](./incode.md)\n```\n"
        )
        root = self.make_repo({
            "real.md": "ok\n",
            "doc.md": (
                "---\nclass: living\ntype: reference\ntitle: T\n"
                "covers: [real.md]\nlast_verified: 2026-08-01\n---\n" + body
            ),
        })
        findings = docgov.dead_body_links(root, os.path.join(root, "doc.md"))
        msgs = [m for m, _ in findings]
        self.assertEqual(len(findings), 1, f"expected exactly one dead link; got {msgs}")
        self.assertIn("nope.md", msgs[0])
        self.assertFalse(any("real.md" in m for m in msgs))
        self.assertFalse(any("incode.md" in m for m in msgs))
        self.assertFalse(any("example.com" in m for m in msgs))

    def test_living_hand_set_status_active_flagged(self):
        root = self.make_repo({
            "target.py": "x = 1\n",
            "ref.md": (
                "---\nclass: living\ntype: reference\ntitle: Ref\n"
                "covers: [target.py]\nlast_verified: 2026-08-01\n"
                "status: active\n---\nbody\n"
            ),
        })
        self.assertTrue(any("status" in m and "active" in m
                            for m in self.msgs(self.lint(root, "ref.md"))))

    def test_living_status_stale_allowed(self):
        root = self.make_repo({
            "target.py": "x = 1\n",
            "ref.md": (
                "---\nclass: living\ntype: reference\ntitle: Ref\n"
                "covers: [target.py]\nlast_verified: 2026-08-01\n"
                "status: stale\n---\nbody\n"
            ),
        })
        self.assertFalse(any("status" in m for m in self.msgs(self.lint(root, "ref.md"))),
                         "living status: stale is the machine marker and must be allowed")

    def test_missing_covers_path_flagged(self):
        root = self.make_repo({
            "ref.md": (
                "---\nclass: living\ntype: reference\ntitle: Ref\n"
                "covers: [ghost.md]\nlast_verified: 2026-08-01\n---\nbody\n"
            ),
        })
        self.assertTrue(any("covers[] path does not exist" in m and "ghost.md" in m
                            for m in self.msgs(self.lint(root, "ref.md"))))

    def test_conditional_immutable_requires_date(self):
        root = self.make_repo({
            "rec.md": (
                "---\nclass: immutable\ntype: record\ntitle: Rec\n---\nbody\n"
            ),
        })
        self.assertTrue(any("missing date" in m for m in self.msgs(self.lint(root, "rec.md"))))

    def test_conditional_raw_requires_event_date(self):
        root = self.make_repo({
            "log.md": (
                "---\nclass: immutable\ntype: transcript\ntitle: Log\n---\nbody\n"
            ),
        })
        self.assertTrue(any("event_date" in m for m in self.msgs(self.lint(root, "log.md"))))

    def test_conditional_living_requires_covers_and_last_verified(self):
        root = self.make_repo({
            "doc.md": (
                "---\nclass: living\ntype: reference\ntitle: Doc\n---\nbody\n"
            ),
        })
        msgs = self.msgs(self.lint(root, "doc.md"))
        self.assertTrue(any("missing covers[]" in m for m in msgs))
        self.assertTrue(any("missing last_verified" in m for m in msgs))

    def test_conditional_transient_requires_status(self):
        root = self.make_repo({
            "n.md": (
                "---\nclass: transient\ntype: note\ntitle: Note\n---\nbody\n"
            ),
        })
        self.assertTrue(any("transient: missing status" in m
                            for m in self.msgs(self.lint(root, "n.md"))))


if __name__ == "__main__":
    unittest.main()
