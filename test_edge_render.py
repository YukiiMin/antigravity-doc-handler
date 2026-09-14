import subprocess
import os
from PIL import Image

svg_content = """<svg xmlns="http://www.w3.org/2000/svg" width="400" height="200" viewBox="0 0 400 200">
  <rect width="100%" height="100%" fill="#ffffff"/>
  <rect x="50" y="50" width="300" height="100" fill="#ffffff" stroke="#000000" stroke-width="2.5" rx="4"/>
  <text x="200" y="105" font-family="Segoe UI, Arial" font-size="16" font-weight="bold" fill="#000000" text-anchor="middle">Test Precision Engine</text>
</svg>"""

tmp_svg = r"C:\Users\Admin\.gemini\antigravity-ide\brain\87b1a733-0a78-4a87-8b33-42d7ca05890d\test_edge.svg"
tmp_png = r"C:\Users\Admin\.gemini\antigravity-ide\brain\87b1a733-0a78-4a87-8b33-42d7ca05890d\test_edge.png"

with open(tmp_svg, "w", encoding="utf-8") as f:
    f.write(svg_content)

edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
cmd = [
    edge_path,
    "--headless",
    "--disable-gpu",
    "--hide-scrollbars",
    "--force-device-scale-factor=3",
    "--window-size=400,200",
    f"--screenshot={tmp_png}",
    tmp_svg
]
res = subprocess.run(cmd, capture_output=True, text=True)
print("Return code:", res.returncode)
print("PNG exists:", os.path.isfile(tmp_png))
if os.path.isfile(tmp_png):
    im = Image.open(tmp_png)
    print("Rendered PNG size:", im.size)
