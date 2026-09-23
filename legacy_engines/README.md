# Legacy Diagram Engines (v1.0 — Deprecated)

> **CẢNH BÁO QUAN TRỌNG**: Thư mục này chứa toàn bộ các engine vẽ diagram phiên bản cũ (v1.0).
> Kể từ phiên bản v2.0, hệ thống đã chuyển dịch toàn bộ sang **`mxgraph_engine.py`** dựa trên nền tảng **mxGraphModel XML** và **Offline HTML5 Canvas HD Runner**.

---

## 1. Danh Sách Các Thành Phần Cũ (Archived Components)

| Thành phần | Công nghệ v1.0 | Lý do đóng băng / Chuyển dịch |
|---|---|---|
| `mermaid_renderer.py` | Mermaid CLI (`mmdc`), Node.js, Puppeteer | Nặng nề (~300MB Node deps), tự động layout ngẫu nhiên gây xoắn dây/chồng lấn, không xuất được file thiết kế mở để người dùng chỉnh sửa. |
| `mermaid_themes/` | JSON Theme presets cho `mmdc` | Đi kèm với Mermaid CLI cũ, không tương thích mxGraph. |
| `puppeteer-config.json` | Puppeteer browser sandbox config | Cấu hình sandbox cho `mmdc` trên Windows. |
| `spec_diagram_engine.py` | SVG thuần Python + Headless Edge screenshot | Toạ độ thủ công, không có khả năng xuất file chuẩn cho Draw.io Desktop biên tập kéo thả. |
| `diagram_editor.py` | Tkinter Desktop Canvas Editor | Giao diện đồ hoạ Tkinter bị giới hạn kiểu dáng, khó đồng bộ tính năng so với hệ sinh thái Draw.io. |
| `plantuml_renderer.py` | Java runtime + `plantuml.jar` | Yêu cầu cài đặt môi trường Java JRE/JDK, tốc độ khởi động JVM chậm, khó tùy biến style hiện đại. |

---

## 2. Đường Lối Chuyển Dịch Lên v2.0 (`mxgraph_engine.py`)

Trong v2.0, công cụ chuyển sang mô hình **Dual-Core**:
1. **Toạ độ & Định tuyến thông minh**: AI/Heuristic tự động tính toán toạ độ (AABB collision-free), phân cụm, và định tuyến dây vuông góc (orthogonal routing) theo chuẩn `MX_INV_01` -> `MX_INV_06`.
2. **File nguồn mở cho người dùng**: Luôn xuất song song file `.drawio` (hoặc `.xml`) vào `diagram_assets/` để người dùng mở bằng Draw.io Desktop kéo thả chỉnh sửa tùy ý.
3. **Engine Render Offline Canvas Full HD / 4K**: Dùng runner HTML5 offline nhúng thư viện `mxClient` chính thức, render qua browser có sẵn trên Windows (`msedge.exe --headless`) ở scale 2x/3x (300 DPI). Không cần cài đặt Node.js hay Java.

---

## 3. Khả Năng Tương Thích Ngược (Backward Compatibility)

Các file shim mỏng được đặt tại thư mục gốc của `tool/pdf_to_docx_converter/`:
- `mermaid_renderer.py` -> Phát `DeprecationWarning` và gọi ủy quyền vào `legacy_engines.mermaid_renderer`.
- `spec_diagram_engine.py` -> Phát `DeprecationWarning` và gọi ủy quyền vào `legacy_engines.spec_diagram_engine`.
- `plantuml_renderer.py` -> Phát `DeprecationWarning` và gọi ủy quyền vào `legacy_engines.plantuml_renderer`.

*Khuyến nghị*: Hãy cập nhật code gọi sang `mxgraph_engine.py` để đạt hiệu năng và chất lượng hiển thị cao nhất.
