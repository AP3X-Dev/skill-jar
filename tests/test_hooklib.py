import shutil
import tempfile
import unittest
from pathlib import Path

from scripts import hooklib


class HooklibTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="hooklib_test_"))
        (self.tmp / ".claude" / "agents").mkdir(parents=True)
        (self.tmp / "development" / "agents" / "claude").mkdir(parents=True)
        (self.tmp / "agent-state").mkdir()
        (self.tmp / "agent-state" / "failed-attempts.md").write_text(
            "# Failed Attempts -- jar-audit\n\n"
            "| ID | Task | What Failed | Lesson |\n"
            "|----|------|-------------|--------|\n",
            encoding="utf-8",
        )
        (self.tmp / ".claude" / "agents" / "fixer.md").write_text(
            "---\nname: fixer\n---\n\n"
            "# Fixer\n\n"
            "Skill: `bug-pipeline`\n\n"
            "## Hooks\n"
            "- `after_task` -> `record_usage` (`agent-state/skill-usage.md`): Record success.\n"
            "- `on_error` -> `record_usage` (`agent-state/skill-usage.md`): Record error.\n"
            "- `on_error` -> `queue_improvement` (`agent-state/skill-usage.md`): Queue error.\n"
            "- `on_error` -> `log_failed_attempt` (`agent-state/failed-attempts.md`): Log failure.\n",
            encoding="utf-8",
        )
        (self.tmp / "development" / "agents" / "claude" / "generated-role.md").write_text(
            "# Generated Role\n\n"
            "Skill: `generated-skill`\n\n"
            "## Hooks\n"
            "- `after_task` -> `record_usage` (`agent-state/skill-usage.md`): Record generated usage.\n",
            encoding="utf-8",
        )

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_load_hooks_from_repo_local_agent(self):
        hooks = hooklib.load_hooks(self.tmp, "fixer")
        self.assertEqual(hooks[0]["event"], "after_task")
        self.assertEqual(hooks[0]["action"], "record_usage")
        self.assertEqual(hooks[0]["target"], "agent-state/skill-usage.md")

    def test_finds_generated_category_agent(self):
        path = hooklib.find_agent_file(self.tmp, "generated-role")
        self.assertEqual(path.relative_to(self.tmp).as_posix(), "development/agents/claude/generated-role.md")

    def test_record_usage_and_queue_improvement_are_append_only(self):
        hooklib.apply_hooks(
            self.tmp,
            "fixer",
            "after_task",
            {"skill": "bug-pipeline", "note": "fixed one bug"},
        )
        hooklib.apply_hooks(
            self.tmp,
            "fixer",
            "on_error",
            {
                "skill": "bug-pipeline",
                "note": "missed the validator gate",
                "failure_task": "bug fix",
                "failure_what": "gate failed",
                "lesson": "rerun audit before marking fixed",
            },
        )

        usage = (self.tmp / "agent-state" / "skill-usage.md").read_text(encoding="utf-8")
        failed = (self.tmp / "agent-state" / "failed-attempts.md").read_text(encoding="utf-8")
        self.assertIn("- [bug-pipeline/fixer/after_task] fixed one bug", usage)
        self.assertIn("- [bug-pipeline/fixer/on_error] missed the validator gate", usage)
        self.assertIn("- [bug-pipeline/fixer/on_error] review candidate: missed the validator gate", usage)
        self.assertIn("| bug fix | gate failed | rerun audit before marking fixed |", failed)

        hooklib.apply_hooks(
            self.tmp,
            "fixer",
            "after_task",
            {"skill": "bug-pipeline", "note": "fixed one bug"},
        )
        usage_again = (self.tmp / "agent-state" / "skill-usage.md").read_text(encoding="utf-8")
        self.assertEqual(usage_again.count("fixed one bug"), 1)

    def test_unsupported_action_fails_closed(self):
        (self.tmp / ".claude" / "agents" / "bad.md").write_text(
            "# Bad\n\nSkill: `bad-skill`\n\n## Hooks\n"
            "- `after_task` -> `rewrite_skill` (`development/bad-skill/SKILL.md`): Unsafe.\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "unsupported hook action"):
            hooklib.apply_hooks(self.tmp, "bad", "after_task", {"skill": "bad-skill", "note": "x"})


if __name__ == "__main__":
    unittest.main()
