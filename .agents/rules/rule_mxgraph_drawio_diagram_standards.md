---
description: Universal standards for Draw.io (mxGraphModel) diagram engineering, pure native XML generation, orthogonal perimeter routing, and zero-collision topology.
---

# Quy Chuẩn Kỹ Thuật Sơ Đồ Draw.io & mxGraphModel (Draw.io Diagram Standards)

> **Mục tiêu**: Đảm bảo toàn bộ sơ đồ Draw.io sinh ra luôn mở/import thành công 100%, không bị Draw.io ghi đè toạ độ thủ công, không bị cắt cụt XML, các đường nối vuông góc rõ ràng và cấu trúc bảng chuẩn mực.

---

## 1. Các Bất Biến Kỹ Thuật Cốt Lõi (Core Invariants)

| Mã Bất Biến | Tên Bất Biến | Mô Tả & Quy Tắc Kỹ Thuật |
|---|---|---|
| `MX_INV_01` | **Pure Native Hierarchy** | **Tuyệt đối CẤM** bọc sơ đồ trong `<UserObject mermaidData="..." plantUmlData="...">`. Khi tồn tại thuộc tính này, Draw.io sẽ kích hoạt plugin nội bộ biên dịch lại mã nguồn khi người dùng bấm **Apply**, tự động chạy Dagre layout và xóa sạch tọa độ thủ công. Toàn bộ bảng và đường nối bắt buộc là `<mxCell>` trực tiếp dưới `<root><mxCell id="1" parent="0"/>`. |
| `MX_INV_02` | **Minimalist & Well-Formed XML** | Loại bỏ toàn bộ thuộc tính thừa/rác (`mermaidBaseStyle`, `mermaidId`, `alternateBounds`, `groupPadding`, `lockedGroup`) để dung lượng file tối ưu (< 300KB). Mọi file xuất ra bắt buộc phải có đầy đủ các thẻ đóng `</mxCell>`, `</root>`, và `</mxGraphModel>` ở cuối file để ngăn ngừa lỗi sập cú pháp khi copy-paste qua clipboard trình duyệt. |
| `MX_INV_03` | **Container-Level Docking** | Các đường nối (Edges) chỉ được gắn `source` và `target` vào **ID của container bảng** (`table_<NAME>`), **tuyệt đối KHÔNG** gắn vào các cell con bên trong (`tableRow` hoặc `partialRectangle`). Gắn vào cell con sẽ khiến đường nối đâm xuyên qua tiêu đề hoặc thân bảng gây rối mắt. |
| `MX_INV_04` | **Orthogonal Perimeter Routing** | Đường nối phải dùng định tuyến vuông góc 90°: `edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;`. Bắt buộc khai báo cổng chu vi đối diện (`exitX`, `exitY`, `entryX`, `entryY`) ở các mép ngoài chuẩn: Top `(0.5, 0.0)`, Bottom `(0.5, 1.0)`, Left `(0.0, 0.5)`, Right `(1.0, 0.5)` để mũi tên xuất phát và tiếp đất dứt khoát từ mép ngoài. |
| `MX_INV_05` | **Dynamic Geometry & Safety Corridors** | Chiều cao của mỗi bảng phải được tính toán động theo số lượng trường: $H = 43 \times (N_{\text{fields}} + 1)$ với `startSize=43` và mỗi dòng cao 43px. Luôn duy trì hành lang giao thông an toàn $\ge 60$px giữa 2 bảng liền kề để các đường nối có không gian chạy song song mà không đè lên nhau. |
| `MX_INV_06` | **Dual Delivery / Target Packaging** | Xuất theo đúng định dạng đích người dùng yêu cầu: file `.drawio` độc lập hoặc `.xml` độc lập, tránh tạo file rác trùng lặp nếu người dùng yêu cầu 1 định dạng duy nhất. |
| `MX_INV_07` | **Monochrome Academic Line-Art** | Mọi sơ đồ học thuật & kỹ thuật (Block, Wiring, Schematic, DFD) phải ưu tiên phong cách Monochrome: `fillColor=#ffffff;strokeColor=#000000;fontColor=#000000;strokeWidth=1.5;`. Các thành phần optional dùng nét đứt xám (`dashed=1;strokeColor=#888888;fontColor=#555555;`). |
| `MX_INV_08` | **Collision-Free Edge Labels & Masks** | Text nhãn trên đường line bắt buộc có `labelBackgroundColor=#ffffff;labelBorderColor=none;` để chống bị đường line gạch ngang qua chữ; định tuyến đi trên hành lang thoáng $\ge 40$px chống đè lên object khác. |
| `MX_INV_09` | **Multi-Page Single-File Capability** | Khi bàn giao trọn bộ nhiều sơ đồ liên quan trong một phân hệ, hỗ trợ đóng gói thành 1 file `.drawio` duy nhất chứa nhiều thẻ `<diagram name="...">` để quản lý tập trung. |
| `MX_INV_10` | **Schematic Clean Direct Tapping & Zero Redundant Rail Labels** | Trong Electrical Schematic: Dây nguồn (+12V Đỏ `#DC2626`, +5V Cam `#D97706`, +3V3 Xanh `#2563EB`, GND Đen `#000000`) đi trực tiếp từ rail vào đỉnh/đáy linh kiện. KHÔNG gắn ô text thừa trên dây nguồn (màu dây và rail header đã tự định danh). Tín hiệu logic từ MCU sang IC phải đi ngang thẳng hàng, cụm pull-up nằm sát bên phải IC tương ứng. |
| `MX_INV_11` | **Fractional Perimeter Port Anchoring** | Khi nối từ 1 Hub trung tâm (MCU/Gateway) ra nhiều linh kiện vệ tinh cùng cột, dùng toạ độ vi phân chu vi (`exitY = 0.05..1.0`) tương ứng với $y_{\text{center}}$ của linh kiện đích để tạo các đường ngang song song 100% (Zero-Zigzag). |
| `MX_INV_12` | **Discrete Parallel Highway Corridors & HTML Wrap** | Các đường bus song song phải đi qua các trục toạ độ rời rạc cách nhau $\ge 30\text{px}$–$50\text{px}$. Nhãn giao thức/tín hiệu dài bắt buộc bọc `<div>...</div>` để text vuông vắn, chống tràn chiều ngang. |
| `MX_INV_13` | **Schematic Horizontal Strip & Multi-Rail Direct Taps** | Trong Electrical Schematic: Bố trí các IC/Module chính theo dải ngang 1 hàng (L-to-R), Rails nguồn trải ngang trên đỉnh ($y \le 100$), Rail GND dưới đáy ($y \ge 700$), cắm thẳng đứng vào linh kiện (Direct Vertical Drop). Tín hiệu GPIO đi qua các bus tầng dưới. Triệt tiêu 100% nhãn text thừa trên dây nguồn. |
| `MX_INV_14` | **DFD 5-Column Orthogonal Flow & Label Offsets** | Sơ đồ luồng dữ liệu (DFD) tuân thủ kiến trúc 5 cột ($C_1$ External $\rightarrow$ $C_2$ Ingestion $\rightarrow$ $C_3$ Processing/Store $\rightarrow$ $C_4$ Communication $\rightarrow$ $C_5$ Cloud). Nhãn trên đường truyền dùng `connectable="0"` kèm `offset` và mask trắng chống đè chữ. |
| `MX_INV_15` | **Dynamic Edge Label Width (Zero Hardcoded Linebreaks)** | CẤM chèn ký tự ngắt dòng thủ công (`\n`, `&#10;`, `<br>`) vào nhãn của đường nối (Edge). Bắt buộc gán `labelWidth=<width>;html=1;whiteSpace=wrap;labelBackgroundColor=#FFFFFF;labelBorderColor=none;` để Draw.io tự động xuống hàng thông minh và co giãn theo kích thước hành lang. |
| `MX_INV_16` | **4-Tier Stroke Weight Contrast Hierarchy** | Bắt buộc áp dụng 4 cấp độ đậm nhạt viền để tạo độ sâu thị giác (Visual Depth): Tier 1 (Khung cụm lớn / Rail nguồn chính: `strokeWidth=2.5`..`3.0`), Tier 2 (Khối vi xử lý trung tâm / IC chính: `strokeWidth=1.8`..`2.0`, nền `#F8F9FA`), Tier 3 (Nút linh kiện ngoại vi / Bảng lưu trữ: `strokeWidth=1.2`), Tier 4 (Đường dây tín hiệu & bus liên kết: `strokeWidth=1.0`). |
| `MX_INV_17` | **Dedicated Rail Header Legend & Clean Bus Tapping** | Trong sơ đồ Schematic nhiều rail nguồn, text tên rail bắt buộc tách thành cột Header/Badge riêng ở cánh trái ($x < x_{\text{first\_ic}}$). Thân các thanh rail trải dài ($x \ge 290$) phải để `value=""` (thanh màu trơn) để các đường dây nguồn cắm thẳng đứng **TUYỆT ĐỐI KHÔNG cắt ngang qua chữ**. |
| `MX_INV_18` | **MCU Egress Waterfall & Zero Component Piercing** | Tuyến bus GPIO từ MCU trung tâm (ESP32) **NGHIÊM CẤM đâm xuyên qua hộp linh kiện phụ** (`S_ESP` LDO / tụ lọc). Bắt buộc xuất phát từ mép phải (`exitX=1.0`), đi vào hành lang dọc riêng ($\ge 80\text{px}$) giữa MCU và IC kế tiếp, rồi đổ bậc thang (waterfall) xuống các tầng bus $y \ge 475$. |
| `MX_INV_19` | **Complete 4-Sided Data Store Enclosure** | Các đối tượng Kho Dữ Liệu (D1, D2) trong DFD bắt buộc có đủ 4 cạnh viền (`top=1;bottom=1;left=1;right=1;` hoặc `shape=rectangle;`) để tránh bị mất viền 2 bên trái/phải trên giao diện Draw.io. |
| `MX_INV_20` | **Dynamic Proportional Label Width & Snug Mask Bounding** | CẤM gán cứng `labelWidth` lớn cho nhãn ngắn. `labelWidth` phải tính động theo độ dài text: $W = \text{clamp}(W_{\text{min}}, N_{\text{chars}} \times 6.1\text{px} + 8\text{px}, W_{\text{max\_corridor}})$ để lớp mask trắng `labelBackgroundColor=#FFFFFF;` ôm khít chữ, **TUYỆT ĐỐI KHÔNG sinh khoảng trắng thừa che lấp các dây lân cận**. |
| `MX_INV_21` | **Dynamic Viewport Bounds & Zero-Clipping Rendering** | Khi xuất ảnh PNG chất lượng cao (Full HD / 4K) qua headless browser: Bắt buộc quét toàn bộ tọa độ `<mxGeometry>` và `<mxPoint>` trong file `.drawio` để tính $(\max_X, \max_Y)$ động. CẤM gán cứng kích thước cửa sổ browser (`--window-size`) hoặc dùng `graph.fit()`. Kích thước viewport bắt buộc phải đạt $\text{CSS Width} \ge \max_X + 160\text{px}$ và $\text{CSS Height} \ge \max_Y + 160\text{px}$, kết hợp PIL auto-crop với 25px uniform padding để đảm bảo 100% không bị cắt cụt đồ hoạ. |

