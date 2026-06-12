#!/usr/bin/env python3
"""Reconcile dropped-in skills with generated jar metadata and state."""

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import jarlib


ROOT = jarlib.repo_root()
TRACKER = Path("agent-state") / "SKILL_FORGE_TRACKER.md"
USAGE = Path("agent-state") / "skill-usage.md"
GENERATOR_COMMANDS = [
    ["python", "scripts/gen-index.py"],
    ["python", "scripts/gen-plugins.py"],
    ["python", "scripts/gen-agent-packs.py"],
]
TRACKER_HEADER = (
    "# Skill Forge Tracker -- skill-jar\n\n"
    "## Queue\n\n"
    "| ID | Skill | Category | Path | Status | Clean Runs | Pressure Focus | Last Evidence | Next Action |\n"
    "|----|-------|----------|------|--------|------------|----------------|---------------|-------------|\n"
)
USAGE_TEMPLATE = (
    "# Skill Usage -- skill-jar\n\n"
    "> Append-only log of skill and agent use. Hooks write usage evidence here; "
    "skill-forge turns queued candidates into RED pressure work.\n\n"
    "## Usage Entries\n\n"
    "## Improvement Queue\n"
)


def read_text(path, default=""):
    if not path.exists():
        return default
    return path.read_text(encoding="utf-8")


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def skill_rows(root):
    return {
        skill["dir_name"]: {
            "category": skill["category"],
            "path": skill["path"].relative_to(root).as_posix(),
        }
        for skill in jarlib.discover_skills(root)
    }


def tracker_skill_names(text):
    names = set()
    for line in text.splitlines():
        if not line.startswith("| SF-"):
            continue
        cells = [cell.strip() for cell in line.split("|")[1:-1]]
        if len(cells) >= 2:
            names.add(cells[1])
    return names


def next_tracker_id(text):
    highest = 0
    for line in text.splitlines():
        if not line.startswith("| SF-"):
            continue
        cells = [cell.strip() for cell in line.split("|")[1:-1]]
        if not cells:
            continue
        try:
            highest = max(highest, int(cells[0].split("-", 1)[1]))
        except (IndexError, ValueError):
            continue
    return "SF-%03d" % (highest + 1)


def append_tracker_rows(root):
    tracker = root / TRACKER
    text = read_text(tracker, TRACKER_HEADER)
    discovered = skill_rows(root)
    existing = tracker_skill_names(text)
    added = 0
    for name in sorted(discovered):
        if name in existing:
            continue
        meta = discovered[name]
        row = (
            "| %s | %s | %s | `%s` | pending-red | 0/3 | drop-in skill pressure | - | RED scenario |"
            % (next_tracker_id(text), name, meta["category"], meta["path"])
        )
        if not text.endswith("\n"):
            text += "\n"
        text += row + "\n"
        existing.add(name)
        added += 1
    write_text(tracker, text)
    stale = sorted(existing - set(discovered))
    return added, stale


def ensure_usage_file(root):
    usage = root / USAGE
    if not usage.exists():
        write_text(usage, USAGE_TEMPLATE)
        return True
    text = usage.read_text(encoding="utf-8")
    changed = False
    if "## Usage Entries" not in text:
        text = text.rstrip() + "\n\n## Usage Entries\n"
        changed = True
    if "## Improvement Queue" not in text:
        text = text.rstrip() + "\n\n## Improvement Queue\n"
        changed = True
    if changed:
        write_text(usage, text)
    return changed


def run_generators(run_command):
    for cmd in GENERATOR_COMMANDS:
        code = run_command(cmd)
        if code != 0:
            raise SystemExit("generator failed: %s" % " ".join(cmd))


def default_run_command(cmd):
    result = subprocess.run(cmd, cwd=ROOT)
    return result.returncode


def sync(root=ROOT, run_command=default_run_command):
    root = Path(root)
    added, stale = append_tracker_rows(root)
    usage_changed = ensure_usage_file(root)
    run_generators(run_command)
    return {
        "tracker_rows_added": added,
        "stale_tracker_rows": stale,
        "usage_file_changed": usage_changed,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Reconcile dropped-in jar skills with generated metadata and state.")
    parser.parse_args(argv)
    summary = sync()
    print(
        "sync complete: %d tracker row(s) added, %d stale tracker row(s), usage file changed=%s"
        % (summary["tracker_rows_added"], len(summary["stale_tracker_rows"]), summary["usage_file_changed"])
    )
    if summary["stale_tracker_rows"]:
        print("stale tracker rows preserved: %s" % ", ".join(summary["stale_tracker_rows"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
