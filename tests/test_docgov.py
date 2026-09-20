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


# ─────────────────────────────────────────────────────────────────────────────
# v0.3.0 — MANIFEST. The blocker ADR-0001 names: one spelling, keys unique across
# the whole file, and a parser that knows which map a key sits in.
# ─────────────────────────────────────────────────────────────────────────────
class ManifestTests(RepoMixin, unittest.TestCase):

    def test_shipped_payload_template_resolves_its_index_file_not_the_word_manual(self):
        # The pre-0.3.0 parser matched `^\s*(?:index|index_file):` line-wise with no path
        # context, so `options.index: manual` overwrote `paths.index: MAIN.md` and the
        # template every adopter copies verbatim resolved its index to the string "manual".
        root = os.path.join(REPO_ROOT, "payload")
        man = docgov.load_manifest(root)
        self.assertEqual(docgov.mpath(man, "index"), "MAIN.md")
        self.assertNotEqual(docgov.mpath(man, "index"), "manual")

    def test_master_and_payload_agree_on_every_manifest_path_key(self):
        # Two spellings of one key is how the collision above got in; a generator that
        # reads these keys cannot be built on top of divergent templates.
        master = docgov.load_manifest(REPO_ROOT)["paths"]
        payload = docgov.load_manifest(os.path.join(REPO_ROOT, "payload"))["paths"]
        legacy = {"index_file", "types_file", "todo_file", "decisions_dir"}
        self.assertEqual(legacy & set(master), set(), f"master still uses {legacy & set(master)}")
        self.assertEqual(legacy & set(payload), set(), f"payload still uses {legacy & set(payload)}")

    def test_options_index_mode_can_never_collide_with_paths_index_again(self):
        for where in (REPO_ROOT, os.path.join(REPO_ROOT, "payload")):
            man = docgov.load_manifest(where)
            self.assertNotIn("index", man["options"], f"{where}: options.index is back")
            self.assertIn("index_mode", man["options"])

    def test_pre_0_3_0_manifest_still_resolves_so_an_unmigrated_repo_keeps_working(self):
        root = self.make_repo({}, manifest=(
            "model_version: 0.2.1\npaths:\n  index_file: DOCS.md\n  types_file: t.yml\n"))
        man = docgov.load_manifest(root)
        self.assertEqual(docgov.mpath(man, "index"), "DOCS.md")
        self.assertEqual(docgov.mpath(man, "types"), "t.yml")


# ─────────────────────────────────────────────────────────────────────────────
# v0.3.0 — GENERATED INDEX (ADR-0001 §1). The model's claim is that front matter IS
# the index; until it is generated, nothing compares the map to the front matter.
# ─────────────────────────────────────────────────────────────────────────────
INDEX_MANIFEST = "model_version: 0.3.0\npaths:\n  index: MAIN.md\n  types: _types.yml\n"
MARKED_INDEX = (
    "---\nclass: living\ntype: reference\ntitle: Map\n"
    "covers: [app.py]\nlast_verified: 2026-08-01\nregistry: always\n---\n"
    "# Map\n\nHand-written prose above.\n\n"
    "<!-- docgov:index -->\n<!-- /docgov:index -->\n\nHand-written prose below.\n"
)


