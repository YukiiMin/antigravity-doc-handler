import os
import subprocess

os.makedirs("scratch", exist_ok=True)
svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="650" height="420" viewBox="0 0 650 420" style="background:#ffffff;">']

symbols = [
    ("one", "One"),
    ("many", "Many"),
    ("one_and_only_one", "One (and only one)"),
    ("zero_or_one", "Zero or one"),
    ("one_or_many", "One or many"),
    ("zero_or_many", "Zero or many"),
]

w = 7.0
stroke_c = "#E65100"
stroke_w = "2.8"

for idx, (sym, label) in enumerate(symbols):
    y = 45 + idx * 60
    px = 360.0  # entity boundary
    py = float(y)
    ux, uy = -1.0, 0.0  # pointing away from entity (to left)
    nx, ny = -uy, ux    # (0, -1), perpendicular

    # Draw main line from x=50 to px
    svg.append(f'<line x1="50" y1="{py}" x2="{px}" y2="{py}" stroke="{stroke_c}" stroke-width="{stroke_w}"/>')
    # Entity boundary line
    svg.append(f'<line x1="{px}" y1="{py-25}" x2="{px}" y2="{py+25}" stroke="#1E293B" stroke-width="2.5"/>')
    svg.append(f'<text x="400" y="{py+5}" font-family="Segoe UI, Arial, sans-serif" font-size="16" font-weight="bold" fill="#1E293B">{label}</text>')

    if sym == "one":
        d = 12.0
        cx, cy = px + ux * d, py + uy * d
        svg.append(f'<line x1="{cx + nx*w:.1f}" y1="{cy + ny*w:.1f}" x2="{cx - nx*w:.1f}" y2="{cy - ny*w:.1f}" stroke="{stroke_c}" stroke-width="{stroke_w}" stroke-linecap="round"/>')
    elif sym == "many":
        d_apex = 16.0
        d_end = 2.0
        ax, ay = px + ux * d_apex, py + uy * d_apex
        e1x, e1y = px + ux * d_end + nx * w, py + uy * d_end + ny * w
        e2x, e2y = px + ux * d_end - nx * w, py + uy * d_end - ny * w
        svg.append(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{e1x:.1f}" y2="{e1y:.1f}" stroke="{stroke_c}" stroke-width="{stroke_w}" stroke-linecap="round"/>')
        svg.append(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{e2x:.1f}" y2="{e2y:.1f}" stroke="{stroke_c}" stroke-width="{stroke_w}" stroke-linecap="round"/>')
    elif sym == "one_and_only_one":
        for d in (8.0, 16.0):
            cx, cy = px + ux * d, py + uy * d
            svg.append(f'<line x1="{cx + nx*w:.1f}" y1="{cy + ny*w:.1f}" x2="{cx - nx*w:.1f}" y2="{cy - ny*w:.1f}" stroke="{stroke_c}" stroke-width="{stroke_w}" stroke-linecap="round"/>')
    elif sym == "zero_or_one":
        # tick closer to entity (d=8)
        cx, cy = px + ux * 8.0, py + uy * 8.0
        svg.append(f'<line x1="{cx + nx*w:.1f}" y1="{cy + ny*w:.1f}" x2="{cx - nx*w:.1f}" y2="{cy - ny*w:.1f}" stroke="{stroke_c}" stroke-width="{stroke_w}" stroke-linecap="round"/>')
        # circle further from entity (d=19)
        ox, oy = px + ux * 19.0, py + uy * 19.0
        svg.append(f'<circle cx="{ox:.1f}" cy="{oy:.1f}" r="5.5" fill="#ffffff" stroke="{stroke_c}" stroke-width="{stroke_w}"/>')
    elif sym == "one_or_many":
        # crow foot flaring to entity
        d_apex = 14.0
        d_end = 2.0
        ax, ay = px + ux * d_apex, py + uy * d_apex
        e1x, e1y = px + ux * d_end + nx * w, py + uy * d_end + ny * w
        e2x, e2y = px + ux * d_end - nx * w, py + uy * d_end - ny * w
        svg.append(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{e1x:.1f}" y2="{e1y:.1f}" stroke="{stroke_c}" stroke-width="{stroke_w}" stroke-linecap="round"/>')
        svg.append(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{e2x:.1f}" y2="{e2y:.1f}" stroke="{stroke_c}" stroke-width="{stroke_w}" stroke-linecap="round"/>')
        # tick further from entity (d=21)
        cx, cy = px + ux * 21.0, py + uy * 21.0
        svg.append(f'<line x1="{cx + nx*w:.1f}" y1="{cy + ny*w:.1f}" x2="{cx - nx*w:.1f}" y2="{cy - ny*w:.1f}" stroke="{stroke_c}" stroke-width="{stroke_w}" stroke-linecap="round"/>')
    elif sym == "zero_or_many":
        # crow foot flaring to entity
        d_apex = 14.0
        d_end = 2.0
        ax, ay = px + ux * d_apex, py + uy * d_apex
        e1x, e1y = px + ux * d_end + nx * w, py + uy * d_end + ny * w
        e2x, e2y = px + ux * d_end - nx * w, py + uy * d_end - ny * w
        svg.append(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{e1x:.1f}" y2="{e1y:.1f}" stroke="{stroke_c}" stroke-width="{stroke_w}" stroke-linecap="round"/>')
        svg.append(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{e2x:.1f}" y2="{e2y:.1f}" stroke="{stroke_c}" stroke-width="{stroke_w}" stroke-linecap="round"/>')
        # circle further from entity (d=22)
        ox, oy = px + ux * 22.0, py + uy * 22.0
        svg.append(f'<circle cx="{ox:.1f}" cy="{oy:.1f}" r="5.5" fill="#ffffff" stroke="{stroke_c}" stroke-width="{stroke_w}"/>')

svg.append("</svg>")
svg_path = "scratch/test_cardinality.svg"
png_path = "scratch/test_cardinality.png"
with open(svg_path, "w", encoding="utf-8") as f:
    f.write("\n".join(svg))

# Render to PNG using chromium headless
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from spec_diagram_engine import _find_chromium_executable
exe = _find_chromium_executable()
if exe:
    cmd = [exe, "--headless", "--disable-gpu", "--window-size=650,420", f"--screenshot={os.path.abspath(png_path)}", os.path.abspath(svg_path)]
    subprocess.run(cmd, check=True)
    print("Rendered PNG successfully:", png_path)
