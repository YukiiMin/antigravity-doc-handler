"""
tests.conformance.test_docx_conformance
End-to-End Conformance test suite for Phase 1 DOCX Module.
Chains the complete tool lifecycle: Register -> Render -> Build -> Inspect -> Patch -> Merge -> Fields -> Validate.
"""

import tempfile
import unittest
from pathlib import Path

import docx

from doctools.core.docx.package_io import PackageWriter
from doctools.core.docx.schema import schema_helper
from doctools.infra.file_store import FileStore
from doctools.operations.docx import (
    docx_build_document,
    docx_inspect_structure,
    docx_merge,
    docx_patch,
    docx_register_template,
    docx_render_template,
    docx_update_fields,
    docx_validate,
)
from doctools.registry import ToolRegistry


class TestDocxConformance(unittest.TestCase):
    """End-to-End conformance verification across the entire DOCX Engine."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)
        self.file_store = FileStore(base_dir=self.base_dir / "store")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_complete_docx_lifecycle_pipeline(self):
        """Executes full multi-step document transformation pipeline."""
        # Step 1: Create a base template document
        tpl_path = self.base_dir / "contract_template.docx"
        doc = docx.Document()
        doc.add_heading("HỢP ĐỒNG SỐ: {{ contract_no }}", level=1)
        p = doc.add_paragraph("Bên A: {{ client_name }}")
        p.runs[0].bold = True
        tbl = doc.add_table(rows=2, cols=2)
        tbl.rows[0].cells[0].paragraphs[0].text = "Hạng mục"
        tbl.rows[0].cells[1].paragraphs[0].text = "Giá trị"
        tbl.rows[1].cells[0].paragraphs[0].text = "{{ item_name }}"
        tbl.rows[1].cells[1].paragraphs[0].text = "{{ item_price }}"
        PackageWriter.write_document_to_path(doc, tpl_path)

        # Step 2: Register Template with Manifest
        manifest_data = {
            "template_id": "tpl_master_contract",
            "version": 1,
            "variables": {
                "contract_no": {"type": "string", "immutable": True},
                "client_name": {"type": "string"},
                "item_name": {"type": "string"},
                "item_price": {"type": "string"},
            },
            "layout_policy_default": {"apply_guards": "apply"},
        }
        reg_env = docx_register_template(
            template_path_or_ref=tpl_path,
            manifest=manifest_data,
            file_store=self.file_store,
        )
        self.assertTrue(reg_env.success)

        # Step 3: Render Template via Path A
        context = {
            "contract_no": "HD-2026-X1",
            "client_name": "Tập đoàn Viễn thông A",
            "item_name": "Phần mềm Antigravity Core",
            "item_price": "500.000.000 VND",
        }
        render_env = docx_render_template(
            template_ref_or_id="tpl_master_contract",
            context_data=context,
            file_store=self.file_store,
        )
        self.assertTrue(render_env.success)
        rendered_ref = render_env.file_ref
        self.assertIsNotNone(rendered_ref)

        # Step 4: Inspect Rendered Document Structure
        inspect_env = docx_inspect_structure(rendered_ref, file_store=self.file_store)
        self.assertTrue(inspect_env.success)
        self.assertIn("structure", inspect_env.stats.extra)
        tree = inspect_env.stats.extra["structure"]
        self.assertEqual(tree["stats"]["table_count"], 1)

        # Step 5: Patch Document In-Place (Modify Price)
        patch_ops = [
            {
                "anchor": "/body/tbl[0]/tr[1]/tc[1]",
                "op": "update_cell",
                "payload": "750.000.000 VND",
            }
        ]
        patch_env = docx_patch(
            file_ref_or_path=rendered_ref,
            operations=patch_ops,
            file_store=self.file_store,
        )
        self.assertTrue(patch_env.success)
        patched_ref = patch_env.file_ref

        # Step 6: Create Appendix via Path B DocSpec Builder
        docspec_data = {
            "docspec_version": "1.0",
            "title": "Phụ lục kỹ thuật đính kèm",
            "blocks": [
                {"type": "heading", "level": 2, "text": "Đặc tả triển khai hệ thống"},
                {"type": "paragraph", "text": "Thời gian bàn giao trong vòng 30 ngày."},
            ],
        }
        docspec_env = docx_build_document(
            source_type="docspec",
            docspec=docspec_data,
            file_store=self.file_store,
        )
        self.assertTrue(docspec_env.success)
        appendix_ref = docspec_env.file_ref

        # Step 7: Merge Patched Contract with Appendix
        merge_env = docx_merge(
            base_ref_or_path=patched_ref,
            parts=[appendix_ref],
            style_conflict_policy="master_wins",
            file_store=self.file_store,
        )
        self.assertTrue(merge_env.success)
        merged_ref = merge_env.file_ref

        # Step 8: Update Dynamic Fields (Inject updateFields)
        field_env = docx_update_fields(
            file_ref_or_path=merged_ref,
            field_update="update_on_open",
            file_store=self.file_store,
        )
        self.assertTrue(field_env.success)
        final_ref = field_env.file_ref

        # Step 9: Final Conformance Quality Gate Validation (DG-01..DG-06)
        val_env = docx_validate(final_ref, file_store=self.file_store)
        self.assertTrue(val_env.success)
        self.assertEqual(len(val_env.diagnostics.errors), 0)

        # Step 10: Verify physical document integrity on disk
        final_file = self.file_store.resolve(final_ref)
        final_doc = docx.Document(final_file)
        full_text = " ".join([p.text for p in final_doc.paragraphs])

        self.assertIn("HỢP ĐỒNG SỐ: HD-2026-X1", full_text)
        self.assertIn("Bên A: Tập đoàn Viễn thông A", full_text)
        self.assertIn("Đặc tả triển khai hệ thống", full_text)

        # Check patched table value
        table_cells = [c.text for row in final_doc.tables[0].rows for c in row.cells]
        self.assertIn("750.000.000 VND", table_cells)


if __name__ == "__main__":
    unittest.main()
