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

## 3. Chiến Lược Tối Ưu Hóa Token: Kiến Trúc Ngôn Ngữ Hybrid (English Core + Bilingual Anchors)

### 3.1. Bản chất kinh tế Token & Cơ chế Trigger
- **Vì sao phải chuyển sang Tiếng Anh?**
  Bộ tokenizer của các LLM hiện đại (Gemini, Claude, GPT) chia từ tiếng Việt có dấu thanh thành 2–3 tokens mỗi âm tiết (ví dụ: *"nghiên cứu chuyển đổi"* tốn ~7 tokens, trong khi *"convert research"* chỉ tốn 2 tokens). Việc giữ ngữ cảnh thuần tiếng Việt làm tiêu hao gấp đôi ngân sách, dễ chạm trần cảnh báo đỏ 20,000 tokens của hệ thống Rules.
- **Giải pháp Hybrid (English Core + Bilingual Anchors)**:
  1. **Thân file (Body)** của `GEMINI.md`, `AGENTS.md`, `rules/`, và `skills/` (kèm `references/`) $\rightarrow$ **100% English**: ngắn gọn, chuẩn xác, tiết kiệm 50% token, triệt tiêu mơ hồ ngữ nghĩa kỹ thuật.
  2. **Trường `description:` của Rules & Skills** $\rightarrow$ **Song ngữ (English + Vietnamese Keywords)**: Cung cấp mô tả tiếng Anh kèm các từ khóa/thuật ngữ tiếng Việt thông dụng (ví dụ: *"rách bảng, chẻ đôi hàng, băm nát run Jinja, ngắt trang, kiểm toán chất lượng"*).
  3. **Giao tiếp trong chat**: User hoàn toàn thoải mái trò chuyện bằng **Tiếng Việt** (dùng từ lóng, biệt ngữ kỹ thuật). Nhờ shared embedding space đa ngôn ngữ kết hợp cùng Bilingual Anchors, AI sẽ nhận diện và kích hoạt đúng 100% Rules và Skills mà không bị lệch.

---

## 4. Kế Hoạch Cho Session Mới (Theo Thứ Tự Ưu Tiên)

Trong session chat mới, AI cần thực hiện tuần tự 2 nhiệm vụ:

### Nhiệm Vụ 1: Dọn Dẹp & Tối Ưu Token Toàn Bộ Context (`chore(agent)`)
- Chuyển ngữ `GEMINI.md` (root và sub-directories) sang English.
- Chuyển ngữ `AGENTS.md` sang English.
- Chuyển ngữ thân 8 rules trong `.agents/rules/*.md` sang English, đồng thời bổ sung **Bilingual Trigger Anchors** vào trường `description:` của 5 rule `model_decision`.
- Chuyển ngữ các file `SKILL.md` và `references/` trong `.agents/skills/` sang English.
- Chạy kiểm thử xác nhận 50/50 test cases, thực hiện micro-commit và push.

### Nhiệm Vụ 2: Triển Khai Tiểu Bước 1.1.2 — Template Registry & Inventory
Sau khi ngữ cảnh đã được tinh gọn và tiết kiệm token tối đa, tiếp tục triển khai Phase 1.1.2:
| Thành Phần Cần Xây Dựng | Vị Trí File | Yêu Cầu Kỹ Thuật |
|---|---|---|
| **Template Manifest Schema** | `doctools/core/docx/manifest.py` | Pydantic model cho Manifest: metadata, biến khai báo, kiểu dữ liệu, danh sách đoạn văn bản bất biến (`immutable_hashes`), layout constraints. |
| **Template Registry** | `doctools/core/docx/registry.py` | Đăng ký, tra cứu, liệt kê (`list_templates`), kiểm tra tính hợp lệ của cặp `template.docx` + `manifest.json`. |
| **Operation API** | `doctools/operations/docx/template_ops.py` | Bổ sung hàm nghiệp vụ `register_template()` và `get_template_info()`. |
| **Unit Tests** | `tests/docx/test_template_registry.py` | Kiểm thử đăng ký template hợp lệ, phát hiện manifest lỗi, từ chối template không khớp. |

---

## 5. Prompt Mẫu Để Bắt Đầu Session Chat Mới (Copy & Paste)

Sau khi mở folder `pdf_to_docx_converter` trong cửa sổ mới (`File -> Open Folder...`), bạn chỉ cần copy đoạn prompt dưới đây gửi cho AI:

```markdown
Chào bạn, tôi vừa mở workspace độc lập cho repo `pdf_to_docx_converter`.
Hãy đọc kỹ `HANDOFF.md`, `GEMINI.md`, và `.agents/skills/doctools-delivery/SKILL.md` để nắm toàn bộ hiện trạng.

Chúng ta có 2 nhiệm vụ cần thực hiện tuần tự:
1. **Nhiệm Vụ 1 (Token Optimization & Context Cleanup)**: 
   - Chuyển ngữ toàn bộ `GEMINI.md`, `AGENTS.md`, 8 rules trong `.agents/rules/`, và toàn bộ `skills/` (kèm references) sang English Core.
   - Bổ sung Bilingual Semantic Anchors (tiếng Anh + từ khóa tiếng Việt thông dụng) vào trường `description:` của Rules và Skills để đảm bảo khi tôi chat bằng Tiếng Việt thì AI vẫn trigger chuẩn xác 100%.
   - Chạy test suite (50/50 pass), tạo micro-commit và push lên `feat/phase-1-docx`.
2. **Nhiệm Vụ 2**: Bắt đầu triển khai **Tiểu bước 1.1.2 — Template Registry & Manifest Schema**.

Hãy xác nhận bạn đã hiểu rõ kế hoạch và bắt đầu thực hiện Nhiệm Vụ 1!
```