class IndexTests(RepoMixin, unittest.TestCase):

    def index_repo(self, extra=None):
        files = {
            "app.py": "x = 1\n",
            "MAIN.md": MARKED_INDEX,
            "ref.md": ("---\nclass: living\ntype: reference\ntitle: Ref\n"
                       "covers: [app.py]\nlast_verified: 2026-08-01\n"
                       "description: what is true today\n---\nbody\n"),
        }
        files.update(extra or {})
        return self.make_repo(files, manifest=INDEX_MANIFEST)

    def block(self, root):
        man = docgov.load_manifest(root)
        return docgov.index_block(root, docgov.load_types(root, man), man)

    def test_a_governed_doc_appears_in_the_map_without_anyone_linking_it(self):
        # hriste had 29 of 44 registry:always|decide docs missing from a hand-kept map.
        self.assertIn("[`ref.md`](ref.md)", self.block(self.index_repo()))

    def test_index_line_is_the_description_because_that_is_what_the_field_is_for(self):
        self.assertIn("| what is true today |", self.block(self.index_repo()))

    def test_a_folded_description_is_not_rendered_as_a_bare_angle_bracket(self):
        # `description: >` is the idiomatic way to write a sentence that wraps; the
        # pre-0.3.0 parser captured the fold indicator and dropped the sentence.
        root = self.index_repo({"folded.md": (
            "---\nclass: living\ntype: reference\ntitle: Folded\n"
            "covers: [app.py]\nlast_verified: 2026-08-01\ndescription: >\n"
            "  one sentence that\n  wraps across lines\n---\nbody\n")})
        self.assertIn("| one sentence that wraps across lines |", self.block(root))

    def test_registry_none_stays_out_of_the_map_it_asked_to_be_left_out_of(self):
        root = self.index_repo({"secret.md": (
            "---\nclass: living\ntype: reference\ntitle: Internal\n"
            "covers: [app.py]\nlast_verified: 2026-08-01\nregistry: none\n---\nbody\n")})
        self.assertNotIn("secret.md", self.block(root))

    def test_registry_always_is_listed_even_though_a_retired_doc_is_not_citable(self):
        # `always` is the override that makes the map show history on purpose.
        root = self.index_repo({"old.md": (
            "---\nclass: transient\ntype: note\ntitle: Retired\n"
            "status: killed\nregistry: always\n---\nbody\n")})
        self.assertIn("old.md", self.block(root))

    def test_a_retired_doc_drops_out_of_the_map_by_default_because_the_map_is_of_today(self):
        # `decide`/absent resolves to "listed iff a reader may cite it now" — the rule
        # spec/front-matter.md left undefined until a generator forced the question.
        root = self.index_repo({"dead.md": (
            "---\nclass: transient\ntype: note\ntitle: Shipped\nstatus: shipped\n---\nbody\n")})
        self.assertNotIn("dead.md", self.block(root))

    def test_sections_follow_the_type_enum_so_the_outline_lives_in_one_place(self):
        types = "beta:\n  class: living\n  requires: []\nalpha:\n  class: living\n  requires: []\n"
        root = self.make_repo({
            "app.py": "x = 1\n", "MAIN.md": MARKED_INDEX,
            "b.md": "---\nclass: living\ntype: beta\ntitle: B\ncovers: [app.py]\nlast_verified: 2026-08-01\n---\nx\n",
            "a.md": "---\nclass: living\ntype: alpha\ntitle: A\ncovers: [app.py]\nlast_verified: 2026-08-01\n---\nx\n",
        }, types=types, manifest=INDEX_MANIFEST)
        block = self.block(root)
        self.assertLess(block.index("### beta"), block.index("### alpha"),
                        "declaration order in _types.yml is the index outline, not alphabetical")

    def test_write_then_check_is_green_and_an_edit_to_front_matter_turns_it_red(self):
        # The gate that makes "front matter is the index" falsifiable.
        root = self.index_repo()
        self.assertEqual(self.run_cli(root, "index", "--write").returncode, 0)
        self.assertEqual(self.run_cli(root, "index", "--check").returncode, 0)
        with open(os.path.join(root, "new.md"), "w") as f:
            f.write("---\nclass: living\ntype: reference\ntitle: New\n"
                    "covers: [app.py]\nlast_verified: 2026-08-01\n---\nbody\n")
        stale = self.run_cli(root, "index", "--check")
        self.assertNotEqual(stale.returncode, 0, "a doc added without a regen must fail the gate")
        self.assertIn("stale", stale.stdout)

    def test_prose_outside_the_markers_survives_regeneration(self):
        # The whole reason for markers: MAIN.md keeps its "how we do things" sections.
        root = self.index_repo()
        self.run_cli(root, "index", "--write")
        with open(os.path.join(root, "MAIN.md")) as f:
            after = f.read()
        self.assertIn("Hand-written prose above.", after)
        self.assertIn("Hand-written prose below.", after)

    def test_an_index_file_with_no_markers_says_which_two_lines_to_add(self):
        root = self.make_repo({
            "app.py": "x = 1\n",
            "MAIN.md": ("---\nclass: living\ntype: reference\ntitle: Map\n"
                        "covers: [app.py]\nlast_verified: 2026-08-01\n---\n# Map\n"),
        }, manifest=INDEX_MANIFEST)
        res = self.run_cli(root, "index", "--write")
        self.assertNotEqual(res.returncode, 0)
        self.assertIn(docgov.INDEX_BEGIN, res.stdout)


