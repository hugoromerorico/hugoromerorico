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
SUIT = "#07090e"
WEB_RED = "#ff3b4a"
FRINGE_CYAN = "#27e0ff"
FRINGE_PINK = "#ff2d78"

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


# ---- Spider-hero: hangs upside down over the graph and webs the SHIP node ----
# Drawn upright with the thread anchor at (0, 0) below the feet, then rotated
# 180 degrees so it hangs from the top edge of the card at x = HANG_X.
HANG_X = 872
ZOOM = 1.15
HAND = (HANG_X + 25 * ZOOM, 83 * ZOOM + 3)  # web-shooting hand, in card coordinates
HIT = (SHIP[0] - 15, CY - 8)  # where the web lands on the SHIP node
HEAD = "M0 -92C8 -92 12 -86 12 -79C12 -71 6 -65 0 -64.5C-6 -65 -12 -71 -12 -79C-12 -86 -8 -92 0 -92Z"


def silhouette(color):
    limb = f'fill="none" stroke="{color}" stroke-linecap="round" stroke-linejoin="round"'
    return (
        f'<path {limb} stroke-width="6.5" d="M-4 -46L-18 -37L-3 -26M4 -46L18 -37L3 -26"/>'
        f'<path {limb} stroke-width="5.2" d="M-10 -62L-20 -68L-25 -82M10 -62L19 -54L9 -47"/>'
        f'<ellipse cx="-4.5" cy="-24.5" rx="4.6" ry="2.9" fill="{color}"/>'
        f'<ellipse cx="4.5" cy="-24.5" rx="4.6" ry="2.9" fill="{color}"/>'
        f'<circle cx="-25" cy="-83" r="3.5" fill="{color}"/>'
        f'<circle cx="9" cy="-47" r="3.3" fill="{color}"/>'
        f'<path fill="{color}" d="M-10.5 -63Q0 -68 10.5 -63L6.5 -45Q0 -42 -6.5 -45Z"/>'
        f'<path fill="{color}" d="{HEAD}"/>'
    )


def eye(sign):
    s = sign
    return (
        f'<path fill="{WHITE}" stroke="{SUIT}" stroke-width=".9" stroke-linejoin="round" '
        f'd="M{-10.2 * s} -83.5Q{-4.5 * s} -84.5 {-1.6 * s} -76.5Q{-6 * s} -72 {-9.6 * s} -75.5Q{-11 * s} -79 {-10.2 * s} -83.5Z"/>'
    )


hero_details = (
    f'<g clip-path="url(#mask-head)" fill="none" stroke="{WEB_RED}" stroke-width=".6" stroke-opacity=".9">'
    '<path d="M0 -77L0 -93M0 -77L-9 -91M0 -77L9 -91M0 -77L-13 -82M0 -77L13 -82M0 -77L-11 -68M0 -77L11 -68M0 -77L0 -64"/>'
    '<path d="M-7 -88Q0 -85.5 7 -88M-11.5 -81Q-7 -84 -7 -88M11.5 -81Q7 -84 7 -88M-9 -70Q-4.500 -72 0 -70Q4.5 -72 9 -70"/>'
    "</g>"
    + eye(1)
    + eye(-1)
    + f'<ellipse cx="0" cy="-56" rx="1.7" ry="2.8" fill="{WEB_RED}"/>'
    f'<path fill="none" stroke="{WEB_RED}" stroke-width=".9" stroke-linecap="round" '
    'd="M0 -57.500L-5 -61M0 -57.500L5 -61M0 -56.500L-6 -57M0 -56.500L6 -57M0 -55L-5 -51.500M0 -55L5 -51.500"/>'
    f'<path fill="none" stroke="{WEB_RED}" stroke-width="1.1" stroke-linecap="round" d="M-27.5 -84.500L-22.500 -85.500M-8 -23.500L-1.500 -23.500M1.500 -23.500L8 -23.500"/>'
)

halftone = (
    f'<circle cx="{HANG_X}" cy="72" r="52" fill="url(#dots)" mask="url(#fade)" opacity=".55"/>'
)

hero = (
    '<g class="swing">'
    f'<line x1="{HANG_X}" y1="0" x2="{HANG_X}" y2="{26 * ZOOM:.1f}" stroke="{WHITE}" stroke-opacity=".75" stroke-width=".9"/>'
    f'<g transform="translate({HANG_X - 1.5} -.5) rotate(180) scale({ZOOM})" opacity=".9">{silhouette(FRINGE_CYAN)}</g>'
    f'<g transform="translate({HANG_X + 1.5} .5) rotate(180) scale({ZOOM})" opacity=".9">{silhouette(FRINGE_PINK)}</g>'
    f'<g transform="translate({HANG_X} 0) rotate(180) scale({ZOOM})">{silhouette(SUIT)}{hero_details}</g>'
    "</g>"
)

