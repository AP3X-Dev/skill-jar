#!/usr/bin/env python3
"""Diff two inventories (original vs rewrite-in-progress) for Parity Mode,
plus a suite of self-checks that run against a single inventory.

Reads JSON files produced by extract-inventory.py and emits a structured
gap list. Legacy reports (missing / extra / kind-drift / signature-drift /
tag-drift) feed Phase 1 Pass C of Parity Mode. v2 adds five additional
reports that catch the cross-module failure patterns the legacy reports
miss:

  - call-graph-delta  : per entry point, transitive callees present in the
                        original but absent from the rewrite (parity only)
  - dead-parameters   : parameters where every call site passes an empty
                        literal or default — wire-not-connected detector
  - dead-reads        : fields written but never read in the rewrite
  - orphan-methods    : public methods defined but never in any entry
                        point's transitive closure
  - content-diff      : prompt-template / regex snapshots that differ
                        beyond threshold between original and rewrite

Self-check mode: dead-parameters / dead-reads / orphan-methods run on any
single inventory (the rewrite). Call-graph-delta and content-diff require
both inventories. This lets the rewrite run this tool without an original
in sight to catch integration-seam bugs early.

Triage: decisions live in a sidecar `triage.yaml` next to the diff output.
Re-running the diff re-renders the markdown with triage state applied.

Usage:
  diff-inventory.py <original.json> <rewrite.json> [-o PARITY_GAPS.md]
  diff-inventory.py <rewrite.json> --self-check -o SELF_CHECK.md
  diff-inventory.py <rewrite.json> --self-check --mode=project-initialization

Exit codes:
  0 = no gate-relevant entries with pending or gap-to-close triage
  1 = gate-relevant entries remain
  2 = usage error
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


# ---------- IO ----------

def load_inventory(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_triage(path: Path) -> dict:
    """Minimal YAML reader (no external deps) for triage.yaml. Supports the
    restricted subset we emit: top-level mapping with `entries:` list of
    small mappings."""
    if not path.exists():
        return {"schema_version": 1, "entries": []}
    entries: list[dict] = []
    current: dict | None = None
    top: dict = {"schema_version": 1, "entries": entries}
    with path.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            if not line.strip() or line.strip().startswith("#"):
                continue
            if line.startswith("schema_version:"):
                try:
                    top["schema_version"] = int(line.split(":", 1)[1].strip())
                except Exception:
                    pass
                continue
            if line.strip() == "entries:" or line.startswith("entries:"):
                continue
            if line.startswith("  - "):
                if current is not None:
                    entries.append(current)
                current = {}
                rest = line[4:].strip()
                if rest and ":" in rest:
                    k, v = rest.split(":", 1)
                    current[k.strip()] = _strip_yaml_scalar(v.strip())
                continue
            if line.startswith("    ") and current is not None:
                s = line.strip()
                if ":" in s:
                    k, v = s.split(":", 1)
                    current[k.strip()] = _strip_yaml_scalar(v.strip())
    if current is not None:
        entries.append(current)
    return top


def _strip_yaml_scalar(v: str) -> str:
    v = v.strip()
    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
        return v[1:-1]
    return v


def write_triage(path: Path, triage: dict) -> None:
    lines = [f"schema_version: {triage.get('schema_version', 1)}", "entries:"]
    for e in triage.get("entries", []):
        lines.append(f"  - report: {e.get('report', '')}")
        for k in ("key", "triage", "note", "at"):
            v = e.get(k)
            if v is None:
                continue
            s = str(v).replace('"', '\\"')
            lines.append(f'    {k}: "{s}"')
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def triage_map(triage: dict) -> dict[tuple[str, str], dict]:
    out: dict[tuple[str, str], dict] = {}
    for e in triage.get("entries", []):
        key = (e.get("report", ""), e.get("key", ""))
        out[key] = e
    return out


# ---------- legacy reports (v1 compatible) ----------

def key_by_qname(sym: dict) -> tuple:
    return (sym["qualified_name"], sym["kind"])


def key_by_file_name(sym: dict) -> tuple:
    return (sym["file"], sym["name"], sym["kind"])


def index_symbols(inv: dict, ignore_locations: set[str]) -> tuple[dict, dict, list]:
    by_q: dict[tuple, dict] = {}
    by_fn: dict[tuple, dict] = {}
    filtered: list[dict] = []
    for s in inv["symbols"]:
        if s.get("location") in ignore_locations:
            continue
        filtered.append(s)
        by_q.setdefault(key_by_qname(s), s)
        by_fn.setdefault(key_by_file_name(s), s)
    return by_q, by_fn, filtered


def match(orig_sym: dict, rewrite_qname_idx: dict, rewrite_fn_idx: dict) -> dict | None:
    k = key_by_qname(orig_sym)
    if k in rewrite_qname_idx:
        return rewrite_qname_idx[k]
    k2 = key_by_file_name(orig_sym)
    return rewrite_fn_idx.get(k2)


def tier1_tags(sym: dict) -> tuple[set, set]:
    return set(sym.get("modifiers", [])), set(sym.get("shape", []))


def normalize_sig(sig: str) -> str:
    return " ".join(sig.split())


def legacy_diff(original: dict, rewrite: dict, ignore_locations: set[str]) -> dict:
    o_q, o_fn, o_syms = index_symbols(original, ignore_locations)
    r_q, r_fn, r_syms = index_symbols(rewrite, ignore_locations)

    missing: list[dict] = []
    kind_drift: list[dict] = []
    sig_drift: list[dict] = []
    tag_drift: list[dict] = []
    matched_rewrite_ids: set[str] = set()

    for osym in o_syms:
        rsym = match(osym, r_q, r_fn)
        if rsym is None:
            for (q, k), cand in r_q.items():
                if q == osym["qualified_name"]:
                    rsym = cand
                    break
        if rsym is None:
            missing.append({"original": osym})
            continue

        matched_rewrite_ids.add(rsym["id"])

        if rsym["kind"] != osym["kind"]:
            kind_drift.append({
                "qualified_name": osym["qualified_name"],
                "original_kind": osym["kind"],
                "rewrite_kind": rsym["kind"],
                "original_file": osym["file"],
                "rewrite_file": rsym["file"],
            })
            continue

        if normalize_sig(osym["signature"]) != normalize_sig(rsym["signature"]):
            sig_drift.append({
                "qualified_name": osym["qualified_name"],
                "original_signature": osym["signature"],
                "rewrite_signature": rsym["signature"],
                "original_file": osym["file"],
                "rewrite_file": rsym["file"],
            })

        o_mods, o_shape = tier1_tags(osym)
        r_mods, r_shape = tier1_tags(rsym)
        mods_lost = sorted(o_mods - r_mods)
        mods_gained = sorted(r_mods - o_mods)
        shape_lost = sorted(o_shape - r_shape)
        shape_gained = sorted(r_shape - o_shape)
        if mods_lost or mods_gained or shape_lost or shape_gained:
            tag_drift.append({
                "qualified_name": osym["qualified_name"],
                "modifiers_lost": mods_lost,
                "modifiers_gained": mods_gained,
                "shape_lost": shape_lost,
                "shape_gained": shape_gained,
                "original_file": osym["file"],
                "rewrite_file": rsym["file"],
            })

    extra = [{"rewrite": r} for r in r_syms if r["id"] not in matched_rewrite_ids]

    return {
        "original_symbols": len(o_syms),
        "rewrite_symbols": len(r_syms),
        "missing": missing,
        "kind_drift": kind_drift,
        "signature_drift": sig_drift,
        "tag_drift": tag_drift,
        "extra": extra,
    }


# ---------- v2 helpers ----------

def is_v2(inv: dict) -> bool:
    return inv.get("schema_version") == "2" or "call_edges" in inv or "field_io" in inv


def index_by_id(inv: dict) -> dict[str, dict]:
    return {s["id"]: s for s in inv.get("symbols", [])}


def is_entry_point(sym: dict) -> bool:
    shape = set(sym.get("shape", []))
    if "entrypoint" in shape:
        return True
    mods = set(sym.get("modifiers", []))
    if "exported" in mods and sym.get("kind") in ("function", "method"):
        if sym.get("location") == "source" and sym.get("visibility") == "public":
            return True
    return False


def transitive_callees(entry_id: str, call_edges: list[dict]) -> set[str]:
    """BFS from entry_id over resolved call edges. Unresolved/ambiguous edges
    are ignored for closure computation."""
    by_caller: dict[str, list[dict]] = {}
    for e in call_edges:
        by_caller.setdefault(e["caller_id"], []).append(e)
    visited: set[str] = set()
    stack = [entry_id]
    while stack:
        cur = stack.pop()
        if cur in visited:
            continue
        visited.add(cur)
        for e in by_caller.get(cur, []):
            if e.get("resolution") == "resolved" and e.get("resolved_callee_id"):
                stack.append(e["resolved_callee_id"])
    return visited


# ---------- v2 reports ----------

def call_graph_delta(original: dict, rewrite: dict) -> list[dict]:
    """For each entry point in the original, compute the transitive callee
    set and compare to the rewrite's for the same qualified_name."""
    if not is_v2(original) or not is_v2(rewrite):
        return []

    o_by_id = index_by_id(original)
    r_by_id = index_by_id(rewrite)
    r_by_qname = {s["qualified_name"]: s for s in rewrite.get("symbols", [])
                   if s.get("location") == "source"}

    o_edges = original.get("call_edges", [])
    r_edges = rewrite.get("call_edges", [])

    entry_points = [s for s in original.get("symbols", []) if is_entry_point(s)]
    results: list[dict] = []

    for ep in entry_points:
        o_closure_ids = transitive_callees(ep["id"], o_edges)
        o_closure_qnames = {
            o_by_id[i]["qualified_name"]
            for i in o_closure_ids if i in o_by_id
        }

        # find the matching rewrite entry point by qualified_name
        rep = r_by_qname.get(ep["qualified_name"])
        if rep is None:
            results.append({
                "entry_point": ep["qualified_name"],
                "missing_entry_point": True,
                "missing_callees": [],
            })
            continue
        r_closure_ids = transitive_callees(rep["id"], r_edges)
        r_closure_qnames = {
            r_by_id[i]["qualified_name"]
            for i in r_closure_ids if i in r_by_id
        }

        missing = sorted(o_closure_qnames - r_closure_qnames)
        # Exclude the entry point itself from "missing"
        missing = [m for m in missing if m != ep["qualified_name"]]
        if missing:
            results.append({
                "entry_point": ep["qualified_name"],
                "missing_entry_point": False,
                "missing_callees": missing,
            })

    return results


