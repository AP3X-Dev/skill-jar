#!/usr/bin/env python3
"""Generate host-specific category agent files from manifests.

Any category may ship an ``agents/manifest.json`` file. This script renders
copy-ready Claude Code and Codex agent files under that category's
``agents/claude`` and ``agents/codex`` directories so role instructions stay in
sync across hosts.

Usage:
    python scripts/gen-agent-packs.py            # write generated files
    python scripts/gen-agent-packs.py --check    # exit 0 if generated files match
"""

import argparse
import json
import re
import sys
from pathlib import Path, PurePosixPath, PureWindowsPath

import jarlib

ROOT = jarlib.repo_root()
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
HOOK_EVENTS = (
    "after_task",
    "on_error",
    "on_reject",
    "on_no_failure",
    "on_loophole",
    "on_fail",
)
HOOK_ACTIONS = (
    "record_usage",
    "queue_improvement",
    "log_failed_attempt",
    "append_note",
    "update_tracker",
    "append_red_package",
    "strengthen_scenario",
    "advance_or_reopen",
    "record_verdict",
    "record_structure_result",
)
TARGET_APPEND_ACTIONS = (
    "append_note",
    "append_red_package",
    "strengthen_scenario",
    "record_verdict",
    "record_structure_result",
)
DEFAULT_HOOKS = [
    {
        "event": "after_task",
        "action": "record_usage",
        "target": "agent-state/skill-usage.md",
        "instructions": "Append a usage note so successful task completions become improvement evidence.",
    },
    {
        "event": "on_error",
        "action": "record_usage",
        "target": "agent-state/skill-usage.md",
        "instructions": "Append an error note so failed runs become improvement evidence.",
    },
    {
        "event": "on_error",
        "action": "queue_improvement",
        "target": "agent-state/skill-usage.md",
        "instructions": "Queue this failure as a future skill-forge pressure candidate.",
    },
    {
        "event": "on_error",
        "action": "log_failed_attempt",
        "target": "agent-state/failed-attempts.md",
        "instructions": "Record the failed approach and exact symptom before stopping.",
    },
]


def manifest_paths():
    return sorted(
        cat / "agents" / "manifest.json"
        for cat in jarlib.category_dirs(ROOT)
        if (cat / "agents" / "manifest.json").exists()
    )


