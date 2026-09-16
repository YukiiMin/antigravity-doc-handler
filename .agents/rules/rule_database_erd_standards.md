---
description: Universal standards for Database ERD schemas, high-resolution rendering, orthogonal routing, and column metadata notation.
---

# Quy Chuẩn Thiết Kế Sơ Đồ Cơ Sở Dữ Liệu (Database ERD Standards)

## 1. Độ Phân Giải & Khung Hình (Resolution & Aspect Ratio)
1. **Chuẩn 4K UHD Siêu Nét**:
   - Master ERD hoặc sơ đồ từ 15+ bảng bắt buộc render ở độ phân giải tối thiểu 4K (chiều rộng >= 3840px hoặc DPI >= 300) để đảm bảo không vỡ nét khi zoom in 100%–400%.
2. **Tỷ lệ Khung hình Cân đối (16:9 hoặc 4:3)**:
   - Sắp xếp các Table Object nằm gần nhau, giảm thiểu khoảng trắng thừa (wasted whitespace).
   - Chiều dài không được trải dải băng quá mức so với chiều rộng (ưu tiên tỷ lệ chữ nhật 16:9 hoặc 4:3).

## 2. Kiểu Đường Nối (Orthogonal Routing)
- Ưu tiên tuyệt đối đường nối vuông góc (Orthogonal / Manhattan routing 90°).
- Loại bỏ các đường cong Bezier lượn sóng hoặc xiên chéo gây rối mắt khi nối qua nhiều tầng bảng.

## 3. Ký Hiệu Khóa & Tính Nullable (Key & Nullability Notation)
1. **Primary Key (PK)**: Bắt buộc gắn vector icon chìa khóa (`<&key>` trong PlantUML) ngay cạnh tên trường khóa chính.
2. **Nullability Indicator**:
   - Bắt buộc hiển thị rõ ràng ký hiệu cho từng cột:
     - `●` (`<color:#0F172A>●</color>`): Not Null (Bắt buộc).
     - `○` (`<color:#94A3B8>○</color>`): Nullable (Cho phép null).
3. **Foreign Key (FK)**: Gắn rõ nhãn `<<FK>>` và đường liên kết chỉ thẳng tới bảng cha tương ứng.

## 4. Công cụ Khuyến nghị (Engine Strategy)
- **Master ERD / Sơ đồ Cực đại (>= 15 bảng yêu cầu kiểm soát tọa độ X, Y và Waypoints)**: Bắt buộc dùng **Canvas ERD Engine** (`spec_diagram_engine.py` / `diagram_editor.py`) với file JSON đặc tả chuẩn gồm `nodes` (X, Y, W, H, columns) và `connections` (ports, waypoints, cardinalities) để kiểm soát pixel-perfect bố cục, chống đè dây và che khuất ký hiệu quan hệ.
- **PlantUML ERD**: Sử dụng khi cần tạo nhanh tài liệu kiến trúc, bắt buộc duy trì khoảng thở tối thiểu `nodesep >= 60`, `ranksep >= 70` để tránh đè bẹp ký hiệu crow's foot.
- **Sub-ERD / Phân hệ nhỏ (3–10 bảng)**: Dùng **Mermaid** với `scale: 3` (300 DPI) hoặc **PlantUML**.

## 5. Quy Chuẩn Định Tuyến Đường Nối & Chống Đè Ký Hiệu Quan Hệ (Connection Routing & Clearance)

1. **Kiến Trúc Tách Rời File JSON cho Đường Nối (Modular Connections Spec)**:
   - Với các sơ đồ ERD lớn (≥ 15 bảng), cấu hình đường nối phải được tách thành file riêng (ví dụ: `specs/<name>_connections.json`) và được nạp tự động qua thuộc tính `"connections_file"` trong file master spec.
   - Mỗi đường nối được định nghĩa gồm:
     - `source`, `target`, `source_port`, `target_port` (`top` | `bottom` | `left` | `right`).
     - `cardinality_source`, `cardinality_target` (`one`, `many`, `||`, `o|`, `o{`, `}|`).
     - `waypoints`: Danh sách tọa độ `[[x, y], ...]` để chủ động bẻ đường lách qua khoảng trống, tuyệt đối không cắt xuyên qua các bảng khác.
     - `corner_radius`: Bán kính bo góc mềm mại (8–14px) bằng Quadratic Bezier, loại bỏ cảm giác gãy khúc chữ L thô cứng.

