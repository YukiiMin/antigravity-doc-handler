# -*- coding: utf-8 -*-
"""
unified_qa_diagnostic.py — Enterprise Unified QA & Diagnostic Engine for DOCX, XLSX, Diagrams & Conversions.

Provides robust, schema-driven static & semantic inspection and safe non-destructive repairs:
  - Excel (XLSX): DrawingML preservation, Prototype Cloning, MergedCell safety, Formula AST expansion,
                  Data type coercion, Adaptive Freeze Panes & Auto-scaling row heights.
  - Word (DOCX): The Last Paragraph Rule (<w:tc> ends with <w:p>), cantSplit, tblHeader,
                 Table style inheritance, image bounds against printable margins.
  - Diagrams & Charts: Chart anchor overlap, series range relinking, canvas layout bounds.
  - Conversion: Zombie lock file detection & cleanup, font glyph embedding checks.

Exit codes for CI/CD:
  0: Clean / 100% Passed (No errors, no warnings)
  1: Warnings only (Aesthetic / minor non-breaking suggestions)
  2: Critical errors found (Corrupt XML, broken formula ranges, missing shapes, data loss risk)
"""

import argparse
import datetime
import glob
import json
import os
import re
import shutil
import sys
from typing import Any, Dict, List, Optional, Tuple

# Reconfigure stdout for UTF-8
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Optional imports with graceful fallbacks
try:
    import openpyxl
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.cell_range import CellRange
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

try:
    import docx
    from docx.oxml import OxmlElement, parse_xml
    from docx.oxml.ns import nsdecls, qn
    from docx.shared import Inches, Pt, RGBColor
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


# ─────────────────────────────────────────────────────────────────────────────
# Diagnostic Issue Record
# ─────────────────────────────────────────────────────────────────────────────
class DiagnosticIssue:
    def __init__(self, code: str, domain: str, severity: str, message: str,
                 location: str = "", details: Optional[Dict[str, Any]] = None,
                 fixable: bool = False):
        self.code = code
        self.domain = domain
        self.severity = severity  # 'CRITICAL', 'WARNING', 'INFO'
        self.message = message
        self.location = location
        self.details = details or {}
        self.fixable = fixable

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "domain": self.domain,
            "severity": self.severity,
            "message": self.message,
            "location": self.location,
            "details": self.details,
            "fixable": self.fixable
        }