def _is_empty_literal_binding(binding: dict) -> bool:
    """Decide whether a single arg_binding indicates the param was passed
    an empty/default value."""
    if binding.get("kind") == "default":
        return True
    if binding.get("kind") == "literal":
        # literal_value is populated for empty-ish literals
        if "literal_value" in binding:
            v = binding["literal_value"]
            return v in ("", None, 0, 0.0, False) or v == [] or v == {}
    return False


def dead_parameters(inventory: dict, original: dict | None = None) -> list[dict]:
    """Parameters in rewrite where every call site passes empty/default."""
    if not is_v2(inventory):
        return []
    edges = inventory.get("call_edges", [])

    # Collect all call sites grouped by (resolved_callee_id, param_name)
    # For unresolved edges, we can still check dead-ness against the nominal callee_name.
    # But matching to a param requires a resolved target. Use resolved only.
    by_target: dict[tuple[str, str], list[dict]] = {}  # (callee_id, param_name) -> bindings
    for e in edges:
        if e.get("resolution") != "resolved":
            continue
        target = e.get("resolved_callee_id")
        if not target:
            continue
        for b in e.get("arg_bindings", []):
            param = b.get("param")
            if not param:
                continue
            by_target.setdefault((target, param), []).append({
                "binding": b,
                "edge": e,
            })

    # Flag any param where 100% of bindings are empty/default (and at least 1 site)
    dead: list[dict] = []
    for (target, param), sites in by_target.items():
        if not sites:
            continue
        empties = [s for s in sites if _is_empty_literal_binding(s["binding"])]
        if len(empties) == len(sites):
            ratio = 1.0
        elif len(empties) >= max(1, int(len(sites) * 0.9)):
            ratio = len(empties) / len(sites)
        else:
            continue
        # Look up target symbol for location info
        target_sym = None
        for s in inventory.get("symbols", []):
            if s["id"] == target:
                target_sym = s
                break
        if target_sym is None:
            continue
        entry = {
            "target_qname": target_sym["qualified_name"],
            "param": param,
            "dead_ratio": ratio,
            "severity": "critical" if ratio == 1.0 else "warning",
            "sites": [
                {
                    "file": s["edge"]["file"],
                    "line": s["edge"]["line"],
                    "expr": s["binding"].get("expr", ""),
                }
                for s in sites
            ],
            "target_file": target_sym["file"],
            "target_line": target_sym["line"],
        }
        # Optional: original comparison (look up how the original wires this param)
        if original is not None and is_v2(original):
            o_by_qname = {s["qualified_name"]: s for s in original.get("symbols", [])}
            o_target = o_by_qname.get(target_sym["qualified_name"])
            if o_target is not None:
                # Find edges that call this target in the original
                non_empty_producers = []
                for oe in original.get("call_edges", []):
                    if oe.get("resolution") != "resolved":
                        continue
                    if oe.get("resolved_callee_id") != o_target["id"]:
                        continue
                    for b in oe.get("arg_bindings", []):
                        if b.get("param") == param and not _is_empty_literal_binding(b):
                            non_empty_producers.append({
                                "file": oe["file"],
                                "line": oe["line"],
                                "expr": b.get("expr", ""),
                            })
                if non_empty_producers:
                    entry["original_producers"] = non_empty_producers
        dead.append(entry)
    dead.sort(key=lambda d: (d["target_file"], d["target_line"], d["param"]))
    return dead


