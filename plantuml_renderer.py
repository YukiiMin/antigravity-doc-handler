"""
plantuml_renderer.py — PlantUML Diagram Engine for AI Document Toolkit.

Renders PlantUML diagrams into high-resolution PNG using local plantuml.jar and Java runtime,
with built-in support for:
- 100% offline Standard Library (C4-PlantUML: <C4/C4_Context>, etc.)
- UTF-8 encoding flag (-charset UTF-8) to prevent Vietnamese character corruption on Windows
- JVM limit expansion (-DPLANTUML_LIMIT_SIZE=16384) to support massive ERD/architecture diagrams
- 2D aspect-ratio scaling (max width <= 14cm, max height <= 20cm)
- Windows subprocess & temp file locking protection
- Atomic injection into DOCX via docx_writer
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from typing import Any
from PIL import Image

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


def _find_java_cmd() -> str:
    """Locate java executable in system PATH."""
    java_path = shutil.which("java") or shutil.which("java.exe")
    if not java_path:
        raise EnvironmentError(
            "Java runtime (JRE/JDK >= 8) not found in system PATH. "
            "Please install Java to use the PlantUML diagram engine."
        )
    return java_path


def _find_plantuml_jar(custom_jar: str | None = None) -> str:
    """
    Locate plantuml.jar using priority chain:
    1. Explicit custom_jar path
    2. Environment variable PLANTUML_JAR
    3. tools/plantuml.jar in current directory
    4. ../tools/plantuml.jar (workspace level)
    5. PATH lookup
    """
    if custom_jar and os.path.isfile(custom_jar):
        return os.path.abspath(custom_jar)

    env_jar = os.environ.get("PLANTUML_JAR")
    if env_jar and os.path.isfile(env_jar):
        return os.path.abspath(env_jar)

    candidate_local = os.path.join(_CURRENT_DIR, "tools", "plantuml.jar")
    if os.path.isfile(candidate_local):
        return os.path.abspath(candidate_local)

    candidate_parent = os.path.join(os.path.dirname(_CURRENT_DIR), "tools", "plantuml.jar")
    if os.path.isfile(candidate_parent):
        return os.path.abspath(candidate_parent)

    which_jar = shutil.which("plantuml.jar")
    if which_jar and os.path.isfile(which_jar):
        return os.path.abspath(which_jar)

    raise FileNotFoundError(
        "plantuml.jar not found. Please place plantuml.jar into 'tools/plantuml.jar' "
        "or set the PLANTUML_JAR environment variable."
    )


def calculate_aspect_dimensions(
    png_w_px: int,
    png_h_px: int,
    max_w_cm: float = 14.0,
    max_h_cm: float = 20.0,
) -> tuple[float, float]:
    """
    Scale 2D preserving aspect ratio:
    width <= max_w_cm (default 14.0cm) AND height <= max_h_cm (default 20.0cm).
    """
    if png_w_px <= 0 or png_h_px <= 0:
        return max_w_cm, max_h_cm

    scaled_h = (png_h_px / png_w_px) * max_w_cm
    if scaled_h <= max_h_cm:
        return round(max_w_cm, 2), round(scaled_h, 2)

    final_h = max_h_cm
    final_w = (png_w_px / png_h_px) * max_h_cm
    final_w = min(final_w, max_w_cm)
    return round(final_w, 2), round(final_h, 2)


def render_plantuml_to_png(
    spec: dict[str, Any],
    base_dir: str | None = None,
    jar_path: str | None = None,
) -> dict[str, Any]:
    """
    Render PlantUML code to high-res PNG and optionally inject it into DOCX.

    Args:
        spec: Dictionary conforming to diagram spec schema:
            - code / plantuml_code: str (required, PlantUML source code)
            - diagram_name: str (default: "diagram")
            - dpi: int (default: 300)
            - width_cm: float (default: 14.0)
            - max_height_cm: float (default: 20.0)
            - output_path: str (optional, overrides default PNG path)
            - inject_into: str (optional, destination DOCX path)
            - placeholder: str (optional, e.g. "{{DIAGRAM_ERD}}")
            - target_heading: str (optional)
            - target_element_index: int (optional)
            - caption / caption_template: str | dict (optional)
        base_dir: Optional base directory for relative path resolution.
        jar_path: Optional explicit path to plantuml.jar.

    Returns:
        Dictionary with execution results:
            - success: bool
            - png_path: str
            - width_cm: float
            - height_cm: float
            - dimensions_px: tuple[int, int]
            - file_size_bytes: int
            - injected: bool
            - docx_path: str | None
    """
    plantuml_code = spec.get("code") or spec.get("plantuml_code")
    if not plantuml_code or not plantuml_code.strip():
        raise ValueError("Field 'code' or 'plantuml_code' is missing or empty in spec")

    java_bin = _find_java_cmd()
    plantuml_jar = _find_plantuml_jar(jar_path)

    diagram_name = spec.get("diagram_name", "diagram")
    dpi = int(spec.get("dpi", 300))

    # Determine destination PNG path
    output_png = spec.get("output_path")
    inject_docx = spec.get("inject_into")
    if inject_docx and not os.path.isabs(inject_docx) and base_dir:
        inject_docx = os.path.abspath(os.path.join(base_dir, inject_docx))

    if output_png:
        if not os.path.isabs(output_png) and base_dir:
            output_png = os.path.abspath(os.path.join(base_dir, output_png))
        else:
            output_png = os.path.abspath(output_png)
    elif inject_docx:
        docx_dir = os.path.dirname(os.path.abspath(inject_docx))
        docx_stem = os.path.splitext(os.path.basename(inject_docx))[0]
        assets_dir = os.path.join(docx_dir, "diagram_assets")
        output_png = os.path.abspath(os.path.join(assets_dir, f"{docx_stem}_{diagram_name}.png"))
    else:
        parent_dir = base_dir or os.getcwd()
        assets_dir = os.path.join(parent_dir, "diagram_assets")
        output_png = os.path.abspath(os.path.join(assets_dir, f"{diagram_name}.png"))

    os.makedirs(os.path.dirname(output_png), exist_ok=True)

    # Windows Trap 2 & Trap 4: Create temp .puml, write with UTF-8, and close handle before subprocess
    tmp_puml = tempfile.NamedTemporaryFile(suffix=".puml", mode="w", encoding="utf-8", delete=False)
    tmp_puml.write(plantuml_code.strip() + "\n")
    tmp_puml.close()

    temp_out_dir = tempfile.mkdtemp(prefix="plantuml_out_")

    # Windows Trap 2: -charset UTF-8
    # Windows Trap 3: -DPLANTUML_LIMIT_SIZE=16384
    cmd = [
        java_bin,
        "-DPLANTUML_LIMIT_SIZE=16384",
        "-jar",
        plantuml_jar,
        "-charset",
        "UTF-8",
        f"-Sdpi={dpi}",
        "-tpng",
        "-o",
        temp_out_dir,
        tmp_puml.name,
    ]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            shell=(os.name == "nt"),
        )
    finally:
        try:
            os.unlink(tmp_puml.name)
        except OSError:
            pass

    # Atomic Protection: check exit code and stderr
    if proc.returncode != 0:
        err_msg = proc.stderr.strip() or proc.stdout.strip()
        shutil.rmtree(temp_out_dir, ignore_errors=True)
        raise RuntimeError(
            f"PlantUML rendering failed (exit code {proc.returncode}). DOCX was not modified.\nDetail:\n{err_msg}"
        )

    # Find generated PNG in temp_out_dir
    generated_pngs = [
        f for f in os.listdir(temp_out_dir) if f.lower().endswith(".png")
    ]
    if not generated_pngs:
        shutil.rmtree(temp_out_dir, ignore_errors=True)
        err_detail = proc.stderr.strip() or proc.stdout.strip()
        raise FileNotFoundError(
            f"PlantUML did not generate any PNG file in output directory.\nConsole output:\n{err_detail}"
        )

    temp_png_path = os.path.join(temp_out_dir, generated_pngs[0])

    # Move generated PNG to target location
    if os.path.isfile(output_png):
        try:
            os.unlink(output_png)
        except OSError:
            pass
    shutil.move(temp_png_path, output_png)
    shutil.rmtree(temp_out_dir, ignore_errors=True)

    # Validate output PNG
    if not os.path.isfile(output_png):
        raise FileNotFoundError(f"Rendered PNG was not created at expected path: {output_png}")

    file_size = os.path.getsize(output_png)
    if file_size < 512:
        raise ValueError(
            f"Rendered PNG is smaller than 512 bytes ({file_size} bytes), indicating an incomplete render: {output_png}"
        )

    # Read dimensions using Pillow and calculate 2D scaled size
    with Image.open(output_png) as img:
        png_w_px, png_h_px = img.size

    max_w = float(spec.get("width_cm") or 14.0)
    max_h = float(spec.get("max_height_cm") or 20.0)
    final_w_cm, final_h_cm = calculate_aspect_dimensions(png_w_px, png_h_px, max_w, max_h)

    # Inject into DOCX if requested
    injected = False
    saved_docx_path: str | None = None
    if inject_docx and os.path.isfile(inject_docx):
        try:
            from .docx_writer import inject_diagram_into_docx
        except (ImportError, ValueError):
            from docx_writer import inject_diagram_into_docx  # type: ignore

        caption_val = spec.get("caption_template") or spec.get("caption")
        diag_spec = {
            "image_path": output_png,
            "width_cm": final_w_cm,
            "height_cm": final_h_cm,
            "placeholder": spec.get("placeholder"),
            "target_heading": spec.get("target_heading"),
            "target_element_index": spec.get("target_element_index"),
            "replace_empty_after": spec.get("replace_empty_after", False),
            "caption_template": caption_val,
        }
        saved_docx_path = inject_diagram_into_docx(inject_docx, diag_spec)
        injected = True

    return {
        "success": True,
        "png_path": output_png,
        "width_cm": final_w_cm,
        "height_cm": final_h_cm,
        "dimensions_px": (png_w_px, png_h_px),
        "file_size_bytes": file_size,
        "injected": injected,
        "docx_path": saved_docx_path,
    }


def render_plantuml(
    plantuml_code: str,
    output_png: str,
    dpi: int = 300,
    jar_path: str | None = None,
) -> dict[str, Any]:
    """
    Direct programmatic API to render PlantUML source code into a PNG file.
    """
    spec = {
        "code": plantuml_code,
        "output_path": output_png,
        "dpi": dpi,
    }
    return render_plantuml_to_png(spec, jar_path=jar_path)


def render_plantuml_from_spec_file(spec_file_path: str) -> dict[str, Any]:
    """Load JSON spec file and execute render_plantuml_to_png."""
    spec_path = os.path.abspath(spec_file_path)
    if not os.path.isfile(spec_path):
        raise FileNotFoundError(f"Spec file not found: {spec_path}")

    with open(spec_path, "r", encoding="utf-8") as f:
        spec = json.load(f)

    base_dir = os.path.dirname(spec_path)
    return render_plantuml_to_png(spec, base_dir=base_dir)