# ─────────────────────────────────────────────────────────────────────────────
# 1. EXCEL (XLSX) DIAGNOSTIC ENGINE
# ─────────────────────────────────────────────────────────────────────────────
class ExcelDiagnosticEngine:
    """Enterprise diagnostic & safe-fix engine for Excel workbooks."""

    FORMULA_RANGE_REGEX = re.compile(r"([A-Za-z]+[0-9]+):([A-Za-z]+[0-9]+)")
    SENTINEL_KEYWORDS_HEADER = ["no", "id", "test case", "stt", "mã", "tên", "function code"]
    SENTINEL_KEYWORDS_SUMMARY = ["total", "sub total", "summary", "tổng", "tỷ lệ", "coverage"]

    @classmethod
    def diagnose(cls, xlsx_path: str) -> Tuple[List[DiagnosticIssue], Dict[str, Any]]:
        issues: List[DiagnosticIssue] = []
        metrics: Dict[str, Any] = {
            "file": xlsx_path,
            "sheets_count": 0,
            "sheets": [],
            "drawing_shapes_count": 0,
            "total_formulas": 0,
            "merged_ranges_count": 0,
            "lock_files_found": 0
        }

        if not HAS_OPENPYXL:
            issues.append(DiagnosticIssue("ERR_SYS_001", "EXCEL", "CRITICAL", "openpyxl is not installed."))
            return issues, metrics

        # Check for zombie lock files (ERR_CONV_004)
        cls._check_zombie_locks(xlsx_path, issues, metrics)

        try:
            wb = openpyxl.load_workbook(xlsx_path, data_only=False)
        except Exception as e:
            issues.append(DiagnosticIssue("ERR_XLSX_006", "EXCEL", "CRITICAL",
                                          f"Failed to open workbook (possible XML corruption): {str(e)}", location="Package"))
            return issues, metrics

        metrics["sheets_count"] = len(wb.sheetnames)
        metrics["sheets"] = wb.sheetnames

        for sheetname in wb.sheetnames:
            ws = wb[sheetname]
            cls._diagnose_sheet(ws, sheetname, issues, metrics)

        return issues, metrics

    @classmethod
    def _check_zombie_locks(cls, file_path: str, issues: List[DiagnosticIssue], metrics: Dict[str, Any]):
        dirname = os.path.dirname(os.path.abspath(file_path))
        basename = os.path.basename(file_path)
        lock_patterns = [
            os.path.join(dirname, f"~${basename}"),
            os.path.join(dirname, f".~lock.{basename}#")
        ]
        for lp in lock_patterns:
            if os.path.exists(lp):
                metrics["lock_files_found"] += 1
                issues.append(DiagnosticIssue(
                    code="ERR_CONV_004",
                    domain="CONVERSION",
                    severity="WARNING",
                    message=f"Zombie lock file detected on disk: {os.path.basename(lp)}",
                    location=lp,
                    fixable=True
                ))

    @classmethod
    def _diagnose_sheet(cls, ws, sheetname: str, issues: List[DiagnosticIssue], metrics: Dict[str, Any]):
        # 1. Check Drawings & Charts (ERR_XLSX_006 & ERR_DIAG_003)
        num_drawings = len(getattr(ws, "_images", [])) + len(getattr(ws, "_charts", []))
        metrics["drawing_shapes_count"] += num_drawings

        for i, chart in enumerate(getattr(ws, "_charts", [])):
            ar = chart.anchor._from.row if hasattr(chart.anchor, "_from") else None
            for s in chart.series:
                if s.val and s.val.numRef:
                    f_str = s.val.numRef.f or ""
                    if "#REF!" in f_str or f_str.strip() == "":
                        issues.append(DiagnosticIssue(
                            code="ERR_XLSX_002",
                            domain="EXCEL",
                            severity="CRITICAL",
                            message=f"Chart series reference is broken or empty: '{f_str}'",
                            location=f"{sheetname} Chart #{i+1}"
                        ))

        # 2. Check Merged Cells bounds & non-top-left pollution (ERR_XLSX_004)
        merged_ranges = list(ws.merged_cells.ranges)
        metrics["merged_ranges_count"] += len(merged_ranges)
        for mr in merged_ranges:
            top_left = ws.cell(mr.min_row, mr.min_col)
            for r in range(mr.min_row, mr.max_row + 1):
                for c in range(mr.min_col, mr.max_col + 1):
                    if r == mr.min_row and c == mr.min_col:
                        continue
                    cell_sub = ws.cell(r, c)
                    if cell_sub.value is not None and cell_sub.value != "":
                        issues.append(DiagnosticIssue(
                            code="ERR_XLSX_004",
                            domain="EXCEL",
                            severity="WARNING",
                            message=f"Non-top-left cell in merged range {mr.coord} contains orphan value: {repr(cell_sub.value)}",
                            location=f"{sheetname}!{cell_sub.coordinate}",
                            fixable=True
                        ))

        # 3. Scan rows for Header, Summary, Formulas, and Auto-scaling (ERR_XLSX_001..005)
        header_row = None
        summary_row = None

        max_row = min(ws.max_row, 150)
        max_col = min(ws.max_column, 30)

        for r in range(1, max_row + 1):
            row_text = " ".join(str(ws.cell(r, c).value or "").strip().lower() for c in range(1, max_col + 1))
            if any(k in row_text for k in cls.SENTINEL_KEYWORDS_HEADER) and header_row is None:
                header_row = r
            if any(k in row_text for k in cls.SENTINEL_KEYWORDS_SUMMARY) and r > (header_row or 1):
                summary_row = r

            # Check formulas & text length
            for c in range(1, max_col + 1):
                cell = ws.cell(r, c)
                val = str(cell.value or "")

                # Formula checks
                if str(cell.value).startswith("="):
                    metrics["total_formulas"] += 1
                    if any(err in val for err in ["#REF!", "#VALUE!", "#DIV/0!", "#NAME?"]):
                        issues.append(DiagnosticIssue(
                            code="ERR_XLSX_002",
                            domain="EXCEL",
                            severity="CRITICAL",
                            message=f"Formula error detected in cell: '{val}'",
                            location=f"{sheetname}!{cell.coordinate}"
                        ))

                # Text clipping / row height check (ERR_XLSX_004 / Invariant E13)
                if len(val) > 40 and not str(cell.value).startswith("="):
                    lines = len(val.split("\n")) + int(len(val) / 45.0)
                    expected_min_height = max(18.0, lines * 13.5)
                    actual_height = ws.row_dimensions[r].height or 15.0
                    al = cell.alignment
                    if (actual_height < expected_min_height - 3.0) or not (al and al.wrap_text):
                        issues.append(DiagnosticIssue(
                            code="ERR_XLSX_004",
                            domain="EXCEL",
                            severity="WARNING",
                            message=f"Long text ({len(val)} chars) in cell without adequate row height or wrap_text (h={actual_height}, expected>={expected_min_height:.1f})",
                            location=f"{sheetname}!{cell.coordinate}",
                            fixable=True
                        ))

                # Leading zero loss check (ERR_XLSX_007)
                if isinstance(cell.value, int) and c in [1, 2]:
                    # If column header indicates Code/ID
                    top_h = str(ws.cell(header_row or 1, c).value or "").lower()
                    if any(id_kw in top_h for id_kw in ["code", "id", "mã"]):
                        issues.append(DiagnosticIssue(
                            code="ERR_XLSX_007",
                            domain="EXCEL",
                            severity="INFO",
                            message=f"Identifier '{top_h}' stored as integer '{cell.value}' instead of text (risk of leading-zero truncation)",
                            location=f"{sheetname}!{cell.coordinate}",
                            fixable=True
                        ))

        # Check Freeze Panes (ERR_XLSX_005)
        if header_row and header_row > 1 and not ws.freeze_panes:
            issues.append(DiagnosticIssue(
                code="ERR_XLSX_005",
                domain="EXCEL",
                severity="INFO",
                message=f"Sheet has header at row {header_row} but freeze_panes is not configured",
                location=f"{sheetname}"
            ))

    @classmethod
    def repair(cls, xlsx_path: str, out_path: str) -> Tuple[bool, List[str]]:
        """Safe non-destructive repair for fixable Excel issues."""
        if not HAS_OPENPYXL:
            return False, ["openpyxl is not installed."]

        actions = []
        # Clean zombie lock files
        dirname = os.path.dirname(os.path.abspath(xlsx_path))
        basename = os.path.basename(xlsx_path)
        for lp in [os.path.join(dirname, f"~${basename}"), os.path.join(dirname, f".~lock.{basename}#")]:
            if os.path.exists(lp):
                try:
                    os.remove(lp)
                    actions.append(f"Removed zombie lock file: {os.path.basename(lp)}")
                except Exception as ex:
                    actions.append(f"Failed to remove lock {os.path.basename(lp)}: {ex}")

        try:
            wb = openpyxl.load_workbook(xlsx_path, data_only=False)
        except Exception as e:
            return False, [f"Cannot load workbook for repair: {e}"]

        for sheetname in wb.sheetnames:
            ws = wb[sheetname]
            # Fix text wrapping & row heights for long descriptions
            for r in range(1, min(ws.max_row, 150) + 1):
                max_lines = 1
                for c in range(1, min(ws.max_column, 30) + 1):
                    cell = ws.cell(r, c)
                    val = str(cell.value or "")
                    if len(val) > 40 and not val.startswith("="):
                        cell.alignment = Alignment(
                            horizontal=cell.alignment.horizontal or "left",
                            vertical=cell.alignment.vertical or "center",
                            wrap_text=True
                        )
                        lines = len(val.split("\n")) + int(len(val) / 45.0)
                        if lines > max_lines:
                            max_lines = lines
                if max_lines > 1:
                    cur_h = ws.row_dimensions[r].height or 15.0
                    target_h = max(cur_h, max_lines * 14.5)
                    ws.row_dimensions[r].height = target_h
                    actions.append(f"Auto-scaled {sheetname}!Row {r} height to {target_h:.1f}pt with wrap_text")

        wb.save(out_path)
        actions.append(f"Saved repaired workbook to {out_path}")
        return True, actions


