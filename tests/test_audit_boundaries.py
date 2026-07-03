"""Tests for the two gate-invisible-drift checks added to audit-jar.py.

- check_not_for_boundaries (decisions.md HD-2): every installable skill states a
  negative routing boundary.
- check_kit_role_names (decisions.md HD-1): role `name:` fields embedded in
  bundled `*-kit.md` files resolve to a role in the sibling agents/manifest.json.

These exercise the pure regex/helper logic on synthetic input AND run each check
against the live jar as a regression guard, so a future skill with no boundary
or a drifted kit name fails the suite, not just the gate.
"""

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
AUDIT_PATH = REPO / "scripts" / "audit-jar.py"


def load_audit_module():
    # audit-jar.py does `import jarlib` from its own directory.
    scripts = str(REPO / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    spec = importlib.util.spec_from_file_location("audit_jar", AUDIT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class BoundaryCheckTests(unittest.TestCase):
    def setUp(self):
        self.audit = load_audit_module()

    def test_regex_matches_markers(self):
        for good in ("## When NOT to use", "This is NOT for greenfield work",
                     "Not for one bug", "explains when not to use it"):
            self.assertIsNotNone(self.audit.NOT_FOR_RE.search(good), good)

    def test_regex_rejects_a_body_without_a_boundary(self):
        body = "---\nname: x\ndescription: use when x\n---\n# x\nDoes a thing.\n"
        self.assertIsNone(self.audit.NOT_FOR_RE.search(body))

    def test_every_installed_skill_has_a_boundary(self):
        self.audit.results.clear()
        self.audit.check_not_for_boundaries()
        fails = [r for r in self.audit.results if not r[0]]
        self.assertEqual(fails, [], "skills missing a NOT-for boundary: %s" % fails)
        # sanity: the check actually ran over the jar's skills
        self.assertGreaterEqual(
            len([r for r in self.audit.results if r[1] == "boundary"]), 20)


class KitRoleCheckTests(unittest.TestCase):
    def setUp(self):
        self.audit = load_audit_module()

    def test_name_and_role_regexes(self):
        m = self.audit.KIT_NAME_RE.match("name: dead-code-reaper-scout")
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1).strip(), "dead-code-reaper-scout")
        self.assertIsNotNone(self.audit.ROLE_NAME_RE.match("dead-code-reaper-scout"))
        # a title-cased or spaced value is not treated as a role-name claim
        self.assertIsNone(self.audit.ROLE_NAME_RE.match("Some Title Here"))

    def test_manifest_role_names_reads_agents(self):
        tmp = Path(tempfile.mkdtemp(prefix="kit_roles_"))
        (tmp / "agents").mkdir()
        (tmp / "agents" / "manifest.json").write_text(
            json.dumps({"agents": [{"name": "foo-scout"}, {"name": "foo-fixer"}]}),
            encoding="utf-8")
        self.assertEqual(self.audit._manifest_role_names(tmp),
                         {"foo-scout", "foo-fixer"})

    def test_manifest_role_names_missing_returns_none(self):
        tmp = Path(tempfile.mkdtemp(prefix="kit_roles_"))
        self.assertIsNone(self.audit._manifest_role_names(tmp))

    def test_every_bundled_kit_resolves(self):
        self.audit.results.clear()
        self.audit.check_kit_role_names()
        fails = [r for r in self.audit.results if not r[0]]
        self.assertEqual(fails, [], "kit role names not resolving: %s" % fails)


if __name__ == "__main__":
    unittest.main()
