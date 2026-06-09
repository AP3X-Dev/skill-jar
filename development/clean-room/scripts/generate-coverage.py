#!/usr/bin/env python3
"""Generate COVERAGE.md from DESIGN_DOC.md.

Walks the design doc's H2/H3 sections and extracts each bullet as a checkbox.
Sections listed in DEFAULT_SECTIONS are included. Additional sections can be
added via --include 'Heading:§tag'. Accepted improvements must be appended
manually from IMPROVEMENTS.md after generation.

When --wires points to a wires.json emitted by generate-wire-ledger.py, a
"## Wires (from §4.5)" section is appended with one checkbox per producer→
consumer wire in the call-graph closure.

Usage:
  generate-coverage.py <DESIGN_DOC.md> [COVERAGE.md]
  generate-coverage.py --include "Data Model:§5" DESIGN_DOC.md
  generate-coverage.py DESIGN_DOC.md --wires clean-room/wires.json
"""
import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_SECTIONS = {
    "Public Contract": "§3",
    "Modules": "§4",
    "Error & Edge Case Catalog": "§7",
    "Cross-Cutting": "§8",
    "Behavioral Specifications from Tests": "§9",
}


def parse(md_text: str) -> dict:
    lines = md_text.splitlines()
    h2 = None
    h3 = None
    out: dict = {}
    for line in lines:
        if line.startswith("## "):
            h2 = line[3:].strip()
            h3 = None
            out.setdefault(h2, {"_bullets": [], "_subs": {}})
        elif line.startswith("### ") and h2:
            h3 = line[4:].strip()
            out[h2]["_subs"].setdefault(h3, [])
        elif re.match(r"^\s*[-*]\s+", line) and h2:
            bullet = re.sub(r"^\s*[-*]\s+", "", line).strip()
            if not bullet:
                continue
            if h3:
                out[h2]["_subs"][h3].append(bullet)
            else:
                out[h2]["_bullets"].append(bullet)
    return out


def render(parsed: dict, include: dict, wires: list[dict] | None) -> tuple[str, int]:
    lines = [
        "# Coverage Checklist",
        "",
        "_Generated from DESIGN_DOC.md. Keep in lockstep. Append accepted "
        "improvements from IMPROVEMENTS.md below._",
        "",
        "## Legend",
        "- [ ] not started",
        "- [~] in progress",
        "- [x] implemented + tests passing",
        "- [!] diverged intentionally (see IMPROVEMENTS.md entry)",
        "- [-] out of scope (see PRP non-goals)",
        "",
    ]
    total = 0
    for h2, tag in include.items():
        section = parsed.get(h2)
        if not section:
            continue
        lines.append(f"## {h2} (from {tag})")
        for b in section["_bullets"]:
            lines.append(f"- [ ] {b}")
            total += 1
        for h3, bullets in section["_subs"].items():
            lines.append(f"### {h3}")
            for b in bullets:
                lines.append(f"- [ ] {b}")
                total += 1
        lines.append("")
    if wires:
        lines.append("## Wires (from §4.5)")
        lines.append("")
        lines.append("_Mechanically derived from the call-graph closure. "
                     "A wire is `[x]` when: (a) the edge exists in the rewrite's "
                     "inventory, (b) no call site passes empty/default for the "
                     "carried parameter, and (c) the consumer actually reads "
                     "any produced state. Use the diff-inventory.py reports to verify._")
        lines.append("")
        for w in wires:
            params = ", ".join(
                (b.get("param") or "arg") for b in w.get("carried_data", [])
            )
            lines.append(
                f"- [ ] `{w['producer_qname']} → {w['consumer_qname']}` "
                f"({w['edge_file']}:{w['edge_line']}, carries: {params or '—'})"
            )
            total += 1
        lines.append("")
    lines += [
        "## Improvements Accepted",
        "_Paste accepted entries from IMPROVEMENTS.md here._",
        "",
        "## Summary",
        f"- Total items: {total}",
        "- Complete: 0",
        "- In progress: 0",
        f"- Remaining: {total}",
        "",
    ]
    return "\n".join(lines), total


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("design_doc", type=Path)
    ap.add_argument("output", type=Path, nargs="?")
    ap.add_argument(
        "--include",
        action="append",
        default=[],
        help="Extra 'Heading:§tag' pair. Repeatable.",
    )
    ap.add_argument(
        "--wires",
        type=Path,
        default=None,
        help="Path to wires.json (from generate-wire-ledger.py) — "
             "adds a Wires section with one checkbox per wire.",
    )
    args = ap.parse_args()

    sections = dict(DEFAULT_SECTIONS)
    for pair in args.include:
        if ":" not in pair:
            print(f"bad --include {pair!r}", file=sys.stderr)
            return 2
        h, tag = pair.split(":", 1)
        sections[h.strip()] = tag.strip()

    wires = None
    if args.wires is not None:
        if not args.wires.is_file():
            print(f"--wires: not a file: {args.wires}", file=sys.stderr)
            return 2
        wires_doc = json.loads(args.wires.read_text(encoding="utf-8"))
        wires = wires_doc.get("wires", [])

    dst = args.output or args.design_doc.parent / "COVERAGE.md"
    text = args.design_doc.read_text(encoding="utf-8")
    rendered, total = render(parse(text), sections, wires)
    dst.write_text(rendered, encoding="utf-8")
    wire_count = len(wires) if wires else 0
    print(f"wrote {dst} with {total} items ({wire_count} wires)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