2. **Quy Tắc Đầu Nối Chuẩn Crow's Foot & Bỏ Nhãn Chữ Trong Physical ERD (Crow's Foot & No Verb Labels)**:
   - **Ký hiệu Crow's Foot**: Các nhánh chân quạ bắt buộc phải **xòe mở rộng về phía biên thực thể** (apex nằm trên đường dây, 3 nhánh chạm hoặc tiến sát biên bảng), vòng tròn `O` rỗng nền trắng (`#FFFFFF`) che đường line bên dưới, vạch `|` vuông góc dứt khoát.
   - **Phân biệt rõ ràng Physical ERD vs Conceptual Diagram**:
     - Trong **Physical ERD (Database Schema)**: **Tuyệt đối KHÔNG hiển thị nhãn chữ động từ quan hệ** (`authenticates`, `holds`, `creates`, `purchases`, `configures`, v.v.). Bản chất Physical ERD đã thể hiện trọn vẹn quan hệ thông qua tên trường khóa ngoại `<<FK>>` và ký hiệu Crow's Foot. Các nhãn động từ chỉ thuộc về **Conceptual Diagram (Sơ đồ khái niệm / Nghiệp vụ)**. Việc gắn nhãn động từ vào Physical ERD là dư thừa, gây rối mắt và làm chật chội không gian các đầu nối.
   - **Quy tắc Text Label (Khi có nhãn chữ ở các loại sơ đồ khác như Screen Flow, Conceptual)**:
     - **Chỉ hiển thị thuần chữ (Plain Text), BỎ HẲN hộp màu (No Rect Box Background)**: Tuyệt đối không vẽ thẻ `<rect>` nền màu/trắng kèm viền xám hay đổ bóng che lên đường line vì sẽ đè bẹp các ký hiệu lân cận.
     - Sử dụng viền chữ trắng mỏng bao quanh nét chữ (Text Halo: `paint-order="stroke fill" stroke="#FFFFFF" stroke-width="3.5px"`) để chữ đọc rõ trên nền đường dây mà không tạo khối hộp che khuất ký hiệu.

3. **Cân Bằng Không Gian Layout & Phân Cụm Ẩn (Invisible Conceptual Zoning & Spatial Balance)**:
   - **Ẩn hoàn toàn Background / Viền Zone trên Canvas (`show_clusters: false`, `visible: false`)**:
     - Bố cục và tọa độ các bảng vẫn được thiết kế và quy hoạch nghiêm ngặt theo các cụm phân hệ nghiệp vụ độc lập (tọa độ tập trung, duy trì hành lang giao thông 100–120px giữa các cụm giúp đường nối chạy xuyên suốt mà không cắt ngang qua các bảng).
     - **Tuyệt đối KHÔNG hiển thị khung viền hình chữ nhật, background màu đệm hay tag tiêu đề phân hệ** trên ảnh xuất bản. Điều này giúp sơ đồ đạt độ tinh gọn, trang nhã, hiện đại (clean & minimalist) và không bị rối mắt bởi các khối viền hộp bao quanh.
   - **Khoảng cách tối ưu giữa các bảng**: Duy trì khoảng cách giữa 2 bảng liền kề chuẩn **90–110px**, không để bảng sát rạt (< 80px) gây đè ký hiệu, cũng không để khoảng cách quá xa (> 250px) gây lãng phí không gian.
   - **Tỷ lệ khung hình**: Bố cục các cụm theo ma trận cân đối tỷ lệ chữ nhật 1.6:1 (3840 x 2400 px), triệt tiêu hoàn toàn khoảng trống thừa.