# ─────────────────────────────────────────────────────────────────────────────
# v0.3.0 — EXTENSION HOOKS (ADR-0001 §2). Under `tooling: pinned` a rule added by
# editing bin/docgov never runs in CI and is lost on the next version bump.
# ─────────────────────────────────────────────────────────────────────────────
HOOK_DOC = ("---\nclass: living\ntype: reference\ntitle: Doc\n"
            "covers: [app.py]\nlast_verified: 2026-08-01\n---\nbody\n")


class HookTests(RepoMixin, unittest.TestCase):

    def test_a_repo_local_rule_blocks_the_merge_the_way_a_built_in_does(self):
        root = self.make_repo({
            "app.py": "x = 1\n", "doc.md": HOOK_DOC,
            ".docgov/checks/house_style.py":
                "def check(root, doc, fields):\n"
                "    return [] if fields.get('owner') else [('house rule: owner required', 'title')]\n",
        })
        res = self.run_cli(root, "check")
        self.assertNotEqual(res.returncode, 0, "a hook finding must reach the exit code")
        self.assertIn("house rule: owner required", res.stdout)

    def test_a_hook_reads_covers_without_parsing_the_file_a_second_time(self):
        # The signature is check(root, doc, fields); fields carries what the built-ins
        # already parsed, so a non-trivial rule is not pushed into re-reading the doc.
        root = self.make_repo({
            "app.py": "x = 1\n", "doc.md": HOOK_DOC,
            ".docgov/checks/anchors.py":
                "def check(root, doc, fields):\n"
                "    return [(f'covers={fields.covers} tier={fields.tier}', None)]\n",
        })
        res = self.run_cli(root, "check")
        self.assertIn("covers=['app.py'] tier=canonical", res.stdout)

    def test_a_hook_that_raises_is_reported_and_goes_red_rather_than_killing_the_gate(self):
        # A broken rule must not read as a pass, and must not take the built-ins with it.
        root = self.make_repo({
            "app.py": "x = 1\n",
            "doc.md": HOOK_DOC.replace("title: Doc\n", "title: Doc\nupdated: 2026-01-01\n"),
            ".docgov/checks/boom.py": "def check(root, doc, fields):\n    raise ValueError('nope')\n",
        })
        res = self.run_cli(root, "check")
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("check hook raised", res.stdout)
        self.assertIn("forbidden key", res.stdout, "built-in findings must still be reported")

    def test_a_hook_that_does_not_import_fails_the_gate_instead_of_being_skipped(self):
        root = self.make_repo({
            "app.py": "x = 1\n", "doc.md": HOOK_DOC,
            ".docgov/checks/broken.py": "this is not python\n",
        })
        res = self.run_cli(root, "check")
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("failed to import", res.stdout)

    def test_an_underscore_module_is_a_helper_and_is_not_run_as_a_rule(self):
        root = self.make_repo({
            "app.py": "x = 1\n", "doc.md": HOOK_DOC,
            ".docgov/checks/_shared.py": "def check(root, doc, fields):\n    return [('never', None)]\n",
        })
        self.assertEqual(self.run_cli(root, "check").returncode, 0)

    def test_a_hook_can_add_a_drift_anchor_the_doc_does_not_list_in_covers(self):
        root = self.make_repo({
            "app.py": "x = 1\n", "extra.py": "y = 1\n", "doc.md": HOOK_DOC,
            ".docgov/checks/extra_anchor.py":
                "def sources(root, doc, fields):\n    return ['extra.py']\n",
        })
        self.git(root, "init", "-q")
        self.git(root, "add", "-A")
        self.git(root, "commit", "-q", "-m", "init")
        with open(os.path.join(root, "extra.py"), "a") as f:
            f.write("y = 2\n")
        res = self.run_cli(root, "sweep")
        self.assertIn("extra.py", res.stdout,
                      "a hook-contributed source must drift the doc like a covers[] entry")

    def test_doc_todo_exempts_one_named_check_and_leaves_the_rest_gating(self):
        # A per-document exemption that silently widens as checks are added is a ratchet
        # (model §9.6) that loosens on its own; `# check:<name>` keeps it pinned.
        root = self.make_repo({
            "app.py": "x = 1\n",
            "doc.md": HOOK_DOC.replace("title: Doc\n", "title: Doc\nupdated: 2026-01-01\n"),
            ".docgov/checks/house.py":
                "def check(root, doc, fields):\n    return [('house finding', None)]\n",
            ".docgov/.doc-todo": "doc.md  # check:house — grandfathered for the house rule only\n",
        })
        res = self.run_cli(root, "check")
        self.assertNotIn("house finding", res.stdout, "the named check must be exempted")
        self.assertIn("forbidden key", res.stdout, "the other checks must still gate")
        self.assertNotEqual(res.returncode, 0)

    def test_a_doc_todo_entry_naming_a_check_nobody_defines_says_so(self):
        # A typo'd or stale check name exempts nothing and looks like it exempts something.
        root = self.make_repo({
            "app.py": "x = 1\n", "doc.md": HOOK_DOC,
            ".docgov/.doc-todo": "doc.md  # check:hosue_rule\n",
        })
        self.assertIn("exempts unknown check 'hosue_rule'", self.run_cli(root, "check").stderr)

    def test_a_repo_keeping_its_index_by_hand_is_not_gated_on_a_map_it_never_generates(self):
        root = self.make_repo({
            "app.py": "x = 1\n", "MAIN.md": MARKED_INDEX,
        }, manifest=INDEX_MANIFEST + "options:\n  index_mode: manual\n")
        res = self.run_cli(root, "index", "--check")
        self.assertEqual(res.returncode, 0)
        self.assertIn("index_mode is `manual`", res.stdout)

    def test_a_bare_doc_todo_line_still_exempts_the_whole_document(self):
        root = self.make_repo({
            "app.py": "x = 1\n",
            "doc.md": HOOK_DOC.replace("title: Doc\n", "title: Doc\nupdated: 2026-01-01\n"),
            ".docgov/.doc-todo": "doc.md\n",
        })
        self.assertEqual(self.run_cli(root, "check").returncode, 0)


