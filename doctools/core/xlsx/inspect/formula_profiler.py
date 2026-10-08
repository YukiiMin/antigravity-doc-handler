"""
doctools.core.xlsx.inspect.formula_profiler
Formula Analyzer implementing R1C1 canonical grouping, dependency graphing,
circular reference detection, and deterministic empty-cell reference warnings (FR-31, D-26, EV-15).
"""

from __future__ import annotations
from collections import defaultdict
import re
from typing import Any, Dict, List, Optional, Set, Tuple
import openpyxl
from openpyxl.formula.tokenizer import Token, Tokenizer
from openpyxl.worksheet.worksheet import Worksheet

CELL_REF_RE = re.compile(r"^(\$?)([A-Za-z]+)(\$?)([0-9]+)$")


def a1_to_r1c1_coordinate(cell_ref: str, base_row: int, base_col: int) -> str:
    """Converts a single A1 cell coordinate into canonical R1C1 notation relative to base cell."""
    m = CELL_REF_RE.match(cell_ref.strip())
    if not m:
        return cell_ref

    abs_col_sign, col_str, abs_row_sign, row_str = m.groups()
    try:
        col_num = openpyxl.utils.column_index_from_string(col_str)
        row_num = int(row_str)
    except Exception:
        return cell_ref

    # Row component
    if abs_row_sign:
        r_part = f"R{row_num}"
    else:
        diff_r = row_num - base_row
        r_part = "R" if diff_r == 0 else f"R[{diff_r}]"

    # Column component
    if abs_col_sign:
        c_part = f"C{col_num}"
    else:
        diff_c = col_num - base_col
        c_part = "C" if diff_c == 0 else f"C[{diff_c}]"

    return f"{r_part}{c_part}"


def normalize_formula_to_r1c1(formula: str, base_row: int, base_col: int) -> str:
    """Converts an entire A1 formula into a canonical R1C1 pattern."""
    if not formula.startswith("="):
        return formula

    try:
        tok = Tokenizer(formula)
    except Exception:
        return formula

    out: List[str] = []
    for t in tok.items:
        if t.type == Token.OPERAND and t.subtype == Token.RANGE:
            val = t.value
            sheet_pfx = ""
            ref = val
            if "!" in val:
                sheet_pfx, ref = val.split("!", 1)
                sheet_pfx += "!"

            if ":" in ref:
                parts = ref.split(":", 1)
                r1 = a1_to_r1c1_coordinate(parts[0], base_row, base_col)
                r2 = a1_to_r1c1_coordinate(parts[1], base_row, base_col)
                out.append(f"{sheet_pfx}{r1}:{r2}")
            else:
                out.append(f"{sheet_pfx}{a1_to_r1c1_coordinate(ref, base_row, base_col)}")
        else:
            out.append(t.value)

    res = "".join(out)
    if not res.startswith("="):
        res = "=" + res
    return res


