# Reference: Diagnostics Triage & Issue Classification

## 1. Cấu Trúc Issue Chuẩn
Mọi chẩn đoán từ các engine (DOCX, XLSX, DIAGRAM, INFRA) đều trả về qua `Diagnostics` gồm `errors`, `warnings`, `info`:
- `code`: Định danh chuẩn (`E-...`, `W-...`, `I-...`).
- `severity`: `error` (chặn phát hành), `warning` (chấp nhận có điều kiện), `info` (quan sát).
- `fixable_by`: `engine`, `ai`, hoặc `human`.
- `suggested_action`: Hành động khuyến nghị.
- `evidence`: Dữ liệu đo đạc kỹ thuật.

## 2. Quy Tắc Xử Lý Lỗi (Fail-Fast Rule)
- Khi có `errors`:
  - `fixable_by="ai"`: Tối đa 2 lần thử sửa cho AI. Nếu lần 2 vẫn không hết lỗi $\rightarrow$ DỪNG LẠI và báo cáo chi tiết.
  - `fixable_by="human"`: Không tự ý sửa; in rõ nguyên nhân và yêu cầu người dùng can thiệp.
  - `fixable_by="engine"`: Chạy lại công cụ sửa tự động (ví dụ `docx.normalize_template`).

## 3. Cảnh Báo Lệch Mẫu (`W-DEV-*`)
- Khi gặp cảnh báo `W-DEV-*` (lệch thiết kế mẫu Excel hoặc Word):
  - Agent KHÔNG tự tiện áp dụng thay đổi làm sai lệch mẫu.
  - Bắt buộc dừng lại, giải thích sự khác biệt và hỏi ý kiến người dùng qua `/grill-me`.
