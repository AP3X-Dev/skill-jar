#!/usr/bin/env python3
"""Generate a wire ledger from an inventory.json (Pass 4.5 — Integration Seams).

Walks the call-graph from every detected entry point and emits:

  - `clean-room/wires.json` — structured list of producer→consumer wires,
    each carrying which parameters the consumer receives and what the
    producer writes/reads around the edge.
  - A seeded `## §4.5 Integration Seams` Markdown section for the design
    doc, with empty prose fields for a subagent to fill in.

The mechanical step is deterministic; the prose step is a follow-up where
an analyzer subagent annotates each wire with: what_data_represents,
invariant, and if_broken_symptom. That subagent cannot add new wires — the
skeleton is complete by construction from the call graph.

Usage:
  generate-wire-ledger.py clean-room/inventory.json
    -o clean-room/wires.json
    --design-doc clean-room/DESIGN_DOC.md     # optional: append §4.5
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def is_entry_point(sym: dict) -> bool:
    shape = set(sym.get("shape", []))
    if "entrypoint" in shape:
        return True
    if (
        "exported" in sym.get("modifiers", [])
        and sym.get("kind") in ("function", "method")
        and sym.get("location") == "source"
        and sym.get("visibility") == "public"
    ):
        return True
    return False


def build_call_index(edges: list[dict]) -> dict[str, list[dict]]:
    by_caller: dict[str, list[dict]] = {}
    for e in edges:
        by_caller.setdefault(e["caller_id"], []).append(e)
    return by_caller


def build_io_index(ios: list[dict]) -> tuple[dict, dict]:
    writes_by_ctx: dict[str, list[dict]] = {}
    reads_by_ctx: dict[str, list[dict]] = {}
    for io in ios:
        ctx = io.get("context_symbol_id", "")
        if io.get("op") == "write":
            writes_by_ctx.setdefault(ctx, []).append(io)
        elif io.get("op") == "read":
            reads_by_ctx.setdefault(ctx, []).append(io)
    return writes_by_ctx, reads_by_ctx


def walk_wires(entry_id: str, by_caller: dict[str, list[dict]],
               sym_by_id: dict[str, dict],
               writes_by_ctx: dict[str, list[dict]],
               reads_by_ctx: dict[str, list[dict]]) -> list[dict]:
    """BFS from entry_id, emitting one wire per resolved call edge."""
    wires: list[dict] = []
    visited: set[str] = set()
    stack = [entry_id]
    while stack:
        cur = stack.pop()
        if cur in visited:
            continue
        visited.add(cur)
        producer = sym_by_id.get(cur)
        for edge in by_caller.get(cur, []):
            if edge.get("resolution") != "resolved":
                continue
            callee_id = edge.get("resolved_callee_id")
            if not callee_id:
                continue
            consumer = sym_by_id.get(callee_id)
            producer_writes = [
                {"field": w["field"], "op_detail": w.get("op_detail")}
                for w in writes_by_ctx.get(cur, [])
            ]
            consumer_reads = [
                {"field": r["field"]}
                for r in reads_by_ctx.get(callee_id, [])
            ]
            wires.append({
                "producer_id": cur,
                "producer_qname": producer["qualified_name"] if producer else cur,
                "consumer_id": callee_id,
                "consumer_qname": consumer["qualified_name"] if consumer else callee_id,
                "edge_file": edge["file"],
                "edge_line": edge["line"],
                "carried_data": [
                    {"param": b.get("param"), "kind": b.get("kind"), "expr": b.get("expr", "")[:80]}
                    for b in edge.get("arg_bindings", [])
                ],
                "producer_writes_near_edge": producer_writes[:8],
                "consumer_reads_at_edge": consumer_reads[:8],
                # Prose fields for the subagent to fill.
                "what_data_represents": "",
                "invariant": "",
                "if_broken_symptom": "",
            })
            stack.append(callee_id)
    return wires


def render_markdown(wires: list[dict]) -> str:
    L = [
        "## 4.5 Integration Seams",
        "",
        "_Auto-generated from the call graph. Prose fields filled by the Pass-4.5 subagent. Do not add new wires here — if a wire is missing, the inventory is incomplete._",
        "",
    ]
    # Group by producer
    groups: dict[str, list[dict]] = {}
    for w in wires:
        groups.setdefault(w["producer_qname"], []).append(w)
    for producer, ws in sorted(groups.items()):
        L.append(f"### Producer: `{producer}`")
        L.append("")
        for w in ws:
            L.append(f"- **wire → `{w['consumer_qname']}`** at {w['edge_file']}:{w['edge_line']}")
            if w["carried_data"]:
                sig = ", ".join(
                    f"{b.get('param') or 'arg'}={b.get('expr') or b.get('kind')}"
                    for b in w["carried_data"]
                )
                L.append(f"  - carried: `{sig}`")
            if w["producer_writes_near_edge"]:
                fs = ", ".join(
                    f"{pw['field']}({pw['op_detail']})" if pw.get("op_detail") else pw["field"]
                    for pw in w["producer_writes_near_edge"]
                )
                L.append(f"  - producer writes: {fs}")
            if w["consumer_reads_at_edge"]:
                fs = ", ".join(r["field"] for r in w["consumer_reads_at_edge"])
                L.append(f"  - consumer reads: {fs}")
            L.append(f"  - what this data represents: _{{{{ TO FILL }}}}_")
            L.append(f"  - invariant: _{{{{ TO FILL }}}}_")
            L.append(f"  - if this wire is broken: _{{{{ TO FILL }}}}_")
        L.append("")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("inventory", type=Path, help="inventory.json (schema v2 required)")
    ap.add_argument("-o", "--output", type=Path, default=None,
                    help="wires.json output (default: <dir>/wires.json)")
    ap.add_argument("--design-doc", type=Path, default=None,
                    help="If provided, append the §4.5 section to this file")
    args = ap.parse_args()

    if not args.inventory.is_file():
        print(f"not a file: {args.inventory}", file=sys.stderr)
        return 2
    inv = json.loads(args.inventory.read_text(encoding="utf-8"))
    if inv.get("schema_version") != "2":
        print("inventory.json must be schema v2 (v1 lacks call_edges)", file=sys.stderr)
        return 2

    sym_by_id = {s["id"]: s for s in inv.get("symbols", [])}
    by_caller = build_call_index(inv.get("call_edges", []))
    writes_by_ctx, reads_by_ctx = build_io_index(inv.get("field_io", []))

    entry_points = [s for s in inv.get("symbols", []) if is_entry_point(s)]
    all_wires: list[dict] = []
    seen_edges: set[tuple[str, str, int]] = set()
    for ep in entry_points:
        wires = walk_wires(ep["id"], by_caller, sym_by_id, writes_by_ctx, reads_by_ctx)
        for w in wires:
            key = (w["producer_id"], w["consumer_id"], w["edge_line"])
            if key in seen_edges:
                continue
            seen_edges.add(key)
            all_wires.append(w)

    out = args.output or (args.inventory.parent / "wires.json")
    out.write_text(json.dumps({
        "inventory": str(args.inventory.resolve()),
        "entry_points": [ep["qualified_name"] for ep in entry_points],
        "wire_count": len(all_wires),
        "wires": all_wires,
    }, indent=2), encoding="utf-8")
    print(f"wrote {out} — {len(all_wires)} wires across {len(entry_points)} entry points")

    if args.design_doc is not None:
        md = render_markdown(all_wires)
        if args.design_doc.exists():
            existing = args.design_doc.read_text(encoding="utf-8")
            if "## 4.5 Integration Seams" in existing:
                print(f"note: §4.5 already present in {args.design_doc}; not appending "
                      f"(edit manually or regenerate)", file=sys.stderr)
            else:
                args.design_doc.write_text(existing.rstrip() + "\n\n" + md + "\n", encoding="utf-8")
                print(f"appended §4.5 to {args.design_doc}")
        else:
            args.design_doc.write_text(md + "\n", encoding="utf-8")
            print(f"wrote {args.design_doc} (§4.5 only)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
