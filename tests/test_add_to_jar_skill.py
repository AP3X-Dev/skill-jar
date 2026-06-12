import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "development" / "add-to-jar" / "SKILL.md"


class AddToJarSkillTests(unittest.TestCase):
    def test_skill_documents_required_drop_in_workflow(self):
        text = SKILL.read_text(encoding="utf-8")

        required_phrases = [
            "name: add-to-jar",
            "exactly one skill",
            "python scripts/sync-jar.py",
            "python scripts/audit-jar.py",
            "agent-state/SKILL_FORGE_TRACKER.md",
            "Do not push",
            "Stop",
        ]

        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
