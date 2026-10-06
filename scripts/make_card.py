"""neofetch-style card: ASCII emblem on the left, key/value info on the right.

Edit INFO / PROJECTS and re-run. Static: no need to run in CI.
"""
from theme import THEMES, esc, window, write

EMBLEM = [  # compass rose — drift / travel / navigation. Axis = column 13 of 27; must stay mirror-symmetric.
    "             N",
    "             ^",
    "        .    |    .",
    "     .       |       .",
    "   .     \\   |   /     .",
    "  .       \\  |  /       .",
    " .         \\ | /         .",
    "W <--------( + )--------> E",
    " .         / | \\         .",
    "  .       /  |  \\       .",
    "   .     /   |   \\     .",
    "     .       |       .",
    "        .    |    .",
    "             v",
    "             S",
]

INFO = [
    ("Role", "backend-first, full-stack by necessity"),
    ("Focus", "enterprise systems · privacy tooling · self-hosting"),
    ("Stack", "TypeScript · NestJS · Next.js · PostgreSQL"),
    ("", "C# · SQL Server · Java · Swift · React Native"),
    ("Infra", "Linux homelab · local LLM inference · automation"),
]
PROJECTS = [
    ("AtlasPlan", "trip planner · Expo + Laravel API + React admin"),
    ("KitchenAI", "native iOS app · Swift"),
    ("claude-pad", "macro pad → Claude Code bridge · Node.js"),
    ("homelab", "privacy-first, local-first, automated backups"),
]
UPTIME = "always improving, always pushing"

W, FS, CHW, LH = 860, 13, 7.8, 21       # width, font size, char width, line height
EX, KX = 36, 316                        # emblem x, info x
VX = KX + 9 * CHW                       # value column
PX, PDX = KX + 2 * CHW, KX + 14 * CHW   # project name / description columns


def build(name, t):
    lines = []  # (svg fragment) — each becomes one staggered line

    def kv(k, v):
        return (f'<text x="{KX}" font-size="{FS}" fill="{t["accent2"]}">{esc(k)}</text>'
                f'<text x="{VX}" font-size="{FS}" fill="{t["fg"]}">{esc(v)}</text>')

    lines.append(f'<text x="{KX}" font-size="{FS+1}" font-weight="700" fill="{t["accent"]}">driftn0de<tspan fill="{t["fg"]}">@</tspan>github</text>')
    lines.append(f'<text x="{KX}" font-size="{FS}" fill="{t["faint"]}">{"-"*16}</text>')
    lines += [kv(k, v) for k, v in INFO]
    lines.append("")
    lines.append(f'<text x="{KX}" font-size="{FS}" fill="{t["accent2"]}">Projects</text>')
    for n, d in PROJECTS:
        lines.append(f'<text x="{KX}" font-size="{FS}" fill="{t["faint"]}">»</text>'
                     f'<text x="{PX}" font-size="{FS}" fill="{t["accent"]}">{esc(n)}</text>'
                     f'<text x="{PDX}" font-size="{FS}" fill="{t["dim"]}">{esc(d)}</text>')
    lines.append("")
    lines.append(kv("Uptime", UPTIME))
    lines.append("")
    swatches = [t["ramp"][i] for i in range(1, 5)] + [t["accent2"], t["warn"], "#ff7b72", t["dim"]]
    lines.append("".join(f'<rect x="{KX+i*26}" y="-12" width="24" height="14" rx="2" fill="{c}"/>'
                         for i, c in enumerate(swatches)))

    top = 62
    h = top + len(lines) * LH + 18
    out = [f'<text x="28" y="56" font-size="13" fill="{t["dim"]}"><tspan fill="{t["accent"]}">driftn0de@github</tspan> ~ $ neofetch</text>']
    for i, frag in enumerate(lines):
        if frag:
            out.append(f'<g class="ln" style="animation-delay:{0.35+i*0.07:.2f}s" transform="translate(0 {top + (i+1)*LH})">{frag}</g>')

    EC, ER = 8.6, 18                     # emblem cell width / row height
    eh = len(EMBLEM) * ER
    ey = top + (len(lines) * LH - eh) / 2 + 14
    for r, row in enumerate(EMBLEM):
        glyphs = "".join(f'<text x="{EX + c*EC + EC/2:.1f}" y="{ey + r*ER:.1f}">{esc(ch)}</text>'
                         for c, ch in enumerate(row) if ch != " ")
        out.append(f'<g class="em" style="animation-delay:{r*0.04:.2f}s" font-size="14" text-anchor="middle" fill="{t["accent"]}">{glyphs}</g>')

    style = """.ln,.em{opacity:0;animation:in .45s ease-out forwards}
.ln{transform-box:fill-box}
@keyframes in{to{opacity:1}}
@media (prefers-reduced-motion:reduce){.ln,.em{opacity:1;animation:none}}"""
    write(name, window(t, W, int(h), "driftn0de — neofetch", "\n".join(out), style))


if __name__ == "__main__":
    for k, t in THEMES.items():
        build(f"card-{k}.svg", t)
