---
description: Cập nhật số liệu trong file Excel của người dùng
---

1. Xác định file nguồn và các vùng không được sửa (hỏi nếu chưa rõ).
2. Chạy `tool:preflight_xlsx`; áp dụng nhánh quyết định trong skill `xlsx-safe-edit`.
3. Chạy `tool:set_cells_xlsx`.
4. Nếu `success = false`, đọc `issues`, xử lý theo `fixable_by`; nếu `success = true`, bàn giao `file_ref.path` và các cảnh báo còn lại.