# ─────────────────────────────────────────────────────────────────────────────
# v0.3.0 — **Proof:** (ADR-0001 §3). The one claim→evidence edge priced per
# paragraph rather than per document.
# ─────────────────────────────────────────────────────────────────────────────
class ProofTests(RepoMixin, unittest.TestCase):

    def proof_repo(self, body):
        return self.make_repo({
            "app.py": "x = 1\n",
            "spec/thing_spec.rb": "describe\n",
            "doc.md": ("---\nclass: living\ntype: reference\ntitle: T\n"
                       "covers: [app.py]\nlast_verified: 2026-08-01\n---\n" + body),
        })

    def proof(self, root):
        return [m for m, _ in docgov.dead_proof_links(root, os.path.join(root, "doc.md"))]

    def test_a_citation_that_resolves_is_the_evidence_the_claim_says_it_is(self):
        self.assertEqual(self.proof(self.proof_repo(
            "Tasks close on merge.\n\n**Proof:** `spec/thing_spec.rb`\n")), [])

    def test_a_citation_pointing_at_a_spec_that_no_longer_exists_is_flagged(self):
        # The failure this edge exists to catch: the spec moved, the claim did not.
        msgs = self.proof(self.proof_repo("Claim.\n\n**Proof:** `spec/gone_spec.rb`\n"))
        self.assertTrue(any("gone_spec.rb" in m for m in msgs), msgs)

    def test_a_backticked_method_name_is_not_a_path_and_is_not_chased(self):
        msgs = self.proof(self.proof_repo(
            "Claim.\n\n**Proof:** `spec/thing_spec.rb` -> `#close!`\n"))
        self.assertEqual(msgs, [], msgs)

    def test_the_marker_written_inside_a_code_span_is_prose_about_the_convention(self):
        # Every doc that documents this convention would otherwise fail on itself.
        self.assertEqual(self.proof(self.proof_repo(
            "Write `**Proof:**` followed by a path.\n")), [])

    def test_the_marker_shown_inside_a_fenced_example_is_teaching_not_citing(self):
        # A guide that documents the convention must not fail on the example it shows —
        # the failure mode the lifted reference implementation had.
        self.assertEqual(self.proof(self.proof_repo(
            "How to cite:\n\n```markdown\nA claim.\n\n**Proof:** `spec/gone_spec.rb`\n```\n")), [])

    def test_a_marker_citing_nothing_at_all_is_flagged_as_an_empty_claim(self):
        msgs = self.proof(self.proof_repo("Claim.\n\n**Proof:** the integration suite\n"))
        self.assertTrue(any("no backtick-quoted path" in m for m in msgs), msgs)

    def test_a_repo_that_never_writes_the_marker_never_sees_this_check(self):
        # Inert by absence is what lets a portable model carry a prose convention.
        self.assertEqual(self.proof(self.proof_repo("Just a claim, no marker.\n")), [])

    def test_source_keeps_its_older_provenance_meaning_and_is_never_chased(self):
        self.assertEqual(self.proof(self.proof_repo(
            "Claim.\n\n**Source:** `notes/gone-meeting.md`\n")), [])


