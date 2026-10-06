---
name: xlsx-safe-edit
description: Sửa nội dung file Excel có sẵn mà không làm mất định dạng/thành phần. Dùng khi người dùng đưa file .xlsx và yêu cầu cập nhật số liệu hoặc văn bản.
---

# Sửa file Excel an toàn

## Khi nào dùng
Người dùng đưa file .xlsx có sẵn và muốn thay đổi giá trị ô. Không dùng để tạo workbook mới từ đầu.

## Quy trình quyết định
1. Gọi `tool:preflight_xlsx`.
   - `fidelity_tier = REJECT` -> dừng, báo người dùng (macro hoặc liên kết ngoài).
   - `fidelity_tier = T2` -> **hỏi người dùng** có chấp nhận rủi ro mất hình khối/phần mở rộng không.
   - `T1` -> tiếp tục.
2. Gọi `tool:set_cells_xlsx` với `updates` rõ ràng; truyền `locked_zones` nếu người dùng nêu vùng không được đụng.
3. Đọc `issues` trong kết quả:
   - `fixable_by = ai` -> sửa đầu vào theo `suggested_action`, gọi lại (tối đa 2 lần).
   - `fixable_by = human` -> hỏi người dùng, không tự quyết.
4. Muốn đối chiếu thêm hoặc kiểm tra file do bên khác sửa: `tool:diff_inventory_xlsx`.

## Bàn giao
Nêu rõ nếu có `W-CALC-NO-CACHE`: giá trị công thức sẽ hiện khi mở bằng Excel.
