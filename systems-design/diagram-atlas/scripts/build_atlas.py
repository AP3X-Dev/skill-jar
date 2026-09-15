"""Build the atlas page from a manifest.

Usage:
  python build_atlas.py manifest.json [--artifact out/atlas.artifact.html] [--standalone out/atlas.html]
                        [--base DIR] [--build-dir DIR] [--no-deliver] [--node node]

Relative paths in the manifest resolve against --base (default: the manifest's directory).
Each diagram may name `spec` (an archify JSON) and/or `archify_html` (an already delivered file).
When `archify_html` is missing and `spec` is present, the vendored renderer (vendor/archify, MIT) delivers
the spec into --build-dir (default <base>/build): showcase first, then standard if showcase fails; the
quality achieved is written into the report. No other skill or npm install is required; Node 18+ only.
Diagrams with neither fall back to their Mermaid file inside <pre class="mermaid">.
The artifact output starts at <title> (the Artifact host adds the document head).
The standalone output is a complete HTML document for docs/ or any web server.
"""
import argparse, json, pathlib, re, sys, subprocess, shutil, html as htmlmod

VENDOR = pathlib.Path(__file__).resolve().parent.parent / "vendor" / "archify" / "bin" / "archify.mjs"
TYPES = ("architecture", "workflow", "sequence", "dataflow", "lifecycle")


def spec_type(spec_path):
    try:
        return json.loads(spec_path.read_text(encoding="utf-8")).get("diagram_type")
    except Exception:
        return None


def deliver(spec_path, out_html, node="node", bin_path=None):
    """Run the vendored archify deliver. Returns (quality, summary) or raises."""
    bin_path = pathlib.Path(bin_path) if bin_path else VENDOR
    if not bin_path.exists():
        raise FileNotFoundError(f"archify renderer not found at {bin_path}")
    dtype = spec_type(spec_path)
    if dtype not in TYPES:
        raise ValueError(f"{spec_path}: diagram_type must be one of {TYPES}, got {dtype!r}")
    out_html.parent.mkdir(parents=True, exist_ok=True)
    last = None
    for quality in ("showcase", "standard"):
        cmd = [node, str(bin_path), "deliver", dtype, str(spec_path), str(out_html), "--quality", quality, "--json"]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(bin_path.parent.parent))
        last = (r.returncode, (r.stdout or "")[-800:], (r.stderr or "")[-800:])
        if r.returncode == 0 and out_html.exists():
            return quality, last[1]
    raise RuntimeError(f"deliver failed for {spec_path.name}: rc={last[0]} stdout={last[1]} stderr={last[2]}")

ACCENTS = {
    "blue":   ("#5b8cff", "#9bb6ff", "#2d4a8a", "91,140,255"),
    "violet": ("#7A5AE0", "#a98cf0", "#3d2f80", "122,90,224"),
    "green":  ("#1F8A5B", "#5bb98a", "#0f4a30", "31,138,91"),
    "orange": ("#F06000", "#f5924d", "#843500", "240,96,0"),
}

