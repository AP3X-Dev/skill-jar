#!/usr/bin/env python3
"""Audit gate for the skill jar. Exits 0 (all green) or 1 (failures found).

The verification gate both repo loops run every cycle (see
agent-state/loop-state.md) and that CI runs on every push. Checks, in order:

  1. Frontmatter   -- every SKILL.md (jar skills + bundled role-skill templates)
                      has frontmatter that parses as YAML with `name` and
                      `description`; description is non-empty and <= 1024 chars.
  2. Triggers      -- every description carries a trigger phrase ("use when" /
                      "use during"), so an agent can route to the skill.
  3. Naming        -- a skill's `name` matches its directory name.
  4. Links         -- every relative Markdown link in the jar's docs resolves to
                      a real file/dir inside the repo (code fences and inline
                      code are stripped first; http/mailto/#anchor links skipped).
  5. Scripts       -- every tracked .py compiles, and scaffold-loop.py stays
                      idempotent (second run into a temp dir creates 0 paths).
  6. Index         -- skills.json is in sync with the layout (gen-index.py --check).
  7. Plugins       -- the marketplace + bundle + per-category plugin manifests
                      are in sync with the category layout (gen-plugins.py --check).

Skills live at `<category>/<skill>/SKILL.md`. Stdlib only (PyYAML used when
present); discovery is shared via jarlib so the generators and this gate agree.

Usage:
    python scripts/audit-jar.py            # full audit
    python scripts/audit-jar.py --quiet    # failures + summary only
"""

import argparse
import py_compile
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import jarlib

ROOT = jarlib.repo_root()
SCRIPTS = ROOT / "scripts"

TRIGGER_RE = re.compile(r"use (when|whenever|during)", re.IGNORECASE)
LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)\s]+)\)")

results = []  # (ok: bool, label: str, detail: str)


def record(ok, label, detail):
    results.append((ok, label, detail))


# ---------------------------------------------------------------------------
# Frontmatter / naming
# ---------------------------------------------------------------------------

def check_frontmatter(path, expected_dir_name=None):
    """Validate one SKILL.md. If expected_dir_name is given, also check naming."""
    rel = path.relative_to(ROOT).as_posix()
    data, err = jarlib.parse_frontmatter(path.read_text(encoding="utf-8"))
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

    if expected_dir_name is not None:
        if name == expected_dir_name:
            record(True, "naming", "%s: name matches directory" % rel)
        else:
            record(False, "naming",
                   "%s: name '%s' != directory '%s'"
                   % (rel, name, expected_dir_name))


def check_all_skills():
    for s in jarlib.discover_skills(ROOT):
        check_frontmatter(s["path"], expected_dir_name=s["dir_name"])
    for tmpl in jarlib.role_skill_templates(ROOT):
        check_frontmatter(tmpl)  # templates: validate, but don't name-check


# ---------------------------------------------------------------------------
# Links
# ---------------------------------------------------------------------------

def strip_code(text):
    text = re.sub(r"```.*?```", "", text, flags=re.S)   # fenced blocks
    text = re.sub(r"`[^`\n]*`", "", text)               # inline code
    return text


def md_files_for_link_audit():
    files = [ROOT / "README.md"]
    for s in jarlib.discover_skills(ROOT):
        files += sorted(s["skill_dir"].rglob("*.md"))
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
# Scripts / generators
# ---------------------------------------------------------------------------

def python_files():
    out = []
    for p in ROOT.rglob("*.py"):
        if any(part in {".git", "__pycache__", ".venv", "venv", "node_modules"}
               for part in p.parts):
            continue
        out.append(p)
    return sorted(out)


def delegate(label, script, ok_msg):
    """Run a generator's --check and record pass/fail."""
    path = SCRIPTS / script
    if not path.exists():
        record(False, label, "scripts/%s not found" % script)
        return
    r = subprocess.run([sys.executable, str(path), "--check"],
                       capture_output=True, text=True)
    if r.returncode == 0:
        record(True, label, ok_msg)
    else:
        out = (r.stdout or r.stderr).strip()
        record(False, label, out.splitlines()[0] if out
               else "%s --check exited %d" % (script, r.returncode))


def check_scripts():
    for p in python_files():
        rel = p.relative_to(ROOT).as_posix()
        try:
            py_compile.compile(str(p), doraise=True)
            record(True, "compile", "%s compiles" % rel)
        except py_compile.PyCompileError as e:
            record(False, "compile", "%s: %s" % (rel, str(e).splitlines()[0]))

    delegate("index", "gen-index.py", "skills.json in sync with the layout")
    delegate("plugins", "gen-plugins.py",
             "marketplace + bundle + category manifests in sync")

    scaffold = ROOT / "development" / "loop-engineer" / "scripts" / "scaffold-loop.py"
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
# main
# ---------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(description="Skill-jar audit gate (exit 0/1).")
    parser.add_argument("--quiet", action="store_true",
                        help="print failures and the summary only")
    args = parser.parse_args(argv)

    check_all_skills()
    for f in md_files_for_link_audit():
        check_links(f)
    check_scripts()

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
