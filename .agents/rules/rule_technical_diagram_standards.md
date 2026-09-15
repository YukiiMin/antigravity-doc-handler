---
description: Universal standards for technical architecture, mobile screen flows, and declarative diagram generation
---

# Quy chuẩn Thiết kế Sơ đồ Kỹ thuật & Luồng Màn hình (Technical Diagram Standards)

## 1. Tầm quan trọng của Declarative JSON Spec (JSON Spec Supremacy)
Khi thiết kế bất kỳ sơ đồ kỹ thuật, kiến trúc hệ thống hoặc luồng màn hình (Screen Flow):
- **Tuyệt đối KHÔNG vẽ ad-hoc hoặc phụ thuộc vào auto-layout không kiểm soát**: Các thuật toán bố trí tự động (như Dagre trong Mermaid) thường dàn trang quá dài ngang (tỷ lệ 4:1), bóp nghẹt font chữ về kích thước siêu nhỏ (3–4pt) khi chèn vào trang văn bản A4 Word/PDF, đồng thời gây rối dây và chồng chéo ngẫu nhiên giữa các lần render.
- **Declarative JSON Spec là "Source of Truth" duy nhất**:
  1. **Deterministic & Reproducible**: Kiểm soát tuyệt đối vị trí tọa độ ($X, Y, W, H$), cổng kết nối (`top`, `bottom`, `left`, `right`) và đường bẻ góc Manhattan vuông góc 90°. Render 100 lần ra kết quả hoàn hảo như nhau.
  2. **Tách biệt Dữ liệu & Trình diễn (Separation of Concerns)**: File `.json` lưu cấu trúc topology và nội dung. Engine xử lý việc render SVG, áp dụng text halo và xuất ảnh 300+ DPI.
  3. **Version Control & Clean Git Diff**: Mọi thay đổi màn hình, luồng chuyển trang hay nhãn nút đều được diff rõ ràng từng dòng trên Git.
  4. **Kiểm tra va chạm tự động (AABB Collision Engine)**: Engine dùng toán học hình chữ nhật (Axis-Aligned Bounding Box) để phát hiện và cảnh báo trước mọi va chạm giữa nhãn nút và hộp màn hình.

## 2. Ngôn ngữ Chuẩn hóa trong Sơ đồ (Language Conventions)
1. **Tên Object / Screen Box — 100% Tiếng Anh Chuẩn Quốc Tế**:
   - Toàn bộ nhãn bên trong hình hộp node (Screen/Service/Module) bắt buộc là tiếng Anh kỹ thuật (ví dụ: `Login Screen`, `Register Screen`, `Home Dashboard`, `Cart Screen`, `Product Detail Screen`, `Navigation Map 2D`).
   - Tuyệt đối không đặt tiếng Việt hoặc nhãn song ngữ dài dòng (`Đăng nhập (Login Screen)`) bên trong hộp màn hình.
2. **Quy tắc Ghép Nhãn Nút Hành động (Action Button on Arrows)**:
   - Sử dụng động từ thao tác tiếng Anh: `Click`, `Tap`, `Select`.
   - **Dự án đơn ngữ không hỗ trợ đa ngữ** (như `SuperMarketBot-Android` chỉ có tiếng Việt): Đặt nhãn nút UI gốc trong ngoặc kép theo đúng codebase: `Click "Đăng nhập"`, `Click "Xem lộ trình\n& Chỉ đường"`, `Click "Đăng xuất"`, `Tap Recommendation Card`.
   - **Dự án có hỗ trợ đa ngữ (i18n)**: Mặc định 100% toàn bộ nhãn hành động là tiếng Anh (`Click "Login"`).

## 3. Ngắt dòng Nhãn Mũi tên & Chống Va chạm (Multi-line & Collision Avoidance)
1. **Chủ động ngắt dòng (`\n`)**:
   - Khi nhãn hành động dài quá 18–22 ký tự, bắt buộc chèn ký tự xuống dòng `\n` để tạo cụm chữ 2–3 dòng gọn gàng trên thân mũi tên.
   - Tuyệt đối không để nhãn chữ 1 dòng quá dài tràn ngang đè lên các khối hộp màn hình hoặc đường nối lân cận.
2. **Kiểm tra va chạm tự động (AABB Collision Engine)**:
   - Trước khi render xuất bản, chạy kiểm tra va chạm tự động trong engine để phát hiện cảnh báo overlap giữa hộp nhãn và hộp node.
   - Nếu có cảnh báo `[WARN] Label collision detected`, phải điều chỉnh ngay `label_pos`, `label_offset_x`, `label_offset_y` hoặc ngắt dòng lại trong file JSON.

## 4. Độ phân giải In ấn & Tỷ lệ Khung hình (Resolution & Aspect Ratio)
- Khổ giấy A4 Portrait Word (`14.0cm` width): duy trì tỷ lệ khung hình từ `1.6:1` đến `1.85:1`.
- Luôn render ảnh PNG ở `scale=3` (300+ DPI vector grade) để hiển thị sắc nét trong tài liệu kỹ thuật.