def dead_reads(inventory: dict, original: dict | None = None) -> list[dict]:
    """Fields written but never read in the rewrite."""
    if not is_v2(inventory):
        return []
    writes: dict[tuple[str, str], list[dict]] = {}  # (owner_id, field) -> writes
    reads: dict[tuple[str, str], int] = {}
    for io in inventory.get("field_io", []):
        key = (io.get("owner_id", ""), io.get("field", ""))
        if io.get("op") == "write":
            writes.setdefault(key, []).append(io)
        elif io.get("op") == "read":
            reads[key] = reads.get(key, 0) + 1

    sym_by_id = index_by_id(inventory)
    dead: list[dict] = []
    for key, w_list in writes.items():
        if reads.get(key, 0) > 0:
            continue
        owner_id, field_name = key
        owner = sym_by_id.get(owner_id) or {"qualified_name": owner_id.rsplit(":", 1)[-1], "file": "", "line": 0}
        entry = {
            "owner_qname": owner.get("qualified_name"),
            "field": field_name,
            "write_count": len(w_list),
            "writes": [
                {"file": w["file"], "line": w["line"], "op_detail": w.get("op_detail")}
                for w in w_list
            ],
        }
        # Original comparison
        if original is not None and is_v2(original):
            o_reads = 0
            for io in original.get("field_io", []):
                if io.get("op") == "read" and io.get("field") == field_name:
                    # best-effort: match by field name across inventories
                    # Matching by owner qualified_name would be stricter.
                    o_reads += 1
            if o_reads > 0:
                entry["original_reads"] = o_reads
        dead.append(entry)
    dead.sort(key=lambda d: (d["owner_qname"] or "", d["field"]))
    return dead


