# Reference: Cross-Module Pipelines & Hand-off Protocol

## 1. Analytics to Document (`WF-CROSS-01`)
1. XLSX Engine chạy `xlsx.mutate` tiêm dữ liệu vào template $\rightarrow$ `xlsx.recalc` cập nhật công thức $\rightarrow$ xuất `file_ref_xlsx`.
2. Trích xuất bảng tóm tắt số liệu qua `xlsx.inspect`.
3. DOCX Engine chạy `docx.build_document` nhúng bảng tóm tắt vào báo cáo Word (`.docx`).
4. Bàn giao bộ đôi sản phẩm: Báo cáo Word + File Excel công thức động 100%.

## 2. Visual Diagram to Document (`WF-CROSS-02`)
1. DIAGRAM Engine chạy `diagram.build` sinh file `.drawio` $\rightarrow$ `diagram.render` xuất ảnh PNG/SVG chuẩn $\ge 300\text{ DPI}$.
2. DOCX Engine nhúng ảnh vào khối `image` trong Word, tự động co giãn trong vùng in $\le 15.92\text{ cm}$.
3. XLSX Engine nhúng ảnh vào Sheet Cover theo Two-Cell Anchor.

## 3. Quản Lý File & Bảo Mật (`WF-CROSS-03`)
- **Giao tiếp qua FileRef mờ**: `resource://<engine>/files/<id>` kèm SHA-256. Không truyền base64 nội tuyến.
- **TTL 24h & Cleanup**: `FileStore` tự động thu dọn file quá hạn và dọn zombie locks (`.~lock.*`, `~$*`).
- **Sandbox Isolation**: Các tiến trình xử lý nặng (Jinja render, LibreOffice, headless Chromium) chạy trong tiến trình cô lập, timeout $\le 60\text{s}$, RAM $\le 2\text{GB}$.
