import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "gen-agent-packs.py"


def load_generator():
    scripts_dir = str(SCRIPT.parent)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("gen_agent_packs", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sample_agent(**overrides):
    agent = {
        "name": "sample-agent",
        "skill": "sample-skill",
        "description": "Sample agent.",
        "title": "Sample Agent",
        "claude_model": "sonnet",
        "codex_reasoning_effort": "medium",
        "tools": ["Read", "Bash"],
        "mission": "Exercise generated lifecycle hooks.",
        "responsibilities": ["Do the assigned task."],
        "rules": ["Stay in scope."],
        "output": ["Report the result."],
    }
    agent.update(overrides)
    return agent


class GeneratedAgentHooksTests(unittest.TestCase):
    def setUp(self):
        self.gen = load_generator()

    def test_body_renders_default_hooks(self):
        text = self.gen.body(sample_agent())

        self.assertIn("## Hooks", text)
        self.assertLess(text.index("## Hooks"), text.index("## Responsibilities"))
        self.assertIn(
            "- `after_task` -> `record_usage` (`agent-state/skill-usage.md`): "
            "Append a usage note so successful task completions become improvement evidence.",
            text,
        )
        self.assertIn(
            "- `on_error` -> `record_usage` (`agent-state/skill-usage.md`): "
            "Append an error note so failed runs become improvement evidence.",
            text,
        )
        self.assertIn(
            "- `on_error` -> `log_failed_attempt` (`agent-state/failed-attempts.md`): "
            "Record the failed approach and exact symptom before stopping.",
            text,
        )

    def test_manifest_hooks_are_validated_and_rendered(self):
        agent = sample_agent(
            hooks=[
                {
                    "event": "on_reject",
                    "action": "append_note",
                    "target": "agent-state/rejections.md",
                    "instructions": "Capture the rejection reason for the next cycle.",
                },
                {
                    "event": "on_no_failure",
                    "action": "record_verdict",
                    "instructions": "Record the clean verdict for loop progress.",
                },
            ]
        )

        self.gen.require_hooks(agent)
        text = self.gen.body(agent)

        self.assertIn(
            "- `on_reject` -> `append_note` (`agent-state/rejections.md`): "
            "Capture the rejection reason for the next cycle.",
            text,
        )
        self.assertIn(
            "- `on_no_failure` -> `record_verdict`: Record the clean verdict for loop progress.",
            text,
        )

    def test_unknown_hook_action_raises_value_error(self):
        agent = sample_agent(
            hooks=[
                {
                    "event": "after_task",
                    "action": "rewrite_skill",
                    "instructions": "Rewrite the skill after every task.",
                }
            ]
        )

        with self.assertRaisesRegex(ValueError, "unsupported hook action"):
            self.gen.require_hooks(agent)


if __name__ == "__main__":
    unittest.main()
