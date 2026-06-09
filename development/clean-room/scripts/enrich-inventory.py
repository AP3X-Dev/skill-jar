#!/usr/bin/env python3
"""Tier-2 (semantic) tag enrichment for inventories.

Tier-2 tags (role / concern / risk) require judgment, so they're assigned by
an LLM pass — typically a research subagent dispatched from Phase 1. This
script never calls an LLM itself. It does two things:

  prompt  Emit one or more prompt files that can be handed to the subagent.
          Symbols are chunked (default 50 per chunk) so each prompt fits
          comfortably in a single response.

  apply   Merge the subagent's JSON responses back into the inventory,
          validating every tag against scripts/inventory-vocab.json.

Clean-room note: this script reads ONLY the inventory (which contains
signatures, not bodies). The original source never enters the implementer's
context. The research subagent may read the original to judge roles/concerns,
but it returns tags only — never verbatim code.

Usage:
  enrich-inventory.py prompt <inventory.json> [-o prompts/] [--chunk-size 50]
  enrich-inventory.py apply  <inventory.json> <response.json> [<response.json>...]
                             [-o enriched-inventory.json]

Response schema (JSON):
  {
    "tags": {
      "<symbol-id>": {
        "role":    ["validator"],
        "concern": ["auth", "network-io"],
        "risk":    ["security-sensitive"]
      },
      ...
    }
  }
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
VOCAB_PATH = SCRIPT_DIR / "inventory-vocab.json"


def load_vocab() -> dict:
    with VOCAB_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


# ---------- prompt emission ----------

PROMPT_HEADER = """\
# Inventory Enrichment — Tier-2 Semantic Tags

You are enriching a symbol inventory extracted from a codebase. For each symbol
below, assign Tier-2 semantic tags from the closed vocabulary.

## Rules

1. Every tag MUST come from the vocabulary. Unknown tags will be rejected by
   the merger and the whole response discarded.
2. Tags are OPTIONAL. If a symbol doesn't clearly fit any tag in a category,
   leave that array empty. Under-tagging is better than guessing.
3. `role` describes what the symbol DOES (pick at most 2).
4. `concern` describes what AREA of the system it touches (pick at most 3).
5. `risk` flags attention-worthy properties (pick at most 2). Use sparingly.
6. If you read the original source to make these judgments, return ONLY tags.
   Do NOT return code, identifiers, comments, or pseudocode — the clean-room
   firewall depends on you returning abstractions only.
7. Respond with ONLY a single JSON object matching the schema. No prose, no
   markdown fencing, no commentary.

## Vocabulary

```json
{vocab_json}
```

## Response schema

```json
{{
  "tags": {{
    "<symbol-id>": {{
      "role":    [...],
      "concern": [...],
      "risk":    [...]
    }}
  }}
}}
```

Symbols not in the batch should be omitted from the response.

## Symbols (batch {batch_index} of {batch_total})

Each symbol below is a JSON line. Use `id` verbatim as the response key.

