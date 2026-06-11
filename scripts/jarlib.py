#!/usr/bin/env python3
"""Shared discovery for the skill jar's tooling.

One source of truth for "what is a skill and what category is it in", imported
by gen-index.py, gen-plugins.py, and audit-jar.py so the three can never
disagree. A skill lives at ``<category>/<skill>/SKILL.md`` -- the directory it
sits in IS its category. No frontmatter field to drift from its location.

Stdlib only. Python 3.8+.
"""

import re
from pathlib import Path

# Top-level directories that are infrastructure/assets, never a skill category.
SKIP_DIR_NAMES = {
    ".git", ".github", ".claude", ".codex", ".claude-plugin",
    "agent-state", "docs", "scripts", "assets", "proof",
    "node_modules", "__pycache__", ".venv", "venv",
}

ALLOWED_MATURITY = {
    "draft",
    "linted",
    "dry-run",
    "dogfooded",
    "external-tested",
    "battle-tested",
}


def repo_root():
    return Path(__file__).resolve().parent.parent


def category_dirs(root):
    """Top-level directories eligible to hold skills (categories)."""
    return sorted(
        p for p in root.iterdir()
        if p.is_dir() and p.name not in SKIP_DIR_NAMES
    )


def discover_skills(root):
    """Every installable jar skill, as dicts sorted by (category, dir_name).

    Each: {category, dir_name, skill_dir (Path), path (Path to SKILL.md)}.
    A skill is exactly ``<category>/<skill>/SKILL.md`` -- one level of nesting.
    The role-skill TEMPLATES bundled deeper inside a skill
    (``<cat>/<skill>/references/role-skills/*.SKILL.md``) are NOT installable
    skills and are excluded here; see role_skill_templates().
    """
    skills = []
    for cat in category_dirs(root):
        for skill_md in sorted(cat.glob("*/SKILL.md")):
            skills.append({
                "category": cat.name,
                "dir_name": skill_md.parent.name,
                "skill_dir": skill_md.parent,
                "path": skill_md,
            })
    return skills


def role_skill_templates(root):
    """Bundled role-skill template files (validated, but not installable)."""
    return sorted(root.glob("*/*/references/role-skills/*.SKILL.md"))


def _minimal_yaml_scalar(value):
    value = value.strip()
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    return value.strip("\"'")


def _parse_minimal_frontmatter(fm):
    data = {}
    lines = fm.strip().splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if not m:
            i += 1
            continue
        key, val = m.group(1), m.group(2)
        if val and val[0] not in "\"'" and ": " in val:
            return None, ("unquoted '%s' value contains ': ' -- "
                          "YAML 'mapping values are not allowed here'" % key)
        if val:
            data[key] = _minimal_yaml_scalar(val)
            i += 1
            continue

        items = []
        j = i + 1
        while j < len(lines):
            item = re.match(r"^\s*-\s+(.+)$", lines[j])
            if not item:
                break
            items.append(_minimal_yaml_scalar(item.group(1)))
            j += 1
        if items:
            data[key] = items
            i = j
        else:
            data[key] = ""
            i += 1
    return data, None


def parse_frontmatter(text):
    """Return (dict, None) on success or (None, error-string) on failure.

    Uses PyYAML when available; falls back to a minimal line parser that still
    catches the unquoted ``key: a: b`` mapping footgun (a recurring SKILL.md
    frontmatter bug).
    """
    if not text.startswith("---"):
        return None, "missing frontmatter opening '---'"
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, "unterminated frontmatter (no closing '---')"
    fm = parts[1]
    try:
        import yaml  # type: ignore
    except ImportError:
        return _parse_minimal_frontmatter(fm)
    try:
        data = yaml.safe_load(fm)
    except Exception as e:  # noqa: BLE001 - report any parse failure
        return None, "YAML parse error: %s" % str(e).splitlines()[0]
    if not isinstance(data, dict):
        return None, "frontmatter is not a mapping"
    return data, None


def skill_meta(skill):
    """(name, description) from a discovered skill's frontmatter; dir name on miss."""
    data, _err = parse_frontmatter(skill["path"].read_text(encoding="utf-8"))
    if not data:
        return skill["dir_name"], ""
    return data.get("name") or skill["dir_name"], data.get("description") or ""


def skill_index_entry(skill, root):
    """Machine-readable index entry for one installable skill."""
    data, _err = parse_frontmatter(skill["path"].read_text(encoding="utf-8"))
    data = data or {}
    tags = data.get("tags")
    if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
        tags = []
    entry = {
        "name": data.get("name") or skill["dir_name"],
        "category": skill["category"],
        "description": data.get("description") or "",
        "path": skill["path"].relative_to(root).as_posix(),
        "tags": tags,
        "core": data.get("core") if isinstance(data.get("core"), bool) else False,
    }
    maturity = data.get("maturity")
    if isinstance(maturity, str) and maturity:
        entry["maturity"] = maturity
    evidence = data.get("evidence")
    if isinstance(evidence, str) and evidence:
        entry["evidence"] = evidence
    return entry
