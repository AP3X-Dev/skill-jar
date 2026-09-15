# Authoring, repair, and the manifest

## 1. Manifest schema

```json
{
  "title": "Project Architecture Atlas",
  "eyebrow_brand": "Project",
  "eyebrow": "Architecture Atlas · Planning baseline 0.1.0",
  "version_label": "v1.0 · 2026-09-14",
  "pill": "Architecture reference",
  "headline": "The platform, drawn once",
  "lede": "One or two sentences on what the page holds and how to read it.",
  "accent": "blue",
  "facts": [ { "label": "Diagrams", "value": "19" }, { "label": "Logins for a rep", "value": "1", "accent": true } ],
  "footer_left": "Internal reference · source documents",
  "footer_right": "Accent · signal blue",
  "groups": [
    {
      "title": "Boundaries and identity",
      "short": "Boundaries",
      "sources": "documents 01, 02, 05",
      "diagrams": [
        {
          "id": "d1",
          "title": "Platform and provider boundaries",
          "source": "05 §1",
          "new": false,
          "caption": "<b>What it settles.</b> One or two sentences, facts from the source only.",
          "spec": "work/d1.workflow.json",
          "archify_html": "work/build/d1.html",
          "mermaid": "work/d1.mmd",
          "quality": "showcase",
          "accent_card": false
        }
      ]
    }
  ]
}
```

`accent` is one of `blue`, `violet`, `green`, `orange`. `spec` is the diagram specification the builder delivers with the vendored renderer into `--build-dir`; `archify_html` may point at an already delivered file instead (it wins when present); when neither exists the builder embeds the `mermaid` file inside `<pre class="mermaid">` with a dark init block. `caption` may contain `<b>`, `<code>`, `<em>`, `<span class="tag">`. `quality` is informational and appears in the report. Exactly one diagram sets `accent_card: true`; the build fails otherwise. Ids are `d` plus an integer and become the panel anchors.

## 2. Mermaid to diagram spec

Schemas live in `vendor/archify/schemas/` (read `common.schema.json` plus the one for your type) and a worked example of each type in `vendor/archify/examples/`. Validate while authoring with `node vendor/archify/bin/archify.mjs validate <type> <spec.json> --quality showcase --json`; the report names the failing subject and supported fixes. Change only the diagnosed subject, one geometry control per repair; if two rounds do not reduce the error count, let the builder fall back to standard and say so. Then:

| Mermaid | Spec type | Constraints learned in practice |
|---|---|---|
| `sequenceDiagram` | `sequence` | Self-messages (`A->>A`) fail layout: turn each into a `note` on the adjacent arrow or a card item. `Note over` becomes a note or a card. Set `meta.column_fit: "spread"` when participant labels do not fit the fixed boxes. Numbered steps survive as label prefixes. |
| `flowchart` with lanes or decisions | `workflow` | Six fixed column centers (about 88, 220, 300, 430, 500, 625 in a 640px lane); `meta.viewBox` does not rescale them. Columns 1 and 2, and 3 and 4, cannot both hold nodes in one lane. Labels never wrap: the validator budgets about 6.8px per character but rendered glyphs are closer to 8.5px; split long labels into `label` plus `sublabel`. Decision diamonds become a node carrying the question and two labeled edges. Two subgraphs such as "today" and "target" work well as two phase bands. |
| `erDiagram` | `architecture` | Entities are `database` components; relationship verbs become connection labels; group with two boundaries. Entities shared by both sides sit outside both boundaries rather than being duplicated. |
| Component or repository maps | `architecture` | Keep at most 12 primary nodes; merge only sibling boxes inside one boundary and list every merge. Two sources inside one boundary each feeding two consumers is non-planar: accept `standard` and say why. Set `brand` only for an exact built-in match. |
| Linear pipelines | `dataflow` | Fixed stage pitch of about 215px regardless of `viewBox`; nodes at most about 130px wide; flow labels short. |
| `stateDiagram` | `lifecycle` | Phase centers fixed at 94, 248, 402, 556, 710; bands drawn at y 112, 264, 436 unconditionally; minimum height 566. Put transition labels below the rail (`labelDy` about 50) and shorten them; a recoverable state is `failure` type with a real transition back. |
| Build orders and dense dependency graphs | `architecture` with region rows and `security-group` bands | Workflow cannot hold two nodes in one lane cell. Emphasize the main chain with `variant: "emphasis"`; components have no variant, so use `type: "security"` plus a tag for blockers. |