CSS = r'''
:root{
  --bg:#070809; --bg-2:#0a0c0e; --panel:#0e1114; --panel-2:#101418;
  --ink:#f3f5f7; --ink-2:#c4cad2; --muted:#8b9099; --faint:#565b63;
  --accent:@ACCENT@; --accent-2:@ACCENT2@; --accent-dim:@ACCENTDIM@;
  --accent-glow:rgba(@RGB@,.30); --accent-soft:rgba(@RGB@,.10); --accent-border:rgba(@RGB@,.24);
  --rule:rgba(255,255,255,.07); --rule-strong:rgba(255,255,255,.13);
  --font:'Geist',-apple-system,'Segoe UI',sans-serif; --mono:'Geist Mono',ui-monospace,monospace;
  --radius:18px; --radius-lg:24px; --radius-btn:14px; --radius-pill:100px;
  color-scheme:dark;
}
*{box-sizing:border-box}
html{background:var(--bg)}
body{margin:0;background:var(--bg);color:var(--ink-2);font-family:var(--font);font-size:15px;line-height:1.45;padding-block:0 120px;padding-inline:clamp(16px,6vw,120px);position:relative;overflow-x:hidden}
body::before{content:"";position:absolute;inset:0 0 auto 0;height:720px;pointer-events:none;
  background-image:linear-gradient(var(--rule) 1px,transparent 1px),linear-gradient(90deg,var(--rule) 1px,transparent 1px);
  background-size:76px 76px;-webkit-mask-image:linear-gradient(#000,transparent);mask-image:linear-gradient(#000,transparent)}
body::after{content:"";position:absolute;top:-360px;left:50%;width:1100px;height:640px;transform:translateX(-50%);pointer-events:none;
  background:radial-gradient(ellipse at center,var(--accent-glow),transparent 62%);filter:blur(10px)}
a{color:var(--accent-2)}
.eyebrow,.src,.tag,.facts,nav.index h2,.group span,.frame-top,.frame-bottom{font-family:var(--mono);text-transform:uppercase;letter-spacing:.16em;font-weight:500}
.frame-top{position:relative;z-index:1;max-width:1280px;margin:0 auto;display:flex;justify-content:space-between;gap:16px;padding-block:40px 0;font-size:10px;color:var(--faint)}
.frame-top b{color:var(--muted);font-weight:500}
header.masthead{position:relative;z-index:1;max-width:1280px;margin:0 auto;padding-block:56px 40px}
.pill{display:inline-flex;align-items:center;gap:8px;padding:6px 14px;border:1px solid var(--rule);border-radius:var(--radius-pill);font-family:var(--mono);font-size:10px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);background:linear-gradient(180deg,rgba(255,255,255,.028),rgba(255,255,255,.004))}
.pill::before{content:"";width:7px;height:7px;border-radius:50%;background:var(--accent);box-shadow:0 0 10px var(--accent)}
h1{font-weight:600;font-size:clamp(40px,5.2vw,74px);line-height:1.02;letter-spacing:-.025em;color:var(--ink);margin:22px 0 22px;text-wrap:balance;max-width:20ch}
.lede{max-width:64ch;color:var(--muted);font-size:clamp(16px,1.35vw,20px);line-height:1.45;font-weight:300;margin:0}
.facts{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:0 28px;margin-top:40px;border-top:1px solid var(--rule);padding-top:18px;font-size:10px;color:var(--faint);letter-spacing:.14em}
.facts div{display:flex;flex-direction:column;gap:6px;padding-block:6px 14px}
.facts b{font-family:var(--font);font-weight:600;font-size:22px;letter-spacing:-.02em;color:var(--ink);text-transform:none}
.facts b.acc{color:var(--accent)}
.wrap{position:relative;z-index:1;max-width:1280px;margin:0 auto;display:grid;grid-template-columns:230px minmax(0,1fr);gap:52px;padding-top:12px}
nav.index{position:sticky;top:20px;align-self:start;font-size:13px}
nav.index h2{font-size:10px;color:var(--accent);margin:22px 0 8px;letter-spacing:.18em}
nav.index h2:first-child{margin-top:0}
nav.index a{display:block;color:var(--muted);text-decoration:none;padding:4px 0 4px 12px;border-left:1px solid var(--rule);font-weight:400}
nav.index a:hover,nav.index a:focus-visible{color:var(--ink);border-left-color:var(--accent);outline:none}
main{min-width:0;display:flex;flex-direction:column;gap:24px}
.group{margin:44px 0 -2px;display:flex;flex-direction:column;gap:8px}
.group .num{font-family:var(--mono);font-size:10px;letter-spacing:.18em;text-transform:uppercase;color:var(--accent);font-weight:500}
.group .ttl{font-weight:600;font-size:clamp(24px,2.4vw,34px);letter-spacing:-.025em;color:var(--ink);line-height:1.1}
.group span{font-size:10px;color:var(--faint);letter-spacing:.14em}
figure.panel{margin:0;position:relative;border:1px solid var(--rule);border-radius:var(--radius);padding:36px 38px 30px;
  background:linear-gradient(180deg,rgba(255,255,255,.028),rgba(255,255,255,.004)),var(--panel)}
figure.panel.accent{border-color:var(--accent-border);
  background:radial-gradient(ellipse at top,var(--accent-soft),transparent 55%),linear-gradient(180deg,rgba(255,255,255,.028),rgba(255,255,255,.004)),var(--panel);
  box-shadow:0 0 0 1px var(--accent-border),0 30px 80px -40px var(--accent-glow)}
figure.panel header{display:flex;flex-wrap:wrap;align-items:baseline;justify-content:space-between;gap:8px 18px;margin-bottom:22px;padding-bottom:16px;border-bottom:1px solid var(--rule)}
figure.panel h3{font-weight:600;font-size:22px;letter-spacing:-.025em;color:var(--ink);margin:0}
.src{font-size:10px;color:var(--faint);letter-spacing:.14em}
.src.new{color:var(--accent)}
.diagram{overflow-x:auto;padding:4px 0 2px;border-radius:var(--radius-btn)}
.diagram pre.mermaid{margin:0;background:transparent;font-family:var(--mono);font-size:12.5px;color:var(--ink-2)}
figcaption{margin-top:22px;padding-top:16px;border-top:1px solid var(--rule);max-width:72ch;color:var(--muted);font-size:14px;line-height:1.5}
figcaption b{color:var(--ink);font-weight:500}
.tag{display:inline-flex;align-items:center;gap:7px;font-size:10px;padding:4px 10px;border-radius:var(--radius-pill);border:1px solid var(--rule);color:var(--muted)}
.tag::before{content:"";width:6px;height:6px;border-radius:50%;background:var(--accent);box-shadow:0 0 8px var(--accent)}
.tag.retired::before{background:var(--faint);box-shadow:none}
code{font-family:var(--mono);font-size:.9em;color:var(--ink);background:var(--panel-2);border:1px solid var(--rule);padding:1px 6px;border-radius:6px}
em{color:var(--ink);font-style:normal;font-weight:500}
.frame-bottom{position:relative;z-index:1;max-width:1280px;margin:80px auto 0;padding-top:20px;border-top:1px solid var(--rule);display:flex;justify-content:space-between;gap:16px;font-size:10px;color:var(--faint)}
@media (max-width:900px){.wrap{grid-template-columns:1fr;gap:24px}nav.index{position:static;display:flex;flex-wrap:wrap;gap:6px 16px}nav.index h2{flex-basis:100%;margin:12px 0 2px}nav.index a{border-left:0;padding:2px 0}figure.panel{padding:24px 20px 20px}}
@media (prefers-reduced-motion:no-preference){nav.index a{transition:color .15s,border-color .15s}}
/* renderer semantic vocabulary recolored to the atlas system: accent family, four inks, one rose for security */
.archify{
  --grid:rgba(255,255,255,.045); --text:#f3f5f7; --text-muted:#8b9099; --text-dim:#565b63; --mask:#0e1114;
  --lane-fill:rgba(255,255,255,.018); --lane-stroke:rgba(255,255,255,.10);
  --arrow:#6b727c; --arrow-emphasis:var(--accent);
  --frontend-fill:rgba(@RGB@,.14);  --frontend-stroke:var(--accent);
  --backend-fill:rgba(@RGB@,.08);   --backend-stroke:var(--accent-2);
  --database-fill:rgba(196,202,210,.07); --database-stroke:#c4cad2;
  --cloud-fill:rgba(139,144,153,.08);    --cloud-stroke:#8b9099;
  --security-fill:rgba(255,138,128,.10); --security-stroke:#ff8a80;
  --messagebus-fill:rgba(@RGB@,.22);  --messagebus-stroke:var(--accent-2);
  --external-fill:rgba(255,255,255,.03); --external-stroke:#6b727c;
}
.archify svg{display:block;width:100%;height:auto;max-width:100%}
.archify svg text{font-family:'JetBrains Mono',ui-monospace,monospace}
.c-grid{stroke:var(--grid);fill:none}
.c-mask{fill:var(--mask);stroke:none}
.c-frontend{fill:var(--frontend-fill);stroke:var(--frontend-stroke)}
.c-backend{fill:var(--backend-fill);stroke:var(--backend-stroke)}
.c-database{fill:var(--database-fill);stroke:var(--database-stroke)}
.c-cloud{fill:var(--cloud-fill);stroke:var(--cloud-stroke)}
.c-security{fill:var(--security-fill);stroke:var(--security-stroke)}
.c-messagebus{fill:var(--messagebus-fill);stroke:var(--messagebus-stroke)}
.c-external{fill:var(--external-fill);stroke:var(--external-stroke)}
.c-security-group{fill:transparent;stroke:var(--security-stroke);stroke-dasharray:4,4}
.c-lane{fill:var(--lane-fill);stroke:var(--lane-stroke);stroke-dasharray:6,6}
.c-region{fill:rgba(255,255,255,.018);stroke:rgba(255,255,255,.12)}
.c-phase{fill:rgba(@RGB@,.04);stroke:rgba(@RGB@,.22);stroke-dasharray:6,6}
.c-group{fill:rgba(255,255,255,.012);stroke:rgba(255,255,255,.10);stroke-dasharray:4,4}
.t-primary{fill:var(--text)} .t-muted{fill:var(--text-muted)} .t-dim{fill:var(--text-dim)}
.t-frontend{fill:var(--frontend-stroke)} .t-backend{fill:var(--backend-stroke)} .t-database{fill:var(--database-stroke)}
.t-cloud{fill:var(--cloud-stroke)} .t-security{fill:var(--security-stroke)} .t-messagebus{fill:var(--messagebus-stroke)} .t-external{fill:var(--external-stroke)}
svg .semantic-sigil{display:none}
svg .brand-mark{pointer-events:none} svg .brand-mark-badge{fill:#fff;stroke:none}
svg .brand-mark-frame{fill:none;stroke:#565b63;stroke-width:.8;vector-effect:non-scaling-stroke}
.a-default{stroke:var(--arrow);fill:none} .a-emphasis{stroke:var(--arrow-emphasis);fill:none}
.a-security{stroke:var(--security-stroke);fill:none;stroke-dasharray:5,5} .a-dashed{stroke:var(--database-stroke);fill:none;stroke-dasharray:4,4}
.m-default{fill:var(--arrow)} .m-emphasis{fill:var(--arrow-emphasis)} .m-security{fill:var(--security-stroke)} .m-dashed{fill:var(--database-stroke)}
.panel.is-live svg[data-animation="trace"] [data-animate="edge"],.viewer-stage.is-live svg[data-animation="trace"] [data-animate="edge"]{animation:archify-edge-flow 2.4s linear 1;animation-delay:calc(var(--step,0) * 160ms)}
.panel.is-live svg[data-animation="trace"] [data-animate="node"],.viewer-stage.is-live svg[data-animation="trace"] [data-animate="node"]{animation:archify-node-pulse 3.6s ease-in-out 1;animation-delay:calc(var(--step,0) * 160ms)}
@media (prefers-reduced-motion:reduce){.panel.is-live svg[data-animation="trace"] [data-animate],.viewer-stage.is-live svg[data-animation="trace"] [data-animate]{animation:none !important}}
@keyframes archify-edge-flow{0%{stroke-dasharray:10 8;stroke-dashoffset:54;opacity:.42}88%{stroke-dasharray:10 8;stroke-dashoffset:0;opacity:1}99.9%{stroke-dasharray:10 8;stroke-dashoffset:0;opacity:1}100%{stroke-dashoffset:0;opacity:1}}
@keyframes archify-node-pulse{0%,72%,100%{filter:none;stroke-width:1.5}18%,36%{filter:drop-shadow(0 0 8px var(--arrow-emphasis));stroke-width:2.4}}
.panel-actions{margin-left:auto;display:flex;gap:8px;flex-wrap:wrap}
.replay,.expand{font-family:var(--mono);font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);background:transparent;border:1px solid var(--rule);border-radius:var(--radius-pill);padding:5px 12px;cursor:pointer}
.replay:hover,.replay:focus-visible,.expand:hover,.expand:focus-visible{color:var(--ink);border-color:var(--accent-border);outline:none}
.replay::before{content:"";display:inline-block;width:6px;height:6px;border-radius:50%;background:var(--accent);box-shadow:0 0 8px var(--accent);margin-right:8px;vertical-align:middle}
.diagram.archify{padding:10px 0 4px}
dialog.viewer{border:0;padding:0;margin:0;max-width:100vw;max-height:100vh;width:100vw;height:100vh;background:transparent;color:var(--ink-2)}
dialog.viewer::backdrop{background:rgba(7,8,9,.92);backdrop-filter:blur(6px)}
.viewer-frame{position:relative;display:grid;grid-template-rows:auto 1fr;height:100vh;padding:clamp(12px,2vw,28px)}
.viewer-head{display:flex;align-items:center;gap:14px;flex-wrap:wrap;padding-bottom:14px;border-bottom:1px solid var(--rule)}
.viewer-head h2{font-weight:600;font-size:clamp(18px,1.8vw,26px);letter-spacing:-.025em;color:var(--ink);margin:0;flex:1 1 auto}
.viewer-head .src{flex-basis:100%;order:3}
.viewer-tools{display:flex;gap:8px;align-items:center}
.viewer-tools button{font-family:var(--mono);font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);background:transparent;border:1px solid var(--rule);border-radius:var(--radius-pill);padding:6px 12px;cursor:pointer;min-width:38px}
.viewer-tools button:hover,.viewer-tools button:focus-visible{color:var(--ink);border-color:var(--accent-border);outline:none}
.viewer-tools .zoom-level{font-family:var(--mono);font-size:10px;color:var(--faint);letter-spacing:.1em;min-width:44px;text-align:center}
.viewer-stage{overflow:auto;padding:18px 4px 4px;cursor:grab;-webkit-overflow-scrolling:touch}
.viewer-stage.dragging{cursor:grabbing;user-select:none}
.viewer-stage .diagram.archify{padding:0;width:max(100%, var(--zoom-width, 100%));transition:width .18s ease}
.viewer-stage .diagram.archify svg{width:100%;height:auto}
@media (prefers-reduced-motion:reduce){.viewer-stage .diagram.archify{transition:none}}
'''

