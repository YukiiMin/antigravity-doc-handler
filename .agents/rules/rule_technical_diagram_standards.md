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
1. **Tên Thực thể, Hộp Màn hình & Phụ trợ — 100% Tiếng Anh Chuẩn Quốc Tế**:
   - Toàn bộ nhãn bên trong hình hộp node (Screen/Service/Module) bắt buộc là tiếng Anh kỹ thuật (ví dụ: `Login Screen`, `Register Screen`, `Home Dashboard`, `Cart Screen`, `Product Detail Screen`, `Navigation Map 2D`).
   - Quy tắc 100% tiếng Anh áp dụng cho TẤT CẢ các thực thể phụ trợ:
     - Group / Cluster titles (ví dụ: `Authentication Flow`, `Main Operations`, `Warehouse Staff Area`).
     - Container boxes, Subtitles, Badges & Role tags (ví dụ: `[Authorized Staff Only]`, `Route: /login`).
   - Tuyệt đối không đặt tiếng Việt hoặc nhãn song ngữ dài dòng (`Đăng nhập (Login Screen)`) bên trong hộp màn hình.

2. **Quy tắc Nhận diện Dự án Đa ngữ (i18n) vs Đơn ngữ (Codebase Heuristic)**:
   - Trước khi vẽ sơ đồ, AI Antigravity quét tài nguyên codebase:
     - **Android**: Kiểm tra `res/values-*/strings.xml` (xem có cả `values-vi` và `values-en` hoặc nhiều locale).
     - **Web/FE (React/Vue/Next/Angular)**: Kiểm tra thư mục `locales/`, `messages/`, file `i18n.ts/js`, các cặp file `en.json`/`vi.json`.
     - **Flutter/Cross-platform**: Kiểm tra thư mục `l10n/` hoặc `arb` files.
   - **Nếu có cấu hình i18n (>= 2 ngôn ngữ)**: Sơ đồ tự động kích hoạt **Mode Đa ngữ** -> 100% nhãn mũi tên và hành động dùng tiếng Anh.
   - **Nếu chỉ có 1 bộ resource ngôn ngữ bản địa**: Kích hoạt **Mode Đơn ngữ Bản địa** -> Áp dụng quy tắc ghép động từ tiếng Anh + text nút gốc.

3. **Quy tắc Ghép Nhãn Nút Hành động trên Mũi tên (Action Button on Arrows)**:
   - **Mode Đa ngữ (i18n)**: Mặc định 100% tiếng Anh (`Tap "Login"`, `Click "View Cart"`, `Select "Settings"`).
   - **Mode Đơn ngữ Bản địa**: Động từ thao tác tiếng Anh + Nhãn nút UI gốc trong ngoặc kép trích xuất chính xác từ codebase:
     - Ví dụ: `Click "Đăng nhập"`, `Tap "Xem lộ trình\n& Chỉ đường"`, `Click "Đăng xuất"`.
   - **Tương tác KHÔNG CÓ nút bấm rõ ràng (Non-button / Gesture / System Events)**:
     - Dùng 100% tiếng Anh kỹ thuật, KHÔNG dùng ngoặc kép:
     - Chạm thẻ: `Tap Item Card`, `Tap Recommendation Banner`.
     - Cử chỉ: `Swipe Down to Refresh`, `Swipe Right to Delete`.
     - Sự kiện hệ thống: `Auto Redirect (3s)`, `Session Expired`.
     - Phần cứng / Quét: `Press System Back`, `Scan Barcode Success`.

4. **Bộ Động từ Thao tác Tiếng Anh Chuẩn hóa**:
   - `Tap`: Dùng cho giao diện Mobile / Touchscreen.
   - `Click`: Dùng cho giao diện Web / Desktop / Mouse click.
   - `Select`: Dùng cho Tabs, Danh sách, Radio buttons, Dropdown menus.
   - `Scan`: Dùng cho Camera, Barcode, mã QR.
   - `Swipe`: Dùng cho cử chỉ vuốt chạm.
   - `Auto`: Dùng cho chuyển hướng hệ thống tự động theo thời gian hoặc sự kiện nền.

## 3. Ngắt dòng Nhãn Mũi tên & Chống Va chạm (Multi-line & Collision Avoidance)
1. **Chủ động ngắt dòng (`\n`)**:
   - Khi nhãn hành động dài quá 18–22 ký tự, bắt buộc chèn ký tự xuống dòng `\n` tại vị trí khoảng trắng tự nhiên gần nhất để tạo cụm chữ 2–3 dòng gọn gàng trên thân mũi tên.
   - Tuyệt đối không để nhãn chữ 1 dòng quá dài (> 25 ký tự) tràn ngang đè lên các khối hộp màn hình hoặc đường nối lân cận.
2. **Kiểm tra va chạm tự động (AABB Collision Engine)**:
   - Trước khi render xuất bản, chạy kiểm tra va chạm tự động trong engine để phát hiện cảnh báo overlap giữa hộp nhãn và hộp node.
   - Nếu có cảnh báo `[WARN] Label collision detected`, phải điều chỉnh ngay `label_pos`, `label_offset_x`, `label_offset_y` hoặc ngắt dòng lại trong file JSON.

## 4. Độ phân giải In ấn & Tỷ lệ Khung hình (Resolution & Aspect Ratio)
- Khổ giấy A4 Portrait Word (`14.0cm` width): duy trì tỷ lệ khung hình từ `1.6:1` đến `1.85:1`.
- Luôn render ảnh PNG ở `scale=3` (300+ DPI vector grade) để hiển thị sắc nét trong tài liệu kỹ thuật.
