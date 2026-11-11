# /// script
# requires-python = ">=3.10"
# dependencies = ["uharfbuzz"]
# ///
"""Builds assets/hero.svg.

Run with:  uv run scripts/build_hero.py

GitHub shows README images without loading web fonts, so every piece of text
is drawn as outlines from Google Sans Flex / Google Sans Code (both OFL).
The fonts are downloaded once into ~/.cache/hero-fonts.
"""
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlretrieve

import uharfbuzz as hb

# ---- Palette and copy: the parts you are most likely to change -------------
NIGHT = "#141c2b"
NIGHT_RAISED = "#243247"
GLOW = "#34507a"
MUTED = "#9eabc0"
WHITE = "#ffffff"
SPARK = "#ffd166"

EYEBROW = "PROBLEM SOLVER AT HEART"
NAME = "Hugo Romero"
LINE_1 = "Turning business strategy into"
LINE_2 = "AI architecture "
LINE_2_SPARK = "that ships."

W, H = 1000, 320
CYCLE = 9  # seconds

# ---- Fonts ------------------------------------------------------------------
FONTS = {
    "flex": "ofl/googlesansflex/GoogleSansFlex[ROND,opsz,slnt,wdth,wght].ttf",
    "code": "ofl/googlesanscode/GoogleSansCode[wght].ttf",
}
CACHE = Path.home() / ".cache" / "hero-fonts"


def load(key: str) -> hb.Face:
    CACHE.mkdir(parents=True, exist_ok=True)
    target = CACHE / f"{key}.ttf"
    if not target.exists():
        urlretrieve("https://raw.githubusercontent.com/google/fonts/main/" + quote(FONTS[key]), target)
    return hb.Face(target.read_bytes())


FACES = {key: load(key) for key in FONTS}


class PathPen:
    """Collects glyph outlines as SVG path data, scaled and flipped to SVG space."""

    def __init__(self):
        self.d = []
        self.ox = self.oy = 0.0
        self.s = 1.0

    def _p(self, pt):
        return f"{self.ox + pt[0] * self.s:.2f} {self.oy - pt[1] * self.s:.2f}"

    def moveTo(self, p):
        self.d.append("M" + self._p(p))

    def lineTo(self, p):
        self.d.append("L" + self._p(p))

    def qCurveTo(self, c, p):
        self.d.append(f"Q{self._p(c)} {self._p(p)}")

    def curveTo(self, c1, c2, p):
        self.d.append(f"C{self._p(c1)} {self._p(c2)} {self._p(p)}")

    def closePath(self):
        self.d.append("Z")

    def endPath(self):
        pass


def text(s, x, y, size, *, font="flex", weight=400, fill=WHITE, tracking=0.0, anchor="start", cls=""):
    """Returns (svg path element, advance width). `tracking` is in em."""
    face = FACES[font]
    f = hb.Font(face)
    variations = {"wght": weight}
    if font == "flex":
        variations["opsz"] = max(6, min(144, size))
    f.set_variations(variations)
    buf = hb.Buffer()
    buf.add_str(s)
    buf.guess_segment_properties()
    hb.shape(f, buf)

    scale = size / face.upem
    track = tracking * size
    width = sum(p.x_advance * scale + track for p in buf.glyph_positions) - track
    start = {"start": x, "middle": x - width / 2, "end": x - width}[anchor]

    pen = PathPen()
    pen.s = scale
    cursor = start
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        pen.ox = cursor + pos.x_offset * scale
        pen.oy = y - pos.y_offset * scale
        f.draw_glyph_with_pen(info.codepoint, pen)
        cursor += pos.x_advance * scale + track
    attr = f' class="{cls}"' if cls else ""
    return f'<path{attr} fill="{fill}" d="{"".join(pen.d)}"/>', width


