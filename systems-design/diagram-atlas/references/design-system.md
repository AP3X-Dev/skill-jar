# Atlas visual system

This is the complete specification. A reader with only this file and `scripts/build_atlas.py` can reproduce the page. The system is a dark, near-black surface language: restraint is the aesthetic, one accent, two background tones, and typography doing the work. Swap the accent and the same system carries a different project without redesign.

## 1. Color

Never more than two background tones in one page. Depth comes from hairline borders and low-alpha white gradients, never from a stack of grays. Every chromatic moment on the page is the accent.

| Token | Hex | Role |
|---|---|---|
| `--bg` | `#070809` | base canvas |
| `--bg-2` | `#0a0c0e` | alternate section |
| `--panel` | `#0e1114` | cards |
| `--panel-2` | `#101418` | inset inside a card |
| `--ink` | `#f3f5f7` | headlines |
| `--ink-2` | `#c4cad2` | body |
| `--muted` | `#8b9099` | secondary text |
| `--faint` | `#565b63` | labels, eyebrows |
| `--rule` | `rgba(255,255,255,.07)` | hairlines |
| `--rule-strong` | `rgba(255,255,255,.13)` | emphasized hairlines |

Accent scale, derived from one hex:

| Derived token | Rule | Blue example |
|---|---|---|
| `--accent` | the chosen hex | `#5b8cff` |
| `--accent-2` | tint toward white about 45 percent | `#9bb6ff` |
| `--accent-dim` | shade toward black about 55 percent | `#2d4a8a` |
| `--accent-glow` | accent at 30 percent alpha | `rgba(91,140,255,.30)` |
| `--accent-soft` | accent at 10 percent alpha | `rgba(91,140,255,.10)` |
| `--accent-border` | accent at 24 percent alpha | `rgba(91,140,255,.24)` |

Approved accents and what they signal: blue `#5b8cff` (signal, the default), violet `#7A5AE0` (product, AI), green `#1F8A5B` (finance, growth), orange `#F06000` (trades, energy). Pick one per page. One rose, `#ff8a80`, is reserved for security and error meaning inside diagrams; it is semantic, not a second accent.

Single theme by design. The page paints its own `background` on `html` and `body` and sets `color-scheme: dark`, so it holds on any host ground.

## 2. Typography

Geist carries every headline and paragraph. Geist Mono is reserved for structural text: eyebrows, labels, metric keys, source references, group numbers, and any number the reader might compare. Structural text is always uppercase with wide tracking. That single split is the most recognizable part of the system.

| Role | Face and weight | Tracking | Size |
|---|---|---|---|
| Display | Geist 600 | `-0.025em` | `clamp(40px, 5.2vw, 74px)`, line-height 1.02 |
| Group title | Geist 600 | `-0.025em` | `clamp(24px, 2.4vw, 34px)`, line-height 1.1 |
| Panel title | Geist 600 | `-0.025em` | 22px |
| Lead | Geist 300 | normal | `clamp(16px, 1.35vw, 20px)`, line-height 1.45, color `--muted` |
| Body and captions | Geist 400 | normal | 14 to 15px, line-height 1.45 to 1.5 |
| Eyebrow, label, source | Geist Mono 500, uppercase | `.14em` to `.18em` | 10px |
| Numeral | Geist 600 | `-0.02em` | 22px in the facts row |
| Diagram text | JetBrains Mono | inherited | as authored by archify |

Load from Google Fonts: `Geist:wght@300;400;500;600`, `Geist+Mono:wght@400;500`, `JetBrains+Mono:wght@400;500;600;700`. Declare system fallbacks. Titles set tight and quiet; lead paragraphs sit in muted gray; hierarchy comes from lightness, not size alone. Headline `text-wrap: balance`, max width about 20 characters; lead max 64 characters; captions max 72 characters.

The diagram SVGs use JetBrains Mono, not Geist Mono, because archify measures label widths in that face; a wider face overflows validated boxes.

## 3. Surfaces

A card is a 1px hairline (`--rule`) over a barely-there white gradient, `linear-gradient(180deg, rgba(255,255,255,.028), rgba(255,255,255,.004))` on top of `--panel`, radius 18px, padding about 36px by 38px. Never a lighter gray block.

Exactly one card per page earns the accent treatment: a radial accent wash from the top edge (`radial-gradient(ellipse at top, var(--accent-soft), transparent 55%)`), an accent border (`--accent-border`), and a wide low shadow `0 0 0 1px var(--accent-border), 0 30px 80px -40px var(--accent-glow)`. In the atlas this is the single most important diagram.

Pills are 100px radius with a hairline border, mono uppercase text at 10px, and a 6 to 7px accent dot with `box-shadow: 0 0 8px var(--accent)` in front. Buttons share the pill treatment; hover and focus lift text to `--ink` and border to `--accent-border`. Inline code sits on `--panel-2` with a hairline and 6px radius.

Radii: 18px cards, 24px large panels, 14px buttons, 100px pills. Nothing sharp, nothing round.

## 4. Ambient chrome and layout