def orphan_methods(inventory: dict) -> list[dict]:
    """Public methods/functions in rewrite that are not in any entry point's closure."""
    if not is_v2(inventory):
        return []
    edges = inventory.get("call_edges", [])

    entry_points = [s for s in inventory.get("symbols", []) if is_entry_point(s)]
    reached: set[str] = set()
    for ep in entry_points:
        reached |= transitive_callees(ep["id"], edges)

    orphans: list[dict] = []
    for s in inventory.get("symbols", []):
        if s.get("location") != "source":
            continue
        if s.get("kind") not in ("function", "method"):
            continue
        if s.get("visibility") != "public":
            continue
        if is_entry_point(s):
            continue
        if s["id"] in reached:
            continue
        # Also suppress anything with common framework-decorator modifier patterns
        # (none currently encoded as Tier-1 modifier; future extension).
        orphans.append({
            "qualified_name": s["qualified_name"],
            "file": s["file"],
            "line": s["line"],
            "kind": s["kind"],
        })
    orphans.sort(key=lambda o: (o["file"], o["line"], o["qualified_name"]))
    return orphans


def content_diff(original: dict, rewrite: dict) -> list[dict]:
    """Compare content_snapshot line/token counts for matched prompt/regex symbols."""
    if not is_v2(original) or not is_v2(rewrite):
        return []
    o_by_q = {s["qualified_name"]: s for s in original.get("symbols", [])
               if s.get("content_snapshot")}
    r_by_q = {s["qualified_name"]: s for s in rewrite.get("symbols", [])
               if s.get("content_snapshot")}
    diffs: list[dict] = []
    for qn, osym in o_by_q.items():
        rsym = r_by_q.get(qn)
        if rsym is None:
            continue
        os_ = osym["content_snapshot"]
        rs_ = rsym["content_snapshot"]
        if os_["sha256"] == rs_["sha256"]:
            continue
        dims = {}
        for dim in ("line_count", "token_count_estimate", "length"):
            if os_.get(dim, 0) == 0:
                dims[dim] = 0.0
            else:
                dims[dim] = (rs_.get(dim, 0) - os_.get(dim, 0)) / os_.get(dim, 1)
        max_drop = -min(dims.values()) if dims else 0.0
        if max_drop >= 0.5:
            severity = "critical"
        elif max_drop >= 0.2:
            severity = "warning"
        elif max_drop >= 0.05:
            severity = "info"
        else:
            severity = "info"
        diffs.append({
            "qualified_name": qn,
            "original": os_,
            "rewrite": rs_,
            "deltas": {k: round(v * 100, 1) for k, v in dims.items()},
            "severity": severity,
        })
    diffs.sort(key=lambda d: (d["severity"] != "critical", d["qualified_name"]))
    return diffs