Always: `meta.animation: "trace"`, `meta.quality_profile: "showcase"`; omit `visual_preset`, `subtitle`, `legend`, `views`. Preserve exact identifiers (issue ids, paths, environment variables) in label, sublabel, or tag; never drop an edge silently. Two or three `cards` drawn from the caption. The vendored renderer runs on Node 18 or newer with no install. Desktop-readability gate: `9 × 930 / viewBoxWidth ≥ 6`, so architecture viewBox width stays at or below about 1390 without sublabel shrink.

## 3. Overlap symptoms and cures

| Symptom | Cause | Cure |
|---|---|---|
| Label runs into the small glyph in every box's corner | archify stamps a role glyph top-left; full-width labels collide | The builder hides `.semantic-sigil`; color and legend carry the role. |
| Labels wider than the validator allowed | SVG text set in a wider face than archify measured | The builder forces JetBrains Mono on `svg text`. |
| Boundary boxes render as heavy black blocks | `.c-region` has no rule outside archify's presets | The builder defines `.c-region`, `.c-phase`, `.c-group` as hairlines. |
| A node sits on a lane border | wide node at column 0 or the last column | Move one column inward or narrow the node. |
| An edge cuts through a band title | vertical drop at the band's title x | Put source and target in the same column, or route right first, then down. |
| Transition label on a state box | lifecycle labels default above the rail | `labelDy` below the rail; shorten; move detail to cards. |
| Large empty band at the bottom of a lifecycle | oversized viewBox | Reduce `meta.viewBox` height toward the 566 minimum. |
| All arrowheads look the same or ids collide | many SVGs share `#arrowhead`, `#grid` | The builder namespaces every `id`, `url(#…)`, `href="#…"`, and `aria-labelledby` per diagram. |
| Garbled arrows and dots in a local preview only | preview server without a charset header | Use `scripts/serve.py`; the file bytes are UTF-8. |

## 4. Inspection loop

1. Build. Read the report: `errors`, `duplicate_ids`, `unresolved_url_refs`, `svg_classes_without_rule` must all be empty; `fallback` lists any diagram still rendered from Mermaid.
2. `python scripts/serve.py 8766 out/` and open the standalone file in the Playwright MCP at 1440 by 1000.
3. In one `browser_run_code_unsafe` call, loop every diagram id: scroll `#<id> .diagram` into view and screenshot it to `shots/<id>.png`. Also open one Expand view, screenshot, zoom twice, screenshot, press Escape, and assert the SVG returned to its panel and `document.documentElement.scrollWidth <= window.innerWidth`.
4. Read every image. Name each overlap precisely: which label, which box or line, which band.
5. Send the repair to the agent that authored that spec with the exact symptom and the required outcome. It re-validates at showcase and re-delivers to the same path.
6. Rebuild, re-shoot only the repaired panels, then publish. Stop the server and delete any `.playwright-mcp` folder that landed in a repository.

## 5. Fan-out pattern

For more than about six diagrams, launch one agent per diagram type with: the vendored renderer path, `vendor/archify/schemas/common.schema.json` plus the schema and example for its type only; the list of `.mmd` files and spec output paths; the constraints table above; the validate command; the instruction to write only its own spec files and to report spec path, quality reached in validation, and every merge, shortening, or moved note. The builder does the delivery. Repairs go back to the same agent by name.

## 6. Outputs

`--artifact` writes the body starting at `<title>`, for hosts that add the document head. `--standalone` wraps the same body in a complete document with charset and viewport, for `docs/`. Commit the manifest, the specs, and the Mermaid sources beside the standalone file so the page can be rebuilt; delivered HTML files are about 700KB each and are build products, not sources.
