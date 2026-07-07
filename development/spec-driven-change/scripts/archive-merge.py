#!/usr/bin/env python3
"""Merge a change's spec deltas into the living specs, in strict order.

The jar-native, stdlib-only stand-in for the merge half of `openspec archive`.
A change ships a delta per capability (## ADDED / MODIFIED / REMOVED / RENAMED
Requirements); on archive those deltas fold into the persistent openspec/specs/
layer so the living spec is always current. The operations MUST apply in the
order RENAMED -> REMOVED -> MODIFIED -> ADDED; getting that order wrong by hand
is exactly the silent corruption this script exists to prevent.

OPTIONAL accelerator. The skill documents the same merge in
references/spec-format.md; an agent can apply it by hand. Stdlib only.

Usage:
    python archive-merge.py --change openspec/changes/<name> --specs openspec/specs
        [--apply]        # write the merged living specs (default: dry-run)
    python archive-merge.py --selftest
"""
import argparse
import re
import sys
from pathlib import Path

REQ_RE = re.compile(r"^(?P<hashes>#{1,6})\s+Requirement:\s*(?P<name>.+?)\s*$")
DELTA_HEADER_RE = re.compile(r"^##\s+(?P<op>[A-Za-z]+)\s+Requirements\s*$")
FROM_RE = re.compile(r"^\s*[-*]?\s*FROM:\s*`?(?P<name>.+?)`?\s*$", re.IGNORECASE)
TO_RE = re.compile(r"^\s*[-*]?\s*TO:\s*`?(?P<name>.+?)`?\s*$", re.IGNORECASE)
DELTA_OPS = ("ADDED", "MODIFIED", "REMOVED", "RENAMED")


def parse_blocks(lines):
    """(preamble_lines, [[name, block_lines], ...]).

    Everything before the first '### Requirement:' is preamble; then one block
    per requirement, from its header through the line before the next
    requirement header (or EOF)."""
    preamble, blocks = [], []
    name, buf = None, []
    for line in lines:
        m = REQ_RE.match(line)
        if m:
            if name is None:
                preamble = buf
            else:
                blocks.append([name, buf])
            name, buf = m.group("name").strip(), [line]
        else:
            buf.append(line)
    if name is None:
        preamble = buf
    else:
        blocks.append([name, buf])
    return preamble, blocks


def parse_renames(lines):
    pairs, pending = [], None
    for line in lines:
        mf = FROM_RE.match(line)
        mt = TO_RE.match(line)
        if mf:
            pending = mf.group("name").strip()
        elif mt and pending is not None:
            pairs.append((pending, mt.group("name").strip()))
            pending = None
    return pairs


def parse_delta(text):
    """Return {ADDED:[[name,buf]], MODIFIED:[[name,buf]], REMOVED:[name],
    RENAMED:[(old,new)]}."""
    sect_lines = {k: [] for k in DELTA_OPS}
    section = None
    for line in text.splitlines():
        m = DELTA_HEADER_RE.match(line)
        if m and m.group("op").upper() in DELTA_OPS:
            section = m.group("op").upper()
            continue
        if m:  # a "## Something Requirements" that isn't a known op ends the section
            section = None
            continue
        if section:
            sect_lines[section].append(line)
    ops = {}
    for op in ("ADDED", "MODIFIED"):
        _, blocks = parse_blocks(sect_lines[op])
        ops[op] = blocks
    _, removed_blocks = parse_blocks(sect_lines["REMOVED"])
    ops["REMOVED"] = [name for name, _ in removed_blocks]
    ops["RENAMED"] = parse_renames(sect_lines["RENAMED"])
    return ops


def _rename_header(buf, new_name):
    return [REQ_RE.sub(lambda m: "### Requirement: " + new_name, ln)
            if REQ_RE.match(ln) else ln for ln in buf]