# ---- Left column ------------------------------------------------------------
LEFT = 56
parts = []
parts.append(text(EYEBROW, LEFT, 104, 12.5, font="code", weight=500, fill=MUTED, tracking=0.12)[0])
parts.append(text(NAME, LEFT - 2, 170, 58, weight=600, tracking=-0.02)[0])
parts.append(text(LINE_1, LEFT, 214, 21, fill=MUTED)[0])
line_2, advance = text(LINE_2, LEFT, 244, 21, fill=MUTED)
parts.append(line_2)
parts.append(text(LINE_2_SPARK, LEFT + advance, 244, 21, weight=600, fill=SPARK)[0])

# ---- Right column: problem -> strategy -> agents -> ship, and round again ----
CY = 158
P, S, SHIP = (606, CY), (706, CY), (926, CY)
AGENTS = [(816, CY - 68), (816, CY), (816, CY + 68)]
R, RA = 17, 13

edges = {"ps": f"M{P[0] + R} {CY}L{S[0] - R} {CY}"}
for i, (ax, ay) in enumerate(AGENTS):
    edges[f"sa{i}"] = f"M{S[0] + R} {CY}C{S[0] + 62} {CY} {ax - 62} {ay} {ax - RA} {ay}"
    edges[f"as{i}"] = f"M{ax + RA} {ay}C{ax + 62} {ay} {SHIP[0] - 62} {CY} {SHIP[0] - R} {CY}"
BOTTOM = CY + 126
edges["loop"] = (
    f"M{SHIP[0]} {CY + R}C{SHIP[0]} {BOTTOM + 14} {SHIP[0] - 40} {BOTTOM} {SHIP[0] - 90} {BOTTOM}"
    f"L{P[0] + 90} {BOTTOM}C{P[0] + 40} {BOTTOM} {P[0]} {BOTTOM + 14} {P[0]} {CY + R}"
)

defs = "\n".join(f'<path id="{k}" d="{d}"/>' for k, d in edges.items())
wires = "\n".join(
    f'<use href="#{k}" class="wire{" loop" if k == "loop" else ""}"/>' for k in edges
)


def node(x, y, r, glow):
    return (
        f'<circle cx="{x}" cy="{y}" r="{r}" fill="{NIGHT_RAISED}" stroke="{MUTED}" stroke-opacity=".35"/>'
        f'<circle cx="{x}" cy="{y}" r="{r * 0.3:.1f}" fill="{MUTED}"/>'
        f'<g class="lit {glow}">'
        f'<circle cx="{x}" cy="{y}" r="{r + 7}" fill="{SPARK}" opacity=".28" filter="url(#soft)"/>'
        f'<circle cx="{x}" cy="{y}" r="{r}" fill="{NIGHT_RAISED}" stroke="{SPARK}" stroke-width="1.5"/>'
        f'<circle cx="{x}" cy="{y}" r="{r * 0.3:.1f}" fill="{SPARK}"/>'
        f"</g>"
    )


nodes = [node(*P, R, "g-p"), node(*S, R, "g-s"), node(*SHIP, R, "g-ship")]
nodes += [node(ax, ay, RA, "g-a") for ax, ay in AGENTS]


def label(s, x, y):
    return text(s, x, y, 10, font="code", weight=500, fill=MUTED, tracking=0.14, anchor="middle")[0]


labels = [
    label("PROBLEM", P[0], CY - R - 13),
    label("STRATEGY", S[0], CY - R - 13),
    label("AGENTS", AGENTS[0][0], AGENTS[0][1] - RA - 13),
    label("SHIP", SHIP[0], CY - R - 13),
    label("ITERATE", (P[0] + SHIP[0]) / 2, BOTTOM - 10),
]


