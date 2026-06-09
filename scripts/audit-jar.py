#!/usr/bin/env python3
"""Audit gate for the skill jar. Exits 0 (all green) or 1 (failures found).

The verification gate both repo loops run every cycle (see
agent-state/loop-state.md). Checks, in order:

  1. Frontmatter   -- every SKILL.md (jar skills + bundled role-skill templates)
                      has frontmatter that parses as YAML with `name` and
                      `description`; description is non-empty and <= 1024 chars.
  2. Triggers      -- every description carries a trigger phrase ("use when" /
                      "use during"), so an agent can route to the skill.
  3. Naming        -- a top-level jar skill's `name` matches its directory name.
  4. Links         -- every relative Markdown link in the jar's docs resolves to
                      a real file/dir inside the repo (code fences and inline
                      code are stripped first; http/mailto/#anchor links skipped).
  5. Scripts       -- every tracked .py compiles, and scaffold-loop.py stays
                      idempotent (second run into a temp dir creates 0 paths).
  6. Index         -- skills.json (the machine-readable jar index) is in sync
                      with the skills' frontmatter (delegates to
                      scripts/gen-index.py --check).
  7. Plugin        -- .claude-plugin/marketplace.json and plugin.json parse,
                      every plugin skill path exists and holds a SKILL.md, and
                      the plugin's skill list matches the jar's top-level
                      skills exactly (no silent drift when a skill is added).

Stdlib only. Uses PyYAML when available; falls back to a minimal frontmatter
check (including the unquoted "key: a: b" mapping footgun) when it is not.

Usage:
    python scripts/audit-jar.py            # full audit
    python scripts/audit-jar.py --quiet    # failures + summary only
"""

import argparse
import json
import py_compile
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Dirs that are loop infrastructure or assets, not jar-skill content.
SKIP_DIR_NAMES = {
    ".git", ".claude", ".codex", "agent-state", "docs", "scripts",
    "assets", "node_modules", "__pycache__", ".venv", "venv",
}

TRIGGER_RE = re.compile(r"use (when|whenever|during)", re.IGNORECASE)
LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)\s]+)\)")

results = []  # (ok: bool, label: str, detail: str)


def record(ok, label, detail):
    results.append((ok, label, detail))


# ---------------------------------------------------------------------------
# Frontmatter
# ---------------------------------------------------------------------------

def parse_frontmatter(text):
    """Return (dict, None) on success or (None, error-string) on failure."""
    if not text.startswith("---"):
        return None, "missing frontmatter opening '---'"
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, "unterminated frontmatter (no closing '---')"
    fm = parts[1]
    try:
        import yaml  # type: ignore
    except ImportError:
        # Minimal fallback: key/value lines + the classic unquoted-colon footgun.
        data = {}
        for line in fm.strip().splitlines():
            m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
            if not m:
                continue
            key, val = m.group(1), m.group(2)
            if val and val[0] not in "\"'" and ": " in val:
                return None, ("unquoted '%s' value contains ': ' -- "
                              "YAML 'mapping values are not allowed here'" % key)
            data[key] = val.strip("\"'")
        return data, None
    try:
        data = yaml.safe_load(fm)
    except Exception as e:  # noqa: BLE001 - report any parse failure
        return None, "YAML parse error: %s" % str(e).splitlines()[0]
    if not isinstance(data, dict):
        return None, "frontmatter is not a mapping"
    return data, None


def skill_files():
    files = sorted(ROOT.glob("*/SKILL.md"))                              # jar skills
    files += sorted(ROOT.glob("*/references/role-skills/*.SKILL.md"))   # templates
    return [f for f in files if f.parts[len(ROOT.parts)] not in SKIP_DIR_NAMES]