class FormulaProfiler:
    """Performs deep static analysis and pattern grouping across formulas."""

    def __init__(self, wb: openpyxl.Workbook) -> None:
        self.wb = wb

    def profile(self, target_sheet: Optional[str] = None) -> Dict[str, Any]:
        """Runs full formula profiling: R1C1 grouping, pattern breaks, dependencies, and empty-cell warnings."""
        sheets = [self.wb[target_sheet]] if target_sheet and target_sheet in self.wb.sheetnames else self.wb.worksheets

        # 1. Collect all formulas and their R1C1 patterns
        formulas_by_col: Dict[Tuple[str, int], List[Dict[str, Any]]] = defaultdict(list)
        function_counts: Dict[str, int] = defaultdict(int)
        dep_graph: Dict[str, Set[str]] = defaultdict(set)
        empty_cell_refs: List[Dict[str, Any]] = []

        for ws in sheets:
            sheet_name = ws.title
            for r in range(1, ws.max_row + 1):
                for c in range(1, ws.max_column + 1):
                    cell = ws.cell(row=r, column=c)
                    val = cell.value
                    if val is not None and str(val).startswith("="):
                        formula_str = str(val).strip()
                        r1c1 = normalize_formula_to_r1c1(formula_str, r, c)
                        item = {
                            "sheet": sheet_name,
                            "row": r,
                            "col": c,
                            "coord": cell.coordinate,
                            "formula": formula_str,
                            "r1c1": r1c1,
                        }
                        formulas_by_col[(sheet_name, c)].append(item)

                        # Parse tokens for function counts and dependencies
                        self._analyze_tokens(
                            formula_str,
                            sheet_name,
                            cell.coordinate,
                            function_counts,
                            dep_graph,
                            empty_cell_refs,
                        )

        # 2. Group into primary patterns and detect pattern breaks (W-FORMULA-PATTERN-BREAK)
        pattern_groups: List[Dict[str, Any]] = []
        pattern_breaks: List[Dict[str, Any]] = []

        for (sheet_name, col_idx), items in formulas_by_col.items():
            if not items:
                continue

            patterns_in_col: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
            for it in items:
                patterns_in_col[it["r1c1"]].append(it)

            # Dominant pattern in column
            dominant_r1c1, dominant_items = max(patterns_in_col.items(), key=lambda kv: len(kv[1]))

            pattern_groups.append({
                "sheet": sheet_name,
                "column": openpyxl.utils.get_column_letter(col_idx),
                "r1c1_pattern": dominant_r1c1,
                "count": len(dominant_items),
                "sample_a1": dominant_items[0]["formula"],
                "range": f"{dominant_items[0]['coord']}:{dominant_items[-1]['coord']}",
            })

            # Any items that deviate from the dominant pattern when dominant has >= 3 items
            if len(dominant_items) >= 3:
                for r1c1, outlier_items in patterns_in_col.items():
                    if r1c1 != dominant_r1c1:
                        for out_it in outlier_items:
                            pattern_breaks.append({
                                "code": "W-FORMULA-PATTERN-BREAK",
                                "sheet": sheet_name,
                                "coord": out_it["coord"],
                                "formula": out_it["formula"],
                                "expected_r1c1": dominant_r1c1,
                                "actual_r1c1": r1c1,
                                "message": f"Cell {out_it['coord']} formula breaks dominant column pattern.",
                            })

        # 3. Detect Circular References (W-FORMULA-CIRCULAR)
        circular_refs = self._detect_cycles(dep_graph)

        return {
            "total_formulas": sum(len(items) for items in formulas_by_col.values()),
            "pattern_groups": pattern_groups,
            "pattern_breaks": pattern_breaks,
            "empty_cell_references": empty_cell_refs,
            "circular_references": circular_refs,
            "function_frequencies": dict(sorted(function_counts.items(), key=lambda kv: -kv[1])),
            "cross_sheet_dependencies_count": sum(len(targets) for targets in dep_graph.values()),
        }

    def _analyze_tokens(
        self,
        formula: str,
        current_sheet: str,
        current_coord: str,
        function_counts: Dict[str, int],
        dep_graph: Dict[str, Set[str]],
        empty_cell_refs: List[Dict[str, Any]],
    ) -> None:
        """Token-level audit: counts functions, records dependency edges, and flags empty-cell references."""
        try:
            tok = Tokenizer(formula)
        except Exception:
            return

        source_node = f"'{current_sheet}'!{current_coord}"

        for t in tok.items:
            if t.type == Token.FUNC:
                fn_name = t.value.rstrip("(").upper()
                function_counts[fn_name] += 1
            elif t.type == Token.OPERAND and t.subtype == Token.RANGE:
                val = t.value
                target_sheet = current_sheet
                ref = val
                if "!" in val:
                    parts = val.split("!", 1)
                    target_sheet = parts[0].strip("'")
                    ref = parts[1]

                if ":" not in ref and CELL_REF_RE.match(ref):
                    target_node = f"'{target_sheet}'!{ref.replace('$', '')}"
                    dep_graph[source_node].add(target_node)

                    # EV-15 Warning: check if referenced cell is completely empty
                    if target_sheet in self.wb.sheetnames:
                        ws_target = self.wb[target_sheet]
                        try:
                            clean_coord = ref.replace("$", "")
                            target_cell = ws_target[clean_coord]
                            if target_cell.value is None:
                                empty_cell_refs.append({
                                    "code": "W-FORMULA-EMPTY-CELL-REF",
                                    "source": source_node,
                                    "target": target_node,
                                    "formula": formula,
                                    "message": f"Formula at {source_node} references empty cell {target_node}.",
                                })
                        except Exception:
                            pass

    def _detect_cycles(self, dep_graph: Dict[str, Set[str]]) -> List[Dict[str, Any]]:
        """DFS cycle detection for circular dependency loops."""
        visited: Dict[str, int] = {}  # 0=unvisited, 1=visiting, 2=visited
        cycles: List[Dict[str, Any]] = []

        def dfs(node: str, path: List[str]) -> None:
            visited[node] = 1
            path.append(node)
            for neighbor in dep_graph.get(node, []):
                state = visited.get(neighbor, 0)
                if state == 1:
                    cycle_start = path.index(neighbor)
                    cycle_path = path[cycle_start:] + [neighbor]
                    cycles.append({
                        "code": "W-FORMULA-CIRCULAR",
                        "cycle": " -> ".join(cycle_path),
                        "root": neighbor,
                    })
                elif state == 0:
                    dfs(neighbor, path)
            path.pop()
            visited[node] = 2

        for n in list(dep_graph.keys()):
            if visited.get(n, 0) == 0:
                dfs(n, [])

        return cycles
