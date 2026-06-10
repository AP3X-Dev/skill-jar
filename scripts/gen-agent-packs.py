#!/usr/bin/env python3
"""Generate host-specific development agent files from one manifest.

The source of truth is ``development/agents/manifest.json``. This script renders
copy-ready Claude Code and Codex agent files so role instructions stay in sync
across hosts.

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
AGENT_ROOT = ROOT / "development" / "agents"
MANIFEST = AGENT_ROOT / "manifest.json"
CLAUDE_DIR = AGENT_ROOT / "claude"
CODEX_DIR = AGENT_ROOT / "codex"
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def load_manifest():
    if not MANIFEST.exists():
        raise ValueError("development/agents/manifest.json is missing")
    try:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("manifest JSON parse error: %s" % exc) from exc
    agents = data.get("agents")
    if not isinstance(agents, list) or not agents:
        raise ValueError("manifest must contain a non-empty agents list")
    return data


def development_skill_names():
    return {
        skill["dir_name"]
        for skill in jarlib.discover_skills(ROOT)
        if skill["category"] == "development"
    }


def require_list(agent, key):
    val = agent.get(key)
    if not isinstance(val, list) or not val or not all(isinstance(x, str) and x for x in val):
        raise ValueError("%s: %s must be a non-empty list of strings" % (agent.get("name"), key))
    return val


def validate_agents(data):
    known_skills = development_skill_names()
    seen = set()
    out = []
    for agent in data["agents"]:
        if not isinstance(agent, dict):
            raise ValueError("each agent entry must be an object")
        name = agent.get("name")
        if not isinstance(name, str) or not NAME_RE.match(name):
            raise ValueError("agent name must be kebab-case: %r" % name)
        if name in seen:
            raise ValueError("duplicate agent name: %s" % name)
        seen.add(name)
        skill = agent.get("skill")
        if skill not in known_skills:
            raise ValueError("%s: unknown development skill %r" % (name, skill))
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


def expected_files(agents):
    files = {}
    for agent in agents:
        files[CLAUDE_DIR / ("%s.md" % agent["name"])] = render_claude(agent)
        files[CODEX_DIR / ("%s.toml" % agent["name"])] = render_codex(agent)
    return files


def existing_generated_files():
    files = []
    if CLAUDE_DIR.exists():
        files += sorted(CLAUDE_DIR.glob("*.md"))
    if CODEX_DIR.exists():
        files += sorted(CODEX_DIR.glob("*.toml"))
    return files


def check(files):
    errors = []
    expected_paths = set(files)
    for path, expected in sorted(files.items()):
        if not path.exists():
            errors.append("missing generated file: %s" % path.relative_to(ROOT).as_posix())
            continue
        if path.read_text(encoding="utf-8") != expected:
            errors.append("stale generated file: %s" % path.relative_to(ROOT).as_posix())
    for path in existing_generated_files():
        if path not in expected_paths:
            errors.append("unexpected generated file: %s" % path.relative_to(ROOT).as_posix())
    return errors


def write(files):
    CLAUDE_DIR.mkdir(parents=True, exist_ok=True)
    CODEX_DIR.mkdir(parents=True, exist_ok=True)
    expected_paths = set(files)
    for path, content in sorted(files.items()):
        path.write_text(content, encoding="utf-8")
    for path in existing_generated_files():
        if path not in expected_paths:
            path.unlink()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate or verify development agent packs.")
    parser.add_argument("--check", action="store_true", help="verify generated files are in sync")
    args = parser.parse_args(argv)
    try:
        agents = validate_agents(load_manifest())
        files = expected_files(agents)
        if args.check:
            errors = check(files)
            if errors:
                print("FAIL: development agent packs are stale")
                for err in errors:
                    print("- %s" % err)
                return 1
            print("OK: development agent packs in sync (%d agents, %d files)" % (len(agents), len(files)))
            return 0
        write(files)
        print("wrote %d agent files for %d agents" % (len(files), len(agents)))
        return 0
    except ValueError as exc:
        print("FAIL: %s" % exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
