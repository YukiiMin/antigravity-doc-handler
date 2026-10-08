"""
tests.test_xlsx.test_format_describer
Test suite for Phase 2.3c: Format Describer (TC-52, TC-53, TC-60).
Verifies:
- TC-52: Comprehensive format profiling (fonts, fills, borders, alignments, theme colors)
- TC-53: Classification across 12 canonical ECMA number format classes
- TC-60: Table border gap anomaly detection (W-XLSX-BORDER-GAP) from EV-15
"""

from pathlib import Path
import tempfile
import unittest

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.styles.colors import Color

from doctools.contract.envelope import ResultEnvelope
from doctools.core.xlsx.inspect.format_profiler import (
    FormatProfiler,
    classify_number_format,
    resolve_color,
)
from doctools.operations.xlsx.inspect_ops import (
    register_xlsx_inspect_tools,
    xlsx_describe_formats,
)
from doctools.registry import ToolRegistry


class TestFormatDescriber(unittest.TestCase):
    """Unit tests for Phase 2.3c: Format Describer."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_file = Path(self.temp_dir.name) / "test_formats.xlsx"

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "FormatSheet"

        # 1. 12 Number Format Classes
        samples = [
            ("A1", "Plain Text", "@"),
            ("A2", 123.45, "#,##0.00"),
            ("A3", 0.85, "0.0%"),
            ("A4", 1500, "$#,##0"),
            ("A5", -250, "_($* #,##0_)"),
            ("A6", "2026-10-08", "yyyy-mm-dd"),
            ("A7", "14:30:00", "hh:mm:ss"),
            ("A8", 1.25, "# ?/?"),
            ("A9", 1200000, "0.00E+00"),
            ("A10", 42, "General"),
            ("A11", 999, '[Red][>100]"High: "#,##0;[Blue]"Low: "#,##0'),  # Custom
        ]
        for coord, val, nf in samples:
            ws[coord] = val
            ws[coord].number_format = nf

        # 2. Rich Styles: Font, Fill, Border
        thin_border = Border(
            left=Side(style="thin", color="000000"),
            right=Side(style="thin", color="000000"),
            top=Side(style="thin", color="000000"),
            bottom=Side(style="thin", color="000000"),
        )
        ws["B1"] = "Styled Header"
        ws["B1"].font = Font(name="Calibri", size=14, bold=True, italic=True)
        ws["B1"].fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
        ws["B1"].border = thin_border
        ws["B1"].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        # 3. EV-15 Table Border Gap simulation (TC-60)
        # Column C: rows 1..4 have hair borders, but row 8 has None
        hair_border = Border(bottom=Side(style="hair", color="808080"))
        for r in range(1, 5):
            ws[f"C{r}"] = f"Header/Row_{r}"
            ws[f"C{r}"].border = hair_border

        ws["C8"] = "Data Without Border"  # Missing border gap!

        wb.save(self.test_file)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_tc53_number_format_classification(self) -> None:
        """TC-53: Verify classification across 12 canonical number format classes."""
        self.assertEqual(classify_number_format("@"), "Text")
        self.assertEqual(classify_number_format("0.0%"), "Percentage")
        self.assertEqual(classify_number_format("$#,##0.00"), "Currency")
        self.assertEqual(classify_number_format("_($* #,##0_)"), "Accounting")
        self.assertEqual(classify_number_format("yyyy-mm-dd"), "Date")
        self.assertEqual(classify_number_format("hh:mm:ss"), "Time")
        self.assertEqual(classify_number_format("# ?/?"), "Fraction")
        self.assertEqual(classify_number_format("0.00E+00"), "Scientific")
        self.assertEqual(classify_number_format("General"), "General")
        self.assertEqual(classify_number_format("[Red][>100]#,##0"), "Custom")

    def test_tc52_theme_color_resolution(self) -> None:
        """TC-52: Verify theme palette index resolution to hex."""
        theme_col = Color(type="theme", theme=4, tint=0.2)
        res = resolve_color(theme_col)
        self.assertIsNotNone(res)
        self.assertEqual(res["type"], "theme")
        self.assertEqual(res["base_hex"], "4F81BD")
        self.assertEqual(res["tint"], 0.2)

    def test_tc52_format_describer_report(self) -> None:
        """TC-52: Verify xlsx.describe_formats returns full style attributes."""
        res: ResultEnvelope = xlsx_describe_formats(self.test_file, sheet="FormatSheet")
        self.assertTrue(res.success)
        extra = res.stats.extra

        self.assertIn("number_format_classes", extra)
        self.assertIn("Text", extra["number_format_classes"])
        self.assertIn("Percentage", extra["number_format_classes"])
        self.assertIn("Currency", extra["number_format_classes"])

        self.assertGreaterEqual(extra["unique_fonts_count"], 1)
        self.assertIn("thin", extra["border_styles_present"])
        self.assertIn("hair", extra["border_styles_present"])

    def test_tc60_border_gap_anomaly_detection(self) -> None:
        """TC-60 (EV-15): Verify border gap detection in tabular data."""
        res: ResultEnvelope = xlsx_describe_formats(self.test_file, sheet="FormatSheet")
        self.assertTrue(res.success)
        extra = res.stats.extra

        gaps = extra["border_gaps_detected"]
        self.assertGreaterEqual(len(gaps), 1)
        gap_c8 = any(g["coord"] == "C8" for g in gaps)
        self.assertTrue(gap_c8, "Expected border gap warning on cell C8")
        self.assertEqual(gaps[0]["code"], "W-XLSX-BORDER-GAP")

    def test_tool_registry_registration(self) -> None:
        """Verify xlsx.describe_formats is registered into ToolRegistry."""
        registry = ToolRegistry()
        register_xlsx_inspect_tools(registry)
        tool_names = [t["name"] for t in registry.list_tools()]
        self.assertIn("xlsx.describe_formats", tool_names)


if __name__ == "__main__":
    unittest.main()
