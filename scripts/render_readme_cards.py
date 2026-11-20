#!/usr/bin/env python3
"""
Render the profile README's cards as animated SVGs into cards/.
- hero.svg: hero card with Lakshya Gupta title/bio + radial contribution clock
- heatmap.svg: contribution calendar in blue
- activity.svg: monthly bar chart with streak and commit statistics
"""
import base64
import datetime
import json
import math
import os
from html import escape

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
DATA = os.path.join(ROOT, "data", "contributions.json")
OUT = os.path.join(ROOT, "cards")
FONTS = os.path.join(ROOT, "fonts")

# Brand design tokens
PAPER = "#f3f3f1"
PAPER_DEEP = "#e2e2de"
INK = "#111111"
INK_SOFT = "#3a3a3c"
MUTED = "#6e6e73"
RULE = "#dcdcd7"
TECH = "#2f55ff"
W = 880  # full card width, GitHub's README column at 100%

SERIF = "'Instrument Serif', Georgia, serif"
SANS = "Geist, system-ui, -apple-system, sans-serif"
MONO = "'Geist Mono', ui-monospace, SFMono-Regular, Menlo, monospace"

FONT_FILES = {
    "serif": ("Instrument Serif", "normal", 400, "serif-400.woff"),
    "serif-i": ("Instrument Serif", "italic", 400, "serif-italic.woff"),
    "sans": ("Geist", "normal", 400, "geist-400.woff"),
    "sans-b": ("Geist", "normal", 600, "geist-600.woff"),
    "mono": ("Geist Mono", "normal", 400, "geistmono-400.woff"),
}

BASE_CSS = """
@keyframes rise{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}
@keyframes fade{from{opacity:0}to{opacity:1}}
@keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}
@keyframes pop{0%{opacity:0;transform:scale(.3)}70%{opacity:1;transform:scale(1.15)}100%{opacity:1;transform:none}}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.25}}
@keyframes nudgeup{0%,100%{transform:none}50%{transform:translate(3px,-3px)}}
.r{opacity:0;animation:rise .8s cubic-bezier(.2,.7,.2,1) both;transform-box:fill-box}
.f{opacity:0;animation:fade .9s ease-out both}
.g{transform-box:fill-box;transform-origin:bottom;transform:scaleY(0);animation:grow .8s cubic-bezier(.2,.7,.2,1) both}
.p{opacity:0;transform-box:fill-box;transform-origin:center;animation:pop .4s ease-out both}
.live{animation:pulse 1.6s ease-in-out infinite}
.nu{transform-box:fill-box;animation:nudgeup 1.8s ease-in-out infinite}
@media (prefers-reduced-motion: reduce){.r,.f,.g,.p,.live,.nu{animation:none!important;opacity:1!important;transform:none!important}}
"""


def font_face(keys):
    out = []
    for k in keys:
        fam, style, weight, fn = FONT_FILES[k]
        font_path = os.path.join(FONTS, fn)
        if os.path.exists(font_path):
            b64 = base64.b64encode(open(font_path, "rb").read()).decode()
            out.append(
                f"@font-face{{font-family:'{fam}';font-style:{style};font-weight:{weight};"
                f"src:url(data:font/woff;base64,{b64}) format('woff')}}"
            )
    return "".join(out)


BOTTOM = 12


def svg(w, h, body, fonts, label, extra_css="", bottom=BOTTOM):
    w, h = w, h + bottom
    css = font_face(fonts) + BASE_CSS + extra_css
    if os.environ.get("STATIC"):
        css += ".r,.f,.g,.p,.live,.nu{animation:none!important;opacity:1!important;transform:none!important}"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.3f}" height="{h}" viewBox="0 0 {w:.3f} {h}" '
        f'role="img" aria-label="{escape(label)}"><title>{escape(label)}</title>'
        f"<style>{css}</style>{body}</svg>"
    )


def write(name, content):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    with open(path, "w") as f:
        f.write(content)
    print(f"wrote cards/{name} ({len(content) // 1024} KB)")


def d(s):
    return f'style="animation-delay:{s:.2f}s"'


BLUE = [PAPER_DEEP, "#c8d3ff", "#94a8ff", "#6280ff", TECH, "#1a3be0"]


