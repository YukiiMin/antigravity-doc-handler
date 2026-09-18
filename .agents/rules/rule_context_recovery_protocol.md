---
description: Mandatory context recovery protocol after conversation truncation (CHECKPOINT signal)
---

# Context Recovery Protocol After Truncation

## 1. CHECKPOINT Detection & Mandatory Recovery Sequence

Khi conversation bắt đầu bằng hoặc chứa `{{ CHECKPOINT N }}` (system-injected truncation summary):

**TRƯỚC KHI** xử lý bất kỳ user request nào, bắt buộc thực hiện theo thứ tự:

1. **Đọc `GEMINI.md`** tại workspace root — critical invariants checklist cho toàn bộ project.
2. **Đọc `.agent_scratchpad.md`** — current goal, completed steps, remaining TODOs.
3. **Không đọc thêm rule files khác** trong recovery sequence (tránh token waste — GEMINI.md đã đủ).
4. Nội tâm confirm: "GEMINI.md đã load, scratchpad đã đọc" → proceed xử lý user request.

**Không được skip bước này dù user đã mô tả task trong message đầu tiên.**

## 2. Mid-Session Rule Self-Check

Khi chuẩn bị viết code mà gặp một trong các pattern sau, **dừng lại và check GEMINI.md trước**:

- Chuẩn bị viết `FOR ALL ENTRIES` với 2 bảng khác nhau (type mismatch risk)
- Chuẩn bị thêm comment giải thích vào ABAP class body
- Chuẩn bị dùng `encodeURIComponent()` trong OData URL
- Chuẩn bị viết `fetchJson().then(function(oData) { if (oData.SomeField)` (array treated as object)
- Chuẩn bị gọi auto-apply sau release TR

## 3. Scratchpad Discipline

- `.agent_scratchpad.md` là **nguồn truth duy nhất** cho task state giữa các session.
- Cập nhật scratchpad **TRƯỚC KHI** kết thúc mỗi response khi task có > 3 steps.
- Khi checkpoint xảy ra, scratchpad là cầu nối duy nhất cho task context còn lại.
- Format bắt buộc:
  ```
  ## Current Goal
  ## Progress / Completed Steps
  ## Key Decisions Made
  ## Remaining TODOs
  ```

## 4. Token Economy During Recovery

- **Không** đọc toàn bộ 17 rule files sau checkpoint — quá tốn token.
- `GEMINI.md` là file duy nhất cần đọc trong recovery. Nó chứa invariants cô đọng từ toàn bộ rules.
- Nếu cần chi tiết về một rule cụ thể → đọc đúng file đó trong `.agents/rules/`.

## 5. Zero-Assumption Context & Clarification Protocol (Session Mới & Template Mới)

Khi tiếp nhận một session mới, một máy mới hoặc một bài toán sinh tài liệu/code với bộ template mới:

### A. Anatomy Inspection (Khảo sát cấu trúc bắt buộc TRƯỚC KHI code)
1. Khảo sát toàn diện Template gốc:
   - Các sheet tổng quan (`Cover`, `Functions`, `Statistics`...) và sheet chi tiết tham chiếu (`Example`, `Template`...).
   - Đếm số dòng mẫu, vị trí hàng Subtotal/Total, các công thức KPI động (`=COUNTIF`, `=SUM`), và tọa độ/chuỗi tham chiếu của Biểu đồ (Charts).
   - Kiểm tra font chữ, cỡ chữ, màu nền, viền và thiết lập Auto-scaling/Wrap text.
2. Khảo sát Dataset đầu vào (Input):
   - Số lượng bản ghi/hàm thực tế, cấu trúc trường dữ liệu, kiểu dữ liệu (raw values vs computed).
   - Nhận diện nguy cơ thay đổi độ cao bảng khiến dòng Subtotal dời vị trí làm gãy công thức chart.

### B. Context Gap Analysis & Clarification Trigger
Nếu phát hiện bất kỳ dấu hiệu nào sau đây:
- Số lượng dòng thực tế khác với template mẫu (ví dụ: template 3 dòng nhưng input 20 dòng).
- File template có biểu đồ hoặc khối thống kê phụ thuộc vào vị trí dòng Subtotal.
- Có sự mơ hồ trong cách phân bổ dữ liệu vào các nhóm (Precondition vs Input parameters vs Condition marks).
- Format file input bị lỗi (bị shrink font size, sai viền, mất merge) so với Template chuẩn.

👉 **BẮT BUỘC DỪNG LẠI (STOP) & HỎI NGƯỜI DÙNG**:
- Liệt kê rõ các điểm khác biệt và đề xuất phương án xử lý cụ thể.
- Sử dụng công cụ `ask_question` hoặc `/grill-me` để chốt 100% phương án trước khi viết code.
- **TUYỆT ĐỐI KHÔNG** tự ý đoán mò, làm rồi sửa nhiều lần gây lãng phí token và thời gian.

