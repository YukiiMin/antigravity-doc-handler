"""
tests.test_docx.test_docspec_fuzzing
Property-based and structural fuzz testing for Path B DocSpec generation (TC-15).
Ensures that random and edge-case DocSpec payloads always produce 100% valid OOXML.
"""

import io
import random
import tempfile
import unittest

import docx

from doctools.contract import Severity
from doctools.contract.docx.docspec import (
    CalloutBlock,
    DocSpec,
    HeadingBlock,
    ListBlock,
    PageBreakBlock,
    PageSetupSpec,
    ParagraphBlock,
    RunSpec,
    TableBlock,
)
from doctools.core.docx.build import docspec_builder
from doctools.gates.docx import docx_quality_gates


class TestDocSpecFuzzing(unittest.TestCase):
    """Fuzzing and property verification: random DocSpecs always produce compliant DOCX."""

    def test_randomized_docspec_permutations(self):
        """Generates 15 pseudo-random DocSpec permutations and verifies OOXML conformance."""
        random.seed(42)  # Deterministic seed for reproducible testing

        block_factories = [
            lambda i: HeadingBlock(level=min(6, (i % 5) + 1), text=f"Heading Fuzz {i}: Tiêu đề kiểm thử"),
            lambda i: ParagraphBlock(
                runs=[
                    RunSpec(text=f"Đoạn run {i} đậm ", bold=True),
                    RunSpec(text="nghiêng ", italic=True),
                    RunSpec(text="màu sắc ", color="FF5500"),
                ]
            ),
            lambda i: ListBlock(
                items=[f"Mục con {i}.1", f"Mục con {i}.2", f"Mục con {i}.3"],
                ordered=(i % 2 == 0),
            ),
            lambda i: TableBlock(
                headers=[f"Col {j}" for j in range(3)],
                rows=[[f"Cell {r}x{c}" for c in range(3)] for r in range(2 + (i % 3))],
                col_widths=[3.0, 4.5, 3.5],
            ),
            lambda i: CalloutBlock(
                kind="warning" if i % 2 == 0 else "info",
                title=f"Hộp cảnh báo {i}",
                text=f"Nội dung ghi chú fuzzing tự động số {i}.",
            ),
            lambda i: PageBreakBlock(),
        ]

        for iteration in range(15):
            # Pick 4 to 8 random blocks
            block_count = random.randint(4, 8)
            blocks = [random.choice(block_factories)(b_idx) for b_idx in range(block_count)]

            orientation = "landscape" if iteration % 3 == 0 else "portrait"
            spec = DocSpec(
                docspec_version="1.0",
                title=f"Tài liệu Fuzzing #{iteration}",
                page_setup=PageSetupSpec(orientation=orientation, margin_top_cm=2.0),
                blocks=blocks,
            )

            res = docspec_builder.build(spec)
            self.assertTrue(len(res.docx_bytes) > 0, f"Iteration {iteration}: docx_bytes empty")

            # Must have zero build errors
            build_errors = [iss for iss in res.issues if iss.severity == Severity.ERROR]
            self.assertEqual(len(build_errors), 0, f"Iteration {iteration} had build errors: {build_errors}")

            # Must pass all Universal Quality Gates (DG-01..DG-06)
            gate_issues = docx_quality_gates.validate(res.docx_bytes)
            gate_errors = [iss for iss in gate_issues if iss.severity == Severity.ERROR]
            self.assertEqual(len(gate_errors), 0, f"Iteration {iteration} violated quality gates: {gate_errors}")

    def test_edge_cases_empty_and_special_characters(self):
        """Verifies stability on Vietnamese diacritics, quotes, and punctuation."""
        spec = DocSpec(
            docspec_version="1.0",
            title="Đặc tả Nghiệm thu Kỹ thuật & Báo cáo",
            blocks=[
                HeadingBlock(level=1, text="1. Tiêu đề chứa dấu: Ă, Â, Đ, Ê, Ô, Ơ, Ư, Ỹ"),
                ParagraphBlock(text='Chữ trong ngoặc kép "nháy kép" và \'nháy đơn\', ký tự đặc biệt: <>&%$.'),
                TableBlock(
                    headers=["Ký tự", "Giá trị"],
                    rows=[
                        ["Dòng 1", "Khoảng trắng và tab\t"],
                        ["Dòng 2", "100% chính xác tuyệt đối"],
                    ],
                ),
            ],
        )

        res = docspec_builder.build(spec)
        self.assertTrue(len(res.docx_bytes) > 0)
        gate_issues = docx_quality_gates.validate(res.docx_bytes)
        self.assertEqual(len([iss for iss in gate_issues if iss.severity == Severity.ERROR]), 0)


if __name__ == "__main__":
    unittest.main()