JS = r'''
(function(){
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  function play(p){ p.classList.remove('is-live'); void p.offsetWidth; p.classList.add('is-live'); }
  var panels = Array.prototype.filter.call(document.querySelectorAll('figure.panel'), function(p){ return p.querySelector('svg[data-animation="trace"]'); });
  if (!reduce && 'IntersectionObserver' in window){
    var io = new IntersectionObserver(function(entries){
      entries.forEach(function(e){ if (e.isIntersecting && !e.target.dataset.played){ e.target.dataset.played = '1'; play(e.target); io.unobserve(e.target); } });
    }, { threshold: 0.3 });
    panels.forEach(function(p){ io.observe(p); });
  }
  document.addEventListener('click', function(ev){
    var b = ev.target.closest('[data-replay]'); if (!b) return;
    var p = document.getElementById(b.getAttribute('data-replay')); if (p) play(p);
  });
  var dlg = document.getElementById('viewer'), stage = document.getElementById('viewer-stage');
  var title = document.getElementById('viewer-title'), src = document.getElementById('viewer-src'), zoomLabel = document.getElementById('viewer-zoom');
  var home = null, zoom = 1, ZOOMS = [1, 1.25, 1.5, 2, 2.5, 3];
  function applyZoom(){ var el = stage.firstElementChild; if (!el) return; el.style.setProperty('--zoom-width', (zoom * 100) + '%'); zoomLabel.textContent = zoom === 1 ? 'Fit' : Math.round(zoom * 100) + '%'; }
  function openViewer(id){
    var fig = document.getElementById(id); if (!fig || !dlg.showModal) return;
    var dia = fig.querySelector('.diagram.archify'); if (!dia) return;
    home = { fig: fig, next: dia.nextSibling };
    title.textContent = fig.querySelector('h3').textContent;
    var s2 = fig.querySelector('.src'); src.textContent = s2 ? s2.textContent : '';
    stage.appendChild(dia); zoom = 1; applyZoom(); stage.scrollTop = 0; stage.scrollLeft = 0;
    dlg.showModal(); stage.classList.remove('is-live'); void stage.offsetWidth; stage.classList.add('is-live');
  }
  function closeViewer(){
    var dia = stage.firstElementChild;
    if (dia && home){ home.fig.insertBefore(dia, home.next); dia.style.removeProperty('--zoom-width'); }
    home = null; stage.classList.remove('is-live'); if (dlg.open) dlg.close();
  }
  document.addEventListener('click', function(ev){ var b = ev.target.closest('[data-expand]'); if (b) openViewer(b.getAttribute('data-expand')); });
  document.getElementById('viewer-close').addEventListener('click', closeViewer);
  dlg.addEventListener('cancel', function(ev){ ev.preventDefault(); closeViewer(); });
  dlg.addEventListener('click', function(ev){ if (ev.target === dlg) closeViewer(); });
  document.getElementById('viewer-replay').addEventListener('click', function(){ stage.classList.remove('is-live'); void stage.offsetWidth; stage.classList.add('is-live'); });
  dlg.querySelectorAll('[data-zoom]').forEach(function(b){ b.addEventListener('click', function(){
    var dir = parseInt(b.getAttribute('data-zoom'), 10); var i = ZOOMS.indexOf(zoom);
    if (dir === 0) zoom = 1; else zoom = ZOOMS[Math.min(ZOOMS.length - 1, Math.max(0, i + dir))];
    applyZoom();
  }); });
  var drag = null;
  stage.addEventListener('pointerdown', function(e){ if (e.button !== 0) return; drag = { x: e.clientX, y: e.clientY, sl: stage.scrollLeft, st: stage.scrollTop }; stage.classList.add('dragging'); stage.setPointerCapture(e.pointerId); });
  stage.addEventListener('pointermove', function(e){ if (!drag) return; stage.scrollLeft = drag.sl - (e.clientX - drag.x); stage.scrollTop = drag.st - (e.clientY - drag.y); });
  stage.addEventListener('pointerup', function(){ drag = null; stage.classList.remove('dragging'); });
  stage.addEventListener('pointercancel', function(){ drag = null; stage.classList.remove('dragging'); });
})();
'''