def load_manifest(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("%s JSON parse error: %s" % (path.relative_to(ROOT).as_posix(), exc)) from exc
    agents = data.get("agents")
    if not isinstance(agents, list) or not agents:
        raise ValueError("%s must contain a non-empty agents list" % path.relative_to(ROOT).as_posix())
    return data


def skill_names(category):
    return {
        skill["dir_name"]
        for skill in jarlib.discover_skills(ROOT)
        if skill["category"] == category
    }


def require_list(agent, key):
    val = agent.get(key)
    if not isinstance(val, list) or not val or not all(isinstance(x, str) and x for x in val):
        raise ValueError("%s: %s must be a non-empty list of strings" % (agent.get("name"), key))
    return val


def require_single_line(agent_name, key, value):
    if "\r" in value or "\n" in value:
        raise ValueError("%s: hook %s must be single-line" % (agent_name, key))


def require_hook_target(agent_name, target):
    require_single_line(agent_name, "target", target)
    if "`" in target:
        raise ValueError("%s: hook target must not contain backticks" % agent_name)
    if "\\" in target:
        raise ValueError("%s: hook target must use agent-state/ paths" % agent_name)

    posix_path = PurePosixPath(target)
    windows_path = PureWindowsPath(target)
    if posix_path.is_absolute() or windows_path.is_absolute() or windows_path.drive:
        raise ValueError("%s: hook target outside agent-state: %s" % (agent_name, target))
    if not posix_path.parts or posix_path.parts[0] != "agent-state" or ".." in posix_path.parts:
        raise ValueError("%s: hook target outside agent-state: %s" % (agent_name, target))
    if posix_path.name == "SKILL.md":
        raise ValueError("%s: hook target cannot be SKILL.md: %s" % (agent_name, target))


def require_hooks(agent):
    hooks = agent.get("hooks")
    if hooks is None:
        return []
    if not isinstance(hooks, list) or not hooks:
        raise ValueError("%s: hooks must be a non-empty list of objects" % agent.get("name"))
    for hook in hooks:
        if not isinstance(hook, dict):
            raise ValueError("%s: each hook must be an object" % agent.get("name"))
        for key in ("event", "action", "instructions"):
            if not isinstance(hook.get(key), str) or not hook[key].strip():
                raise ValueError("%s: hook %s must be a non-empty string" % (agent.get("name"), key))
            require_single_line(agent.get("name"), key, hook[key])
        if hook["event"] not in HOOK_EVENTS:
            raise ValueError("%s: unsupported hook event: %s" % (agent.get("name"), hook["event"]))
        if hook["action"] not in HOOK_ACTIONS:
            raise ValueError("%s: unsupported hook action: %s" % (agent.get("name"), hook["action"]))
        if "target" in hook and (not isinstance(hook["target"], str) or not hook["target"].strip()):
            raise ValueError("%s: hook target must be a non-empty string" % agent.get("name"))
        if hook["action"] in TARGET_APPEND_ACTIONS and not hook.get("target"):
            raise ValueError("%s: %s requires explicit hook target" % (agent.get("name"), hook["action"]))
        if "target" in hook:
            require_hook_target(agent.get("name"), hook["target"])
    return hooks


def validate_agents(data, category):
    known_skills = skill_names(category)
    seen = set()
    out = []
    for agent in data["agents"]:
        if not isinstance(agent, dict):
            raise ValueError("%s: each agent entry must be an object" % category)
        name = agent.get("name")
        if not isinstance(name, str) or not NAME_RE.match(name):
            raise ValueError("%s: agent name must be kebab-case: %r" % (category, name))
        if name in seen:
            raise ValueError("%s: duplicate agent name: %s" % (category, name))
        seen.add(name)
        skill = agent.get("skill")
        if skill not in known_skills:
            raise ValueError("%s: %s references unknown skill %r" % (category, name, skill))
        for key in ("description", "title", "mission"):
            if not isinstance(agent.get(key), str) or not agent[key].strip():
                raise ValueError("%s: %s must be a non-empty string" % (name, key))
        require_list(agent, "tools")
        require_list(agent, "responsibilities")
        require_list(agent, "rules")
        require_list(agent, "output")
        require_hooks(agent)
        if agent.get("claude_model") not in ("sonnet", "opus"):
            raise ValueError("%s: claude_model must be sonnet or opus" % name)
        if agent.get("codex_reasoning_effort") not in ("low", "medium", "high"):
            raise ValueError("%s: codex_reasoning_effort must be low, medium, or high" % name)
        out.append(agent)
    return out


def check_skill_references(category, agents):
    """Ensure SKILL.md points to its generated roles without embedding bodies."""
    errors = []
    by_skill = {}
    for agent in agents:
        by_skill.setdefault(agent["skill"], []).append(agent["name"])
    for skill, names in sorted(by_skill.items()):
        skill_md = ROOT / category / skill / "SKILL.md"
        text = skill_md.read_text(encoding="utf-8")
        rel = skill_md.relative_to(ROOT).as_posix()
        if "../agents/README.md" not in text:
            errors.append("%s: missing generated agent-pack link to ../agents/README.md" % rel)
        if "../agents/manifest.json" not in text:
            errors.append("%s: missing generated agent manifest link to ../agents/manifest.json" % rel)
        for name in names:
            if name not in text:
                errors.append("%s: missing generated agent role `%s`" % (rel, name))
    return errors


def body(agent):
    hooks = DEFAULT_HOOKS + (agent.get("hooks") or [])
    lines = [
        "# %s" % agent["title"],
        "",
        "Skill: `%s`" % agent["skill"],
        "",
        agent["mission"].strip(),
        "",
        "## Hooks",
    ]
    for hook in hooks:
        if hook.get("target"):
            lines.append("- `%s` -> `%s` (`%s`): %s" %
                         (hook["event"], hook["action"], hook["target"], hook["instructions"]))
        else:
            lines.append("- `%s` -> `%s`: %s" %
                         (hook["event"], hook["action"], hook["instructions"]))
    lines += [
        "",
        "## Responsibilities",
    ]
    lines += ["- %s" % item for item in agent["responsibilities"]]
    lines += ["", "## Rules"]
    lines += ["- %s" % item for item in agent["rules"]]
    lines += ["", "## Output"]
    lines += ["- %s" % item for item in agent["output"]]
    return "\n".join(lines).rstrip() + "\n"


def render_claude(agent):
    header = [
        "---",
        "name: %s" % agent["name"],
        "description: %s" % json.dumps(agent["description"], ensure_ascii=False),
        "model: %s" % agent["claude_model"],
        "tools: %s" % ", ".join(agent["tools"]),
        "---",
        "",
    ]
    return "\n".join(header) + body(agent)


def render_codex(agent):
    text = body(agent)
    if "'''" in text:
        raise ValueError("%s: developer instructions cannot contain triple single quotes" % agent["name"])
    return "\n".join([
        'name = %s' % json.dumps(agent["name"]),
        'description = %s' % json.dumps(agent["description"]),
        'model = %s' % json.dumps(agent.get("codex_model", "gpt-5")),
        'model_reasoning_effort = %s' % json.dumps(agent["codex_reasoning_effort"]),
        "developer_instructions = '''",
        text.rstrip(),
        "'''",
        "",
    ])


def expected_files(agent_root, agents):
    files = {}
    claude_dir = agent_root / "claude"
    codex_dir = agent_root / "codex"
    for agent in agents:
        files[claude_dir / ("%s.md" % agent["name"])] = render_claude(agent)
        files[codex_dir / ("%s.toml" % agent["name"])] = render_codex(agent)
    return files


def existing_generated_files(agent_root):
    files = []
    claude_dir = agent_root / "claude"
    codex_dir = agent_root / "codex"
    if claude_dir.exists():
        files += sorted(claude_dir.glob("*.md"))
    if codex_dir.exists():
        files += sorted(codex_dir.glob("*.toml"))
    return files


def build_expected():
    manifests = manifest_paths()
    if not manifests:
        raise ValueError("no category agent manifests found")
    files = {}
    agent_count = 0
    for path in manifests:
        category = path.parent.parent.name
        agents = validate_agents(load_manifest(path), category)
        reference_errors = check_skill_references(category, agents)
        if reference_errors:
            raise ValueError("; ".join(reference_errors))
        files.update(expected_files(path.parent, agents))
        agent_count += len(agents)
    return files, agent_count, len(manifests)


def check(files):
    errors = []
    expected_paths = set(files)
    for path, expected in sorted(files.items()):
        if not path.exists():
            errors.append("missing generated file: %s" % path.relative_to(ROOT).as_posix())
            continue
        if path.read_text(encoding="utf-8") != expected:
            errors.append("stale generated file: %s" % path.relative_to(ROOT).as_posix())
    for path in manifest_paths():
        for generated in existing_generated_files(path.parent):
            if generated not in expected_paths:
                errors.append("unexpected generated file: %s" % generated.relative_to(ROOT).as_posix())
    return errors


def write(files):
    expected_paths = set(files)
    for path in manifest_paths():
        (path.parent / "claude").mkdir(parents=True, exist_ok=True)
        (path.parent / "codex").mkdir(parents=True, exist_ok=True)
        for generated in existing_generated_files(path.parent):
            if generated not in expected_paths:
                generated.unlink()
    for path, content in sorted(files.items()):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate or verify category agent packs.")
    parser.add_argument("--check", action="store_true", help="verify generated files are in sync")
    args = parser.parse_args(argv)
    try:
        files, agent_count, manifest_count = build_expected()
        if args.check:
            errors = check(files)
            if errors:
                print("FAIL: category agent packs are stale")
                for err in errors:
                    print("- %s" % err)
                return 1
            print("OK: category agent packs in sync (%d manifests, %d agents, %d files)" %
                  (manifest_count, agent_count, len(files)))
            return 0
        write(files)
        print("wrote %d agent files for %d agents across %d manifests" %
              (len(files), agent_count, manifest_count))
        return 0
    except ValueError as exc:
        print("FAIL: %s" % exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
