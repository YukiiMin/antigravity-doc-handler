"""
mermaid_renderer.py — Mermaid Diagram Engine for AI Document Toolkit.

Renders Mermaid code into high-resolution PNG using @mermaid-js/mermaid-cli (mmdc),
with built-in styling themes (clean_modern, enterprise), 2D aspect-ratio scaling
(max width <= 14cm, max height <= 20cm), Windows subprocess & temp file locking protection,
and atomic injection into DOCX via docx_writer.
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
_THEMES_DIR = os.path.join(_CURRENT_DIR, "mermaid_themes")
_PUPPETEER_CONFIG = os.path.join(_CURRENT_DIR, "puppeteer-config.json")


def _find_mmdc_cmd() -> list[str]:
    """
    Locate the mmdc executable or npx fallback.
    Returns a command prefix list, e.g. ['mmdc.cmd'] or ['npx.cmd', '-y', '@mermaid-js/mermaid-cli'].
    """
    mmdc_path = shutil.which("mmdc") or shutil.which("mmdc.cmd")
    if mmdc_path:
        return [mmdc_path]

    npx_path = shutil.which("npx") or shutil.which("npx.cmd")
    if npx_path:
        return [npx_path, "-y", "@mermaid-js/mermaid-cli"]

    raise EnvironmentError(
        "Neither mmdc nor npx found in system PATH. Node.js (@mermaid-js/mermaid-cli) is required."
    )


def _resolve_theme_config(preset: str | None) -> str | None:
    """Resolve theme preset name to path, or return custom json path."""
    if not preset:
        preset = "clean_modern"

    # Built-in theme preset
    theme_file = os.path.join(_THEMES_DIR, f"{preset}.json")
    if os.path.isfile(theme_file):
        return os.path.abspath(theme_file)

    # Custom theme path
    if os.path.isfile(preset):
        return os.path.abspath(preset)

    # Default fallback
    fallback = os.path.join(_THEMES_DIR, "clean_modern.json")
    return os.path.abspath(fallback) if os.path.isfile(fallback) else None


def calculate_aspect_dimensions(
    png_w_px: int,
    png_h_px: int,
    max_w_cm: float = 14.0,
    max_h_cm: float = 20.0,
) -> tuple[float, float]:
    """
    Scale 2D preserving aspect ratio (Patch 1):
    width <= max_w_cm (default 14.0cm) AND height <= max_h_cm (default 20.0cm).
    """
    if png_w_px <= 0 or png_h_px <= 0:
        return max_w_cm, max_h_cm

    scaled_h = (png_h_px / png_w_px) * max_w_cm
    if scaled_h <= max_h_cm:
        return round(max_w_cm, 2), round(scaled_h, 2)

    # Height exceeds max_h_cm -> scale based on height
    final_h = max_h_cm
    final_w = (png_w_px / png_h_px) * max_h_cm
    final_w = min(final_w, max_w_cm)
    return round(final_w, 2), round(final_h, 2)


def render_mermaid_to_png(
    spec: dict[str, Any],
    base_dir: str | None = None,
) -> dict[str, Any]:
    """
    Render Mermaid code to PNG and optionally inject it into DOCX.

    Args:
        spec: Dictionary conforming to mermaid-render spec schema:
            - mermaid_code: str (required)
            - diagram_name: str (default: "diagram")
            - theme_preset: str ("clean_modern" | "enterprise" | custom path)
            - scale: int/float (default: 2)
            - width_cm: float (default: 14.0)
            - max_height_cm: float (default: 20.0)
            - output_path: str (optional, overrides default PNG path)
            - inject_into: str (optional, destination DOCX path)
            - placeholder: str (optional, e.g. "{{DIAGRAM_AUTH_FLOW}}")
            - target_heading: str (optional)
            - target_element_index: int (optional)
            - caption_template: dict | str (optional)
        base_dir: Optional base directory for relative path resolution.

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
    mermaid_code = spec.get("mermaid_code")
    if not mermaid_code or not mermaid_code.strip():
        raise ValueError("Field 'mermaid_code' is missing or empty in spec")

    diagram_name = spec.get("diagram_name", "diagram")
    scale_factor = str(spec.get("scale", 2))
    theme_config = _resolve_theme_config(spec.get("theme_preset"))

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
        # Convention: diagram_assets/ next to destination DOCX
        docx_dir = os.path.dirname(os.path.abspath(inject_docx))
        docx_stem = os.path.splitext(os.path.basename(inject_docx))[0]
        assets_dir = os.path.join(docx_dir, "diagram_assets")
        output_png = os.path.abspath(os.path.join(assets_dir, f"{docx_stem}_{diagram_name}.png"))
    else:
        # Convention: diagram_assets/ in base_dir or cwd
        parent_dir = base_dir or os.getcwd()
        assets_dir = os.path.join(parent_dir, "diagram_assets")
        output_png = os.path.abspath(os.path.join(assets_dir, f"{diagram_name}.png"))

    os.makedirs(os.path.dirname(output_png), exist_ok=True)

    # Windows Patch 4: Create temp .mmd and CLOSE it before subprocess to prevent OS file lock
    tmp = tempfile.NamedTemporaryFile(suffix=".mmd", mode="w", encoding="utf-8", delete=False)
    tmp.write(mermaid_code.strip() + "\n")
    tmp.close()

    cmd_prefix = _find_mmdc_cmd()
    cmd = list(cmd_prefix)
    cmd.extend(["-i", tmp.name, "-o", output_png, "-s", scale_factor])

    if theme_config and os.path.isfile(theme_config):
        cmd.extend(["-c", theme_config])

    if os.path.isfile(_PUPPETEER_CONFIG):
        cmd.extend(["-p", _PUPPETEER_CONFIG])

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            shell=(os.name == "nt"),
        )
    finally:
        # Clean up temporary .mmd file
        try:
            os.unlink(tmp.name)
        except OSError:
            pass

    # Atomic Protection: if Mermaid CLI failed, fail loudly and NEVER touch DOCX
    if proc.returncode != 0:
        err_msg = proc.stderr.strip() or proc.stdout.strip()
        raise RuntimeError(
            f"Mermaid CLI rendering failed (exit code {proc.returncode}). DOCX was not modified.\nDetail:\n{err_msg}"
        )

    # Validate output PNG
    if not os.path.isfile(output_png):
        raise FileNotFoundError(f"Rendered PNG was not created at expected path: {output_png}")

    file_size = os.path.getsize(output_png)
    if file_size < 1024:
        raise ValueError(
            f"Rendered PNG is smaller than 1KB ({file_size} bytes), indicating an incomplete render: {output_png}"
        )

    # Read dimensions using Pillow and calculate 2D scaled size (Patch 1)
    with Image.open(output_png) as img:
        png_w_px, png_h_px = img.size

    max_w = float(spec.get("width_cm") or 14.0)
    max_h = float(spec.get("max_height_cm") or 20.0)
    final_w_cm, final_h_cm = calculate_aspect_dimensions(png_w_px, png_h_px, max_w, max_h)

    # Inject into DOCX if requested
    injected = False
    saved_docx_path: str | None = None
    if inject_docx:
        from .docx_writer import inject_diagram_into_docx

        diag_spec = {
            "image_path": output_png,
            "width_cm": final_w_cm,
            "height_cm": final_h_cm,
            "placeholder": spec.get("placeholder"),
            "target_heading": spec.get("target_heading"),
            "target_element_index": spec.get("target_element_index"),
            "replace_empty_after": spec.get("replace_empty_after", False),
            "caption_template": spec.get("caption_template"),
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


def render_mermaid_from_spec_file(spec_file_path: str) -> dict[str, Any]:
    """Load JSON spec file and execute render_mermaid_to_png."""
    spec_path = os.path.abspath(spec_file_path)
    if not os.path.isfile(spec_path):
        raise FileNotFoundError(f"Spec file not found: {spec_path}")

    with open(spec_path, "r", encoding="utf-8") as f:
        spec = json.load(f)

    base_dir = os.path.dirname(spec_path)
    return render_mermaid_to_png(spec, base_dir=base_dir)