def check_skill_file(path):
    rel = path.relative_to(ROOT).as_posix()
    text = path.read_text(encoding="utf-8")
    data, err = parse_frontmatter(text)
    if err:
        record(False, "frontmatter", "%s: %s" % (rel, err))
        return
    record(True, "frontmatter", "%s parses" % rel)

    name = data.get("name")
    desc = data.get("description")
    if not name or not isinstance(name, str):
        record(False, "frontmatter", "%s: missing/empty `name`" % rel)
    if not desc or not isinstance(desc, str):
        record(False, "frontmatter", "%s: missing/empty `description`" % rel)
        return
    if len(desc) > 1024:
        record(False, "frontmatter",
               "%s: description is %d chars (max 1024)" % (rel, len(desc)))
    if TRIGGER_RE.search(desc):
        record(True, "trigger", "%s description has a trigger phrase" % rel)
    else:
        record(False, "trigger",
               "%s: description lacks 'Use when/during' trigger" % rel)

    # Top-level jar skill: directory name must match the frontmatter name.
    if path.parent.parent == ROOT and path.name == "SKILL.md":
        if name == path.parent.name:
            record(True, "naming", "%s: name matches directory" % rel)
        else:
            record(False, "naming",
                   "%s: name '%s' != directory '%s'" % (rel, name, path.parent.name))


# ---------------------------------------------------------------------------
# Links
# ---------------------------------------------------------------------------

def strip_code(text):
    text = re.sub(r"```.*?```", "", text, flags=re.S)   # fenced blocks
    text = re.sub(r"`[^`\n]*`", "", text)               # inline code
    return text


def md_files_for_link_audit():
    files = [ROOT / "README.md"]
    for d in sorted(ROOT.iterdir()):
        if d.is_dir() and d.name not in SKIP_DIR_NAMES and (d / "SKILL.md").exists():
            files += sorted(d.rglob("*.md"))
    return [f for f in files if f.exists()]


def check_links(path):
    rel = path.relative_to(ROOT).as_posix()
    text = strip_code(path.read_text(encoding="utf-8"))
    broken = []
    for m in LINK_RE.finditer(text):
        target = m.group(2)
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        if "<" in target:  # template placeholder, not a real path
            continue
        target = target.split("#", 1)[0]
        if not target:
            continue
        resolved = (path.parent / target).resolve()
        inside = ROOT == resolved or ROOT in resolved.parents
        if not resolved.exists() or not inside:
            broken.append(target)
    if broken:
        record(False, "links", "%s: broken -> %s" % (rel, ", ".join(broken)))
    else:
        record(True, "links", "%s: all relative links resolve" % rel)


# ---------------------------------------------------------------------------
# Scripts
# ---------------------------------------------------------------------------

def python_files():
    out = []
    for p in ROOT.rglob("*.py"):
        if any(part in {".git", "__pycache__", ".venv", "venv", "node_modules"}
               for part in p.parts):
            continue
        out.append(p)
    return sorted(out)