# ─────────────────────────────────────────────────────────────────────────────
# v0.3.0 — ADR NUMBERING (ADR-0001 §4).
# ─────────────────────────────────────────────────────────────────────────────
ADR_MANIFEST = ("model_version: 0.3.0\npaths:\n  types: _types.yml\n"
                "  decisions: docs/decisions\n")


def _adr(num, slug):
    return (f"---\nclass: immutable\ntype: adr\ntitle: {slug}\ndate: 2026-01-01\n---\n"
            f"# ADR-{num} — {slug}\n")


class AdrNumberingTests(RepoMixin, unittest.TestCase):

    def test_two_files_claiming_one_number_in_one_tree_is_what_a_rebase_leaves_behind(self):
        root = self.make_repo({
            "docs/decisions/0013-alpha.md": _adr("0013", "alpha"),
            "docs/decisions/0013-beta.md": _adr("0013", "beta"),
        }, manifest=ADR_MANIFEST)
        msgs = self.msgs(self.lint(root, "docs/decisions/0013-alpha.md"))
        self.assertTrue(any("claimed by 2 files" in m for m in msgs), msgs)

    def test_distinct_numbers_in_one_home_are_left_alone(self):
        root = self.make_repo({
            "docs/decisions/0013-alpha.md": _adr("0013", "alpha"),
            "docs/decisions/0014-beta.md": _adr("0014", "beta"),
        }, manifest=ADR_MANIFEST)
        self.assertEqual(self.msgs(self.lint(root, "docs/decisions/0013-alpha.md")), [])

    def test_next_proposes_a_number_free_on_every_branch_the_checkout_can_see(self):
        # A human scanning one working tree proposes a number another branch already took.
        root = self.make_repo({"docs/decisions/0002-here.md": _adr("0002", "here")},
                              manifest=ADR_MANIFEST)
        self.git(root, "init", "-q")
        self.git(root, "add", "-A")
        self.git(root, "commit", "-q", "-m", "init")
        self.git(root, "checkout", "-q", "-b", "other")
        os.rename(os.path.join(root, "docs/decisions/0002-here.md"),
                  os.path.join(root, "docs/decisions/0009-there.md"))
        self.git(root, "add", "-A")
        self.git(root, "commit", "-q", "-m", "renumber")
        self.git(root, "checkout", "-q", "-")
        self.assertEqual(self.run_cli(root, "adr", "next").stdout.strip(), "0010",
                         "next must clear the highest number on ANY visible branch, not just HEAD")

    def test_branches_disagreeing_on_a_number_warn_but_do_not_decide_the_merge(self):
        # check reads refs, and a CI checkout is depth 1 with one branch: there the honest
        # answer is "I cannot see the others", not "they agree". A gate must not be wrong
        # exactly where it cannot know.
        root = self.make_repo({"docs/decisions/0002-thing.md": _adr("0002", "thing")},
                              manifest=ADR_MANIFEST)
        self.git(root, "init", "-q")
        self.git(root, "add", "-A")
        self.git(root, "commit", "-q", "-m", "init")
        self.git(root, "checkout", "-q", "-b", "other")
        os.remove(os.path.join(root, "docs/decisions/0002-thing.md"))
        with open(os.path.join(root, "docs/decisions/0007-thing.md"), "w") as f:
            f.write(_adr("0007", "thing"))      # renumbered cleanly — only the branches disagree
        self.git(root, "add", "-A")
        self.git(root, "commit", "-q", "-m", "renumber")
        res = self.run_cli(root, "check")
        self.assertIn("is numbered 2 ways across branches", res.stderr)
        self.assertEqual(res.returncode, 0, "a cross-branch disagreement must not block a merge")


if __name__ == "__main__":
    unittest.main()