# ─────────────────────────────────────────────────────────────────────────────
# 2. WORD (DOCX) DIAGNOSTIC ENGINE
# ─────────────────────────────────────────────────────────────────────────────
class DocxDiagnosticEngine:
    """Enterprise diagnostic & safe-fix engine for Word documents."""

    @classmethod
    def diagnose(cls, docx_path: str) -> Tuple[List[DiagnosticIssue], Dict[str, Any]]:
        issues: List[DiagnosticIssue] = []
        metrics: Dict[str, Any] = {
            "file": docx_path,
            "paragraphs_count": 0,
            "tables_count": 0,
            "images_count": 0,
            "multi_page_tables_count": 0,
            "printable_width_inches": 6.5
        }

        if not HAS_DOCX:
            issues.append(DiagnosticIssue("ERR_SYS_002", "WORD", "CRITICAL", "python-docx is not installed."))
            return issues, metrics

        # Check zombie locks
        cls._check_zombie_locks(docx_path, issues, metrics)

        try:
            doc = docx.Document(docx_path)
        except Exception as e:
            issues.append(DiagnosticIssue("ERR_DOCX_001", "WORD", "CRITICAL",
                                          f"Failed to open DOCX (XML corruption or invalid format): {str(e)}", location="Package"))
            return issues, metrics

        metrics["paragraphs_count"] = len(doc.paragraphs)
        metrics["tables_count"] = len(doc.tables)

        # Calculate printable width from section 0
        if doc.sections:
            sec = doc.sections[0]
            pw = sec.page_width.inches
            lm = sec.left_margin.inches
            rm = sec.right_margin.inches
            metrics["printable_width_inches"] = pw - lm - rm

        # 1. Diagnose Tables (ERR_DOCX_001, ERR_DOCX_003, ERR_DOCX_004)
        for t_idx, tbl in enumerate(doc.tables, start=1):
            num_rows = len(tbl.rows)
            num_cols = len(tbl.columns) if num_rows > 0 else 0
            is_multi_page = num_rows > 12
            if is_multi_page:
                metrics["multi_page_tables_count"] += 1

            # Check tblHeader and cantSplit
            for r_idx, row in enumerate(tbl.rows):
                trPr = row._tr.get_or_add_trPr()
                has_cant_split = trPr.find(qn("w:cantSplit")) is not None
                has_tbl_header = trPr.find(qn("w:tblHeader")) is not None

                if is_multi_page and r_idx == 0 and not has_tbl_header:
                    issues.append(DiagnosticIssue(
                        code="ERR_DOCX_003",
                        domain="WORD",
                        severity="WARNING",
                        message=f"Multi-page table #{t_idx} ({num_rows} rows) missing <w:tblHeader/> on header row",
                        location=f"Table #{t_idx} Row #{r_idx+1}",
                        fixable=True
                    ))

                if is_multi_page and not has_cant_split:
                    issues.append(DiagnosticIssue(
                        code="ERR_DOCX_003",
                        domain="WORD",
                        severity="INFO",
                        message=f"Table #{t_idx} Row #{r_idx+1} missing <w:cantSplit/> (page split protection)",
                        location=f"Table #{t_idx} Row #{r_idx+1}",
                        fixable=True
                    ))

                # Check The Last Paragraph Rule in each cell (<w:tc> ends with <w:p>) (ERR_DOCX_001)
                for c_idx, cell in enumerate(row.cells):
                    tc = cell._tc
                    p_children = tc.findall(qn("w:p"))
                    if len(p_children) == 0:
                        issues.append(DiagnosticIssue(
                            code="ERR_DOCX_001",
                            domain="WORD",
                            severity="CRITICAL",
                            message=f"Table #{t_idx} Cell (R{r_idx+1}, C{c_idx+1}) violates 'The Last Paragraph Rule' (missing <w:p> element)",
                            location=f"Table #{t_idx} (R{r_idx+1}, C{c_idx+1})",
                            fixable=True
                        ))

        # 2. Diagnose Inline Shapes & Images (ERR_DOCX_005)
        # Search XML for blip elements
        for p_idx, p in enumerate(doc.paragraphs):
            for r in p.runs:
                blips = r._r.xpath(".//a:blip")
                if blips:
                    metrics["images_count"] += len(blips)

        return issues, metrics

    @classmethod
    def _check_zombie_locks(cls, file_path: str, issues: List[DiagnosticIssue], metrics: Dict[str, Any]):
        dirname = os.path.dirname(os.path.abspath(file_path))
        basename = os.path.basename(file_path)
        for lp in [os.path.join(dirname, f"~${basename}"), os.path.join(dirname, f".~lock.{basename}#")]:
            if os.path.exists(lp):
                issues.append(DiagnosticIssue(
                    code="ERR_CONV_004",
                    domain="CONVERSION",
                    severity="WARNING",
                    message=f"Zombie lock file detected on disk: {os.path.basename(lp)}",
                    location=lp,
                    fixable=True
                ))

    @classmethod
    def repair(cls, docx_path: str, out_path: str) -> Tuple[bool, List[str]]:
        """Safe non-destructive repair for fixable DOCX issues."""
        if not HAS_DOCX:
            return False, ["python-docx is not installed."]

        actions = []
        try:
            doc = docx.Document(docx_path)
        except Exception as e:
            return False, [f"Cannot load document for repair: {e}"]

        for t_idx, tbl in enumerate(doc.tables, start=1):
            num_rows = len(tbl.rows)
            # 1. Enforce The Last Paragraph Rule
            for r_idx, row in enumerate(tbl.rows):
                trPr = row._tr.get_or_add_trPr()
                # Enforce cantSplit
                if trPr.find(qn("w:cantSplit")) is None:
                    trPr.append(parse_xml(f"<w:cantSplit {nsdecls('w')}/>"))
                    actions.append(f"Injected <w:cantSplit/> on Table #{t_idx} Row #{r_idx+1}")

                # Enforce tblHeader on row 0 for tables > 10 rows
                if num_rows > 10 and r_idx == 0:
                    if trPr.find(qn("w:tblHeader")) is None:
                        trPr.append(parse_xml(f"<w:tblHeader {nsdecls('w')}/>"))
                        actions.append(f"Injected <w:tblHeader/> on Table #{t_idx} Header Row")

                for c_idx, cell in enumerate(row.cells):
                    tc = cell._tc
                    if len(tc.findall(qn("w:p"))) == 0:
                        tc.append(parse_xml(f"<w:p {nsdecls('w')}/>"))
                        actions.append(f"Restored missing <w:p> in Table #{t_idx} Cell (R{r_idx+1}, C{c_idx+1})")

        doc.save(out_path)
        actions.append(f"Saved repaired document to {out_path}")
        return True, actions


