"""Extract Mermaid blocks from a markdown or HTML file into one .mmd per diagram plus a manifest skeleton.

Usage: python extract_mermaid.py <source.md|.html> --out <dir> [--prefix d] [--source-label "05"]
Markdown: each ```mermaid fence becomes a diagram; the nearest preceding heading is the title;
          the first paragraph after the fence is the caption.
HTML:     each <pre class="mermaid"> becomes a diagram; the nearest preceding h2/h3 is the title.
"""
import argparse, json, pathlib, re, html as htmlmod

ap = argparse.ArgumentParser()
ap.add_argument("src"); ap.add_argument("--out", required=True); ap.add_argument("--prefix", default="d")
ap.add_argument("--source-label", default="", help="document reference to prefix each panel's source, e.g. '05'")
a = ap.parse_args()
src = pathlib.Path(a.src); out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
text = src.read_text(encoding="utf-8")
diagrams = []
if src.suffix.lower() in (".md", ".markdown"):
    parts = re.split(r"(^#{1,3} .+$)", text, flags=re.M)
    heading = ""
    for chunk in parts:
        if re.match(r"^#{1,3} ", chunk):
            heading = re.sub(r"^#+\s*", "", chunk).strip(); continue
        for m in re.finditer(r"```mermaid\n(.*?)```\s*\n(?:\n)?([^\n#][^\n]*)?", chunk, re.S):
            diagrams.append({"title": heading, "body": m.group(1).strip(), "caption": (m.group(2) or "").strip()})
else:
    for m in re.finditer(r"<h[23][^>]*>(.*?)</h[23]>.*?<pre class=\"mermaid\">\s*(.*?)</pre>", text, re.S):
        title = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        body = re.sub(r"%%\{init.*?\}%%\s*", "", htmlmod.unescape(m.group(2)), flags=re.S).strip()
        diagrams.append({"title": title, "body": body, "caption": ""})

manifest = {"title": src.stem.replace("-", " ").title(), "eyebrow": "", "version_label": "", "pill": "Architecture reference",
            "headline": "", "lede": "", "accent": "blue", "facts": [], "footer_left": "", "footer_right": "",
            "groups": [{"title": "Diagrams", "sources": a.source_label, "diagrams": []}]}
for i, d in enumerate(diagrams, 1):
    did = f"{a.prefix}{i}"
    (out / f"{did}.mmd").write_text(f"# {d['title']}\n# caption: {d['caption']}\n{d['body']}\n", encoding="utf-8", newline="\n")
    kind = d["body"].split()[0] if d["body"] else ""
    manifest["groups"][0]["diagrams"].append({
        "id": did, "title": d["title"], "source": (a.source_label + f" §{i}").strip(), "new": False,
        "caption": f"<b>What it settles.</b> {d['caption']}".strip(), "archify_html": f"{did}.html",
        "mermaid": f"{did}.mmd", "quality": "", "accent_card": False, "mermaid_kind": kind})
(out / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
print(f"{len(diagrams)} diagrams -> {out}/{a.prefix}N.mmd and {out}/manifest.json")
