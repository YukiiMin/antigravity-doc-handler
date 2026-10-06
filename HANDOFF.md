# Project Handoff: AI-Native Document & Diagram Engine (`pdf_to_docx_converter`)

> **Thời điểm lập**: 2026-10-07
> **Nhánh hiện tại**: `feat/phase-1-docx`
> **Trạng thái**: Hoàn tất Phase 0, Phase 1.1.0, Phase 1.1.1 và Tái cấu trúc Agent Context Architecture. Sẵn sàng cho **Tiểu bước 1.1.2**.

---

## 1. Hướng Dẫn Mở Workspace Chuẩn (Session Mới)

Để tránh hiện tượng AI bị nhiễu bởi các file và quy tắc của dự án mẹ SAP (`ZSCORT`), bạn thực hiện theo các bước sau trong Antigravity IDE:

1. **Mở đúng thư mục làm việc**:
   - Chọn menu `File` $\rightarrow$ `Open Folder...` (phím tắt `Ctrl + K, Ctrl + O`).
   - Chọn đường dẫn: `d:\Minh\For_myself\ZSCORT_GSU26_SAP05\tool\pdf_to_docx_converter`.
   - Nhấn **Select Folder**.
2. **Kiểm tra trạng thái sau khi mở**:
   - Thư mục gốc hiển thị trong Explorer là `pdf_to_docx_converter`.
   - IDE sẽ tự động nhận diện `GEMINI.md`, `.agents/rules/`, và `.agents/skills/` cục bộ của repo này mà không bị chồng lấn quy tắc SAP.
3. **Mở khung Chat mới**:
   - Bắt đầu một session chat mới hoàn toàn sạch sẽ, không lo đầy context.

---

## 2. Bản Đồ Hiện Trạng Dự Án (Project Status)

### 2.1. Tiến độ các giai đoạn
- [x] **Phase 0 — Foundation & Plumbing (100% DONE)**:
  - Phân rã kiến trúc 5 tầng, xóa sạch các module monolithic cũ (`legacy_engines`).
  - Toàn bộ mã nguồn cũ được lưu trữ an toàn tại nhánh `origin/archive/legacy-v1`.
- [x] **Tiểu bước 1.1.0 — Schema Helper & Package IO (100% DONE - Commit `d35de53`)**:
  - `TagOrderRegistry` và `SchemaHelper` OOXML cho `w:pPr`, `w:rPr`, `w:tblPr`, `w:tcPr`.
  - `PackageIO` bóc tách và đóng gói an toàn file `.docx` không qua thư mục tạm.
- [x] **Tiểu bước 1.1.1 — Template Linter & Run Consolidator (100% DONE - Commit `fb29cab`)**:
  - `TemplateLinter` phát hiện rách Run Jinja và ô bảng trống paragraph.
  - `JinjaNormalizer` hàn gắn Run Splitting giữa các tag Jinja.
- [x] **Tái Cấu Trúc Agent Context Architecture (100% DONE)**:
  - **Rules**: Cấu hình chuẩn `trigger: glob` (kèm `globs:`) cho 3 engine (`docx`, `xlsx`, `diagram`) và `trigger: model_decision` cho 5 rules chuyên môn.
  - **GEMINI.md**: Viết lại gọn nhẹ 48 dòng tại root, bổ sung module GEMINI tại `doctools/core/docx/` và `doctools/operations/docx/`.
  - **Skills**: Khai tử hoàn toàn Workflows cũ, triển khai `doctools-delivery` và master skill `agent-context-architecture`.

### 2.2. Kiểm thử tự động (Quality Gate)
- **50/50 test cases PASS 100%** trong ~1.01s.
- Lệnh chạy kiểm thử: `python -m unittest discover -s tests`.

---

## 3. Nhiệm Vụ Tiếp Theo: Tiểu Bước 1.1.2 (Template Registry & Inventory)

Trong session chat mới, nhiệm vụ đầu tiên là triển khai **Tiểu bước 1.1.2** thuộc **Phase 1.1 (Template Path Foundation)**:

| Thành Phần Cần Xây Dựng | Vị Trí File | Yêu Cầu Kỹ Thuật |
|---|---|---|
| **Template Manifest Schema** | `doctools/core/docx/manifest.py` | Pydantic model cho Manifest: metadata, biến khai báo, kiểu dữ liệu, danh sách đoạn văn bản bất biến (`immutable_hashes`), layout constraints. |
| **Template Registry** | `doctools/core/docx/registry.py` | Đăng ký, tra cứu, liệt kê (`list_templates`), kiểm tra tính hợp lệ của cặp `template.docx` + `manifest.json`. |
| **Operation API** | `doctools/operations/docx/template_ops.py` | Bổ sung hàm nghiệp vụ `register_template()` và `get_template_info()`. |
| **Unit Tests** | `tests/docx/test_template_registry.py` | Kiểm thử đăng ký template hợp lệ, phát hiện manifest lỗi, từ chối template không khớp. |

---

## 4. Prompt Mẫu Để Bắt Đầu Session Chat Mới (Copy & Paste)

Sau khi mở folder `pdf_to_docx_converter` trong cửa sổ mới, bạn chỉ cần copy đoạn prompt dưới đây gửi cho AI:

```markdown
Chào bạn, tôi vừa mở workspace độc lập cho repo `pdf_to_docx_converter`.
Hãy đọc kỹ `HANDOFF.md`, `GEMINI.md`, và `.agents/skills/doctools-delivery/SKILL.md` để nắm hiện trạng.
Hiện tại chúng ta đã hoàn tất Phase 0, 1.1.0 và 1.1.1 (50/50 tests pass).
Mục tiêu tiếp theo của chúng ta là thực hiện **Tiểu bước 1.1.2 — Template Registry & Manifest Schema**.
Hãy kiểm tra test suite hiện tại và lập kế hoạch thực hiện 1.1.2 theo đúng quy chuẩn micro-commit!
```
