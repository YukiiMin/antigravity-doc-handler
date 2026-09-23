"""
spec_diagram_engine.py — Backward-compatible shim for legacy PrecisionDiagram engine.
DEPRECATED since v2.0: Migrated to legacy_engines.spec_diagram_engine.
Prefer mxgraph_engine for new code.
"""

from __future__ import annotations

import warnings

warnings.warn(
    "spec_diagram_engine is deprecated as of v2.0 and moved to legacy_engines. "
    "Please migrate to mxgraph_engine for native Draw.io XML and Full HD Canvas export.",
    category=DeprecationWarning,
    stacklevel=2,
)

try:
    from .legacy_engines.spec_diagram_engine import *  # type: ignore
    from .legacy_engines.spec_diagram_engine import (
        PrecisionDiagram,
        Node,
        Edge,
        NodeType,
        PortType,
        ColumnDef,
        ClusterDef,
        _find_chromium_executable,
    )
except (ImportError, ValueError):
    from legacy_engines.spec_diagram_engine import *  # type: ignore
    from legacy_engines.spec_diagram_engine import (
        PrecisionDiagram,
        Node,
        Edge,
        NodeType,
        PortType,
        ColumnDef,
        ClusterDef,
        _find_chromium_executable,
    )