Every page carries two ambient layers, near invisible until you look: a 76px hairline grid (`--rule` lines) masked to fade out over the top 720px of the frame, and one wide accent ellipse bleeding in from just above the top edge (`radial-gradient(ellipse, var(--accent-glow), transparent 62%)`, blurred 10px, about 1100 by 640px, centered). Together they replace decoration entirely.

Frame: a top rule row in mono at 10px, faint, with the project on the left and the version and date on the right; a matching bottom rule row. Masthead: pill, headline, lead, then a facts row separated by a hairline, each fact a mono label over a large numeral, with numerals that matter set in the accent. Side gutters `clamp(16px, 6vw, 120px)`; content max width 1280px.

Body: a sticky 230px index on the left listing groups (mono, accent) and panels (muted, hairline left border, accent on hover), and a single column of panels on the right with 24px gaps. Groups are introduced by a two-digit mono number in the accent, the title, and a faint mono note of the source documents. The number is real information: it is the reading order.

Panel anatomy: header row with title, source reference in mono (accent when the diagram is new to the source set), and the Replay and Expand pills on the right; a hairline; the diagram; a hairline; the caption starting with a bold "What it settles." At phone width the index becomes a wrapped row above the panels and panel padding drops to 24px by 20px.

## 5. Motion

Static is the resting state. When a panel is at least 30 percent visible the builder adds `is-live`, which runs two finite animations once: edges draw in with `stroke-dasharray: 10 8` from offset 54 to 0 over 2.4s, staggered 160ms per authored step; nodes pulse once with a drop-shadow in the accent over 3.6s. Replay removes and re-adds the class. `prefers-reduced-motion: reduce` disables both. The expand view reuses the same classes on its stage.

## 6. Expand view

A native `<dialog>` covering the viewport with a 92 percent near-black backdrop and 6px blur. Header: the panel title, then Zoom out, a mono zoom readout (Fit, 125%, 150%, 200%, 250%, 300%), Zoom in, Fit, Replay trace, and Close with the Esc hint, all as pills; the source reference beneath. The stage scrolls, shows a grab cursor, and pans on drag. The panel's own SVG is moved into the stage and moved back on close, so ids stay unique and nothing is cloned.

## 7. SVG semantic-class remap

archify emits class-based SVG. The builder defines these on `.archify` so the diagrams sit in the system rather than on archify's slate palette.

| Class family | Treatment |
|---|---|
| `.c-frontend` | fill accent at 14 percent, stroke `--accent` |
| `.c-backend` | fill accent at 8 percent, stroke `--accent-2` |
| `.c-messagebus` | fill accent at 22 percent, stroke `--accent-2` |
| `.c-database` | fill `rgba(196,202,210,.07)`, stroke `#c4cad2` |
| `.c-cloud` | fill `rgba(139,144,153,.08)`, stroke `#8b9099` |
| `.c-external` | fill `rgba(255,255,255,.03)`, stroke `#6b727c` |
| `.c-security`, `.a-security`, `.m-security` | rose `#ff8a80`, fill at 10 percent, dashed edges |
| `.c-mask` | `--panel` so edges hide behind boxes |
| `.c-grid` | `rgba(255,255,255,.045)` |
| `.c-lane`, `.c-region`, `.c-phase`, `.c-group` | hairline frames at 10 to 12 percent white (phase tinted accent at 4 percent) |
| `.a-default`, `.m-default` | `#6b727c` |
| `.a-emphasis`, `.m-emphasis` | `--accent` |
| `.a-dashed`, `.m-dashed` | `#c4cad2`, dashed |
| `.t-primary`, `.t-muted`, `.t-dim` | `#f3f5f7`, `#8b9099`, `#565b63` |
| `.semantic-sigil` | `display: none`; the corner role glyph collides with full-width labels and the legend already carries the role |

## 8. Do and don't

Do: keep one or two background tones; let mono uppercase labels carry structure; reserve the accent card for the single most important panel; use hairlines and gap for separation before reaching for a box; set numerals in the accent only when they matter.

Don't: introduce a second chromatic color for decoration; build depth from lighter gray fills or heavy shadows; set body copy in mono or headlines in caps; add gradient backgrounds, emoji, or icon-only accents; center everything; round everything.

## 9. Token starter

```css
--bg:#070809; --bg-2:#0a0c0e; --panel:#0e1114; --panel-2:#101418;
--ink:#f3f5f7; --ink-2:#c4cad2; --muted:#8b9099; --faint:#565b63;
--rule:rgba(255,255,255,.07); --rule-strong:rgba(255,255,255,.13);
--accent:#5b8cff; --accent-2:#9bb6ff; --accent-dim:#2d4a8a;
--accent-glow:rgba(91,140,255,.30); --accent-soft:rgba(91,140,255,.10); --accent-border:rgba(91,140,255,.24);
--font:'Geist',-apple-system,'Segoe UI',sans-serif; --mono:'Geist Mono',ui-monospace,monospace;
--radius:18px; --radius-lg:24px; --radius-btn:14px; --radius-pill:100px;
```