hx, hy = HIT
web_shot = (
    f'<path class="shot" pathLength="1" fill="none" stroke="{WHITE}" stroke-opacity=".85" stroke-width="1.1" '
    f'stroke-linecap="round" d="M{HAND[0]} {HAND[1]}L{hx} {hy}"/>'
    f'<path class="splat" fill="none" stroke="{WHITE}" stroke-opacity=".85" stroke-width="1" stroke-linecap="round" '
    f'd="M{hx - 5} {hy - 1}L{hx + 4} {hy + 2}M{hx - 1} {hy - 5}L{hx + 2} {hy + 5}M{hx - 4} {hy + 4}L{hx + 4} {hy - 3}"/>'
)
thwip = (
    f'<g class="thwip" transform="rotate(-9 916 104)">'
    + text("THWIP!", 916, 104, 11.5, weight=800, fill=SPARK, tracking=0.04)[0]
    + "</g>"
)

NL = "\n"
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t d">
<title id="t">{NAME}. {EYEBROW.capitalize()}.</title>
<desc id="d">{LINE_1} {LINE_2}{LINE_2_SPARK} A spark travels from problem to strategy, fans out to three agents, reaches ship, and loops back to iterate. A cartoon spider-hero hangs upside down from the top edge and webs the ship node as it lights up.</desc>
<defs>
<radialGradient id="glow" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="translate(820 300) scale(520 330)">
<stop stop-color="{GLOW}" stop-opacity=".55"/><stop offset="1" stop-color="{GLOW}" stop-opacity="0"/>
</radialGradient>
<filter id="soft" x="-80%" y="-80%" width="260%" height="260%"><feGaussianBlur stdDeviation="7"/></filter>
<clipPath id="card"><rect width="{W}" height="{H}" rx="20"/></clipPath>
<pattern id="dots" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(28)"><circle cx="2.5" cy="2.5" r="1.15" fill="{WEB_RED}"/></pattern>
<radialGradient id="fade-g"><stop offset=".35" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>
<mask id="fade"><circle cx="{HANG_X}" cy="72" r="52" fill="url(#fade-g)"/></mask>
<clipPath id="mask-head"><path d="{HEAD}"/></clipPath>
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
.swing {{ transform-origin: {HANG_X}px 0; animation: swing {CYCLE}s ease-in-out infinite both }}
.shot {{ stroke-dasharray: 1; animation: shot {CYCLE}s linear infinite both }}
.splat {{ animation: splat {CYCLE}s linear infinite both }}
.thwip {{ animation: thwip {CYCLE}s linear infinite both }}
@keyframes swing {{ 0%, 54%, 100% {{ transform: rotate(0deg) }} 13% {{ transform: rotate(3deg) }} 27% {{ transform: rotate(-3deg) }} 41% {{ transform: rotate(2deg) }} }}
@keyframes shot {{ 0%, 59% {{ stroke-dashoffset: 1; opacity: 1 }} 63%, 88% {{ stroke-dashoffset: 0; opacity: 1 }} 93%, 100% {{ stroke-dashoffset: 0; opacity: 0 }} }}
@keyframes splat {{ 0%, 62.5% {{ opacity: 0 }} 63.5%, 88% {{ opacity: 1 }} 93%, 100% {{ opacity: 0 }} }}
@keyframes thwip {{ 0%, 60% {{ opacity: 0 }} 62%, 69% {{ opacity: 1 }} 73%, 100% {{ opacity: 0 }} }}
@media (prefers-reduced-motion: reduce) {{
  .lit, .swing, .shot, .splat, .thwip {{ animation: none }}
  .g-ship {{ opacity: 1 }}
  .shot {{ stroke-dashoffset: 0 }}
  .thwip {{ opacity: 0 }}
  .spark {{ display: none }}
}}
</style>

<g clip-path="url(#card)">
<rect width="{W}" height="{H}" fill="{NIGHT}"/>
<rect width="{W}" height="{H}" fill="url(#glow)"/>
</g>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="19.5" fill="none" stroke="{WHITE}" stroke-opacity=".08"/>

{NL.join(parts)}

{halftone}
{wires}
{NL.join(sparks)}
{NL.join(nodes)}
{NL.join(labels)}
{web_shot}
{hero}
{thwip}
</svg>
'''

out = Path(__file__).resolve().parent.parent / "assets" / "hero.svg"
out.write_text(svg)
print(f"wrote {out} ({len(svg) / 1024:.1f} kB)")