def spark(edge, start, end, r=3.5, opacity=1.0):
    """A dot that waits, runs along `edge` between two fractions of the cycle, then hides."""
    fade = 0.012
    return (
        f'<circle class="spark" r="{r}" fill="{SPARK}" opacity="0">'
        f'<animateMotion dur="{CYCLE}s" repeatCount="indefinite" calcMode="spline" '
        f'keyTimes="0;{start};{end};1" keyPoints="0;0;1;1" '
        f'keySplines="0 0 1 1;.45 0 .25 1;0 0 1 1"><mpath href="#{edge}"/></animateMotion>'
        f'<animate attributeName="opacity" dur="{CYCLE}s" repeatCount="indefinite" '
        f'keyTimes="0;{start};{start + fade:.3f};{end - fade:.3f};{end};1" '
        f'values="0;0;{opacity};{opacity};0;0"/>'
        f"</circle>"
    )


sparks = [spark("ps", 0.03, 0.14)]
sparks += [spark(f"sa{i}", 0.19 + i * 0.015, 0.33 + i * 0.015, r=3) for i in range(3)]
sparks += [spark(f"as{i}", 0.50 + i * 0.015, 0.63 + i * 0.015, r=3) for i in (1, 0, 2)]
sparks += [spark("loop", 0.72, 0.97, r=3, opacity=0.6)]

NL = "\n"
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t d">
<title id="t">{NAME}. {EYEBROW.capitalize()}.</title>
<desc id="d">{LINE_1} {LINE_2}{LINE_2_SPARK} A spark travels from problem to strategy, fans out to three agents, reaches ship, and loops back to iterate.</desc>
<defs>
<radialGradient id="glow" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="translate(820 300) scale(520 330)">
<stop stop-color="{GLOW}" stop-opacity=".55"/><stop offset="1" stop-color="{GLOW}" stop-opacity="0"/>
</radialGradient>
<filter id="soft" x="-80%" y="-80%" width="260%" height="260%"><feGaussianBlur stdDeviation="7"/></filter>
<clipPath id="card"><rect width="{W}" height="{H}" rx="20"/></clipPath>
{defs}
</defs>
<style>
.wire {{ fill: none; stroke: {MUTED}; stroke-opacity: .28; stroke-width: 1.25 }}
.loop {{ stroke-dasharray: 2 7; stroke-linecap: round; stroke-opacity: .4 }}
.lit {{ opacity: 0; animation: {CYCLE}s linear infinite both }}
.g-p {{ animation-name: p }}
.g-s {{ animation-name: s }}
.g-a {{ animation-name: a }}
.g-ship {{ animation-name: ship }}
@keyframes p {{ 0%, 12% {{ opacity: 1 }} 17%, 94% {{ opacity: 0 }} 98%, 100% {{ opacity: 1 }} }}
@keyframes s {{ 0%, 12% {{ opacity: 0 }} 15%, 30% {{ opacity: 1 }} 36%, 100% {{ opacity: 0 }} }}
@keyframes a {{ 0%, 32% {{ opacity: 0 }} 36%, 44% {{ opacity: 1 }} 48% {{ opacity: .55 }} 52%, 60% {{ opacity: 1 }} 68%, 100% {{ opacity: 0 }} }}
@keyframes ship {{ 0%, 62% {{ opacity: 0 }} 66%, 88% {{ opacity: 1 }} 95%, 100% {{ opacity: 0 }} }}
@media (prefers-reduced-motion: reduce) {{
  .lit {{ animation: none }}
  .g-ship {{ opacity: 1 }}
  .spark {{ display: none }}
}}
</style>

<g clip-path="url(#card)">
<rect width="{W}" height="{H}" fill="{NIGHT}"/>
<rect width="{W}" height="{H}" fill="url(#glow)"/>
</g>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="19.5" fill="none" stroke="{WHITE}" stroke-opacity=".08"/>

{NL.join(parts)}

{wires}
{NL.join(sparks)}
{NL.join(nodes)}
{NL.join(labels)}
</svg>
'''

out = Path(__file__).resolve().parent.parent / "assets" / "hero.svg"
out.write_text(svg)
print(f"wrote {out} ({len(svg) / 1024:.1f} kB)")
