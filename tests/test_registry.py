"""
Unit test suite for doctools.registry (Central ToolRegistry and MCP Dispatcher).
Kiểm tra đăng ký công cụ, kiểm thực tiền tố namespace, bắt ngoại lệ tự động,
và định dạng danh mục công cụ MCP.
"""

from __future__ import annotations
import unittest
from typing import Optional
from pydantic import BaseModel, Field

from doctools import ToolRegistry
from doctools.contract.envelope import Diagnostics, ResultEnvelope, Stats
from doctools.contract.fileref import FileRef
from doctools.contract.issues import Engine, Issue, Severity


class DummyInputModel(BaseModel):
    template_path: str = Field(..., description="Đường dẫn tới file mẫu")
    strict: bool = Field(default=True, description="Chế độ kiểm tra nghiêm ngặt")


class TestToolRegistry(unittest.TestCase):
    """Kiểm tra hoạt động của ToolRegistry."""

    def setUp(self) -> None:
        self.registry = ToolRegistry()

    def test_valid_tool_registration(self) -> None:
        @self.registry.register(
            name="docx.lint_template",
            description="Kiểm tra tính hợp lệ của mẫu tài liệu Word",
            input_model=DummyInputModel,
        )
        def lint_handler(template_path: str, strict: bool = True) -> ResultEnvelope:
            diag = Diagnostics(engine=Engine.DOCX)
            return ResultEnvelope(
                success=True,
                diagnostics=diag,
                guarantees_applied=["template_linted"],
            )

        self.assertTrue(self.registry.is_registered("docx.lint_template"))
        meta = self.registry.get_tool_metadata("docx.lint_template")
        self.assertIsNotNone(meta)
        self.assertEqual(meta.engine, Engine.DOCX)
        self.assertEqual(meta.name, "docx.lint_template")
        self.assertIn("properties", meta.input_schema)
        self.assertIn("template_path", meta.input_schema["properties"])

    def test_invalid_prefix_rejected(self) -> None:
        # Thiếu dấu chấm
        with self.assertRaises(ValueError):
            @self.registry.register("invalid_tool_name", "Description")
            def h1() -> ResultEnvelope:
                return ResultEnvelope(success=True, diagnostics=Diagnostics(engine=Engine.DOCX))

        # Tiền tố không nằm trong VALID_NAMESPACES
        with self.assertRaises(ValueError):
            @self.registry.register("unknown_module.action", "Description")
            def h2() -> ResultEnvelope:
                return ResultEnvelope(success=True, diagnostics=Diagnostics(engine=Engine.DOCX))

    def test_collision_detection(self) -> None:
        @self.registry.register("xlsx.preflight", "Description 1")
        def h_first() -> ResultEnvelope:
            return ResultEnvelope(success=True, diagnostics=Diagnostics(engine=Engine.XLSX))

        # Đăng ký trùng tên lần 2 bắt buộc báo lỗi va chạm
        with self.assertRaises(ValueError) as ctx:
            @self.registry.register("xlsx.preflight", "Description 2")
            def h_second() -> ResultEnvelope:
                return ResultEnvelope(success=True, diagnostics=Diagnostics(engine=Engine.XLSX))

        self.assertIn("Tool collision", str(ctx.exception))

    def test_successful_execution_and_timing(self) -> None:
        @self.registry.register("diagram.plan_layout", "Lập kế hoạch layout sơ đồ")
        def plan_handler(spec: dict) -> ResultEnvelope:
            diag = Diagnostics(engine=Engine.DIAGRAM)
            return ResultEnvelope(
                success=True,
                diagnostics=diag,
                guarantees_applied=["topology_planned"],
            )

        result = self.registry.execute("diagram.plan_layout", {"spec": {"nodes": []}})

        self.assertTrue(result.success)
        self.assertIn("topology_planned", result.guarantees_applied)
        self.assertIsNotNone(result.stats)
        self.assertGreaterEqual(result.stats.render_time_ms, 0.0)

    def test_unknown_tool_execution(self) -> None:
        result = self.registry.execute("infra.non_existent_tool")
        self.assertFalse(result.success)
        self.assertTrue(result.diagnostics.has_errors)
        self.assertEqual(result.diagnostics.errors[0].code, "E-REGISTRY-TOOL-NOT-FOUND")

    def test_uncaught_exception_middleware(self) -> None:
        @self.registry.register("docx.render_template", "Render mẫu tài liệu")
        def buggy_handler() -> ResultEnvelope:
            raise ZeroDivisionError("Simulated unexpected crash in engine logic")

        # Middleware phải tóm ngoại lệ và biến đổi thành ResultEnvelope(success=False)
        result = self.registry.execute("docx.render_template")

        self.assertFalse(result.success)
        self.assertTrue(result.diagnostics.has_errors)
        err = result.diagnostics.errors[0]
        self.assertEqual(err.code, "E-SYS-UNCAUGHT-EXCEPTION")
        self.assertIn("ZeroDivisionError", err.message)
        self.assertIsNotNone(result.stats)

    def test_list_tools_filtering(self) -> None:
        @self.registry.register("docx.inspect", "Soi tài liệu docx")
        def h_docx() -> ResultEnvelope:
            return ResultEnvelope(success=True, diagnostics=Diagnostics(engine=Engine.DOCX))

        @self.registry.register("xlsx.mutate", "Đột biến bảng tính")
        def h_xlsx() -> ResultEnvelope:
            return ResultEnvelope(success=True, diagnostics=Diagnostics(engine=Engine.XLSX))

        # Toàn bộ tools
        all_tools = self.registry.list_tools()
        self.assertEqual(len(all_tools), 2)

        # Lọc chỉ lấy DOCX
        docx_tools = self.registry.list_tools(engine=Engine.DOCX)
        self.assertEqual(len(docx_tools), 1)
        self.assertEqual(docx_tools[0]["name"], "docx.inspect")

        # Lọc chỉ lấy XLSX
        xlsx_tools = self.registry.list_tools(engine=Engine.XLSX)
        self.assertEqual(len(xlsx_tools), 1)
        self.assertEqual(xlsx_tools[0]["name"], "xlsx.mutate")


if __name__ == "__main__":
    unittest.main()
