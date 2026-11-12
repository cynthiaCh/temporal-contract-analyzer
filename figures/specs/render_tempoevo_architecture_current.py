"""Render the Chinese implementation diagram from its editable JSON specification.

Uses local JSON-to-SVG rendering with the Python standard library only.
Coordinates are in SVG pixels.
"""
import argparse
import json
from pathlib import Path
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parent
FONT = "Arial, PingFang SC, Microsoft YaHei, Noto Sans CJK SC, sans-serif"
ICONS = {
    "document": '<path d="M6 3h9l5 5v17H6z M15 3v6h5 M9 13h8 M9 17h8 M9 21h5"/>',
    "ast": '<path d="M14 8v5 M5 13h18 M5 13v6 M14 13v6 M23 13v6"/><rect x="10" y="2" width="8" height="6" rx="1"/><rect x="1" y="19" width="8" height="7" rx="1"/><rect x="10" y="19" width="8" height="7" rx="1"/><rect x="19" y="19" width="8" height="7" rx="1"/>',
    "chip": '<rect x="6" y="6" width="16" height="16" rx="3"/><rect x="10" y="10" width="8" height="8" rx="1"/><path d="M10 2v4 M18 2v4 M10 22v4 M18 22v4 M2 10h4 M2 18h4 M22 10h4 M22 18h4"/>',
    "search": '<circle cx="12" cy="12" r="8"/><path d="M18 18l8 8"/>',
    "code": '<path d="M9 7l-7 7 7 7 M19 7l7 7-7 7 M16 4l-4 20"/>',
    "score": '<rect x="5" y="5" width="19" height="21" rx="2"/><path d="M10 5V2h9v3 M9 13l3 3 7-7 M9 21h10"/>',
    "human": '<circle cx="11" cy="8" r="5"/><path d="M2 26v-5a9 9 0 0118 0 M19 17l3 3 5-6"/>',
    "database": '<ellipse cx="14" cy="6" rx="11" ry="4"/><path d="M3 6v16c0 5 22 5 22 0V6 M3 14c0 5 22 5 22 0"/>',
    "layers": '<path d="M2 8l12-6 12 6-12 6z M2 14l12 6 12-6 M2 20l12 6 12-6"/>',
    "pause": '<circle cx="14" cy="14" r="11"/><path d="M10 9v10 M18 9v10"/>',
}


def validate(spec):
    width, height = spec["canvas"]["width"], spec["canvas"]["height"]
    nodes = {n["id"]: n for n in spec["nodes"]}
    if len(nodes) != len(spec["nodes"]):
        raise ValueError("Duplicate node IDs")
    for n in nodes.values():
        if n["icon"] not in ICONS:
            raise ValueError("Unknown icon: " + n["icon"])
        if not (0 <= n["x"] < n["x"] + n["w"] <= width and
                0 <= n["y"] < n["y"] + n["h"] <= height):
            raise ValueError("Node outside canvas: " + n["id"])
    for i, a in enumerate(spec["nodes"]):
        for b in spec["nodes"][i + 1:]:
            if (max(a["x"], b["x"]) < min(a["x"] + a["w"], b["x"] + b["w"]) and
                    max(a["y"], b["y"]) < min(a["y"] + a["h"], b["y"] + b["h"])):
                raise ValueError("Overlapping nodes: " + a["id"] + ", " + b["id"])
    for edge in spec["edges"]:
        if edge["from"] not in nodes or edge["to"] not in nodes:
            raise ValueError("Unknown edge endpoint")
        if len(edge["points"]) < 2:
            raise ValueError("An edge needs at least two points")


