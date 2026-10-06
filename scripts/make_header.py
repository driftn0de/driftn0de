"""Header: the handle as a block banner that 'prints' left-to-right, plus a tagline.

The banner is drawn as shapes (blocks + line strokes), not text, so it renders identically
whatever monospace font the viewer has. Static: re-run only when the copy changes.
"""
from theme import THEMES, esc, window, write

BANNER = [  # pyfiglet "ANSI Shadow" — baked in so no runtime dependency
    "██████╗ ██████╗ ██╗███████╗████████╗███╗   ██╗ ██████╗ ██████╗ ███████╗",
    "██╔══██╗██╔══██╗██║██╔════╝╚══██╔══╝████╗  ██║██╔═████╗██╔══██╗██╔════╝",
    "██║  ██║██████╔╝██║█████╗     ██║   ██╔██╗ ██║██║██╔██║██║  ██║█████╗  ",
    "██║  ██║██╔══██╗██║██╔══╝     ██║   ██║╚██╗██║████╔╝██║██║  ██║██╔══╝  ",
    "██████╔╝██║  ██║██║██║        ██║   ██║ ╚████║╚██████╔╝██████╔╝███████╗",
    "╚═════╝ ╚═╝  ╚═╝╚═╝╚═╝        ╚═╝   ╚═╝  ╚═══╝ ╚═════╝ ╚═════╝ ╚══════╝",
]
TAGLINE = "backend-first · full-stack by necessity · privacy-first, local-first"
PROMPT = "~ $ whoami"

W, CW, CH = 860, 10, 18          # canvas width, banner cell width/height
ARMS = {"═": "EW", "║": "NS", "╔": "ES", "╗": "WS", "╚": "NE", "╝": "NW"}
TYPE_DUR = 1.6                    # seconds for the banner to print


def banner_shapes(t, x0, y0):
    blocks, strokes = [], []
    for r, row in enumerate(BANNER):
        c = 0
        while c < len(row):
            if row[c] == "█":  # merge horizontal runs into one rect
                s = c
                while c < len(row) and row[c] == "█":
                    c += 1
                blocks.append(f'<rect x="{x0+s*CW}" y="{y0+r*CH}" width="{(c-s)*CW}" height="{CH}"/>')
                continue
            arms = ARMS.get(row[c])
            if arms:
                cx, cy = x0 + c * CW + CW / 2, y0 + r * CH + CH / 2
                end = {"N": (cx, y0 + r * CH), "S": (cx, y0 + (r + 1) * CH),
                       "E": (x0 + (c + 1) * CW, cy), "W": (x0 + c * CW, cy)}
                strokes += [f"M{cx} {cy}L{end[a][0]} {end[a][1]}" for a in arms]
            c += 1
    return (f'<g fill="{t["accent"]}">{"".join(blocks)}</g>'
            f'<path d="{" ".join(strokes)}" stroke="{t["faint"]}" stroke-width="2" stroke-linecap="square" fill="none"/>')


def build(name, t):
    bw, bh = len(BANNER[0]) * CW, len(BANNER) * CH
    bx, by = (W - bw) // 2, 84
    tag_y = by + bh + 44
    char_w = 7.8
    tag_len = len(TAGLINE) * char_w
    tag_x = (W - tag_len) / 2
    h = tag_y + 34

    body = f"""
<text x="28" y="60" font-size="13" fill="{t['dim']}"><tspan fill="{t['accent']}">driftn0de@github</tspan> {esc(PROMPT)}</text>
<clipPath id="wipe"><rect x="{bx}" y="{by}" width="0" height="{bh}">
  <animate attributeName="width" from="0" to="{bw}" begin="0.3s" dur="{TYPE_DUR}s" fill="freeze"/>
</rect></clipPath>
<g clip-path="url(#wipe)">{banner_shapes(t, bx, by)}</g>
<rect class="cur" x="{bx}" y="{by}" width="{CW}" height="{bh}" fill="{t['fg']}" opacity="0.5">
  <animate attributeName="x" from="{bx}" to="{bx+bw}" begin="0.3s" dur="{TYPE_DUR}s" fill="freeze"/>
  <set attributeName="opacity" to="0" begin="{0.3+TYPE_DUR}s" fill="freeze"/>
</rect>
<g class="tag">
<text x="{tag_x}" y="{tag_y}" font-size="13" textLength="{tag_len}" lengthAdjust="spacing" fill="{t['fg']}">{esc(TAGLINE)}</text>
<rect class="blink" x="{tag_x+tag_len+4}" y="{tag_y-12}" width="8" height="15" fill="{t['accent']}"/>
</g>"""
    style = f""".tag{{opacity:0;animation:in .6s ease-out {0.4+TYPE_DUR}s forwards}}
.blink{{animation:blink 1.1s steps(1) {1.0+TYPE_DUR}s infinite}}
@keyframes in{{to{{opacity:1}}}}
@keyframes blink{{50%{{opacity:0}}}}
@media (prefers-reduced-motion:reduce){{.tag{{opacity:1;animation:none}}.blink{{animation:none}}}}"""
    write(name, window(t, W, h, "driftn0de — zsh", body, style))


if __name__ == "__main__":
    for k, t in THEMES.items():
        build(f"header-{k}.svg", t)
