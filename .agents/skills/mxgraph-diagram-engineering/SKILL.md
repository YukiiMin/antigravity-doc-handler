---
name: mxgraph-diagram-engineering
description: Comprehensive workflow and toolchain for generating, laying out, routing, validating, and repairing Draw.io (mxGraphModel) diagrams and ERDs using pure native XML.
---

# Skill: mxGraphModel & Draw.io Diagram Engineering

> **Mục tiêu**: Chuẩn hóa quy trình tạo, sửa đổi và kiểm tra sơ đồ trên Draw.io (`mxGraphModel`). Ngăn chặn 100% lỗi từ chối Apply, đè tọa độ, cắt cụt XML và dây nối đâm xuyên thân bảng.  
> **Quy tắc liên quan**: Đọc [`.agents/rules/rule_mxgraph_drawio_diagram_standards.md`](file:///d:/Minh/For_myself/ZSCORT_GSU26_SAP05/.agents/rules/rule_mxgraph_drawio_diagram_standards.md) trước khi triển khai.

---

## 1. Khi Nào Kích Hoạt Skill Này?
- Khi cần sinh file `.drawio` hoặc `.xml` cho Draw.io từ mô tả thực thể (Mermaid, PlantUML, JSON spec).
- Khi người dùng gặp lỗi *"Bấm Apply không ăn"*, sơ đồ bị reset tọa độ, hoặc Draw.io báo lỗi cú pháp ngầm.
- Khi cần đi lại đường dây (Orthogonal Routing) cho sơ đồ Draw.io phức tạp (>= 15 bảng).
- Khi kiểm tra tính hợp lệ của sơ đồ Draw.io trước khi bàn giao.

---

## 2. Các Bất Biến Bắt Buộc (Critical Invariants Quickref)

| Invariant | Quy Định Cốt Lõi |
|---|---|
| **MX_INV_01** | **Pure Native Hierarchy**: Cấm thẻ `<UserObject mermaidData/plantUmlData>`. Tất cả table và edge phải là `<mxCell>` trực tiếp dưới `parent="1"`. |
| **MX_INV_02** | **Minimalist & Well-Formed XML**: Loại bỏ thuộc tính rác (`mermaidBaseStyle`, `mermaidId`, `alternateBounds`). File < 300KB, đủ 100% thẻ đóng. |
| **MX_INV_03** | **Container-Level Docking**: Edge chỉ nối từ `table_X` sang `table_Y`, cấm nối vào cell con (`tableRow`/`partialRectangle`). |
| **MX_INV_04** | **Orthogonal Perimeter Routing**: `edgeStyle=orthogonalEdgeStyle;` kèm cổng viền đối diện (`exitX, exitY, entryX, entryY` chuẩn 0.0, 0.5, 1.0). |
| **MX_INV_05** | **Dynamic Geometry Scaling**: Chiều cao $H = 43 \times (N_{\text{fields}} + 1)$, hành lang giao thông giữa các bảng $\ge 60$px. |
| **MX_INV_06** | **Dual Delivery**: Xuất định dạng đích người dùng yêu cầu (.drawio hoặc .xml độc lập, tránh tạo file rác trùng lặp). |
| **MX_INV_07** | **Monochrome Academic Line-Art**: Sơ đồ kỹ thuật ưu tiên Monochrome: `#ffffff` fill, `#000000` text/viền, nét đứt `#888888` cho optional. |
| **MX_INV_08** | **Collision-Free Labels & Masks**: Text nhãn trên line có `labelBackgroundColor=#ffffff;` chống đè chữ; hành lang chạy line $\ge 40$px. |
| **MX_INV_09** | **Multi-Page Single-File Capability**: Hỗ trợ đóng gói đa sơ đồ trong 1 file `.drawio` duy nhất với nhiều tab `<diagram name="...">`. |
| **MX_INV_10** | **Schematic Direct Taps & No Text Clutter**: Dây nguồn màu (+12V Red, +5V Orange, +3V3 Blue, GND Black) đi thẳng từ rail vào IC/MCU. Không gắn ô text thừa trên dây nguồn. |
| **MX_INV_11** | **Fractional Perimeter Port Anchoring**: Nối Hub sang vệ tinh dùng toạ độ vi phân chu vi (`exitY = 0.05..1.0`) khớp $y_{\text{center}}$ đích để tạo đường ngang phẳng 100% (Zero-Zigzag). |
| **MX_INV_12** | **Discrete Highway Corridors & HTML Wrap**: Bus song song đi qua các trục toạ độ rời rạc cách $\ge 30$–$50$px. Nhãn dài bọc `<div>...</div>` vuông vắn chống tràn. |
| **MX_INV_13** | **Schematic Horizontal Strip & Multi-Rail Direct Taps**: Schematic: Module chính xếp dải ngang 1 hàng (L-to-R), Rails nguồn trên đỉnh, GND dưới đáy cắm thẳng đứng. GPIO đi qua bus tầng dưới. |
| **MX_INV_14** | **DFD 5-Column Orthogonal Flow & Label Offsets**: DFD tuân thủ 5 cột ($C_1$ External $\rightarrow$ $C_2$ Ingestion $\rightarrow$ $C_3$ Processing/Store $\rightarrow$ $C_4$ Comm $\rightarrow$ $C_5$ Cloud). Nhãn dùng `connectable="0"` + `offset` mask trắng. |
| **MX_INV_15** | **Dynamic Edge Label Width**: Cấm `\n`/`<br>` trong label; bắt buộc `labelWidth=<W>;html=1;whiteSpace=wrap;labelBackgroundColor=#FFFFFF;` để Draw.io auto-wrap theo hành lang. |
| **MX_INV_16** | **4-Tier Stroke Depth Hierarchy**: Tier 1 (Khung lớn/Rail: 2.5–3.0px) > Tier 2 (MCU/IC: 1.8–2.0px, `#F8F9FA`) > Tier 3 (Ngoại vi: 1.2px) > Tier 4 (Line dây: 1.0px). |
| **MX_INV_17** | **Dedicated Rail Header Legend & Clean Bus Tapping**: Tách text tên rail sang cột Header riêng ($x < x_{\text{first\_ic}}$), thân rail để `value=""` chống đè chữ khi cắm dây nguồn. |
| **MX_INV_18** | **MCU Egress Waterfall & Zero Component Piercing**: Dây GPIO từ MCU xuất phát từ mép phải (`exitX=1.0`), đi vào hành lang riêng ($\ge 80\text{px}$) rồi đổ waterfall xuống bus $y \ge 475$, không cắt qua sub-box. |
| **MX_INV_19** | **Complete 4-Sided Data Store Enclosure**: Đối tượng Kho Dữ Liệu (D1, D2) trong DFD bắt buộc có đủ 4 cạnh viền (`top=1;bottom=1;left=1;right=1;`) chống mất viền trái/phải. |
| **MX_INV_20** | **Dynamic Proportional Label Width & Snug Mask Bounding**: `labelWidth` tính động theo độ dài text và font metrics, đảm bảo mask trắng `labelBackgroundColor` ôm khít chữ, không sinh khoảng trắng thừa che lấp dây lân cận. |
| **MX_INV_21** | **Dynamic Viewport Bounds & Zero-Clipping Rendering**: Headless render ảnh PNG phải quét `<mxGeometry>` tính $(\max_X, \max_Y)$ động. Kích thước viewport $\ge \max + 160\text{px}$, PIL auto-crop 25px uniform padding chống cắt cụt đồ hoạ. |

---

## 3. Cấu Trúc Khối Bảng Native Chuẩn (Template Code)

### A. Thẻ Gốc & Lớp Cơ Bản:
```xml
<mxGraphModel dx="2060" dy="1124" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="850" pageHeight="1100" math="0" shadow="0">
  <root>
    <mxCell id="0" />
    <mxCell id="1" parent="0" />
    <!-- Danh sách tables và edges tại đây -->
  </root>
</mxGraphModel>
```

### B. Bảng 3 Cột (Type | Field Name | Key):
```xml
<!-- Container Bảng -->
<mxCell id="table_USER" value="USER"
  style="shape=table;startSize=43;container=1;collapsible=0;childLayout=tableLayout;fixedRows=1;rowLines=1;fontSize=16;fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;strokeWidth=1;align=center;resizeLast=1;html=1;"
  vertex="1" parent="1">
  <mxGeometry x="100" y="200" width="278" height="129" as="geometry" />
</mxCell>

<!-- Hàng 1 (Row) -->
<mxCell id="row_USER_1"
  style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=1;strokeWidth=1;collapsible=0;dropTarget=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;top=0;left=0;right=0;bottom=0;"
  vertex="1" parent="table_USER">
  <mxGeometry y="43" width="278" height="43" as="geometry" />
</mxCell>

<!-- 3 Cột của Hàng 1 -->
<mxCell id="row_USER_1_c1" value="int"
  style="shape=partialRectangle;connectable=0;strokeWidth=1;fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;top=1;left=1;bottom=1;right=1;align=left;spacingLeft=8;overflow=hidden;fontSize=16;"
  vertex="1" parent="row_USER_1">
  <mxGeometry width="82" height="43" as="geometry" />
</mxCell>
<mxCell id="row_USER_1_c2" value="UserID"
  style="shape=partialRectangle;connectable=0;strokeWidth=1;fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;top=1;left=1;bottom=1;right=1;align=left;spacingLeft=8;overflow=hidden;fontSize=16;"
  vertex="1" parent="row_USER_1">
  <mxGeometry x="82" width="153" height="43" as="geometry" />
</mxCell>
<mxCell id="row_USER_1_c3" value="PK"
  style="shape=partialRectangle;connectable=0;strokeWidth=1;fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;top=1;left=1;bottom=1;right=1;align=left;spacingLeft=8;overflow=hidden;fontSize=16;"
  vertex="1" parent="row_USER_1">
  <mxGeometry x="235" width="43" height="43" as="geometry" />
</mxCell>
```

---

## 4. Bảng Tra Cứu Cổng Docking & Đầu Mũi Tên Crow's Foot

### Vector Cổng Chu Vi (Border Ports):
- **North (Đỉnh)**: `exitX=0.5; exitY=0.0;`
- **South (Đáy)**: `exitX=0.5; exitY=1.0;`
- **West (Trái)**: `exitX=0.0; exitY=0.5;`
- **East (Phải)**: `exitX=1.0; exitY=0.5;`

### Ký Hiệu Đầu Mũi Tên Quan Hệ (Crow's Foot):
```
Mandatory 1  (||)  -> startArrow=ERmandOne; endArrow=ERmandOne;
Zero or 1    (o|)  -> startArrow=ERzeroToOne; endArrow=ERzeroToOne;
Zero or Many (o{)  -> startArrow=ERzeroToMany; endArrow=ERzeroToMany;
One or Many  (|{)  -> startArrow=ERoneToMany; endArrow=ERoneToMany;
```

---

## 5. Quy Trình Vận Hành 3 Bước

### Bước 1 — Chuẩn Bị Dữ Liệu & Quy Hoạch Topology
Xác định thực thể trung tâm (Hub Entity) và phân cụm vệ tinh theo 4 hướng la bàn (North, South, East, West).

### Bước 2 — Sinh XML Thuần Bằng Script
Sử dụng engine tái sử dụng:
```bash
python .agents/skills/mxgraph-diagram-engineering/scripts/build_drawio.py --input <DATA_FILE> --output <OUT_FILE>
```

### Bước 3 — Chạy Kiểm Tra 4 Cổng (4-Gate QA)
Bắt buộc chạy trước khi bàn giao:
```bash
python .agents/skills/mxgraph-diagram-engineering/scripts/validate_drawio.py --file <OUT_FILE>
```
Đạt Exit code 0 mới xem là hoàn thành.
