#!/usr/bin/env python3
"""Generate (or verify) the jar's plugin manifests from the directory layout.

The jar ships as a Claude Code plugin marketplace. Selective install works by
category: each category folder (`development/`, `marketing/`, ...) becomes its
own installable plugin (`skill-jar-development`, ...). A user runs:

    /plugin marketplace add AP3X-Dev/skill-jar
    /plugin install skill-jar-development@skill-jar   # one category
    /plugin install skill-jar-marketing@skill-jar     # another

Install the categories you want -- there is intentionally NO all-in-one bundle
plugin. A repo-root bundle would copy the entire repo (agent-state, .github,
scripts, fixtures) into every user's cache, and the only no-symlink way to
build one is exactly that. Categories install independently instead.

This script is the single source of truth for the manifests, ALL derived from
where skills physically live (the folder a skill sits in is its category):

    .claude-plugin/marketplace.json        -- lists one plugin per non-empty category
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
VERSION = "1.2.0"


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

    # marketplace.json -- one plugin entry per non-empty category (no bundle).
    plugins = []
    for category, names in groups.items():
        plugins.append({
            "name": plugin_name(category),
            "source": "./%s" % category,
            "description": "%s-category skills: %s." % (category, ", ".join(names)),
        })
    marketplace = {
        "name": MARKETPLACE_NAME,
        "owner": OWNER,
        "description": "A growing collection of Agent Skills -- "
                       "install one or more categories.",
        "plugins": plugins,
    }

    files = {".claude-plugin/marketplace.json": render(marketplace)}

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
        # Flag any plugin.json on disk the generator no longer produces
        # (a removed bundle at the root, or an emptied category).
        on_disk = list(ROOT.glob(".claude-plugin/plugin.json")) \
            + list(ROOT.glob("*/.claude-plugin/plugin.json"))
        for pj in on_disk:
            rel = pj.relative_to(ROOT).as_posix()
            if rel not in files:
                stale.append("%s (stale -- not generated)" % rel)
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
