# doctools — Document & Diagram Engineering Engine Quickref

> **Sub-repo Root Context**. Áp dụng cho toàn bộ `tool/pdf_to_docx_converter`.
> Architecture: `README.md` | Master Plan: `ai_native_toolkit_modular_architecture_plan.md` | Task State: `.agent_scratchpad.md`

---

## 1. CHECKPOINT Recovery Protocol (BẮT BUỘC)

Khi nhận `{{ CHECKPOINT N }}` signal hoặc context bị reset:
1. **Đọc file này** (GEMINI.md) — xác nhận invariants và scope boundary.
2. **Đọc `.agent_scratchpad.md`** — lấy current goal, completed steps, và remaining TODOs.
3. Không thực hiện code action ngay — xác nhận xong mới phản hồi user.

---

## 2. Bản Đồ Module & Cơ Chế Nạp Context (Glob / Progressive)

Hệ thống vận hành theo cơ chế **Hierarchical Scope + Glob Rules + Progressive Skills**:

| Module | Thư mục mã nguồn & Tests | Rule tự động kích hoạt (Glob) | Skill chuyên môn (.agents/skills/) |
|---|---|---|---|
| **DOCX** | `doctools/core/docx/`, `doctools/operations/docx/`, `tests/test_docx/` | `rule_docx_engine_standards.md` | `docx-handler` |
| **XLSX** | `doctools/core/xlsx/`, `doctools/operations/xlsx/`, `tests/test_xlsx/` | `rule_xlsx_engine_standards.md` | `excel-handler` |
| **DIAGRAM** | `doctools/core/diagram/`, `doctools/operations/diagram/`, `tests/test_diagram/` | `rule_diagram_engine_standards.md` | `mxgraph-diagram-engineering` |
| **QA / GATES** | `doctools/gates/`, `tests/conformance/` | `rule_quality_gate_and_verification.md` | `doc-spreadsheet-diagnostics` |
| **DELIVERY** | Toàn bộ repo khi thực thi micro-commit `X.Y.Z` | `rule_git_workflow.md` | `doctools-delivery` |

*Lưu ý*: Chi tiết các bất biến OpenXML (`ERR_DOCX_*`), 14 nguyên tắc Excel (`E1–E14`), và 21 nguyên tắc Draw.io (`MX_INV_01–21`) được cấu hình **glob** tự động nạp khi chạm vào file tương ứng; không nhồi nhét vào root.

---

## 3. Bất Biến Cốt Lõi Dự Án (Core Invariants)

1. **Scope Boundary & Git Invariant**:
   - CHỈ commit/push vào repo con (`antigravity-doc-handler`). TUYỆT ĐỐI KHÔNG chạm vào main repo SAP.
   - **NGHIÊM CẤM tự ý commit/push**: Chỉ thực thi khi user đồng ý tường minh (*"commit cho tôi"*, *"xác nhận lệnh commit"*).
2. **Kỷ luật Sửa Lỗi (Max 1 Fix Attempt)**:
   - Tối đa 1 lần thử sửa cho mỗi lỗi. Nếu không đạt hoặc sinh lỗi mới: DỪNG LẠI, giải thích root cause, chờ feedback. Không đoán mò.
3. **Giới Hạn Tệp Tin & Trình Bày Code**:
   - Mọi tệp code mới phải tuân thủ nghiêm ngặt **< 300 dòng/file**.
   - CẤM truncate code dạng `// rest of code remains unchanged`.
4. **Bảo Tồn Dual-Run & Zero Python at Root**:
   - Mã nguồn nằm gọn trong `doctools/`, `tests/`, và `legacy_engines/`. Tuyệt đối không để script python ở root repo.
5. **Kỷ Luật Task & Scratchpad**:
   - Duy trì `.agent_scratchpad.md` ở root workspace. Đọc ở đầu iteration, cập nhật trước khi kết thúc response.