# ---------- rendering ----------

LEGEND = (
    "- `missing`: absent from rewrite — close or mark `preserved-divergence`\n"
    "- `kind-drift`: symbol kind changed — usually a real regression\n"
    "- `signature-drift`: callable/type signature differs after normalization\n"
    "- `tag-drift`: Tier-1 tags (async, throws, error-type, exported, ...) diverged\n"
    "- `extra`: rewrite-only symbol — intentional improvement or scope creep?\n"
    "- `call-graph-delta`: callee reachable from entry point in original is unreached in rewrite\n"
    "- `dead-parameters`: param where every call site passes empty/default — wire not connected\n"
    "- `dead-reads`: field written but never read — consumer not wired up\n"
    "- `orphan-methods`: public method defined but never reached from any entry point\n"
    "- `content-diff`: prompt/regex content shrunk significantly between original and rewrite\n"
)


def triage_status_for(tmap: dict, report: str, key: str) -> tuple[str, str]:
    """Returns (status, note). status ∈ pending/gap-to-close/intentional-divergence/false-positive."""
    e = tmap.get((report, key))
    if e is None:
        return ("pending", "")
    return (e.get("triage", "pending"), e.get("note", ""))


def render(result: dict, include_extras: bool, triage: dict,
           mode: str) -> str:
    tmap = triage_map(triage)
    L: list[str] = []
    L.append("# Parity Gaps")
    L.append("")
    L.append("_Generated by diff-inventory.py (schema v2)._")
    L.append("")

    # summary
    s = result["summary"]
    L.append("## Summary")
    for k, v in s.items():
        L.append(f"- {k}: {v}")
    L.append("")

    L.append("## Legend")
    L.append(LEGEND)

    # legacy reports
    if result.get("missing"):
        L.append("## missing")
        for m in result["missing"]:
            o = m["original"]
            L.append(f"- `{o['qualified_name']}` [{o['kind']}] — {o['file']}:{o['line']}")
        L.append("")
    if result.get("kind_drift"):
        L.append("## kind-drift")
        for k in result["kind_drift"]:
            L.append(f"- `{k['qualified_name']}` : {k['original_kind']} → {k['rewrite_kind']}")
        L.append("")
    if result.get("signature_drift"):
        L.append("## signature-drift")
        for k in result["signature_drift"]:
            L.append(f"- `{k['qualified_name']}`")
            L.append(f"  - original: `{k['original_signature']}`")
            L.append(f"  - rewrite:  `{k['rewrite_signature']}`")
        L.append("")
    if result.get("tag_drift"):
        L.append("## tag-drift")
        for k in result["tag_drift"]:
            parts = []
            if k["modifiers_lost"]: parts.append(f"lost mods: {', '.join(k['modifiers_lost'])}")
            if k["modifiers_gained"]: parts.append(f"gained mods: {', '.join(k['modifiers_gained'])}")
            if k["shape_lost"]: parts.append(f"lost shape: {', '.join(k['shape_lost'])}")
            if k["shape_gained"]: parts.append(f"gained shape: {', '.join(k['shape_gained'])}")
            L.append(f"- `{k['qualified_name']}` — " + "; ".join(parts))
        L.append("")
    if include_extras and result.get("extra"):
        L.append("## extra (rewrite-only)")
        for e in result["extra"]:
            r = e["rewrite"]
            L.append(f"- `{r['qualified_name']}` [{r['kind']}] — {r['file']}:{r['line']}")
        L.append("")

    # v2 reports
    if result.get("call_graph_delta"):
        L.append("## call-graph-delta")
        for d in result["call_graph_delta"]:
            status, note = triage_status_for(tmap, "call-graph-delta", d["entry_point"])
            if d.get("missing_entry_point"):
                L.append(f"### `{d['entry_point']}` — **entry point itself missing in rewrite**")
                L.append(f"- triage: {status}" + (f" — {note}" if note else ""))
                continue
            L.append(f"### `{d['entry_point']}`")
            for m in d["missing_callees"]:
                L.append(f"- **missing-callee:** `{m}`")
            L.append(f"- triage: {status}" + (f" — {note}" if note else ""))
        L.append("")

    if result.get("dead_parameters"):
        L.append("## dead-parameters")
        for d in result["dead_parameters"]:
            key = f"{d['target_qname']}({d['param']})"
            status, note = triage_status_for(tmap, "dead-parameters", key)
            ratio_pct = round(d["dead_ratio"] * 100, 1)
            L.append(f"- **`{key}`** — {len(d['sites'])} call sites, {ratio_pct}% empty/default (severity: {d['severity']})")
            for site in d["sites"][:5]:
                L.append(f"  - {site['file']}:{site['line']}  →  `{site['expr']}`")
            if d.get("original_producers"):
                L.append("  - original comparison: non-empty producers exist in original:")
                for p in d["original_producers"][:3]:
                    L.append(f"    - {p['file']}:{p['line']}  →  `{p['expr']}`")
            L.append(f"  - triage: {status}" + (f" — {note}" if note else ""))
        L.append("")

    if result.get("dead_reads"):
        L.append("## dead-reads")
        for d in result["dead_reads"]:
            key = f"{d['owner_qname']}.{d['field']}"
            status, note = triage_status_for(tmap, "dead-reads", key)
            L.append(f"- **`{key}`** — {d['write_count']} writes, 0 reads")
            for w in d["writes"][:3]:
                detail = f" (op_detail: {w['op_detail']})" if w.get("op_detail") else ""
                L.append(f"  - write: {w['file']}:{w['line']}{detail}")
            if d.get("original_reads"):
                L.append(f"  - original comparison: {d['original_reads']} read site(s) exist in original")
            L.append(f"  - triage: {status}" + (f" — {note}" if note else ""))
        L.append("")

    if result.get("orphan_methods"):
        L.append("## orphan-methods")
        for d in result["orphan_methods"]:
            status, note = triage_status_for(tmap, "orphan-methods", d["qualified_name"])
            L.append(f"- **`{d['qualified_name']}`** [{d['kind']}] — {d['file']}:{d['line']}")
            L.append(f"  - triage: {status}" + (f" — {note}" if note else ""))
        L.append("")

    if result.get("content_diff"):
        L.append("## content-diff")
        for d in result["content_diff"]:
            status, note = triage_status_for(tmap, "content-diff", d["qualified_name"])
            L.append(f"- **`{d['qualified_name']}`** — severity: {d['severity']}")
            L.append(f"  - original: {d['original']['line_count']} lines, {d['original']['token_count_estimate']} tokens, sha {d['original']['sha256'][:12]}")
            L.append(f"  - rewrite:  {d['rewrite']['line_count']} lines, {d['rewrite']['token_count_estimate']} tokens, sha {d['rewrite']['sha256'][:12]}")
            deltas = d["deltas"]
            L.append(f"  - delta: line {deltas.get('line_count', 0):+.1f}%, token {deltas.get('token_count_estimate', 0):+.1f}%")
            L.append(f"  - triage: {status}" + (f" — {note}" if note else ""))
        L.append("")

    L.append("## Triage verbs")
    L.append("- `gap-to-close` → becomes a requirement in PRP.md")
    L.append("- `intentional-divergence` → logged in IMPROVEMENTS.md Preserved Divergence")
    L.append("- `false-positive` → static-analysis limitation; record reason")
    L.append("- `pending` → not yet triaged (gate failure)")
    L.append("")
    if mode == "project-initialization":
        L.append("_Gate mode: `project-initialization` — dead-parameters / dead-reads / orphan-methods are informational only; call-graph-delta and content-diff remain gated._")
        L.append("")

    return "\n".join(L)