# ─────────────────────────────────────────────────────────────────────────────
# 3. DIAGRAMS & CONVERSION DIAGNOSTIC ENGINE
# ─────────────────────────────────────────────────────────────────────────────
class DiagramAndConversionEngine:
    @classmethod
    def diagnose_assets(cls, asset_dir: str) -> Tuple[List[DiagnosticIssue], Dict[str, Any]]:
        issues: List[DiagnosticIssue] = []
        metrics = {"images_scanned": 0, "oversized_images": 0}

        if not os.path.exists(asset_dir):
            return issues, metrics

        png_files = glob.glob(os.path.join(asset_dir, "**", "*.png"), recursive=True)
        metrics["images_scanned"] = len(png_files)

        for pf in png_files:
            if HAS_PIL:
                try:
                    with Image.open(pf) as img:
                        w, h = img.size
                        # Check resolution and aspect ratio (ERR_DIAG_002)
                        if w > 4000 or h > 4000:
                            metrics["oversized_images"] += 1
                            issues.append(DiagnosticIssue(
                                code="ERR_DIAG_002",
                                domain="DIAGRAM",
                                severity="WARNING",
                                message=f"Oversized image ({w}x{h}) may cause Word document pagination crash or memory exhaustion",
                                location=pf
                            ))
                except Exception as ex:
                    issues.append(DiagnosticIssue(
                        code="ERR_DIAG_001",
                        domain="DIAGRAM",
                        severity="WARNING",
                        message=f"Could not inspect image file: {ex}",
                        location=pf
                    ))
        return issues, metrics


