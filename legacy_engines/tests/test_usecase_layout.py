"""
tests/test_usecase_layout.py — Test execution of Use Case diagram generator and fidelity checks.
"""
import os
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(TESTS_DIR, ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from tools.gen_usecase_diagram import generate_usecase_svg, render_to_png, USE_CASES, ACTORS


def test_usecase_diagram_generation():
    assert len(USE_CASES) == 48, f"Expected 48 use cases, got {len(USE_CASES)}"
    assert len(ACTORS) == 6, f"Expected 6 actors, got {len(ACTORS)}"

    svg_content = generate_usecase_svg()
    assert "<svg" in svg_content
    assert "</svg>" in svg_content
    assert "Smart Supermarket System" not in svg_content or "<rect" in svg_content

    out_png = os.path.join(ROOT_DIR, "diagram_assets", "usecase_smart_mart.png")
    res = render_to_png(svg_content, out_png, scale=3)
    assert res["success"] is True
    assert os.path.isfile(out_png)
    assert res["dimensions"] == (3072, 2703)
    print(f"PASS: Use Case Diagram successfully verified ({res['dimensions']} px, {res['file_size']} bytes).")


if __name__ == "__main__":
    test_usecase_diagram_generation()
