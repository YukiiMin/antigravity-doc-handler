"""
Unit test suite for doctools.contract Pydantic schemas.
Kiểm định toàn diện FileRef, Issue, Diagnostics, ResultEnvelope, và BaseSpec.
"""

from __future__ import annotations
import unittest
from datetime import datetime, timezone
from pydantic import ValidationError

from doctools.contract import (
    FileRef,
    Issue,
    Location,
    Severity,
    Engine,
    FixableBy,
    Diagnostics,
    Stats,
    ResultEnvelope,
    BaseSpec,
)


class TestFileRef(unittest.TestCase):
    """Kiểm tra hợp đồng FileRef và các ràng buộc dữ liệu."""

    def test_valid_fileref(self) -> None:
        valid_hash = "a" * 64
        f = FileRef(
            uri="resource://docx/files/out-123",
            sha256=valid_hash,
            size=2048,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        self.assertEqual(f.uri, "resource://docx/files/out-123")
        self.assertEqual(f.sha256, valid_hash)
        self.assertEqual(f.size, 2048)
        self.assertIsNone(f.expires_at)

    def test_sha256_normalization_to_lowercase(self) -> None:
        upper_hash = "A1B2C3D4" * 8
        f = FileRef(
            uri="resource://xlsx/files/kpi-999",
            sha256=upper_hash,
            size=100,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertEqual(f.sha256, upper_hash.lower())

    def test_invalid_sha256_length_or_chars(self) -> None:
        # Thiếu ký tự (< 64)
        with self.assertRaises(ValidationError):
            FileRef(
                uri="resource://diagram/files/erd",
                sha256="abc123",
                size=10,
                mime="image/png",
            )
        # Chứa ký tự không phải hex
        with self.assertRaises(ValidationError):
            FileRef(
                uri="resource://diagram/files/erd",
                sha256="g" * 64,
                size=10,
                mime="image/png",
            )

    def test_negative_size_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            FileRef(
                uri="resource://docx/files/test",
                sha256="0" * 64,
                size=-1,
                mime="application/pdf",
            )

    def test_invalid_uri_format(self) -> None:
        with self.assertRaises(ValidationError):
            FileRef(
                uri="invalid-relative-path.docx",
                sha256="0" * 64,
                size=100,
                mime="application/pdf",
            )

    def test_frozen_immutability(self) -> None:
        f = FileRef(
            uri="resource://docx/files/out",
            sha256="1" * 64,
            size=500,
            mime="application/pdf",
        )
        with self.assertRaises(ValidationError):
            f.size = 600  # type: ignore

    def test_extra_fields_forbidden(self) -> None:
        with self.assertRaises(ValidationError):
            FileRef(
                uri="resource://docx/files/out",
                sha256="1" * 64,
                size=500,
                mime="application/pdf",
                unexpected_field="hack",  # type: ignore
            )


class TestIssueAndDiagnostics(unittest.TestCase):
    """Kiểm tra hợp đồng Issue và hành vi của Diagnostics."""

    def test_valid_issue_creation(self) -> None:
        loc = Location(sheet="Summary", cell="B7", range="B7:D14")
        issue = Issue(
            code="E-XLSX-SHIFT-FORMULA",
            severity=Severity.ERROR,
            engine=Engine.XLSX,
            message="Formula shift exceeded template boundary",
            location=loc,
            fixable_by=FixableBy.AI,
            suggested_action="Adjust mutation offset parameter",
            evidence={"expected_range": "B7:D20", "actual_range": "B7:D30"},
        )
        self.assertEqual(issue.code, "E-XLSX-SHIFT-FORMULA")
        self.assertEqual(issue.severity, Severity.ERROR)
        self.assertEqual(issue.location.sheet, "Summary")
        self.assertEqual(issue.location.cell, "B7")

    def test_diagnostics_routing_and_helpers(self) -> None:
        diag = Diagnostics(engine=Engine.DOCX)
        self.assertFalse(diag.has_errors)
        self.assertEqual(diag.total_count, 0)

        err_issue = Issue(
            code="E-DOCX-OPENXML-TC-P",
            severity=Severity.ERROR,
            engine=Engine.DOCX,
            message="Cell missing required <w:p> element",
        )
        warn_issue = Issue(
            code="W-DEV-STYLE-MISMATCH",
            severity=Severity.WARNING,
            engine=Engine.DOCX,
            message="Font style deviated from reference template",
            fixable_by=FixableBy.HUMAN,
        )
        info_issue = Issue(
            code="I-DOCX-PERF-OPTIMIZED",
            severity=Severity.INFO,
            engine=Engine.DOCX,
            message="Render finished in 45ms",
        )

        diag.add_issue(err_issue)
        diag.add_issue(warn_issue)
        diag.add_issue(info_issue)

        self.assertTrue(diag.has_errors)
        self.assertEqual(len(diag.errors), 1)
        self.assertEqual(len(diag.warnings), 1)
        self.assertEqual(len(diag.info), 1)
        self.assertEqual(diag.total_count, 3)


class TestResultEnvelope(unittest.TestCase):
    """Kiểm tra phong bì kết quả thống nhất ResultEnvelope."""

    def test_successful_envelope(self) -> None:
        fileref = FileRef(
            uri="resource://diagram/files/master-erd",
            sha256="e" * 64,
            size=40960,
            mime="application/vnd.jgraph.mxfile",
        )
        diag = Diagnostics(engine=Engine.DIAGRAM)
        stats = Stats(render_time_ms=128.5, elements_processed=24)

        env = ResultEnvelope(
            success=True,
            file_ref=fileref,
            diagnostics=diag,
            guarantees_applied=["pure_mxGraphModel_enforced", "orthogonal_perimeter_routed"],
            stats=stats,
        )
        self.assertTrue(env.success)
        self.assertEqual(len(env.guarantees_applied), 2)
        self.assertEqual(env.stats.render_time_ms, 128.5)

    def test_inconsistent_success_with_errors_rejected(self) -> None:
        diag = Diagnostics(engine=Engine.DOCX)
        diag.add_issue(
            Issue(
                code="E-DOCX-SEC-INJECTION",
                severity=Severity.ERROR,
                engine=Engine.DOCX,
                message="Dangerous Jinja template injection detected",
            )
        )
        # Bắt buộc raise lỗi do success=True nhưng diagnostics lại có errors
        with self.assertRaises(ValidationError):
            ResultEnvelope(
                success=True,
                diagnostics=diag,
            )

    def test_failed_envelope_with_errors_allowed(self) -> None:
        diag = Diagnostics(engine=Engine.XLSX)
        diag.add_issue(
            Issue(
                code="E-XLSX-LOCK-VIOLATION",
                severity=Severity.ERROR,
                engine=Engine.XLSX,
                message="Attempted write to locked cell C10",
            )
        )
        env = ResultEnvelope(
            success=False,
            diagnostics=diag,
        )
        self.assertFalse(env.success)
        self.assertTrue(env.diagnostics.has_errors)

    def test_envelope_json_roundtrip(self) -> None:
        fileref = FileRef(
            uri="resource://docx/files/report",
            sha256="f" * 64,
            size=1024,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        diag = Diagnostics(engine=Engine.DOCX)
        env = ResultEnvelope(
            success=True,
            file_ref=fileref,
            diagnostics=diag,
            guarantees_applied=["cantSplit_enforced"],
            stats=Stats(render_time_ms=50.0),
        )
        json_data = env.model_dump_json()
        restored = ResultEnvelope.model_validate_json(json_data)
        self.assertEqual(restored.success, env.success)
        self.assertEqual(restored.file_ref.sha256, env.file_ref.sha256)
        self.assertEqual(restored.guarantees_applied, ["cantSplit_enforced"])


class TestBaseSpec(unittest.TestCase):
    """Kiểm tra lớp cơ sở đặc tả BaseSpec."""

    class MockCustomSpec(BaseSpec):
        doc_type: str = "report"
        page_count: int = 10

    def test_basespec_serialization_and_deserialization(self) -> None:
        spec = self.MockCustomSpec(
            title="Quarterly Review",
            description="Q3 performance report",
            doc_type="report",
            page_count=15,
            meta={"author": "YukiiMin"},
        )
        json_str = spec.to_json()
        loaded = self.MockCustomSpec.from_json(json_str)

        self.assertEqual(loaded.title, "Quarterly Review")
        self.assertEqual(loaded.version, "2.0")
        self.assertEqual(loaded.page_count, 15)
        self.assertEqual(loaded.meta["author"], "YukiiMin")

    def test_basespec_forbids_unknown_fields(self) -> None:
        with self.assertRaises(ValidationError):
            self.MockCustomSpec(
                title="Invalid Spec",
                unrecognized_key="should_fail",  # type: ignore
            )


if __name__ == "__main__":
    unittest.main()