---

## 2. Cấu Trúc Khối Bảng Chuẩn (Native 3-Column Table Entity)

Cấu trúc cây XML chuẩn cho 1 bảng Entity kiểu Mermaid trong Draw.io:

```xml
<!-- 1. Container Table -->
<mxCell id="table_MEMBER" value="MEMBER"
  style="shape=table;startSize=43;container=1;collapsible=0;childLayout=tableLayout;fixedRows=1;rowLines=1;fontSize=16;fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;strokeWidth=1;align=center;resizeLast=1;html=1;"
  vertex="1" parent="1">
  <mxGeometry x="100" y="200" width="278" height="215" as="geometry" />
</mxCell>

<!-- 2. Table Row -->
<mxCell id="row_MEMBER_1"
  style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=1;strokeWidth=1;collapsible=0;dropTarget=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;top=0;left=0;right=0;bottom=0;"
  vertex="1" parent="table_MEMBER">
  <mxGeometry y="43" width="278" height="43" as="geometry" />
</mxCell>

<!-- 3. Cells in Row (Type | Name | Key) -->
<mxCell id="cell_MEMBER_1_type" value="int"
  style="shape=partialRectangle;connectable=0;strokeWidth=1;fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;top=1;left=1;bottom=1;right=1;align=left;spacingLeft=8;overflow=hidden;fontSize=16;"
  vertex="1" parent="row_MEMBER_1">
  <mxGeometry width="82" height="43" as="geometry" />
</mxCell>
<mxCell id="cell_MEMBER_1_name" value="MemberID"
  style="shape=partialRectangle;connectable=0;strokeWidth=1;fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;top=1;left=1;bottom=1;right=1;align=left;spacingLeft=8;overflow=hidden;fontSize=16;"
  vertex="1" parent="row_MEMBER_1">
  <mxGeometry x="82" width="153" height="43" as="geometry" />
</mxCell>
<mxCell id="cell_MEMBER_1_key" value="PK"
  style="shape=partialRectangle;connectable=0;strokeWidth=1;fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;top=1;left=1;bottom=1;right=1;align=left;spacingLeft=8;overflow=hidden;fontSize=16;"
  vertex="1" parent="row_MEMBER_1">
  <mxGeometry x="235" width="43" height="43" as="geometry" />
</mxCell>
```