DIALOG = '''
<dialog class="viewer" id="viewer" aria-labelledby="viewer-title">
  <div class="viewer-frame">
    <div class="viewer-head">
      <h2 id="viewer-title"></h2>
      <div class="viewer-tools">
        <button type="button" data-zoom="-1" aria-label="Zoom out">&minus;</button>
        <span class="zoom-level" id="viewer-zoom">Fit</span>
        <button type="button" data-zoom="1" aria-label="Zoom in">+</button>
        <button type="button" data-zoom="0">Fit</button>
        <button type="button" id="viewer-replay">Replay trace</button>
        <button type="button" id="viewer-close" aria-label="Close full view">Close &nbsp;Esc</button>
      </div>
      <span class="src" id="viewer-src"></span>
    </div>
    <div class="viewer-stage" id="viewer-stage"></div>
  </div>
</dialog>
'''

MERMAID_INIT = ("%%{init: {'theme':'base','themeVariables':{'background':'#0e1114','primaryColor':'#101418','primaryTextColor':'#f3f5f7',"
                "'primaryBorderColor':'#2a3340','secondaryColor':'#101418','secondaryTextColor':'#f3f5f7','secondaryBorderColor':'#2a3340',"
                "'tertiaryColor':'#0a0c0e','tertiaryTextColor':'#c4cad2','tertiaryBorderColor':'#2a3340','lineColor':'#8b9099','textColor':'#c4cad2',"
                "'mainBkg':'#101418','nodeBorder':'#2a3340','clusterBkg':'#0a0c0e','clusterBorder':'#2a3340','titleColor':'#f3f5f7','edgeLabelBackground':'#0e1114',"
                "'actorBkg':'#101418','actorBorder':'#2a3340','actorTextColor':'#f3f5f7','actorLineColor':'#565b63','signalColor':'#c4cad2','signalTextColor':'#c4cad2',"
                "'labelBoxBkgColor':'#101418','labelBoxBorderColor':'#2a3340','labelTextColor':'#f3f5f7','fontFamily':'Geist Mono, ui-monospace, monospace','fontSize':'12px'}}}%%\n")