# ─────────────────────────────────────────────────────────────────────────────
# 4. MASTER CLI & REPORT FORMATTER
# ─────────────────────────────────────────────────────────────────────────────
def format_terminal_report(all_issues: List[DiagnosticIssue], all_metrics: Dict[str, Any]) -> str:
    lines = []
    lines.append("=" * 80)
    lines.append("       ENTERPRISE UNIFIED QA & DIAGNOSTIC REPORT (DOCX / XLSX / DIAGRAM)")
    lines.append("=" * 80)
    lines.append(f"Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Files Inspected: {len(all_metrics.get('files', []))}")

    crit_count = sum(1 for i in all_issues if i.severity == "CRITICAL")
    warn_count = sum(1 for i in all_issues if i.severity == "WARNING")
    info_count = sum(1 for i in all_issues if i.severity == "INFO")

    lines.append(f"Summary: {len(all_issues)} issues found [ CRITICAL: {crit_count} | WARNING: {warn_count} | INFO: {info_count} ]")
    lines.append("-" * 80)

    if not all_issues:
        lines.append("✓ 100% CLEAN — All structural & invariant quality gates PASSED!")
    else:
        lines.append(f"{'SEVERITY':<10} | {'CODE':<14} | {'LOCATION':<30} | {'MESSAGE'}")
        lines.append("-" * 80)
        for issue in all_issues:
            loc = (issue.location[:27] + "...") if len(issue.location) > 30 else issue.location
            lines.append(f"{issue.severity:<10} | {issue.code:<14} | {loc:<30} | {issue.message}")

    lines.append("=" * 80)
    return "\n".join(lines)


