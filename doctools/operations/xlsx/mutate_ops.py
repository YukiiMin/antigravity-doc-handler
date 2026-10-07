"""
doctools.operations.xlsx.mutate_ops — Thao tác MCP đột biến bảng tính Excel (xlsx.mutate).
Tuân thủ FR-05, FR-06, FR-09, D-02, E1..E14 của Foundation Plan v1.1:
- Tiếp nhận MutationSpec JSON từ AI caller.
- Tải template an toàn (data_only=False) bảo toàn DrawingML và công thức.
- Nhân bản Prototype Row, đồng bộ viền vùng merge, dịch chuyển công thức AST.
- Ghi đè file đích hoặc cấp phát FileRef trong FileStore, trả về ResultEnvelope.
"""

from __future__ import annotations
import io
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import openpyxl
from pydantic import BaseModel, ConfigDict

from doctools.contract.envelope import Diagnostics, FileRef, ResultEnvelope, Stats
from doctools.contract.issues import Engine, Issue, Severity
from doctools.contract.xlsx.mutation import MutationSpec
from doctools.core.xlsx.mutate.mutator import XlsxMutator
from doctools.core.xlsx.template import XlsxTemplateRegistry, get_default_xlsx_template_registry
from doctools.infra.file_store import FileStore
from doctools.registry import ToolRegistry


class MutateInput(BaseModel):
    """Schema đầu vào cho MCP tool xlsx.mutate."""
    model_config = ConfigDict(extra="ignore")

    spec: Union[Dict[str, Any], MutationSpec]
    template_path: Optional[str] = None
    output_path: Optional[str] = None


def xlsx_mutate(
    spec: Union[MutationSpec, Dict[str, Any]],
    template_path: Optional[str] = None,
    output_path: Optional[str] = None,
    template_registry: Optional[XlsxTemplateRegistry] = None,
    file_store: Optional[FileStore] = None,
) -> ResultEnvelope:
    """
    Thực thi đột biến bảng tính theo MutationSpec và trả về ResultEnvelope.
    """
    diag = Diagnostics(engine=Engine.XLSX)
    guarantees: List[str] = ["E1_TEMPLATE_DRIVEN", "ERR_XLSX_004_SAFE_MERGE"]

    # 1. Parse MutationSpec
    if isinstance(spec, dict):
        try:
            parsed_spec = MutationSpec.model_validate(spec)
        except Exception as exc:
            diag.add_issue(
                Issue(
                    code="E-XLSX-SPEC-INVALID",
                    severity=Severity.ERROR,
                    engine=Engine.XLSX,
                    message=f"MutationSpec không hợp lệ: {exc}",
                )
            )
            return ResultEnvelope(success=False, diagnostics=diag)
    else:
        parsed_spec = spec

    # 2. Xác định đường dẫn template nguồn
    resolved_template_path = template_path
    locked_zones = list(parsed_spec.locked_zones)

    if not resolved_template_path:
        t_reg = template_registry or get_default_xlsx_template_registry()
        tpl = t_reg.get(parsed_spec.template_ref_or_id)
        if tpl:
            resolved_template_path = tpl.file_path
            locked_zones.extend(tpl.manifest.locked_zones)
        elif os.path.exists(parsed_spec.template_ref_or_id):
            resolved_template_path = parsed_spec.template_ref_or_id
        elif file_store:
            try:
                resolved_template_path = file_store.get_real_path(parsed_spec.template_ref_or_id)
            except Exception:
                pass

    if not resolved_template_path or not os.path.exists(resolved_template_path):
        diag.add_issue(
            Issue(
                code="E-XLSX-TEMPLATE-NOT-FOUND",
                severity=Severity.ERROR,
                engine=Engine.XLSX,
                message=f"Không tìm thấy template Excel: {parsed_spec.template_ref_or_id}",
            )
        )
        return ResultEnvelope(success=False, diagnostics=diag)

    # 3. Tải workbook bảo toàn DrawingML & công thức (data_only=False)
    try:
        wb = openpyxl.load_workbook(resolved_template_path, data_only=False)
        guarantees.append("ERR_XLSX_006_DRAWINGML_PRESERVED")
    except Exception as exc:
        diag.add_issue(
            Issue(
                code="E-XLSX-LOAD-FAILED",
                severity=Severity.ERROR,
                engine=Engine.XLSX,
                message=f"Không thể mở workbook template: {exc}",
            )
        )
        return ResultEnvelope(success=False, diagnostics=diag)

    # 4. Thực thi Mutator
    mutator = XlsxMutator(wb, locked_zones=locked_zones)
    mutation_issues = mutator.mutate(parsed_spec)

    for iss in mutation_issues:
        diag.add_issue(iss)

    has_error = any(iss.severity == Severity.ERROR for iss in mutation_issues)
    if has_error:
        return ResultEnvelope(success=False, diagnostics=diag, guarantees_applied=guarantees)

    # 5. Lưu kết quả và cấp phát FileRef
    fs = file_store or FileStore()
    _XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    out_fileref: Optional[FileRef] = None

    try:
        if output_path is not None:
            dest = Path(output_path).resolve()
            dest.parent.mkdir(parents=True, exist_ok=True)
            wb.save(str(dest))
            out_fileref = fs.store_file(dest, mime=_XLSX_MIME, engine="xlsx")
        else:
            buf = io.BytesIO()
            wb.save(buf)
            buf.seek(0)
            hint_name = parsed_spec.output_filename_hint or "mutated_result.xlsx"
            out_fileref = fs.store_bytes(
                data=buf.getvalue(),
                mime=_XLSX_MIME,
                engine="xlsx",
                filename_hint=hint_name,
            )
    except Exception as exc:
        diag.add_issue(
            Issue(
                code="E-XLSX-SAVE-FAILED",
                severity=Severity.ERROR,
                engine=Engine.XLSX,
                message=f"Không thể lưu workbook đầu ra: {exc}",
            )
        )
        return ResultEnvelope(success=False, diagnostics=diag)

    stats = Stats(
        elements_processed=len(parsed_spec.expansions) + len(parsed_spec.cell_updates),
        extra={
            "sheets": wb.sheetnames,
            "expansions_count": len(parsed_spec.expansions),
            "cell_updates_count": len(parsed_spec.cell_updates),
        },
    )

    return ResultEnvelope(
        success=True,
        file_ref=out_fileref,
        diagnostics=diag,
        guarantees_applied=guarantees,
        stats=stats,
    )


def register_xlsx_mutate_tools(
    registry: ToolRegistry,
    template_registry: Optional[XlsxTemplateRegistry] = None,
) -> None:
    """Đăng ký công cụ xlsx.mutate vào hệ thống ToolRegistry."""
    t_reg = template_registry or get_default_xlsx_template_registry()

    @registry.register(
        name="xlsx.mutate",
        description="Đột biến bảng tính Excel: nhân bản dòng mẫu, cập nhật ô và co giãn dải ô công thức.",
        input_model=MutateInput,
    )
    def handle_mutate(
        spec: Union[Dict[str, Any], MutationSpec],
        template_path: Optional[str] = None,
        output_path: Optional[str] = None,
    ) -> ResultEnvelope:
        return xlsx_mutate(
            spec=spec,
            template_path=template_path,
            output_path=output_path,
            template_registry=t_reg,
            file_store=registry.file_store,
        )