FONTS = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600&family=Geist+Mono:wght@400;500&family=JetBrains+Mono:wght@400;500;600;700&display=swap">'


def esc(t): return htmlmod.escape(t, quote=True)

def namespace(svg, prefix):
    ids = set(re.findall(r' id="([^"]+)"', svg))
    for i in sorted(ids, key=len, reverse=True):
        svg = svg.replace(f' id="{i}"', f' id="{prefix}-{i}"').replace(f'url(#{i})', f'url(#{prefix}-{i})').replace(f'href="#{i}"', f'href="#{prefix}-{i}"')
    return re.sub(r'aria-labelledby="([^"]*)"', lambda m: 'aria-labelledby="' + " ".join(f"{prefix}-{t}" for t in m.group(1).split()) + '"', svg)

def load_svg(path):
    doc = path.read_text(encoding="utf-8")
    if "<svg" not in doc: raise ValueError(f"no <svg> in {path}")
    return doc[doc.index("<svg"):doc.index("</svg>") + 6]

def mermaid_body(path):
    body = path.read_text(encoding="utf-8")
    return "\n".join(l for l in body.splitlines() if not l.startswith("# ")).strip()


def build(manifest, base, build_dir=None, do_deliver=True, node="node", archify_bin=None):
    build_dir = pathlib.Path(build_dir) if build_dir else base / "build"
    acc = ACCENTS.get(manifest.get("accent", "blue"), ACCENTS["blue"])
    css = CSS.replace("@ACCENT@", acc[0]).replace("@ACCENT2@", acc[1]).replace("@ACCENTDIM@", acc[2]).replace("@RGB@", acc[3])
    report = {"converted": [], "fallback": [], "errors": [], "delivered": {}}
    accent_cards = [d["id"] for g in manifest["groups"] for d in g["diagrams"] if d.get("accent_card")]
    if len(accent_cards) != 1: report["errors"].append(f"exactly one accent_card required, got {accent_cards}")

    nav, main = [], []
    for gi, g in enumerate(manifest["groups"], 1):
        nav.append(f'  <h2>{esc(g["title"])}</h2>')
        main.append(f'<div class="group"><span class="num">{gi:02d} · {esc(g.get("short", g["title"].split(" and ")[0]))}</span><span class="ttl">{esc(g["title"])}</span><span>{esc(g.get("sources", ""))}</span></div>')
        for d in g["diagrams"]:
            did = d["id"]; nav.append(f'  <a href="#{did}">{esc(d["title"])}</a>')
            src_cls = "src new" if d.get("new") else "src"
            src_txt = ("new · " if d.get("new") else "") + d.get("source", "")
            body, actions = None, ""
            ap = d.get("archify_html")
            if (not ap or not (base / ap).exists()) and d.get("spec") and do_deliver:
                sp = base / d["spec"]
                if sp.exists():
                    try:
                        q, _ = deliver(sp, build_dir / f"{did}.html", node=node, bin_path=archify_bin)
                        ap = str((build_dir / f"{did}.html").relative_to(base)) if str(build_dir).startswith(str(base)) else str(build_dir / f"{did}.html")
                        d["archify_html"] = ap
                        report["delivered"][did] = q
                        if d.get("quality") and d["quality"] != q:
                            report["errors"].append(f"{did}: manifest says quality {d['quality']} but delivered at {q}")
                    except Exception as e:
                        report["errors"].append(f"{did}: {e}")
                else:
                    report["errors"].append(f"{did}: spec not found: {sp}")
            if ap and (base / ap).exists():
                try:
                    svg = namespace(load_svg(base / ap), did).replace("<svg ", '<svg preserveAspectRatio="xMidYMid meet" ', 1)
                    body = f'<div class="diagram archify" data-diagram="{did}">\n{svg}\n</div>'
                    actions = (f'<span class="panel-actions"><button class="replay" type="button" data-replay="{did}">Replay trace</button>'
                               f'<button class="expand" type="button" data-expand="{did}" aria-haspopup="dialog">Expand</button></span>')
                    report["converted"].append(did)
                except Exception as e:
                    report["errors"].append(f"{did}: {e}")
            if body is None:
                mp = d.get("mermaid")
                if not mp or not (base / mp).exists():
                    report["errors"].append(f"{did}: no archify_html and no mermaid"); continue
                body = f'<div class="diagram"><pre class="mermaid">\n{MERMAID_INIT}{esc(mermaid_body(base / mp))}\n</pre></div>'
                report["fallback"].append(did)
            acc_cls = " accent" if d.get("accent_card") else ""
            main.append(f'''<figure class="panel{acc_cls}" id="{did}">
  <header><h3>{esc(d["title"])}</h3><span class="{src_cls}">{esc(src_txt)}</span>{actions}</header>
  {body}
  <figcaption>{d.get("caption", "")}</figcaption>
</figure>''')

    facts = "".join(f'<div><span>{esc(f["label"])}</span><b{" class=\"acc\"" if f.get("accent") else ""}>{esc(str(f["value"]))}</b></div>' for f in manifest.get("facts", []))
    body_html = f'''<title>{esc(manifest["title"])}</title>
{FONTS}
<style>{css}</style>

<div class="frame-top"><span><b>{esc(manifest.get("eyebrow_brand", manifest["title"].split(" ")[0]))}</b> · {esc(manifest.get("eyebrow", ""))}</span><span>{esc(manifest.get("version_label", ""))}</span></div>
<header class="masthead">
  <span class="pill">{esc(manifest.get("pill", "Architecture reference"))}</span>
  <h1>{esc(manifest.get("headline", manifest["title"]))}</h1>
  <p class="lede">{esc(manifest.get("lede", ""))}</p>
  <div class="facts">{facts}</div>
</header>

<div class="wrap">
<nav class="index" aria-label="Diagram index">
{chr(10).join(nav)}
</nav>
<main>
{chr(10).join(main)}
</main>
</div>
{DIALOG}
<script>{JS}</script>
<div class="frame-bottom"><span>{esc(manifest.get("footer_left", ""))}</span><span>{esc(manifest.get("footer_right", ""))}</span></div>
'''
    # report checks
    ids = re.findall(r' id="([^"]+)"', body_html)
    report["duplicate_ids"] = sorted({i for i in ids if ids.count(i) > 1})
    report["unresolved_url_refs"] = sorted({u for u in set(re.findall(r'url\(#([^)]+)\)', body_html)) if f' id="{u}"' not in body_html})
    used = {c for m in re.findall(r'class="([^"]+)"', body_html) for c in m.split() if c.startswith(("c-", "t-", "a-", "m-", "s-"))}
    defined = set(re.findall(r'\.((?:c|t|a|m|s)-[a-z-]+)\s*[{,]', css))
    report["svg_classes_without_rule"] = sorted(used - defined - {"s-frontend", "s-backend", "s-database", "s-cloud", "s-security", "s-messagebus", "s-external"})
    return body_html, report


