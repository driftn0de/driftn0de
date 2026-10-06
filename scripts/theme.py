"""Shared palette + SVG helpers. Every generator renders a dark and a light variant."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono','DejaVu Sans Mono',monospace"

THEMES = {
    "dark": {
        "bg": "#0d1117", "panel": "#010409", "border": "#30363d", "bar": "#161b22",
        "fg": "#c9d1d9", "dim": "#7d8590", "faint": "#484f58",
        "accent": "#2ee6c9", "accent2": "#79c0ff", "warn": "#e3b341",
        "ramp": ["#161b22", "#0b3d3a", "#0f6b63", "#1aa594", "#2ee6c9"],
    },
    "light": {
        "bg": "#ffffff", "panel": "#f6f8fa", "border": "#d0d7de", "bar": "#eaeef2",
        "fg": "#1f2328", "dim": "#59636e", "faint": "#afb8c1",
        "accent": "#0b7a6b", "accent2": "#0969da", "warn": "#9a6700",
        "ramp": ["#ebedf0", "#b4ede3", "#5fd4c2", "#1fa392", "#0b6b5e"],
    },
}


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def window(t: dict, w: int, h: int, title: str, body: str, style: str = "") -> str:
    """A terminal window: rounded panel, title bar with three dots, centered title."""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(title)}">
<style>
text{{font-family:{MONO};}}
{style}
</style>
<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="10" fill="{t['panel']}" stroke="{t['border']}"/>
<path d="M0.5 10.5a10 10 0 0 1 10-10h{w-21}a10 10 0 0 1 10 10V32.5H0.5z" fill="{t['bar']}"/>
<line x1="0.5" y1="32.5" x2="{w-0.5}" y2="32.5" stroke="{t['border']}"/>
<circle cx="20" cy="16.5" r="5.5" fill="#ff5f57"/><circle cx="38" cy="16.5" r="5.5" fill="#febc2e"/><circle cx="56" cy="16.5" r="5.5" fill="#28c840"/>
<text x="{w/2}" y="21" text-anchor="middle" font-size="12" fill="{t['dim']}">{esc(title)}</text>
{body}
</svg>
"""


def write(name: str, svg: str) -> None:
    ASSETS.mkdir(exist_ok=True)
    (ASSETS / name).write_text(svg, encoding="utf-8")
    print("wrote", ASSETS / name)
