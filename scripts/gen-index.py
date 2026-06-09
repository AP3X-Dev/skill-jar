#!/usr/bin/env python3
"""Generate (or verify) skills.json -- the jar's machine-readable index.

An agent fetching this repo reads ONE file to route, instead of crawling
directories: skills.json lists every top-level jar skill with its name,
description (the frontmatter routing text), and path.

The index is GENERATED -- never edit it by hand. The audit gate
(scripts/audit-jar.py) runs this script with --check every cycle and in CI,
so a stale index fails the build instead of rotting silently.

Usage:
    python scripts/gen-index.py            # (re)write skills.json
    python scripts/gen-index.py --check    # exit 0 if in sync, 1 if stale
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "skills.json"

# Loop infrastructure / assets -- not jar-skill content.
SKIP_DIR_NAMES = {
    ".git", ".github", ".claude", ".codex", "agent-state", "docs", "scripts",
    "assets", "node_modules", "__pycache__", ".venv", "venv",
}


def parse_frontmatter(text):
    """Return the frontmatter dict, or None if it doesn't parse."""
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    fm = parts[1]
    try:
        import yaml  # type: ignore
        data = yaml.safe_load(fm)
        return data if isinstance(data, dict) else None
    except ImportError:
        data = {}
        for line in fm.strip().splitlines():
            m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
            if m:
                data[m.group(1)] = m.group(2).strip("\"'")
        return data or None
    except Exception:
        return None


def build_index():
    """Build the index dict from top-level */SKILL.md frontmatter."""
    skills = []
    for f in sorted(ROOT.glob("*/SKILL.md")):
        if f.parent.name in SKIP_DIR_NAMES:
            continue
        data = parse_frontmatter(f.read_text(encoding="utf-8"))
        if not data:
            continue  # the audit gate reports broken frontmatter separately
        skills.append({
            "name": data.get("name", f.parent.name),
            "description": data.get("description", ""),
            "path": f.relative_to(ROOT).as_posix(),
        })
    skills.sort(key=lambda s: s["name"])
    return {
        "_generated": "by scripts/gen-index.py -- do not edit by hand; "
                      "the audit gate fails if this file is stale",
        "skills": skills,
    }


def render(index):
    return json.dumps(index, indent=2, ensure_ascii=False) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate or verify skills.json (exit 0/1).")
    parser.add_argument("--check", action="store_true",
                        help="verify skills.json is in sync; write nothing")
    args = parser.parse_args(argv)

    expected = render(build_index())
    if args.check:
        if not INDEX.exists():
            print("FAIL: skills.json missing -- run scripts/gen-index.py")
            return 1
        actual = INDEX.read_text(encoding="utf-8")
        if actual != expected:
            print("FAIL: skills.json is stale -- run scripts/gen-index.py")
            return 1
        print("OK: skills.json in sync (%d skills)"
              % len(build_index()["skills"]))
        return 0

    INDEX.write_text(expected, encoding="utf-8")
    print("wrote %s (%d skills)" % (INDEX, len(build_index()["skills"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