def apply_delta(living_text, delta_text):
    """Apply a delta to a living spec. Returns (new_text, actions).

    Order is fixed: RENAMED -> REMOVED -> MODIFIED -> ADDED. Raises ValueError
    on a conflict (rename/remove/modify a missing requirement, or add an
    existing one) rather than silently producing a wrong spec."""
    preamble, blocks = parse_blocks(living_text.splitlines())
    order = [name for name, _ in blocks]
    bymap = {name: buf for name, buf in blocks}
    ops = parse_delta(delta_text)
    actions = []

    for old, new in ops["RENAMED"]:
        if old not in bymap:
            raise ValueError("RENAMED: requirement %r not found in living spec" % old)
        bymap[new] = _rename_header(bymap.pop(old), new)
        order[order.index(old)] = new
        actions.append("RENAMED %r -> %r" % (old, new))

    for name in ops["REMOVED"]:
        if name not in bymap:
            raise ValueError("REMOVED: requirement %r not found in living spec" % name)
        bymap.pop(name)
        order.remove(name)
        actions.append("REMOVED %r" % name)

    for name, buf in ops["MODIFIED"]:
        if name not in bymap:
            raise ValueError("MODIFIED: requirement %r not found in living spec" % name)
        bymap[name] = buf
        actions.append("MODIFIED %r" % name)

    for name, buf in ops["ADDED"]:
        if name in bymap:
            raise ValueError("ADDED: requirement %r already exists in living spec" % name)
        bymap[name] = buf
        order.append(name)
        actions.append("ADDED %r" % name)

    parts = []
    pre = "\n".join(preamble).rstrip()
    if pre:
        parts.append(pre)
    for name in order:
        parts.append("\n".join(bymap[name]).rstrip())
    return "\n\n".join(parts).rstrip() + "\n", actions


def merge_change(change_dir, specs_dir, apply=False):
    change, specs = Path(change_dir), Path(specs_dir)
    delta_files = sorted((change / "specs").rglob("spec.md"))
    if not delta_files:
        raise SystemExit("no delta specs found under %s/specs/*/spec.md" % change)
    results = []
    for df in delta_files:
        capability = df.parent.name
        living = specs / capability / "spec.md"
        living_text = living.read_text(encoding="utf-8") if living.exists() else ""
        new_text, actions = apply_delta(living_text, df.read_text(encoding="utf-8"))
        results.append((capability, actions))
        if apply:
            living.parent.mkdir(parents=True, exist_ok=True)
            living.write_text(new_text, encoding="utf-8")
    return results


LIVING = """\
# Authentication

### Requirement: Password Login
The system MUST accept a username and password.

#### Scenario: valid login
- GIVEN a registered user
- WHEN they submit correct credentials
- THEN a session is created

### Requirement: Legacy Theme
The system MAY render the old theme.

#### Scenario: legacy
- GIVEN the flag
- WHEN set
- THEN old theme
"""

DELTA = """\
## RENAMED Requirements
- FROM: `Password Login`
- TO: `Credential Login`

## REMOVED Requirements
### Requirement: Legacy Theme

## ADDED Requirements
### Requirement: Two-Factor Authentication
The system MUST require a second factor.

#### Scenario: otp
- GIVEN 2FA on
- WHEN valid credentials
- THEN an OTP challenge
"""


def selftest():
    new_text, actions = apply_delta(LIVING, DELTA)
    assert "### Requirement: Credential Login" in new_text, new_text
    assert "Password Login" not in new_text, new_text
    assert "Legacy Theme" not in new_text, new_text
    assert "### Requirement: Two-Factor Authentication" in new_text, new_text
    assert actions[0].startswith("RENAMED"), actions
    assert actions[-1].startswith("ADDED"), actions

    # conflicts raise, not corrupt
    for bad in ("## REMOVED Requirements\n### Requirement: Nope\n",
                "## ADDED Requirements\n### Requirement: Credential Login\nThe system MUST x.\n#### Scenario: s\n- GIVEN a\n- WHEN b\n- THEN c\n"):
        try:
            apply_delta(new_text, bad)
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError for delta: %r" % bad)

    # adding onto an empty living spec works
    added, _ = apply_delta("", "## ADDED Requirements\n### Requirement: X\nThe system MUST x.\n#### Scenario: s\n- GIVEN a\n- WHEN b\n- THEN c\n")
    assert "### Requirement: X" in added
    print("archive-merge selftest: ok (%d actions on the sample delta)" % len(actions))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Merge spec deltas into the living specs.")
    ap.add_argument("--change", help="path to the change dir (contains specs/<cap>/spec.md)")
    ap.add_argument("--specs", help="path to the living specs dir (openspec/specs)")
    ap.add_argument("--apply", action="store_true", help="write the merge (default: dry-run)")
    ap.add_argument("--selftest", action="store_true", help="run embedded checks and exit")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()
    if not (args.change and args.specs):
        ap.error("--change and --specs are required (or use --selftest)")

    try:
        results = merge_change(args.change, args.specs, apply=args.apply)
    except ValueError as e:
        print("MERGE CONFLICT: %s" % e)
        return 1
    mode = "applied" if args.apply else "dry-run"
    for capability, actions in results:
        print("[%s] %s:" % (mode, capability))
        for a in actions:
            print("  " + a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
