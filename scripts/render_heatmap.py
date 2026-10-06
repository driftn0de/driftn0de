"""data/contributions.json -> assets/heatmap-{dark,light}.svg

53x7 grid of rounded cells revealed once along the diagonal, month/weekday labels,
a Less→More legend and a stats footer. Runs daily in CI.
"""
import json
from datetime import date

from theme import ROOT, THEMES, esc, window, write

W = 860
CELL, GAP = 11, 3
STEP = CELL + GAP
GX, GY = 76, 82          # grid origin (grid is centered in the 860px panel)
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def columns(days):
    """Group days into week columns (Sunday-first, like GitHub)."""
    cols, col = [], []
    for d in days:
        dow = (date.fromisoformat(d["date"]).weekday() + 1) % 7  # Sun=0
        if dow == 0 and col:
            cols.append(col)
            col = []
        col.append((dow, d))
    if col:
        cols.append(col)
    return cols[-53:]


def build(name, t, data):
    cols = columns(data["days"])
    s = data["stats"]
    cells, labels = [], []
    last_month = None
    for wi, col in enumerate(cols):
        m = date.fromisoformat(col[0][1]["date"]).month
        if m != last_month:
            if wi < len(cols) - 2:
                labels.append(f'<text x="{GX + wi*STEP}" y="{GY-10}" font-size="11" fill="{t["dim"]}">{MONTHS[m-1]}</text>')
            last_month = m
        for dow, d in col:
            tip = f'{d["count"]} contribution{"s" if d["count"] != 1 else ""} on {d["date"]}'
            cells.append(f'<rect class="c" style="animation-delay:{(wi+dow)*14}ms" x="{GX+wi*STEP}" y="{GY+dow*STEP}" '
                         f'width="{CELL}" height="{CELL}" rx="2.5" fill="{t["ramp"][d["level"]]}"><title>{tip}</title></rect>')
    for dow, lab in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        labels.append(f'<text x="{GX-10}" y="{GY+dow*STEP+10}" text-anchor="end" font-size="11" fill="{t["dim"]}">{lab}</text>')

    gy_end = GY + 7 * STEP
    legend_x = GX + len(cols) * STEP - 5 * STEP - 34
    legend = [f'<text x="{legend_x-8}" y="{gy_end+22}" text-anchor="end" font-size="11" fill="{t["dim"]}">Less</text>']
    legend += [f'<rect x="{legend_x+i*STEP}" y="{gy_end+12}" width="{CELL}" height="{CELL}" rx="2.5" fill="{c}"/>'
               for i, c in enumerate(t["ramp"])]
    legend.append(f'<text x="{legend_x+5*STEP+4}" y="{gy_end+22}" font-size="11" fill="{t["dim"]}">More</text>')

    best = s["best_day"]
    best_txt = f'{best["count"]} on {date.fromisoformat(best["date"]).strftime("%b %d")}' if best and best["count"] else "—"
    facts = [("contributions", f'{s["total"]:,}'), ("active days", s["active_days"]),
             ("longest streak", f'{s["longest_streak"]}d'), ("current streak", f'{s["current_streak"]}d'),
             ("best day", best_txt)]
    fy = gy_end + 64
    colw = (W - 2 * GX) / len(facts)
    footer = [f'<line x1="{GX}" y1="{fy-30}" x2="{GX+len(cols)*STEP-GAP}" y2="{fy-30}" stroke="{t["border"]}" stroke-dasharray="3 4"/>']
    for i, (k, v) in enumerate(facts):
        x = GX + i * colw
        footer.append(f'<g class="f" style="animation-delay:{1.2+i*0.1:.1f}s"><text x="{x}" y="{fy}" font-size="16" font-weight="700" fill="{t["accent"]}">{esc(str(v))}</text>'
                      f'<text x="{x}" y="{fy+18}" font-size="11" fill="{t["dim"]}">{k}</text></g>')

    h = fy + 40
    body = (f'<text x="28" y="56" font-size="13" fill="{t["dim"]}"><tspan fill="{t["accent"]}">driftn0de@github</tspan> ~ $ ./contributions.sh --last 365d</text>'
            + "".join(labels) + "".join(cells) + "".join(legend) + "".join(footer))
    style = """.c{opacity:0;transform-box:fill-box;transform-origin:center;animation:pop .35s cubic-bezier(.2,.8,.2,1) forwards}
.f{opacity:0;animation:fade .5s ease-out forwards}
@keyframes pop{from{opacity:0;transform:translateY(-4px) scale(.6)}to{opacity:1;transform:none}}
@keyframes fade{to{opacity:1}}
@media (prefers-reduced-motion:reduce){.c,.f{opacity:1;animation:none}}"""
    write(name, window(t, W, h, f"driftn0de — contributions · updated {data['generated']}", body, style))


if __name__ == "__main__":
    data = json.loads((ROOT / "data" / "contributions.json").read_text())
    for k, t in THEMES.items():
        build(f"heatmap-{k}.svg", t, data)