---

## 3. Cấu Trúc Đường Nối Chuẩn (Native Orthogonal Edge)

```xml
<mxCell id="edge_1" edge="1" parent="1" source="table_ACCOUNT" target="table_MEMBER"
  style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=light-dark(#9370DB,#cccccc);strokeWidth=1;startArrow=ERmandOne;startSize=8;endArrow=ERzeroToOne;endSize=8;exitX=0.5;exitY=1.0;exitDx=0;exitDy=0;entryX=0.5;entryY=0.0;entryDx=0;entryDy=0;">
  <mxGeometry relative="1" as="geometry" />
</mxCell>
```

### Các Ký Hiệu Đầu Mũi Tên Quan Hệ (Crow's Foot in Draw.io):
- **1 bắt buộc (Mandatory One)**: `startArrow=ERmandOne` / `endArrow=ERmandOne`
- **0 hoặc 1 (Zero or One)**: `startArrow=ERzeroToOne` / `endArrow=ERzeroToOne`
- **1 hoặc nhiều (Mandatory Many)**: `startArrow=ERoneToMany` / `endArrow=ERoneToMany`
- **0 hoặc nhiều (Zero or Many)**: `startArrow=ERzeroToMany` / `endArrow=ERzeroToMany`

---

## 4. Chiến Lược Bố Cục (2D Radial Topology Strategy)

