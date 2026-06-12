import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SYNC_PATH = REPO / "scripts" / "sync-jar.py"


def load_sync_module():
    spec = importlib.util.spec_from_file_location("sync_jar", SYNC_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class SyncJarTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sync_jar_test_"))
        (self.tmp / "agent-state").mkdir()
        (self.tmp / "development" / "sample-skill").mkdir(parents=True)
        (self.tmp / "development" / "sample-skill" / "SKILL.md").write_text(
            "---\n"
            "name: sample-skill\n"
            "description: Use when testing drop-in reconciliation.\n"
            "---\n"
            "\n"
            "# sample-skill\n",
            encoding="utf-8",
        )
        (self.tmp / "agent-state" / "SKILL_FORGE_TRACKER.md").write_text(
            "# Skill Forge Tracker -- skill-jar\n"
            "\n"
            "## Queue\n"
            "\n"
            "| ID | Skill | Category | Path | Status | Clean Runs | Pressure Focus | Last Evidence | Next Action |\n"
            "|----|-------|----------|------|--------|------------|----------------|---------------|-------------|\n",
            encoding="utf-8",
        )

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_adds_missing_skill_forge_row_and_usage_file(self):
        sync_jar = load_sync_module()
        calls = []

        summary = sync_jar.sync(self.tmp, run_command=lambda cmd: calls.append(cmd) or 0)

        tracker = (self.tmp / "agent-state" / "SKILL_FORGE_TRACKER.md").read_text(encoding="utf-8")
        usage = (self.tmp / "agent-state" / "skill-usage.md").read_text(encoding="utf-8")
        self.assertIn("| SF-001 | sample-skill | development | `development/sample-skill/SKILL.md` | pending-red | 0/3 | drop-in skill pressure | - | RED scenario |", tracker)
        self.assertIn("## Usage Entries", usage)
        self.assertIn("## Improvement Queue", usage)
        self.assertEqual(summary["tracker_rows_added"], 1)
        self.assertEqual(calls, [
            ["python", "scripts/gen-index.py"],
            ["python", "scripts/gen-plugins.py"],
            ["python", "scripts/gen-agent-packs.py"],
        ])

    def test_preserves_existing_rows_and_reports_missing_skill_rows(self):
        tracker = self.tmp / "agent-state" / "SKILL_FORGE_TRACKER.md"
        tracker.write_text(
            tracker.read_text(encoding="utf-8")
            + "| SF-009 | removed-skill | development | `development/removed-skill/SKILL.md` | pending-red | 0/3 | old pressure | - | RED scenario |\n",
            encoding="utf-8",
        )
        sync_jar = load_sync_module()

        summary = sync_jar.sync(self.tmp, run_command=lambda cmd: 0)

        text = tracker.read_text(encoding="utf-8")
        self.assertIn("removed-skill", text)
        self.assertEqual(summary["stale_tracker_rows"], ["removed-skill"])
        self.assertEqual(summary["tracker_rows_added"], 1)


if __name__ == "__main__":
    unittest.main()