def render(spec):
    validate(spec)
    width, height = spec["canvas"]["width"], spec["canvas"]["height"]
    palette = spec["palette"]
    ink, muted = palette["ink"], palette["muted"]
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
           '<title id="title">' + escape(spec["title"]) + '</title>',
           '<desc id="desc">' + escape(spec["description"]) + '</desc>', '<defs>']
    for name in ("flow", "memory", "stop"):
        color = palette[name]
        svg.append(f'<marker id="arrow-{name}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10Z" fill="{color}"/></marker>')
    for name, body in ICONS.items():
        svg.append(f'<symbol id="icon-{name}" viewBox="0 0 28 28" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{body}</symbol>')
    svg += ['</defs>', '<rect width="100%" height="100%" fill="#FFFFFF"/>',
            f'<g font-family="{FONT}" fill="{ink}">']

    def text(x, y, label, size=22, color=None, weight=400, anchor="start", kind="text"):
        svg.append(f'<text data-kind="{kind}" x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{color or ink}" text-anchor="{anchor}">{escape(label)}</text>')

    def rect(x, y, w, h, fill, stroke="none", radius=16, stroke_width=1.8):
        svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"/>')

    def pill(x, y, w, label, fill, color, size=18):
        rect(x, y, w, 32, fill, radius=16)
        text(x + w / 2, y + 23, label, size, color, 600, "middle", "pill")

    rect(56, 49, 8, 65, palette["flow"], radius=4)
    text(82, 99, "TempoEvo", 58, weight=700)
    text(440, 98, "时序契约引导的代码修复与经验演进", 39, weight=600)
    text(57, 137, spec["subtitle"], 24, muted)
    pill(1634, 66, 310, "基础模型参数冻结", "#E7F4F1", "#176766", 22)

    for group in spec["groups"]:
        theme = palette[group["theme"]]
        rect(group["x"], group["y"], group["w"], group["h"], theme["panel"], theme["stroke"], 28)
        rect(group["x"] + 28, group["y"] + 28, 51, 51, theme["accent"], radius=15)
        text(group["x"] + 53.5, group["y"] + 65, group["letter"], 31, "#FFFFFF", 700, "middle")
        text(group["x"] + 96, group["y"] + 63, group["title"], 33, weight=600)

    # Edges precede cards, so card fills mask any joining geometry cleanly.
    for edge in spec["edges"]:
        kind = edge.get("kind", "flow")
        color = palette[kind]
        points = " ".join(f'{x},{y}' for x, y in edge["points"])
        dash = ' stroke-dasharray="9 7"' if kind == "memory" else ""
        svg.append(f'<polyline data-from="{edge["from"]}" data-to="{edge["to"]}" points="{points}" fill="none" stroke="{color}" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"{dash} marker-end="url(#arrow-{kind})"/>')
        if edge.get("label"):
            lx, ly = edge["label_at"]
            lw = edge["label_width"]
            rect(lx - lw / 2, ly - 22, lw, 30, "#FFFFFF", radius=15)
            text(lx, ly, edge["label"], 20, color, 600, "middle")

    for n in spec["nodes"]:
        theme = palette[n["theme"]]
        x, y, w, h = (n[k] for k in ("x", "y", "w", "h"))
        svg.append(f'<g id="{n["id"]}" data-node="true" data-x="{x}" data-y="{y}" data-w="{w}" data-h="{h}">')
        rect(x, y, w, h, theme["card"], theme["stroke"], 18)
        svg.append(f'<use href="#icon-{n["icon"]}" x="{x + 23}" y="{y + 24}" width="34" height="34" color="{theme["accent"]}"/>')
        text(x + 72, y + 49, n["title"], n.get("title_size", 28), n.get("title_color", ink), 600, kind="node-title")
        if n.get("role"):
            pw = n.get("role_width", 82)
            pill(x + w - pw - 20, y + 23, pw, n["role"], theme["badge"], theme["accent"], 17)
        baseline = y + n.get("body_y", 91)
        for i, line in enumerate(n.get("lines", [])):
            text(x + 26, baseline + i * n.get("line_height", 31), line, n.get("body_size", 22), muted, kind="node-body")
        svg.append('</g>')

    for note in spec["notes"]:
        text(note["x"], note["y"], note["text"], note.get("size", 21), palette.get(note.get("color", "muted"), muted), note.get("weight", 400))

    for mode in spec["modes"]:
        rect(mode["x"], mode["y"], mode["w"], mode["h"], "#F3F8FD", "#D3E1EF", 20)
        text(mode["x"] + 26, mode["y"] + 40, mode["title"], 28, "#326CA2", 600)
        text(mode["x"] + 26, mode["y"] + 80, mode["body"], 22, muted)

    text(57, 1690, spec["version_note"], 19, muted)
    for key, x, label in [("flow", 1255, "执行流程"), ("memory", 1493, "跨任务检索"), ("stop", 1753, "无更新分支")]:
        dash = ' stroke-dasharray="8 6"' if key == "memory" else ""
        svg.append(f'<path d="M{x} 1682h48" stroke="{palette[key]}" stroke-width="3"{dash}/>')
        text(x + 60, 1690, label, 20, muted)
    svg.append('</g></svg>')
    return "\n".join(svg) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", nargs="?", type=Path, default=ROOT / "tempoevo_architecture_current.json")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    validate(spec)
    if args.validate:
        print("Valid specification; node bounds, overlap and edge references checked.")
        return
    output = args.output or ROOT.parent / (args.spec.stem + ".svg")
    output.write_text(render(spec), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
