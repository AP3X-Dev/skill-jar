"""Tests for the spec-driven-change bundled scripts.

Loads the two hyphenated scripts as modules and exercises their pure logic so a
future edit that breaks the grammar validator or the delta merger fails the jar
suite, not just at runtime. Mirrors the importlib-load pattern used for
audit-jar.py in test_audit_boundaries.py.
"""

import importlib.util
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "development" / "spec-driven-change" / "scripts"


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


validate = load("validate_spec", "validate-spec.py")
merge = load("archive_merge", "archive-merge.py")


GOOD = (
    "### Requirement: Login\nThe system MUST accept a password.\n\n"
    "#### Scenario: ok\n- GIVEN a user\n- WHEN correct\n- THEN a session\n"
)


class ValidateSpec(unittest.TestCase):
    def test_selftest_passes(self):
        self.assertEqual(validate.selftest(), 0)

    def test_good_spec_has_no_errors(self):
        errs, _ = validate.validate_text(GOOD, "good")
        self.assertEqual(errs, [])

    def test_scenario_wrong_hash_depth_is_error(self):
        text = GOOD.replace("#### Scenario:", "### Scenario:")
        errs, _ = validate.validate_text(text, "bad")
        self.assertTrue(any("exactly 4 hashes" in e for e in errs), errs)

    def test_requirement_without_scenario_is_error(self):
        errs, _ = validate.validate_text(
            "### Requirement: Lonely\nThe system SHALL do a thing.\n", "x")
        self.assertTrue(any("no Scenario" in e for e in errs), errs)

    def test_unknown_delta_header_is_error(self):
        errs, _ = validate.validate_text(
            "## APPENDED Requirements\n### Requirement: X\nThe system MUST x.\n"
            "#### Scenario: s\n- GIVEN a\n- WHEN b\n- THEN c\n", "d")
        self.assertTrue(any("unknown delta section" in e for e in errs), errs)

    def test_removed_requirement_exempt_from_scenario_rule(self):
        errs, _ = validate.validate_text(
            "## REMOVED Requirements\n### Requirement: Gone\n", "d")
        self.assertEqual(errs, [])


class ArchiveMerge(unittest.TestCase):
    def test_selftest_passes(self):
        self.assertEqual(merge.selftest(), 0)

    def test_added_appends_and_merged_output_validates(self):
        living = "# Cap\n\n" + GOOD
        delta = ("## ADDED Requirements\n### Requirement: Logout\n"
                 "The system MUST end a session.\n\n#### Scenario: bye\n"
                 "- GIVEN a session\n- WHEN the user logs out\n- THEN it ends\n")
        new_text, actions = merge.apply_delta(living, delta)
        self.assertIn("### Requirement: Logout", new_text)
        self.assertIn("### Requirement: Login", new_text)
        self.assertTrue(actions[0].startswith("ADDED"))
        # the merged living spec is itself valid
        errs, _ = validate.validate_text(new_text, "merged")
        self.assertEqual(errs, [])

    def test_conflicts_raise_not_corrupt(self):
        with self.assertRaises(ValueError):
            merge.apply_delta(GOOD, "## REMOVED Requirements\n### Requirement: Nope\n")
        with self.assertRaises(ValueError):
            merge.apply_delta(
                "### Requirement: Login\nThe system MUST x.\n#### Scenario: s\n"
                "- GIVEN a\n- WHEN b\n- THEN c\n",
                "## ADDED Requirements\n### Requirement: Login\nThe system MUST x.\n"
                "#### Scenario: s\n- GIVEN a\n- WHEN b\n- THEN c\n")

    def test_order_is_renamed_removed_modified_added(self):
        living = ("### Requirement: A\nThe system MUST a.\n#### Scenario: s\n"
                  "- GIVEN a\n- WHEN b\n- THEN c\n")
        delta = ("## RENAMED Requirements\n- FROM: `A`\n- TO: `B`\n")
        new_text, actions = merge.apply_delta(living, delta)
        self.assertIn("### Requirement: B", new_text)
        self.assertNotIn("### Requirement: A\n", new_text)
        self.assertTrue(actions[0].startswith("RENAMED"))


if __name__ == "__main__":
    unittest.main()
