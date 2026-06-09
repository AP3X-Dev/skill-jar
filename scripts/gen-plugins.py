#!/usr/bin/env python3
"""Generate (or verify) the jar's plugin manifests from the directory layout.

The jar ships as a Claude Code plugin marketplace. Selective install works by
category: each category folder (`development/`, `marketing/`, ...) becomes its
own installable plugin (`skill-jar-development`, ...), plus a `skill-jar`
bundle that installs everything. A user runs:

    /plugin marketplace add AP3X-Dev/skill-jar
    /plugin install skill-jar-development@skill-jar   # just one category
    /plugin install skill-jar@skill-jar                # everything

This script is the single source of truth for three sets of files, ALL derived
from where skills physically live (the folder a skill sits in is its category):

    .claude-plugin/marketplace.json     -- lists the bundle + every non-empty category
    .claude-plugin/plugin.json          -- the bundle plugin (source "./"); skills as ./<cat>/<skill>
    <category>/.claude-plugin/plugin.json  -- one per non-empty category (source "./<cat>"); skills as ./<skill>

No symlinks (Windows-hostile): each skill lives inside exactly one category
directory, so every declared path is `./`-relative and inside its plugin root.

GENERATED -- never edit these manifests by hand. The audit gate runs
`gen-plugins.py --check`, so any drift between the layout and the manifests
fails the build.

Usage:
    python scripts/gen-plugins.py            # (re)write the manifests
    python scripts/gen-plugins.py --check    # exit 0 if in sync, 1 if stale
"""

import argparse
import json
import sys

import jarlib

ROOT = jarlib.repo_root()

# Project identity (not per-skill) -- the only hand-set values.
MARKETPLACE_NAME = "skill-jar"
OWNER = {"name": "AP3X"}
VERSION = "1.0.0"


def grouped_skills():
    """{category: [dir_name, ...sorted]} for every non-empty category."""
    groups = {}
    for s in jarlib.discover_skills(ROOT):
        groups.setdefault(s["category"], []).append(s["dir_name"])
    return {c: sorted(names) for c, names in sorted(groups.items())}


def plugin_name(category):
    return "%s-%s" % (MARKETPLACE_NAME, category)


def render(obj):
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def build_manifests():
    """Return {relative_path: rendered_json} for every manifest file."""
    groups = grouped_skills()
    total = sum(len(v) for v in groups.values())

    # marketplace.json -- bundle first, then one entry per non-empty category.
    plugins = [{
        "name": MARKETPLACE_NAME,
        "source": "./",
        "description": "All %d jar skills across %d categor%s."
                       % (total, len(groups), "y" if len(groups) == 1 else "ies"),
    }]
    for category, names in groups.items():
        plugins.append({
            "name": plugin_name(category),
            "source": "./%s" % category,
            "description": "%s-category skills: %s." % (category, ", ".join(names)),
        })
    marketplace = {
        "name": MARKETPLACE_NAME,
        "owner": OWNER,
        "description": "A growing collection of Agent Skills -- install the whole "
                       "jar or a single category.",
        "plugins": plugins,
    }

    files = {".claude-plugin/marketplace.json": render(marketplace)}

    # Bundle plugin.json (source "./"): every skill, path includes its category.
    bundle_skills = []
    for category, names in groups.items():
        bundle_skills += ["./%s/%s" % (category, n) for n in names]
    files[".claude-plugin/plugin.json"] = render({
        "name": MARKETPLACE_NAME,
        "description": "Every skill in the jar, all categories.",
        "version": VERSION,
        "author": OWNER,
        "skills": sorted(bundle_skills),
    })

    # One plugin.json per non-empty category (source "./<category>").
    for category, names in groups.items():
        files["%s/.claude-plugin/plugin.json" % category] = render({
            "name": plugin_name(category),
            "description": "The jar's %s-category skills." % category,
            "version": VERSION,
            "author": OWNER,
            "skills": ["./%s" % n for n in names],
        })

    return files


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate or verify the jar's plugin manifests (exit 0/1).")
    parser.add_argument("--check", action="store_true",
                        help="verify the manifests are in sync; write nothing")
    args = parser.parse_args(argv)

    files = build_manifests()

    if args.check:
        stale = []
        for rel, expected in files.items():
            path = ROOT / rel
            if not path.exists() or path.read_text(encoding="utf-8") != expected:
                stale.append(rel)
        # Also flag a category plugin.json that exists but should NOT (emptied category).
        for pj in ROOT.glob("*/.claude-plugin/plugin.json"):
            rel = pj.relative_to(ROOT).as_posix()
            if rel not in files:
                stale.append("%s (stale -- category has no skills)" % rel)
        if stale:
            print("FAIL: plugin manifests stale -- run scripts/gen-plugins.py: "
                  + ", ".join(sorted(stale)))
            return 1
        print("OK: plugin manifests in sync (%d files)" % len(files))
        return 0

    for rel, content in files.items():
        path = ROOT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    print("wrote %d manifest file(s): %s" % (len(files), ", ".join(sorted(files))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
