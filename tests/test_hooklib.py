import shutil
import tempfile
import unittest
from pathlib import Path

from scripts import hooklib


def split_markdown_row(row):
    cells = []
    current = []
    escaped = False
    for char in row.strip():
        if escaped:
            current.append(char)
            escaped = False
        elif char == "\\":
            current.append(char)
            escaped = True
        elif char == "|":
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    cells.append("".join(current).strip())
    return cells[1:-1]


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

    def test_failed_attempt_cells_escape_pipes_and_normalize_newlines(self):
        hooklib.append_failed_attempt(
            self.tmp,
            "bug | fix\ncycle",
            "gate\tfailed | badly",
            "rerun\naudit | before marking fixed",
        )

        rows = (self.tmp / "agent-state" / "failed-attempts.md").read_text(encoding="utf-8").splitlines()
        attempt_row = next(row for row in rows if row.startswith("| FA-"))
        cells = split_markdown_row(attempt_row)
        self.assertEqual(len(cells), 4)
        self.assertEqual(cells[1], "bug \\| fix cycle")
        self.assertEqual(cells[2], "gate failed \\| badly")
        self.assertEqual(cells[3], "rerun audit \\| before marking fixed")

    def test_update_tracker_escapes_payload_cells_and_preserves_existing_escaped_pipes(self):
        tracker = self.tmp / "agent-state" / "SKILL_FORGE_TRACKER.md"
        tracker.write_text(
            "# Skill Forge Tracker -- skill-jar\n\n"
            "## Queue\n\n"
            "| ID | Skill | Category | Path | Status | Clean Runs | Pressure Focus | Last Evidence | Next Action |\n"
            "|----|-------|----------|------|--------|------------|----------------|---------------|-------------|\n"
            "| SF-001 | bug-pipeline | development | `development/bug-pipeline/SKILL.md` | pending-red | 0/3 | pressure \\| focus | old evidence | RED scenario |\n",
            encoding="utf-8",
        )

        hooklib.update_tracker(
            self.tmp,
            "bug-pipeline",
            "pending | review\nblocked",
            "1/3",
            "validator | failed\nrerun",
            "write RED | package\tfirst",
        )

        row = next(
            line
            for line in tracker.read_text(encoding="utf-8").splitlines()
            if line.startswith("| SF-001")
        )
        cells = split_markdown_row(row)
        self.assertEqual(len(cells), 9)
        self.assertEqual(cells[4], "pending \\| review blocked")
        self.assertEqual(cells[6], "pressure \\| focus")
        self.assertEqual(cells[7], "validator \\| failed rerun")
        self.assertEqual(cells[8], "write RED \\| package first")

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