def check_scripts():
    for p in python_files():
        rel = p.relative_to(ROOT).as_posix()
        try:
            py_compile.compile(str(p), doraise=True)
            record(True, "compile", "%s compiles" % rel)
        except py_compile.PyCompileError as e:
            record(False, "compile", "%s: %s" % (rel, str(e).splitlines()[0]))

    gen_index = ROOT / "scripts" / "gen-index.py"
    if gen_index.exists():
        r = subprocess.run([sys.executable, str(gen_index), "--check"],
                           capture_output=True, text=True)
        if r.returncode == 0:
            record(True, "index", "skills.json in sync with frontmatter")
        else:
            record(False, "index",
                   (r.stdout or r.stderr).strip().splitlines()[0]
                   if (r.stdout or r.stderr).strip() else
                   "gen-index.py --check exited %d" % r.returncode)
    else:
        record(False, "index", "scripts/gen-index.py not found")

    scaffold = ROOT / "loop-engineer" / "scripts" / "scaffold-loop.py"
    if not scaffold.exists():
        record(False, "idempotency", "scaffold-loop.py not found")
        return
    tmp = Path(tempfile.mkdtemp(prefix="jar_audit_"))
    try:
        cmd = [sys.executable, str(scaffold),
               "--loop-name", "audit-probe", "--repo", str(tmp)]
        r1 = subprocess.run(cmd, capture_output=True, text=True)
        r2 = subprocess.run(cmd, capture_output=True, text=True)
        if r1.returncode != 0 or r2.returncode != 0:
            record(False, "idempotency",
                   "scaffold-loop.py exited %d/%d" % (r1.returncode, r2.returncode))
            return
        m = re.search(r"Summary: (\d+) created", r2.stdout)
        if m and m.group(1) == "0":
            record(True, "idempotency", "scaffold-loop.py: second run created 0 paths")
        else:
            record(False, "idempotency",
                   "scaffold-loop.py second run created %s paths (expected 0)"
                   % (m.group(1) if m else "?"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------------------
# Plugin manifests
# ---------------------------------------------------------------------------

def check_plugin_manifests():
    """marketplace.json + plugin.json parse, paths resolve, no skill drift."""
    mp_path = ROOT / ".claude-plugin" / "marketplace.json"
    pj_path = ROOT / ".claude-plugin" / "plugin.json"

    manifests = {}
    for path in (mp_path, pj_path):
        rel = path.relative_to(ROOT).as_posix()
        if not path.exists():
            record(False, "plugin", "%s missing" % rel)
            continue
        try:
            manifests[path.name] = json.loads(path.read_text(encoding="utf-8"))
            record(True, "plugin", "%s parses" % rel)
        except json.JSONDecodeError as e:
            record(False, "plugin", "%s: %s" % (rel, e))

    mp = manifests.get("marketplace.json")
    if mp is not None:
        missing = [k for k in ("name", "owner", "plugins") if not mp.get(k)]
        if missing:
            record(False, "plugin",
                   "marketplace.json missing field(s): %s" % ", ".join(missing))
        else:
            record(True, "plugin", "marketplace.json has name/owner/plugins")

    pj = manifests.get("plugin.json")
    if pj is None:
        return
    declared = pj.get("skills") or []
    bad = []
    for entry in declared:
        if not entry.startswith("./"):
            bad.append("%s (must start with ./)" % entry)
            continue
        if not (ROOT / entry / "SKILL.md").exists():
            bad.append("%s (no SKILL.md)" % entry)
    if bad:
        record(False, "plugin", "plugin.json skill paths: %s" % ", ".join(bad))
    else:
        record(True, "plugin", "plugin.json skill paths all hold a SKILL.md")

    # Drift gate: the plugin must expose exactly the jar's top-level skills.
    declared_dirs = {e[2:].strip("/") for e in declared if e.startswith("./")}
    actual_dirs = {f.parent.name for f in ROOT.glob("*/SKILL.md")
                   if f.parent.name not in SKIP_DIR_NAMES}
    if declared_dirs == actual_dirs:
        record(True, "plugin", "plugin.json skill list matches the jar (%d)"
               % len(actual_dirs))
    else:
        gone = declared_dirs - actual_dirs
        new = actual_dirs - declared_dirs
        parts = []
        if new:
            parts.append("missing from plugin.json: %s" % ", ".join(sorted(new)))
        if gone:
            parts.append("declared but absent: %s" % ", ".join(sorted(gone)))
        record(False, "plugin", "skill list drift -- %s" % "; ".join(parts))


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(description="Skill-jar audit gate (exit 0/1).")
    parser.add_argument("--quiet", action="store_true",
                        help="print failures and the summary only")
    args = parser.parse_args(argv)

    for f in skill_files():
        check_skill_file(f)
    for f in md_files_for_link_audit():
        check_links(f)
    check_scripts()
    check_plugin_manifests()

    fails = [r for r in results if not r[0]]
    for ok, label, detail in results:
        if ok and args.quiet:
            continue
        print("%s [%s] %s" % ("PASS" if ok else "FAIL", label, detail))
    print()
    print("Summary: %d checks, %d failed." % (len(results), len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
