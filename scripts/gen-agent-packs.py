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
from pathlib import Path

import jarlib

ROOT = jarlib.repo_root()
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


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
        if agent.get("claude_model") not in ("sonnet", "opus"):
            raise ValueError("%s: claude_model must be sonnet or opus" % name)
        if agent.get("codex_reasoning_effort") not in ("low", "medium", "high"):
            raise ValueError("%s: codex_reasoning_effort must be low, medium, or high" % name)
        out.append(agent)
    return out


def body(agent):
    lines = [
        "# %s" % agent["title"],
        "",
        "Skill: `%s`" % agent["skill"],
        "",
        agent["mission"].strip(),
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
