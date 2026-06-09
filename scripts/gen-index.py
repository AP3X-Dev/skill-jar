#!/usr/bin/env python3
"""Generate (or verify) skills.json -- the jar's machine-readable index.

An agent fetching this repo reads ONE file to route, instead of crawling
directories: skills.json lists every jar skill with its name, category,
description (the frontmatter routing text), and path
(`<category>/<skill>/SKILL.md`).

GENERATED -- never edit by hand. The audit gate (scripts/audit-jar.py) runs
this with --check, so a stale index fails the build instead of rotting.

Usage:
    python scripts/gen-index.py            # (re)write skills.json
    python scripts/gen-index.py --check    # exit 0 if in sync, 1 if stale
"""

import argparse
import json
import sys

import jarlib

ROOT = jarlib.repo_root()
INDEX = ROOT / "skills.json"


def build_index():
    skills = []
    for s in jarlib.discover_skills(ROOT):
        name, desc = jarlib.skill_meta(s)
        skills.append({
            "name": name,
            "category": s["category"],
            "description": desc,
            "path": s["path"].relative_to(ROOT).as_posix(),
        })
    skills.sort(key=lambda s: (s["category"], s["name"]))
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
    n = len(build_index()["skills"])
    if args.check:
        if not INDEX.exists():
            print("FAIL: skills.json missing -- run scripts/gen-index.py")
            return 1
        if INDEX.read_text(encoding="utf-8") != expected:
            print("FAIL: skills.json is stale -- run scripts/gen-index.py")
            return 1
        print("OK: skills.json in sync (%d skills)" % n)
        return 0

    INDEX.write_text(expected, encoding="utf-8")
    print("wrote %s (%d skills)" % (INDEX, n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