"""


def emit_prompts(inv_path: Path, out_dir: Path, chunk_size: int) -> int:
    inv = json.loads(inv_path.read_text(encoding="utf-8"))
    vocab = load_vocab()
    tier2 = {
        "role": vocab["tier2"]["role"],
        "concern": vocab["tier2"]["concern"],
        "risk": vocab["tier2"]["risk"],
    }
    vocab_json = json.dumps(tier2, indent=2)

    symbols = inv.get("symbols", [])
    # Skip test/fixture/migration by default — reviewer can change
    candidates = [s for s in symbols if s.get("location") == "source"]
    chunks = [candidates[i : i + chunk_size] for i in range(0, len(candidates), chunk_size)]
    out_dir.mkdir(parents=True, exist_ok=True)

    for i, chunk in enumerate(chunks, 1):
        header = PROMPT_HEADER.format(
            vocab_json=vocab_json,
            batch_index=i,
            batch_total=len(chunks),
        )
        lines = [header]
        for s in chunk:
            compact = {
                "id": s["id"],
                "name": s["name"],
                "kind": s["kind"],
                "file": s["file"],
                "line": s["line"],
                "signature": s["signature"],
                "tier1": {
                    "modifiers": s.get("modifiers", []),
                    "shape": s.get("shape", []),
                },
            }
            lines.append(json.dumps(compact))
        out_path = out_dir / f"prompt-{i:04d}.md"
        out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"wrote {len(chunks)} prompt(s) to {out_dir} "
          f"({len(candidates)} source symbols; {len(symbols) - len(candidates)} non-source skipped)")
    return 0


# ---------- response application ----------

def validate_tags(tags: dict, vocab: dict) -> list[str]:
    errs = []
    t2 = vocab["tier2"]
    allowed = {k: set(t2[k]) for k in ("role", "concern", "risk")}
    for cat in ("role", "concern", "risk"):
        vals = tags.get(cat, [])
        if not isinstance(vals, list):
            errs.append(f"{cat} must be a list, got {type(vals).__name__}")
            continue
        for v in vals:
            if v not in allowed[cat]:
                errs.append(f"invalid {cat} tag: {v!r}")
    return errs


def apply_responses(inv_path: Path, response_paths: list[Path], out_path: Path) -> int:
    inv = json.loads(inv_path.read_text(encoding="utf-8"))
    vocab = load_vocab()
    by_id = {s["id"]: s for s in inv["symbols"]}

    applied = 0
    unknown_ids: list[str] = []
    validation_errs: list[str] = []

    for rp in response_paths:
        try:
            resp = json.loads(rp.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"skip {rp}: parse failed: {e}", file=sys.stderr)
            continue
        tag_map = resp.get("tags", {})
        if not isinstance(tag_map, dict):
            print(f"skip {rp}: 'tags' is not an object", file=sys.stderr)
            continue

        for sid, tags in tag_map.items():
            if sid not in by_id:
                unknown_ids.append(sid)
                continue
            errs = validate_tags(tags, vocab)
            if errs:
                validation_errs.extend(f"{sid}: {e}" for e in errs)
                continue
            sym = by_id[sid]
            sym["tier2"] = {
                "role": sorted(set(tags.get("role", []))),
                "concern": sorted(set(tags.get("concern", []))),
                "risk": sorted(set(tags.get("risk", []))),
            }
            applied += 1

    if validation_errs:
        for e in validation_errs[:20]:
            print(f"validation: {e}", file=sys.stderr)
        print(f"... {len(validation_errs)} validation error(s) total", file=sys.stderr)
    if unknown_ids:
        print(f"{len(unknown_ids)} unknown symbol id(s) in responses "
              f"(first 5: {unknown_ids[:5]})", file=sys.stderr)

    out_path.write_text(json.dumps(inv, indent=2), encoding="utf-8")
    print(f"wrote {out_path} — tier2 applied to {applied} symbol(s)")
    return 0 if not validation_errs else 1


# ---------- main ----------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_prompt = sub.add_parser("prompt", help="Emit enrichment prompts")
    p_prompt.add_argument("inventory", type=Path)
    p_prompt.add_argument("-o", "--output-dir", type=Path, default=Path("clean-room/enrichment-prompts"))
    p_prompt.add_argument("--chunk-size", type=int, default=50)

    p_apply = sub.add_parser("apply", help="Merge response(s) back into inventory")
    p_apply.add_argument("inventory", type=Path)
    p_apply.add_argument("responses", nargs="+", type=Path)
    p_apply.add_argument("-o", "--output", type=Path, default=None,
                         help="Output path (default: overwrites inventory)")

    args = ap.parse_args()

    if args.cmd == "prompt":
        if not args.inventory.is_file():
            print(f"inventory not found: {args.inventory}", file=sys.stderr)
            return 2
        return emit_prompts(args.inventory, args.output_dir, args.chunk_size)

    if args.cmd == "apply":
        if not args.inventory.is_file():
            print(f"inventory not found: {args.inventory}", file=sys.stderr)
            return 2
        for rp in args.responses:
            if not rp.is_file():
                print(f"response not found: {rp}", file=sys.stderr)
                return 2
        out = args.output or args.inventory
        return apply_responses(args.inventory, args.responses, out)

    return 2


if __name__ == "__main__":
    sys.exit(main())
