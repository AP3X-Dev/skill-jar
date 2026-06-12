import unittest
from pathlib import Path

from scripts import hooklib


REPO = Path(__file__).resolve().parents[1]


class RepoHookWiringTests(unittest.TestCase):
    def test_repo_local_agents_declare_expected_lifecycle_hooks(self):
        fixer_events = {(h["event"], h["action"]) for h in hooklib.load_hooks(REPO, "fixer")}
        hunter_events = {(h["event"], h["action"]) for h in hooklib.load_hooks(REPO, "hunter")}
        validator_events = {(h["event"], h["action"]) for h in hooklib.load_hooks(REPO, "validator")}

        self.assertEqual(
            fixer_events,
            {
                ("after_task", "record_usage"),
                ("after_task", "append_note"),
                ("on_error", "log_failed_attempt"),
                ("after_task_audit", "append_note"),
                ("on_error_audit", "log_failed_attempt"),
            },
        )
        self.assertEqual(
            hunter_events,
            {
                ("after_task", "record_usage"),
                ("after_task", "append_note"),
                ("on_error", "log_failed_attempt"),
            },
        )
        self.assertEqual(
            validator_events,
            {
                ("after_task", "record_usage"),
                ("after_task", "append_note"),
                ("on_reject", "log_failed_attempt"),
                ("after_task_audit", "append_note"),
                ("on_reject_audit", "log_failed_attempt"),
            },
        )

    def test_driver_prompts_reference_hook_dispatcher(self):
        for rel in (
            "docs/prompts/jar-audit-driver.md",
            "docs/prompts/bug-pipeline-driver.md",
            "docs/prompts/skill-forge-driver.md",
        ):
            with self.subTest(prompt=rel):
                text = (REPO / rel).read_text(encoding="utf-8")
                self.assertIn("scripts/dispatch-agent-hooks.py", text, rel)


if __name__ == "__main__":
    unittest.main()
