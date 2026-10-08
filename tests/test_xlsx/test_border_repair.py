"""
tests.test_xlsx.test_border_repair — Unit tests for Phase 2.4.4: Table Border Repair by Explicit Policy.
Verifies:
- TC-60: Table borders repaired when border_policy is explicitly 'inherit_prototype' (D-04, FR-14)
- TC-44: Template borders strictly preserved when border_policy is default 'preserve_exact' (D-04, FR-06)
"""

import unittest
import openpyxl
from openpyxl.styles import Border, Side

from doctools.contract.xlsx.mutation import MutationSpec, TableExpansion
from doctools.core.xlsx.mutate.mutator import XlsxMutator


class TestBorderRepairPolicy(unittest.TestCase):
    """Unit tests for border repair via explicit policy."""

    def test_tc44_preserve_exact_does_not_mutate_missing_borders(self) -> None:
        """TC-44: Default policy 'preserve_exact' does NOT silently alter missing borders."""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "TestSheet"

        hair_side = Side(border_style="hair", color="000000")
        hair_border = Border(top=hair_side, bottom=hair_side, left=hair_side, right=hair_side)

        # Prototype row (row 2)
        ws["A2"] = "ID"
        ws["B2"] = "Name"
        ws["A2"].border = hair_border
        ws["B2"].border = hair_border

        # Existing lower row without border (row 5)
        ws["A5"] = "Existing Data"
        self.assertFalse(ws["A5"].border and any(getattr(ws["A5"].border, s).style for s in ("top", "bottom", "left", "right")))

        # Expand table with default border_policy='preserve_exact'
        spec = MutationSpec(
            template_ref_or_id="memory",
            border_policy="preserve_exact",
            expansions=[
                TableExpansion(
                    sheet="TestSheet",
                    prototype_row=2,
                    start_row=3,
                    consume_prototype=False,
                    rows_data=[["001", "Item 1"]],
                    border_policy="preserve_exact",
                )
            ],
        )

        mutator = XlsxMutator(wb)
        issues = mutator.mutate(spec)

        # A5 must still NOT have border (preserved verbatim)
        has_border_a5 = ws["A5"].border and any(getattr(ws["A5"].border, s).style for s in ("top", "bottom", "left", "right"))
        self.assertFalse(has_border_a5, "Default preserve_exact policy must NOT silently repair borders")
        repair_issues = [i for i in issues if i.code == "I-XLSX-BORDER-REPAIRED"]
        self.assertEqual(len(repair_issues), 0)

    def test_tc60_inherit_prototype_repairs_missing_borders(self) -> None:
        """TC-60: Explicit policy 'inherit_prototype' repairs missing borders from prototype row."""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "TestSheet"

        thin_side = Side(border_style="thin", color="000000")
        thin_border = Border(top=thin_side, bottom=thin_side, left=thin_side, right=thin_side)

        # Prototype row (row 2)
        ws["A2"] = "ID"
        ws["B2"] = "Name"
        ws["A2"].border = thin_border
        ws["B2"].border = thin_border

        # Existing row 5 with value but missing border
        ws["A5"] = "Existing Data"
        ws["B5"] = "Existing Desc"

        spec = MutationSpec(
            template_ref_or_id="memory",
            border_policy="inherit_prototype",
            expansions=[
                TableExpansion(
                    sheet="TestSheet",
                    prototype_row=2,
                    start_row=3,
                    consume_prototype=False,
                    rows_data=[["001", "Item 1"]],
                    border_policy="inherit_prototype",
                )
            ],
        )

        mutator = XlsxMutator(wb)
        issues = mutator.mutate(spec)

        # 'Existing Data' was shifted from row 5 to row 6 after inserting 1 row at row 3
        cell_a6 = ws["A6"]
        cell_b6 = ws["B6"]
        self.assertEqual(cell_a6.value, "Existing Data")

        self.assertIsNotNone(cell_a6.border.bottom.style)
        self.assertEqual(cell_a6.border.bottom.style, "thin")
        self.assertIsNotNone(cell_b6.border.bottom.style)
        self.assertEqual(cell_b6.border.bottom.style, "thin")

        # Repaired count should be logged in info issues
        repair_issues = [i for i in issues if i.code == "I-XLSX-BORDER-REPAIRED"]
        self.assertEqual(len(repair_issues), 1)
        self.assertIn("inherit_prototype", repair_issues[0].message)


if __name__ == "__main__":
    unittest.main()