def level_for(c):
    return 0 if c == 0 else 1 if c <= 5 else 2 if c <= 15 else 3 if c <= 30 else 4 if c <= 50 else 5


def hero(data):
    h = 420
    cx, cy = 665, 210
    R_in = 64
    dr = 13.5
    days = data["days"]

    # Orbital guide rings
    tracks = []
    for row in range(7):
        r = R_in + row * dr
        tracks.append(f'<circle cx="{cx}" cy="{cy}" r="{r:.1f}" fill="none" stroke="{RULE}" stroke-width="0.8" opacity=".5"/>')

    # Radial contribution cells (53 weeks arranged around circle)
    cells = []
    seen = set()
    months = []
    for i, day in enumerate(days):
        col, row = divmod(i, 7)
        date = datetime.date.fromisoformat(day["date"])
        deg = col * (360.0 / 53.0)
        if date.day <= 7 and (date.year, date.month) not in seen and row == 0:
            seen.add((date.year, date.month))
            months.append((col, deg, date.strftime("%b")))
        r = R_in + row * dr
        c = day["count"]
        color = BLUE[level_for(c)]
        slot_w = (2 * math.pi * r) / 53.0
        cw = max(4.5, slot_w - 2.8)
        ch = 9.0
        delay = 0.5 + (col / 53.0) * 1.3 + row * 0.03
        cells.append(
            f'<rect class="p" style="animation-delay:{delay:.2f}s" '
            f'x="{cx - cw/2:.2f}" y="{cy - r - ch/2:.2f}" width="{cw:.2f}" height="{ch:.2f}" '
            f'rx="2" fill="{color}" transform="rotate({deg:.2f} {cx} {cy})">'
            f'<title>{day["date"]}: {c} contribution{"s" if c != 1 else ""}</title></rect>'
        )

    # Perimeter month markers
    r_month = 170
    labels = []
    for col, deg, name in months:
        rad = math.radians(deg - 90)
        x = cx + r_month * math.cos(rad)
        y = cy + r_month * math.sin(rad) + 4
        labels.append(f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="middle" font-family="{MONO}" font-size="10" fill="{MUTED}">{name}</text>')

    # Subtle radar beam rotation
    radar = f"""
<g transform="translate({cx} {cy})">
  <circle r="154" fill="none" stroke="{RULE}" stroke-dasharray="3 3" opacity=".6"/>
  <line x1="0" y1="0" x2="0" y2="-154" stroke="{TECH}" stroke-width="1.2" stroke-linecap="round" opacity=".4">
    <animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="14s" repeatCount="indefinite"/>
  </line>
</g>
"""

    # Center statistics hub
    center = f"""
<circle cx="{cx}" cy="{cy}" r="52" fill="{PAPER}" stroke="{RULE}" stroke-width="1"/>
<text class="r" {d(0.6)} x="{cx}" y="{cy - 8}" text-anchor="middle" font-family="{SERIF}" font-size="34" fill="{INK}">{data["total_contributions"]:,}</text>
<text class="f" {d(0.7)} x="{cx}" y="{cy + 12}" text-anchor="middle" font-family="{MONO}" font-size="9" letter-spacing="1.2" fill="{MUTED}">CONTRIBUTIONS</text>
<text class="f" {d(0.8)} x="{cx}" y="{cy + 26}" text-anchor="middle" font-family="{MONO}" font-size="9" letter-spacing="0.8" fill="{TECH}">365 DAYS</text>
"""

    body = f"""
<defs>
  <linearGradient id="shine" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="600" y2="0">
    <stop offset="0" stop-color="{INK}"/><stop offset=".42" stop-color="{INK}"/>
    <stop offset=".5" stop-color="{TECH}"/><stop offset=".58" stop-color="{INK}"/>
    <stop offset="1" stop-color="{INK}"/>
    <animateTransform attributeName="gradientTransform" type="translate" values="-600 0;600 0;600 0"
      keyTimes="0;.45;1" dur="7s" begin="1.6s" repeatCount="indefinite"/>
  </linearGradient>
</defs>
<rect width="{W}" height="{h}" rx="14" fill="{PAPER}"/>
<g class="f" {d(0)}>
  <rect class="live" x="48" y="49" width="8" height="8" rx="2" fill="{TECH}"/>
  <text x="66" y="57" font-family="{MONO}" font-size="12" letter-spacing="1" fill="{MUTED}">SOFTWARE &amp; AI/ML ENGINEER</text>
</g>
<text class="r" {d(0.15)} x="44" y="190" font-family="{SERIF}" font-size="116" letter-spacing="-2.5" fill="{INK}">Lakshya</text>
<text class="r" {d(0.3)} x="44" y="290" font-family="{SERIF}" font-style="italic" font-size="116" letter-spacing="-2.5" fill="url(#shine)">Gupta</text>
<g class="r" {d(0.55)}>
  <text x="48" y="338" font-family="{SANS}" font-size="18" fill="{INK_SOFT}">Building production-grade AI systems, agentic RAG,</text>
  <text x="48" y="365" font-family="{SANS}" font-size="18" fill="{INK_SOFT}">and high-performance full-stack applications.</text>
</g>
<g class="f" {d(0.8)}>
  <text x="48" y="396" font-family="{MONO}" font-size="13" fill="{INK}">lakshyapf.vercel.app</text>
  <text class="nu" x="210" y="396" font-family="{MONO}" font-size="13" fill="{TECH}">&#8599;</text>
</g>

<!-- Circular Contribution Wheel -->
{''.join(tracks)}
{radar}
{''.join(cells)}
<g class="f" {d(1.6)}>
  {''.join(labels)}
</g>
{center}
"""
    write("hero.svg", svg(W, h, body, ["serif", "serif-i", "sans", "mono"],
                          f'Lakshya Gupta. Software & AI/ML Engineer. {data["total_contributions"]:,} contributions in the last year.'))


def activity(data):
    h = 340
    monthly = data["monthly"][-12:]
    best = max(monthly[:-1] or monthly, key=lambda m: m["total"])
    top = max(1, best["total"])
    x0, x1, base, maxh, gap = 40, 600, 292, 140, 10
    bw = (x1 - x0 - gap * (len(monthly) - 1)) / len(monthly)
    bars = []
    for i, m in enumerate(monthly):
        partial = i == len(monthly) - 1
        is_best = m is best
        bh = max(4, round(m["total"] / top * maxh))
        x = x0 + i * (bw + gap)
        fill = TECH if is_best else ("#c9c9c4" if partial else INK)
        label = datetime.date.fromisoformat(m["month"] + "-01").strftime("%b")
        bars.append(
            f'<rect class="g" style="animation-delay:{0.4 + i * 0.07:.2f}s" x="{x:.1f}" y="{base - bh}" '
            f'width="{bw:.1f}" height="{bh}" rx="4" fill="{fill}"><title>{label}: {m["total"]:,}</title></rect>'
            f'<text class="f" style="animation-delay:{0.4 + i * 0.07:.2f}s" x="{x + bw / 2:.1f}" y="{base + 22}" '
            f'text-anchor="middle" font-family="{MONO}" font-size="11" fill="{MUTED}">{label}</text>'
        )
        if is_best:
            bars.append(
                f'<text class="p" style="animation-delay:1.3s" x="{x + bw / 2:.1f}" y="{base - bh - 10}" '
                f'text-anchor="middle" font-family="{MONO}" font-size="11" fill="{TECH}">{m["total"]:,}</text>'
            )
    cs = data["current_streak"]["length"]
    ls = data["longest_streak"]["length"]
    streak_note = "current streak, and the longest" if cs >= ls else f"current streak, longest {ls}"
    total_days = len(data["days"])
    stats = [
        (f'{cs} <tspan font-style="italic">days</tspan>', streak_note),
        (f'{data["active_days"]}<tspan fill="#8e8e93"> / {total_days}</tspan>', "days with a commit"),
        (f'{data["best_day"]["count"]}', "on the busiest day"),
    ]
    side = []
    for i, (big, small) in enumerate(stats):
        y = 104 + i * 92
        side.append(
            f'<g class="r" {d(0.7 + i * 0.15)}>'
            f'<text x="650" y="{y}" font-family="{SERIF}" font-size="40" fill="{INK}">{big}</text>'
            f'<text x="650" y="{y + 24}" font-family="{SANS}" font-size="13" fill="{MUTED}">{small}</text></g>'
        )
        if i < 2:
            side.append(f'<rect class="f" {d(0.7)} x="650" y="{y + 44}" width="190" height="1" fill="{RULE}"/>')
    body = f"""
<rect width="{W}" height="{h}" rx="14" fill="{PAPER}"/>
<text class="f" {d(0.2)} x="40" y="58" font-family="{MONO}" font-size="12" letter-spacing="1" fill="{MUTED}">THE LAST 12 MONTHS ON GITHUB</text>
<text class="r" {d(0.3)} x="38" y="114" font-family="{SERIF}" font-size="52" fill="{INK}">{data["total_contributions"]:,} <tspan font-style="italic">contributions</tspan></text>
{''.join(bars)}
{''.join(side)}
"""
    write("activity.svg", svg(W, h, body, ["serif", "serif-i", "sans", "mono"],
                              f'{data["total_contributions"]:,} contributions in the last year, {cs}-day streak'))


def heatmap(data):
    days = data["days"]
    first = datetime.date.fromisoformat(days[0]["date"])
    lead = (first.weekday() + 1) % 7  # sunday = 0
    cell, step, gx, gy = 12, 15, 44, 96
    cells, months, seen = [], [], set()
    for i, day in enumerate(days):
        k = i + lead
        col, row = divmod(k, 7)
        date = datetime.date.fromisoformat(day["date"])
        if date.day <= 7 and (date.year, date.month) not in seen and row == 0:
            seen.add((date.year, date.month))
            months.append((col, date.strftime("%b")))
        c = day["count"]
        delay = 0.4 + col * 0.02 + row * 0.015
        cells.append(
            f'<rect class="p" style="animation-delay:{delay:.2f}s" x="{gx + col * step}" y="{gy + row * step}" '
            f'width="{cell}" height="{cell}" rx="3" fill="{BLUE[level_for(c)]}">'
            f'<title>{day["date"]}: {c} contribution{"s" if c != 1 else ""}</title></rect>'
        )
    ncols = (len(days) + lead + 6) // 7
    right = gx + ncols * step - 3
    labels = "".join(
        f'<text x="{gx + col * step}" y="{gy + 7 * step + 16}" font-family="{MONO}" font-size="11" fill="{MUTED}">{m}</text>'
        for col, m in months if col < ncols - 12
    )
    legend_x = right - len(BLUE) * 14
    legend = "".join(
        f'<rect x="{legend_x + i * 14}" y="{gy + 7 * step + 6}" width="11" height="11" rx="2.5" fill="{c}"/>'
        for i, c in enumerate(BLUE)
    )
    h = gy + 7 * step + 44
    body = f"""
<rect width="{W}" height="{h}" rx="14" fill="{PAPER}"/>
<text class="r" {d(0.2)} x="42" y="62" font-family="{SERIF}" font-size="34" fill="{INK}">Every day, <tspan font-style="italic" fill="{TECH}">in blue</tspan></text>
<text class="f" {d(0.2)} x="{right}" y="60" text-anchor="end" font-family="{MONO}" font-size="12" letter-spacing="1" fill="{MUTED}">REFRESHED DAILY</text>
{''.join(cells)}
<g class="f" {d(1.5)}>{labels}
<text x="{legend_x - 8}" y="{gy + 7 * step + 16}" text-anchor="end" font-family="{MONO}" font-size="11" fill="{MUTED}">less</text>
{legend}
<text x="{legend_x + len(BLUE) * 14 + 2}" y="{gy + 7 * step + 16}" font-family="{MONO}" font-size="11" fill="{MUTED}">more</text></g>
"""
    write("heatmap.svg", svg(W, h, body, ["serif", "serif-i", "mono"],
                             f'Contribution graph: {data["total_contributions"]:,} contributions in the last year'))


if __name__ == "__main__":
    if not os.path.exists(DATA):
        print(f"data file missing: {DATA}", file=os.sys.stderr)
        os.sys.exit(1)
    data = json.load(open(DATA))
    hero(data)
    heatmap(data)
    activity(data)
