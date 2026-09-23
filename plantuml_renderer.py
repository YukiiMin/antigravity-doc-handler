"""
plantuml_renderer.py — Backward-compatible shim for legacy PlantUML engine.
DEPRECATED since v2.0: Migrated to legacy_engines.plantuml_renderer.
Prefer mxgraph_engine for new code.
"""

from __future__ import annotations

import warnings

warnings.warn(
    "plantuml_renderer is deprecated as of v2.0 and moved to legacy_engines. "
    "Please migrate to mxgraph_engine for native Draw.io XML and Full HD Canvas export.",
    category=DeprecationWarning,
    stacklevel=2,
)

try:
    from .legacy_engines.plantuml_renderer import *  # type: ignore
    from .legacy_engines.plantuml_renderer import render_plantuml_to_png
except (ImportError, ValueError):
    from legacy_engines.plantuml_renderer import *  # type: ignore
    from legacy_engines.plantuml_renderer import render_plantuml_to_png
