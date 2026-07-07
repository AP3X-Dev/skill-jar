#!/usr/bin/env python3
"""Validate spec-driven-change requirement/scenario specs and spec deltas.

The jar-native, stdlib-only stand-in for `openspec validate`. It makes the
grammar's silent failures loud: a Scenario at the wrong hash depth, a
Requirement with no scenario, an unknown delta-section header. These are the
mistakes that otherwise parse as prose and ship a spec nobody can machine-read.

This script is an OPTIONAL accelerator. The skill works without it -- an agent
can check the same rules by hand from references/spec-format.md. It assumes
nothing but a Python 3 runtime; absence is a clean skip.

Usage:
    python validate-spec.py <path> [<path> ...]   # .md files, or dirs (recurses *.md)
    python validate-spec.py --selftest            # run embedded checks, exit 0/1

Exit code: 0 = no errors (warnings allowed), 1 = one or more errors.
"""
import argparse
import re
import sys
from pathlib import Path

DELTA_SECTIONS = ("ADDED", "MODIFIED", "REMOVED", "RENAMED")
DELTA_HEADER_RE = re.compile(r"^##\s+(?P<op>[A-Za-z]+)\s+Requirements\s*$")
REQ_RE = re.compile(r"^(?P<hashes>#{1,6})\s+Requirement:\s*(?P<name>.+?)\s*$")
SCEN_RE = re.compile(r"^(?P<hashes>#{1,6})\s+Scenario:\s*(?P<name>.+?)\s*$")
# A "Scenario:" that is NOT a proper header: a bullet, or bare text.
SCEN_LOOSE_RE = re.compile(r"^\s*(?:[-*]\s*)?Scenario:\s", re.IGNORECASE)
SECTION_H2_RE = re.compile(r"^##\s+\S")
NORMATIVE_RE = re.compile(r"\b(?:MUST NOT|SHALL NOT|MUST|SHALL|SHOULD|MAY)\b")
GWT_RE = re.compile(r"\b(?:GIVEN|WHEN|THEN)\b")


def validate_text(text, source="<text>"):
    """Return (errors, warnings) as lists of 'source:line: message' strings."""
    errors, warnings = [], []
    lines = text.splitlines()
    is_delta = any(DELTA_HEADER_RE.match(ln) for ln in lines)

    def err(lineno, msg):
        errors.append("%s:%d: %s" % (source, lineno, msg))

    def warn(lineno, msg):
        warnings.append("%s:%d: %s" % (source, lineno, msg))

    # First pass: flag wrong-depth headers and unknown delta sections, and
    # record the structure (requirement blocks with their governing section).
    section = None  # current delta op, in delta mode
    reqs = []       # {line, name, section, scen_count, has_norm, first_line, last_line}
    cur = None

    def close(end_line):
        if cur is not None:
            cur["last_line"] = end_line
            reqs.append(cur)

    for i, line in enumerate(lines, 1):
        mdelta = DELTA_HEADER_RE.match(line)
        if mdelta:
            close(i - 1)
            cur = None
            op = mdelta.group("op").upper()
            if op not in DELTA_SECTIONS:
                err(i, "unknown delta section '%s' (expected: ## %s Requirements)"
                    % (line.strip(), " / ## ".join(s.title() for s in DELTA_SECTIONS)))
                section = None
            else:
                section = op
            continue
        # A plain H2 that isn't a delta header ends any open requirement block.
        if SECTION_H2_RE.match(line) and not mdelta:
            close(i - 1)
            cur = None
            section = None if is_delta else section
            continue

        mreq = REQ_RE.match(line)
        if mreq:
            close(i - 1)
            if len(mreq.group("hashes")) != 3:
                err(i, "Requirement must use exactly 3 hashes (### Requirement:), found %d"
                    % len(mreq.group("hashes")))
            cur = {"line": i, "name": mreq.group("name").strip(), "section": section,
                   "scen_count": 0, "has_norm": bool(NORMATIVE_RE.search(mreq.group("name"))),
                   "first_line": i, "last_line": None}
            continue

        mscen = SCEN_RE.match(line)
        if mscen:
            if len(mscen.group("hashes")) != 4:
                err(i, "Scenario must use exactly 4 hashes (#### Scenario:), found %d "
                    "-- a wrong depth is read as prose and fails silently"
                    % len(mscen.group("hashes")))
            if cur is not None:
                cur["scen_count"] += 1
            continue

        # A "Scenario:" that did not match the strict header shape.
        if SCEN_LOOSE_RE.match(line):
            err(i, "line looks like a Scenario but is not a '#### Scenario:' header "
                "(exactly 4 hashes, no leading bullet)")
            continue

        if cur is not None:
            if NORMATIVE_RE.search(line):
                cur["has_norm"] = True
            if GWT_RE.search(line):
                # a GWT line inside a requirement but outside any scenario is a smell
                pass
    close(len(lines))

    # Second pass: per-requirement structural rules.
    for r in reqs:
        # In a delta, REMOVED / RENAMED name a requirement without a body.
        exempt = is_delta and r["section"] in ("REMOVED", "RENAMED")
        if not exempt and r["scen_count"] == 0:
            err(r["line"], "Requirement '%s' has no Scenario -- every requirement needs "
                ">= 1 '#### Scenario:'" % r["name"])
        if not exempt and not r["has_norm"]:
            warn(r["line"], "Requirement '%s' has no normative keyword "
                "(MUST / SHALL / SHOULD / MAY)" % r["name"])

    # A delta file must actually carry at least one delta section.
    if not is_delta and any("changes" in Path(source).parts and "specs" in Path(source).parts
                            for _ in [0]) and reqs:
        pass  # spec-vs-delta location heuristics are the skill's job, not the linter's.

    return errors, warnings