# ---------- gate ----------

def compute_gate(result: dict, triage: dict, mode: str) -> tuple[bool, list[str]]:
    """Returns (passed, list_of_failing_entries)."""
    tmap = triage_map(triage)
    failing: list[str] = []

    soft_in_init_mode = {"dead-parameters", "dead-reads", "orphan-methods"}

    def check(report: str, key: str, soft: bool = False) -> None:
        status, _ = triage_status_for(tmap, report, key)
        if status in ("pending", "gap-to-close"):
            if soft and mode == "project-initialization":
                return
            failing.append(f"{report}: {key} ({status})")

    # legacy
    for m in result.get("missing", []):
        check("missing", m["original"]["qualified_name"])
    for k in result.get("kind_drift", []):
        check("kind-drift", k["qualified_name"])
    for k in result.get("signature_drift", []):
        check("signature-drift", k["qualified_name"])
    for k in result.get("tag_drift", []):
        check("tag-drift", k["qualified_name"])

    # v2
    for d in result.get("call_graph_delta", []):
        if d.get("missing_entry_point") or d.get("missing_callees"):
            check("call-graph-delta", d["entry_point"])
    for d in result.get("dead_parameters", []):
        # only critical severity gates
        if d["severity"] == "critical":
            check("dead-parameters", f"{d['target_qname']}({d['param']})", soft=True)
    for d in result.get("dead_reads", []):
        check("dead-reads", f"{d['owner_qname']}.{d['field']}", soft=True)
    for d in result.get("orphan_methods", []):
        check("orphan-methods", d["qualified_name"], soft=True)
    for d in result.get("content_diff", []):
        if d["severity"] == "critical":
            check("content-diff", d["qualified_name"])

    return (not failing, failing)