def standalone(body):
    head_end = body.index("</style>") + len("</style>")
    return ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            + body[:head_end] + '\n<style>[hidden]{display:none!important}img{max-width:100%}</style>\n</head>\n<body>\n' + body[head_end:].lstrip() + '\n</body>\n</html>\n')


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest"); ap.add_argument("--artifact"); ap.add_argument("--standalone"); ap.add_argument("--base")
    ap.add_argument("--build-dir"); ap.add_argument("--no-deliver", action="store_true"); ap.add_argument("--node", default="node")
    ap.add_argument("--archify-bin", help="override the vendored renderer path")
    a = ap.parse_args()
    mpath = pathlib.Path(a.manifest); base = pathlib.Path(a.base).resolve() if a.base else mpath.resolve().parent
    manifest = json.loads(mpath.read_text(encoding="utf-8"))
    body, report = build(manifest, base, build_dir=a.build_dir, do_deliver=not a.no_deliver, node=a.node, archify_bin=a.archify_bin)
    if a.artifact: pathlib.Path(a.artifact).parent.mkdir(parents=True, exist_ok=True); pathlib.Path(a.artifact).write_text(body, encoding="utf-8", newline="\n")
    if a.standalone: pathlib.Path(a.standalone).parent.mkdir(parents=True, exist_ok=True); pathlib.Path(a.standalone).write_text(standalone(body), encoding="utf-8", newline="\n")
    print(json.dumps(report, indent=1))
    sys.exit(1 if report["errors"] or report["duplicate_ids"] or report["unresolved_url_refs"] or report["svg_classes_without_rule"] else 0)