def validate_path(path):
    p = Path(path)
    files = sorted(p.rglob("*.md")) if p.is_dir() else [p]
    all_err, all_warn = [], []
    for f in files:
        try:
            text = f.read_text(encoding="utf-8")
        except OSError as e:
            all_err.append("%s: cannot read (%s)" % (f, e))
            continue
        e, w = validate_text(text, str(f))
        all_err += e
        all_warn += w
    return all_err, all_warn


SELFTEST_GOOD = """\
### Requirement: Two-Factor Authentication
The system MUST require a second factor during login.

#### Scenario: OTP required
- GIVEN a user with 2FA enabled
- WHEN the user submits valid credentials
- THEN an OTP challenge is presented
"""

SELFTEST_BAD_HASHES = """\
### Requirement: Two-Factor Authentication
The system MUST require a second factor during login.

### Scenario: wrong depth
- GIVEN a user
- WHEN they log in
- THEN nothing
"""

SELFTEST_NO_SCENARIO = """\
### Requirement: Lonely
The system SHALL do a thing.
"""

SELFTEST_DELTA_OK = """\
## ADDED Requirements
### Requirement: Dark Mode
The system MUST offer a dark theme.

#### Scenario: toggle
- GIVEN the settings page
- WHEN the user enables dark mode
- THEN the UI renders dark

## REMOVED Requirements
### Requirement: Legacy Theme
"""

SELFTEST_DELTA_BADHEADER = """\
## APPENDED Requirements
### Requirement: X
The system MUST x.

#### Scenario: s
- GIVEN a
- WHEN b
- THEN c
"""


def selftest():
    checks = []

    def expect(name, text, want_errors):
        errs, _ = validate_text(text, name)
        ok = (len(errs) > 0) == want_errors
        checks.append((name, ok, errs))
        assert ok, "%s: expected errors=%s, got %r" % (name, want_errors, errs)

    expect("good-spec", SELFTEST_GOOD, False)
    expect("bad-scenario-hashes", SELFTEST_BAD_HASHES, True)
    expect("requirement-without-scenario", SELFTEST_NO_SCENARIO, True)
    expect("valid-delta", SELFTEST_DELTA_OK, False)
    expect("unknown-delta-header", SELFTEST_DELTA_BADHEADER, True)

    # The wrong-depth scenario must be the specific error we care about.
    errs, _ = validate_text(SELFTEST_BAD_HASHES, "b")
    assert any("exactly 4 hashes" in e for e in errs), errs
    # REMOVED requirement is exempt from the scenario rule.
    errs, _ = validate_text(SELFTEST_DELTA_OK, "d")
    assert errs == [], errs

    print("validate-spec selftest: %d checks passed" % len(checks))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Validate spec-driven-change specs and deltas.")
    ap.add_argument("paths", nargs="*", help=".md files or directories")
    ap.add_argument("--selftest", action="store_true", help="run embedded checks and exit")
    ap.add_argument("--quiet", action="store_true", help="print only the summary line")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()
    if not args.paths:
        ap.error("give at least one path, or --selftest")

    errors, warnings = [], []
    for path in args.paths:
        e, w = validate_path(path)
        errors += e
        warnings += w

    if not args.quiet:
        for w in warnings:
            print("WARN  " + w)
        for e in errors:
            print("ERROR " + e)
    print("spec validation: %d error(s), %d warning(s)" % (len(errors), len(warnings)))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