# ---------- main ----------

def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("first", type=Path, help="Inventory of the original (parity) or the rewrite (self-check)")
    ap.add_argument("second", type=Path, nargs="?", default=None, help="Inventory of the rewrite (parity mode only)")
    ap.add_argument("-o", "--output", type=Path, default=None,
                    help="Markdown output path (default: ./PARITY_GAPS.md or ./SELF_CHECK.md)")
    ap.add_argument("--json", action="store_true", help="Emit raw JSON diff to stdout instead of markdown")
    ap.add_argument("--ignore-locations", default="test,fixture,benchmark,example",
                    help="Comma-separated location tags to skip on both sides")
    ap.add_argument("--no-extras", action="store_true", help="Skip the 'extra in rewrite' section")
    ap.add_argument("--self-check", action="store_true",
                    help="Run dead-parameter / dead-read / orphan-method reports on a single inventory")
    ap.add_argument("--mode", choices=["normal", "project-initialization"], default="normal",
                    help="project-initialization relaxes dead-*/orphan-methods gates (pre-wiring phase)")
    ap.add_argument("--triage", type=Path, default=None,
                    help="Triage sidecar path (default: <output-dir>/triage.yaml)")
    args = ap.parse_args()

    if not args.first.is_file():
        print(f"not a file: {args.first}", file=sys.stderr)
        return 2

    first = load_inventory(args.first)
    second = load_inventory(args.second) if args.second and args.second.is_file() else None

    if args.self_check:
        rewrite = first
        original = None
    else:
        if second is None:
            print("parity mode requires two inventories; use --self-check for single-inventory reports", file=sys.stderr)
            return 2
        original = first
        rewrite = second

    ignore = {t.strip() for t in args.ignore_locations.split(",") if t.strip()}

    # Legacy reports (parity only)
    if original is not None:
        legacy = legacy_diff(original, rewrite, ignore)
    else:
        legacy = {
            "original_symbols": 0,
            "rewrite_symbols": len([s for s in rewrite.get("symbols", [])
                                     if s.get("location") not in ignore]),
            "missing": [],
            "kind_drift": [],
            "signature_drift": [],
            "tag_drift": [],
            "extra": [],
        }

    # v2 reports
    cgd = call_graph_delta(original, rewrite) if original else []
    deadp = dead_parameters(rewrite, original)
    deadr = dead_reads(rewrite, original)
    orphs = orphan_methods(rewrite)
    cdiff = content_diff(original, rewrite) if original else []

    result = {
        "summary": {
            "original_symbols": legacy["original_symbols"],
            "rewrite_symbols": legacy["rewrite_symbols"],
            "missing": len(legacy["missing"]),
            "kind_drift": len(legacy["kind_drift"]),
            "signature_drift": len(legacy["signature_drift"]),
            "tag_drift": len(legacy["tag_drift"]),
            "extra": len(legacy["extra"]),
            "call_graph_delta_entries": len(cgd),
            "dead_parameters": len(deadp),
            "dead_reads": len(deadr),
            "orphan_methods": len(orphs),
            "content_diff": len(cdiff),
        },
        "missing": legacy["missing"],
        "kind_drift": legacy["kind_drift"],
        "signature_drift": legacy["signature_drift"],
        "tag_drift": legacy["tag_drift"],
        "extra": legacy["extra"],
        "call_graph_delta": cgd,
        "dead_parameters": deadp,
        "dead_reads": deadr,
        "orphan_methods": orphs,
        "content_diff": cdiff,
    }

    default_name = "SELF_CHECK.md" if args.self_check else "PARITY_GAPS.md"
    out_path = args.output or Path(default_name)
    triage_path = args.triage or out_path.parent / "triage.yaml"
    triage = load_triage(triage_path)

    if args.json:
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(render(result, include_extras=not args.no_extras,
                                    triage=triage, mode=args.mode), encoding="utf-8")
        s = result["summary"]
        print(f"wrote {out_path} — "
              f"missing:{s['missing']} cgd:{s['call_graph_delta_entries']} "
              f"dead-params:{s['dead_parameters']} dead-reads:{s['dead_reads']} "
              f"orphans:{s['orphan_methods']} content:{s['content_diff']}")

    # Ensure triage sidecar exists (empty if first run)
    if not triage_path.exists():
        write_triage(triage_path, {"schema_version": 1, "entries": []})

    passed, failing = compute_gate(result, triage, args.mode)
    if not passed:
        print(f"gate: {len(failing)} entries pending/gap-to-close", file=sys.stderr)
        for f in failing[:20]:
            print(f"  {f}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