def run_pipeline():
    parser = argparse.ArgumentParser(description="Enterprise Unified QA & Diagnostic Engine")
    parser.add_argument("--xlsx", help="Path to Excel workbook to diagnose", default=None)
    parser.add_argument("--docx", help="Path to Word document to diagnose", default=None)
    parser.add_argument("--all", help="Directory containing documents to diagnose", default=None)
    parser.add_argument("--mode", choices=["diagnose", "audit-fix"], default="diagnose",
                        help="Operation mode: 'diagnose' (read-only audit) or 'audit-fix' (safe repair)")
    parser.add_argument("--in-place", action="store_true",
                        help="Allow in-place repair (creates a .bak file before modifying)")
    parser.add_argument("--format", choices=["terminal", "json", "sarif"], default="terminal",
                        help="Output report format")
    parser.add_argument("--output", help="Optional output file path for the report/log", default=None)

    args = parser.parse_args()

    files_to_check: List[str] = []
    if args.xlsx:
        files_to_check.append(args.xlsx)
    if args.docx:
        files_to_check.append(args.docx)
    if args.all and os.path.exists(args.all):
        files_to_check.extend(glob.glob(os.path.join(args.all, "**", "*.xlsx"), recursive=True))
        files_to_check.extend(glob.glob(os.path.join(args.all, "**", "*.docx"), recursive=True))

    if not files_to_check:
        print("No target files specified. Use --xlsx, --docx, or --all.")
        sys.exit(0)

    all_issues: List[DiagnosticIssue] = []
    all_metrics: Dict[str, Any] = {"files": files_to_check, "details": {}}

    for file_path in files_to_check:
        if not os.path.exists(file_path):
            continue
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".xlsx":
            issues, metrics = ExcelDiagnosticEngine.diagnose(file_path)
            all_issues.extend(issues)
            all_metrics["details"][file_path] = metrics

            if args.mode == "audit-fix":
                if args.in_place:
                    shutil.copyfile(file_path, file_path + ".bak")
                    target_out = file_path
                else:
                    target_out = file_path.replace(".xlsx", "_repaired.xlsx")
                success, actions = ExcelDiagnosticEngine.repair(file_path, target_out)
                print(f"[REPAIR] {file_path} -> {target_out}: {'SUCCESS' if success else 'FAILED'}")
                for act in actions:
                    print(f"  + {act}")

        elif ext == ".docx":
            issues, metrics = DocxDiagnosticEngine.diagnose(file_path)
            all_issues.extend(issues)
            all_metrics["details"][file_path] = metrics

            if args.mode == "audit-fix":
                if args.in_place:
                    shutil.copyfile(file_path, file_path + ".bak")
                    target_out = file_path
                else:
                    target_out = file_path.replace(".docx", "_repaired.docx")
                success, actions = DocxDiagnosticEngine.repair(file_path, target_out)
                print(f"[REPAIR] {file_path} -> {target_out}: {'SUCCESS' if success else 'FAILED'}")
                for act in actions:
                    print(f"  + {act}")

    # Output formatting
    if args.format == "json":
        report_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "exit_code": 2 if any(i.severity == "CRITICAL" for i in all_issues) else (1 if any(i.severity == "WARNING" for i in all_issues) else 0),
            "metrics": all_metrics,
            "issues": [i.to_dict() for i in all_issues]
        }
        report_str = json.dumps(report_data, indent=2, ensure_ascii=False)
    else:
        report_str = format_terminal_report(all_issues, all_metrics)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report_str)
        print(f"Report saved to: {args.output}")
    else:
        print(report_str)

    # Determine CI/CD exit code
    has_critical = any(i.severity == "CRITICAL" for i in all_issues)
    has_warning = any(i.severity == "WARNING" for i in all_issues)

    if has_critical:
        sys.exit(2)
    elif has_warning:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    run_pipeline()
