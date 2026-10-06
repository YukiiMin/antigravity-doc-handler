"""Các operation: mỏng, chỉ ghép core + rào chắn + phong bì Result. Tự kiểm sau khi ghi."""
from __future__ import annotations

from .contract.inputs import DiffInventoryIn, PreflightIn, SetCellsIn
from .contract.models import Result
from .core.guards import make_file_ref, resolve_in_roots
from .core.xlsx import diff as xdiff
from .core.xlsx import mutate as xmutate
from .core.xlsx import preflight as xpre
from .registry import operation


@operation(name="preflight_xlsx", input_model=PreflightIn, read_only=True, idempotent=True,
           description="Quét file .xlsx (chỉ đọc): liệt kê thành phần (ảnh, chart, pivot, CF, DV, merge, công thức...) "
                       "và đánh giá rủi ro trước khi sửa. Gọi TRƯỚC mọi thao tác ghi.")
def preflight_xlsx(p: PreflightIn) -> Result:
    inv = xpre.scan(resolve_in_roots(p.path))
    tier, issues = xpre.assess(inv)
    return Result(success=tier != "REJECT", data={"inventory": inv, "fidelity_tier": tier}, issues=issues)


@operation(name="set_cells_xlsx", input_model=SetCellsIn, read_only=False, idempotent=True,
           description="Ghi giá trị vào ô của một sheet trên BẢN SAO (không ghi đè nguồn). Tôn trọng vùng khóa, ô gộp; "
                       "tự đối chiếu Inventory trước/sau và báo mất thành phần.")
def set_cells_xlsx(p: SetCellsIn) -> Result:
    src = resolve_in_roots(p.path)
    out = resolve_in_roots(p.out_path) if p.out_path else src.with_name(f"{src.stem}_out.xlsx")
    before = xpre.scan(src)
    issues = xmutate.set_cells(src, out, p.sheet, p.updates, p.locked_zones, p.allow_formulas)
    if any(i.severity == "error" for i in issues):
        return Result(success=False, issues=issues)                      # không ghi gì (all-or-nothing)
    after = xpre.scan(out)
    issues += xdiff.diff_inventory(before, after, {})
    if after["formulas"]:
        from .contract.models import Issue
        issues.append(Issue(code="W-CALC-NO-CACHE", severity="warning", fixable_by="engine",
                            message="File lưu ra chưa có giá trị tính sẵn cho công thức; Excel sẽ tính khi mở.",
                            suggested_action="Nếu cần đọc giá trị ngay, dùng công cụ recalc (ngoài phạm vi mẫu)."))
    ok = not any(i.severity == "error" for i in issues)
    return Result(success=ok, data={"cells_written": len(p.updates), "released": ok},
                  file_ref=make_file_ref(out), issues=issues)


@operation(name="diff_inventory_xlsx", input_model=DiffInventoryIn, read_only=True, idempotent=True,
           description="So Inventory của hai file .xlsx; mọi thay đổi không khai báo trong declared_changes là lỗi.")
def diff_inventory_xlsx(p: DiffInventoryIn) -> Result:
    b, a = xpre.scan(resolve_in_roots(p.before)), xpre.scan(resolve_in_roots(p.after))
    issues = xdiff.diff_inventory(b, a, p.declared_changes)
    return Result(success=not issues, data={"before": b, "after": a}, issues=issues)