Khi sắp xếp sơ đồ phức tạp (nhiều hơn 15 bảng):
1. **Xác định Thực Thể Trung Tâm (Core Hub)**: Đặt bảng đóng vai trò giao dịch trọng yếu nhất (ví dụ: `PRODUCT`, `ORDER`, `INVOICE`) ở vùng trung tâm sơ đồ.
2. **Quy hoạch Hướng Theo Phân Hệ (Hub-and-Spoke)**:
   - **Bắc (North)**: Cấu trúc phân cấp kho / vật lý (`FLOOR -> ZONE -> AISLE -> SHELF -> SLOT`).
   - **Tây (West)**: Khách hàng, tài khoản và thanh toán (`ACCOUNT -> MEMBER -> INVOICE`).
   - **Nam (South)**: Công thức, đề xuất hoặc phân loại phụ trợ.
   - **Đông (East)**: Tự động hóa, robot, bản đồ định vị hoặc log hệ thống.
3. **Triệt Tiêu Đường Chéo**: Bố trí các bảng có liên kết trực tiếp nằm trên cùng một trục X hoặc Y để đường nối là một đường thẳng vuông góc dứt khoát, không cắt ngang qua các cụm phân hệ khác.

---

## 5. Quy Trình Kiểm Tra Bắt Buộc (The 4-Gate Diagnostic)

Trước khi chuyển giao file cho người dùng, bắt buộc chạy kiểm thử xác nhận:
1. **Cổng 1 (Well-formed XML)**: `xml.etree.ElementTree.parse()` thành công, kiểm tra đủ thẻ đóng.
2. **Cổng 2 (Unique IDs & Valid Parents)**: Không có trùng lặp ID; mọi cell con trỏ đúng ID cha tồn tại.
3. **Cổng 3 (AABB Collision-Free)**: Khoảng cách giữa 2 hộp bảng bất kỳ $\ge 8$px (khuyến nghị $\ge 50$px).
4. **Cổng 4 (Edge Integrity)**: Không có edge bị cô lập (dangling), `source` và `target` đều tồn tại và bắt đầu bằng `table_`.
