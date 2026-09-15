---
name: diagram-atlas
description: "Build one dark, self-contained 'architecture atlas' web page that embeds many diagrams as animated, replayable, expandable panels, each with a source label and a 'what it settles' caption, from Mermaid sources or diagram specs. Standalone: it vendors the MIT archify renderer and its own complete visual system (near-black surfaces, four inks, hairline rules, one accent, Geist and Geist Mono), so it needs only Python 3 and Node 18+, no other skill, brand guide, or npm install. Use when a team wants all of a project's architecture diagrams on one page, an animated version of a Mermaid diagram set, a diagrams page in a restrained dark editorial look, or to regenerate or extend an existing atlas. NOT for a single diagram (render it with the vendored renderer directly) or for light-theme or brand-specific pages."
---

# Diagram Atlas

One page, many diagrams. Each panel is a validated SVG rendered by the vendored archify engine (`vendor/archify`, MIT), set inside a restrained dark shell: two background tones, four inks, hairline rules, one chromatic accent, Geist for voice and Geist Mono for structure. Traces animate once when a panel scrolls into view and replay on demand. Every panel expands to a full-screen view with zoom and drag-to-pan. The full visual system is specified in [references/design-system.md](references/design-system.md); nothing outside this folder is required to reproduce the look or the diagrams.

**Output:** an artifact body (starts at `<title>`, for hosts that add the document head), a standalone HTML file (complete document, for `docs/`), and a build report that must show zero errors, zero duplicate ids, zero unresolved marker references, zero unstyled SVG classes, exactly one accent card, and the quality each diagram delivered at.

## Quick start

```bash
# 1. Pull Mermaid blocks out of a markdown or HTML file: one .mmd per diagram + a manifest skeleton
python scripts/extract_mermaid.py architecture/05-DIAGRAMS.md --out work/ --source-label 05

# 2. Author one diagram spec per .mmd (type rules in references/authoring-and-repair.md §2); name it in the manifest as "spec"
#    Validate while authoring:  node vendor/archify/bin/archify.mjs validate <type> work/d1.<type>.json --quality showcase --json

# 3. Fill work/manifest.json (title, lede, facts, groups, per-diagram source and caption), then build.
#    The builder delivers every spec itself (showcase, then standard on failure) and assembles the page.
python scripts/build_atlas.py work/manifest.json --build-dir work/build --artifact out/atlas.artifact.html --standalone out/atlas.html

# 4. Inspect every panel (references/authoring-and-repair.md §4), repair specs, rebuild, ship
```

Rebuild the worked example any time: `python scripts/build_atlas.py templates/manifest.example.json --build-dir /tmp/b --standalone /tmp/atlas.html` (nineteen diagrams, about fifteen seconds on Node 20).

## Operating contract

1. **Collect.** `extract_mermaid.py` writes `dNN.mmd` files with title and caption comments and a manifest skeleton. Add new diagrams as `.mmd` files by hand. Group them in reading order; the group numbers on the page are that order and nothing else.
2. **Author.** One spec per diagram following the type table in the authoring reference. More than about six diagrams: fan out to subagents by diagram type, each with only its files, the vendored renderer path, and the constraints table.
3. **Deliver.** The builder runs `deliver` for every `spec` at `showcase`, falls back to `standard` only if showcase fails, and records the achieved quality per diagram. A manifest `quality` that disagrees with the delivered quality is an error, so a fallback is never silent.
4. **Build.** `build_atlas.py` lifts only the `<svg>` from each delivered file, namespaces every id and marker reference per diagram, applies the semantic-class remap from the design system, hides the renderer's corner glyphs, forces the measured monospace on SVG text, adds Replay and Expand and the viewer dialog. A diagram with neither spec nor delivered file falls back to its Mermaid block with a dark init.
5. **Inspect.** Serve with `scripts/serve.py`, screenshot each `#dNN .diagram` at 1440 wide, read every image, name each overlap precisely, and repair the spec. Never hand-edit an SVG.
6. **Ship.** Publish the artifact body; commit the standalone copy under `docs/` together with the manifest and the specs so the page can be rebuilt. Delivered HTML files are build products, about 700KB each; do not commit them.

## Rules that keep it honest

- The spec is the source; the SVG is a build product. Fix specs, not output.
- Exactly one accent card per page. The builder fails otherwise.
- Every caption claim comes from the source document the panel names.
- A `standard`-quality diagram is labeled as such in the manifest and the report; showcase is the bar.
- The Mermaid in the source document stays the editable record; the atlas is a presentation copy and says so on the page.
- Files under `vendor/archify` are not edited. Upgrade by replacing the folder and rebuilding the example.

## Bundled material

- [references/design-system.md](references/design-system.md): the complete visual specification, tokens, type, surfaces, motion, and the SVG semantic-class remap.
- [references/authoring-and-repair.md](references/authoring-and-repair.md): manifest schema, Mermaid-to-spec type rules and renderer constraints, overlap symptoms and cures, inspection loop, fan-out pattern.
- `scripts/build_atlas.py`, `scripts/extract_mermaid.py`, `scripts/serve.py`.
- `vendor/archify/`: the diagram renderer (MIT, provenance in `vendor/archify/VENDORED.md`). Node 18 or newer, no install.
- `templates/manifest.example.json` with `templates/example/specs` and `templates/example/mermaid`: a complete nineteen-diagram worked example.
