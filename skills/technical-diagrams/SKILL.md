---
name: technical-diagrams
description: Multi-engine technical architecture, ERD, C4, OOP Class, mobile screen flow, and sequence diagrams with 300+ DPI rendering, unified JSON specs, and Word/DOCX auto-injection.
---

# Antigravity Skill: Technical Diagram Engine (`technical-diagrams`)

Use this skill when designing, generating, rendering, or editing publication-grade technical diagrams, database schemas, system architectures, or mobile application screen flows for DEV/BA documentation, SRS reports, and Word/PDF deliverables.

---

## 🌟 Multi-Engine Architecture & Core Principles

The toolkit adopts a **3-Engine Architecture** unified behind a **Single Source of Truth (JSON Spec)**:

```
                  Unified JSON Spec File (.json)
                                │
         ┌──────────────────────┼──────────────────────┐
         ▼                      ▼                      ▼
  "engine": "canvas"     "engine": "mermaid"    "engine": "plantuml"
         │                      │                      │
  spec_diagram_engine     mermaid_renderer       plantuml_renderer
  (Headless Chromium)       (mmdc CLI)          (Java + plantuml.jar)
         │                      │                      │
         └──────────────────────┼──────────────────────┘
                                ▼
                   PNG High-Res (scale=3 / 300+ DPI)
                                │
                                ▼
               docx_writer.py (Unified Auto-Inject Pipeline)
                 - Width: 14.0 cm (A4 Portrait standard)
                 - Max Height: 20.0 cm
                 - Strict keepNext chaining for Headings & Captions
```

### Core Architecture Rules:
1. **JSON là Single Source of Truth**: Mọi sơ đồ đều bắt đầu từ file JSON spec. Trực tiếp lưu trữ, version control, và tái sử dụng.
2. **Field `"engine"` là Dispatcher Key**: Quyết định backend (`"canvas"`, `"mermaid"`, `"plantuml"`).
3. **Đầu ra chuẩn hóa**: Cả 3 engine đều xuất ra PNG chất lượng cao (300+ DPI / scale=3), kích thước tự động co giãn theo tỷ lệ 2D (rộng tối đa 14.0cm, cao tối đa 20.0cm) để vừa vặn hoàn hảo trên trang A4 Word.
4. **Atomic Protection**: Nếu engine biên dịch lỗi, tiến trình dừng ngay lập tức và báo lỗi chi tiết, tuyệt đối KHÔNG can thiệp làm hỏng file Word (`.docx`).

---

## 📊 Bảng Phân Loại 12 Loại Sơ Đồ & Chọn Engine Đúng

| # | Loại Diagram | Người dùng chính | Engine | Cú pháp / Đặc điểm |
|---|---|---|---|---|
| 1 | **Screen Flow (Mobile/Web)** | Dev + BA | `canvas` | Pixel-perfect coordinate, Manhattan routing, kéo thả trên `diagram_editor.py` |
| 2 | **Sequence Diagram** | Dev + BA | `mermaid` | `sequenceDiagram` — API call chain, luồng xác thực |
| 3 | **Flowchart / Business Process** | BA | `mermaid` | `flowchart TD / LR` — Logic nghiệp vụ, rẽ nhánh if/else |
| 4 | **State Diagram** | Dev | `mermaid` | `stateDiagram-v2` — Vòng đời đơn hàng, IoT device lifecycle |
| 5 | **ERD (Entity-Relationship)** | Dev + BA | `plantuml` | `@startuml` + Crow's foot (`\|\|--o{`), PK/FK, không lag với 50+ bảng |
| 6 | **Class Diagram (OOP)** | Dev | `plantuml` | `@startuml` + Class, visibility (`+/-/#`), Inheritance, Composition |
| 7 | **Package / Directory Architecture** | Dev / Architect | `plantuml` | `@startuml` + `package`, `folder`, `node`, `database` |
| 8 | **Component / Deployment** | DevOps / Architect | `plantuml` | `@startuml` + Microservices, Docker container, Cloud sprites |
| 9 | **Activity / Swimlane** | BA | `plantuml` | `@startuml` + Phân làn partition `\|User\|`, `\|System\|`, `\|Gateway\|` |
| 10 | **C4 Architecture** | Architect | `plantuml` | `!include <C4/C4_Context>` — Context, Container, Component layers |
| 11 | **Use Case Diagram** | BA | `plantuml` | `@startuml` + `actor`, `usecase`, `<<include>>`, `<<extend>>` |
| 12 | **Mind Map** | BA + Dev | `plantuml` | `@startmindmap` — Cây tính năng, phân rã yêu cầu |

---

## 🧠 AI Decision Tree: Chọn Engine Cho Từng Yêu Cầu

```
Khi người dùng hoặc tài liệu yêu cầu vẽ sơ đồ:
│
├─ Là Screen Flow của màn hình ứng dụng (App/Web UI Navigation) có tọa độ cụ thể?
│   └─► engine: "canvas"  (spec_diagram_engine.py / diagram_editor.py)
│
├─ Là luồng giao tiếp theo thời gian / phân nhánh logic / máy trạng thái?
│   ├─ Sequence Diagram (Actor, API, Message exchange) ──► engine: "mermaid"
│   ├─ Flowchart logic / Quy trình nghiệp vụ ──────────► engine: "mermaid"
│   └─ State Diagram (Vòng đời đơn hàng, trạng thái) ──► engine: "mermaid"
│
└─ Là kiến trúc tĩnh / cấu trúc dữ liệu / OOP / hạ tầng / phân vai?
    ├─ Database Tables, PK/FK, Quan hệ 1-N, N-N ────────► engine: "plantuml" (ERD)
    ├─ OOP Classes, Interface, Methods, Attributes ────► engine: "plantuml" (Class)
    ├─ Thư mục dự án, Cấu trúc Module/Package ─────────► engine: "plantuml" (Package)
    ├─ Microservices, Docker, Deployment, Cloud ───────► engine: "plantuml" (Component)
    ├─ Quy trình đa vai trò phân làn (Swimlane) ────────► engine: "plantuml" (Activity)
    ├─ Kiến trúc tổng thể C4 (Context / Container) ────► engine: "plantuml" (C4)
    ├─ Actor & Use Case trong SRS ─────────────────────► engine: "plantuml" (Use Case)
    └─ Cây tính năng / Phân rã nghiệp vụ (Mind Map) ────► engine: "plantuml" (Mindmap)
```

---

## 🛡️ 4 Bẫy Kỹ Thuật PlantUML Trên Windows & Quy Tắc Khắc Phục

> **BẮT BUỘC TUÂN THỦ**: Tránh treo tiến trình, vỡ font tiếng Việt hoặc cắt cụt ảnh.

1. **C4 Standard Library Nội Bộ (Tuyệt đối không dùng URL Raw GitHub)**:
   - ❌ **Cấm**: `!include https://raw.githubusercontent.com/.../C4_Context.puml` (treo máy 30-60s khi offline/mạng chặn).
   - ✅ **Chuẩn**: Dùng thư viện C4 đóng gói sẵn trong mọi bản `plantuml.jar` hiện đại (chạy 100% offline):
     ```plantuml
     @startuml
     !include <C4/C4_Context>
     ...
     @enduml
     ```
2. **Chống Vỡ Font Tiếng Việt Trên Windows (-charset UTF-8)**:
   - Mọi subprocess gọi Java đều bắt buộc truyền cờ `-charset UTF-8` và file nguồn `.puml` phải ghi với mã hóa `utf-8`.
3. **Nâng Trần Kích Thước Ảnh Java (-DPLANTUML_LIMIT_SIZE=16384)**:
   - Mặc định PlantUML giới hạn 4096px. Luôn truyền cờ JVM `-DPLANTUML_LIMIT_SIZE=16384` ở đầu lệnh java để render các ERD lớn ở độ phân giải 300 DPI không bị mờ hay cắt ngang.
4. **Auto-Inject Vào File Word Đích**:
   - Khi spec có field `"inject_into"`, dispatcher tự động chèn diagram vào vị trí placeholder hoặc heading tương ứng, tự động căn giữa và gán caption chuẩn APA.

---

## 📐 Unified JSON Spec Schema

### 1. Schema cho `engine: "plantuml"` hoặc `engine: "mermaid"`

```json
{
  "engine": "plantuml",
  "diagram_type": "erd",
  "code": "@startuml\n...\n@enduml",
  "caption": "Hình 1: Sơ đồ ERD Cơ sở Dữ liệu Hệ thống",
  "inject_into": "BAO_CAO_THIET_KE.docx",
  "target_heading": "3.1 Thiết kế Cơ sở Dữ liệu",
  "placeholder": "[[DIAGRAM_DATABASE_ERD]]",
  "width_cm": 14.0,
  "max_height_cm": 20.0
}
```

### 2. Schema cho `engine: "canvas"` (Precision Screen Flow)

```json
{
  "engine": "canvas",
  "diagram_type": "screen_flow",
  "width": 1400,
  "height": 770,
  "font_family": "Segoe UI, -apple-system, BlinkMacSystemFont, Roboto, sans-serif",
  "font_size": 10.5,
  "bg_color": "#ffffff",
  "nodes": [
    {
      "id": "login",
      "label": "Login Screen",
      "x": 80,
      "y": 320,
      "width": 150,
      "height": 54,
      "type": "primary"
    }
  ],
  "edges": [
    {
      "source": "login",
      "target": "home",
      "source_port": "right",
      "target_port": "left",
      "label": "Click \"Đăng nhập\"",
      "line_style": "solid",
      "waypoints": []
    }
  ]
}
```

---

## 📝 Mẫu Code PlantUML Chuẩn Cho Từng Loại

### 1. ERD (Entity-Relationship Diagram)
```plantuml
@startuml
hide circle
skinparam linetype ortho

entity "User" as user {
  * user_id : INTEGER <<PK>>
  --
  username : VARCHAR(50)
  email : VARCHAR(100)
  created_at : TIMESTAMP
}

entity "Order" as ord {
  * order_id : INTEGER <<PK>>
  --
  * user_id : INTEGER <<FK>>
  total_price : DECIMAL(10,2)
  status : ENUM
  order_date : DATE
}

user ||--o{ ord : "places"
@enduml
```

### 2. Class Diagram (OOP)
```plantuml
@startuml
skinparam classAttributeIconSize 0

interface IRepository<T> {
  + getById(id: int): T
  + save(entity: T): void
}

class UserRepository implements IRepository {
  - dbContext: DatabaseContext
  + getById(id: int): User
  + save(entity: User): void
}

class User {
  - id: int
  - name: String
  - email: String
  + getId(): int
  + getEmail(): String
}

UserRepository --> User : "manages"
@enduml
```

### 3. C4 Architecture (Context Diagram)
```plantuml
@startuml
!include <C4/C4_Context>

Person(user, "Người dùng", "Khách hàng sử dụng ứng dụng di động")
System(app, "Hệ thống SCORT", "Hệ thống sao chép đối tượng dữ liệu SAP")
System_Ext(sap_core, "SAP S/4HANA", "Hệ thống ERP trung tâm")
System_Ext(vnpay, "VNPay Gateway", "Cổng thanh toán điện tử")

Rel(user, app, "Thao tác trên ứng dụng", "HTTPS")
Rel(app, sap_core, "Đồng bộ dữ liệu qua", "OData V4 / RFC")
Rel(app, vnpay, "Thanh toán qua", "REST API")
@enduml
```

### 4. Activity Diagram với Swimlanes
```plantuml
@startuml
|Khách hàng|
start
:Mở ứng dụng;
:Chọn sản phẩm vào giỏ;
:Bấm "Thanh toán";

|Hệ thống|
:Kiểm tra tồn kho;
if (Còn hàng?) then (có)
  :Tạo đơn hàng tạm;
  |Cổng thanh toán|
  :Xử lý giao dịch thẻ;
  :Trả kết quả thành công;
  |Hệ thống|
  :Cập nhật trạng thái "Đã thanh toán";
  :Gửi email xác nhận;
  |Khách hàng|
  :Xem thông báo thành công;
else (hết)
  |Hệ thống|
  :Báo lỗi "Sản phẩm hết hàng";
  |Khách hàng|
  :Điều chỉnh giỏ hàng;
endif
stop
@enduml
```

### 5. Use Case Diagram
```plantuml
@startuml
left to right direction
actor "Khách hàng" as customer
actor "Quản trị viên" as admin

rectangle "Hệ thống E-Commerce" {
  usecase "Xem sản phẩm" as UC1
  usecase "Đặt hàng" as UC2
  usecase "Thanh toán trực tuyến" as UC3
  usecase "Quản lý kho hàng" as UC4
  usecase "Xem báo cáo doanh thu" as UC5
}

customer --> UC1
customer --> UC2
UC2 ..> UC3 : <<include>>
admin --> UC4
admin --> UC5
@enduml
```

### 6. Mind Map (Cây tính năng)
```plantuml
@startmindmap
* Hệ thống SCORT
** Quản trị Đối tượng (Objects)
*** Quản lý Local TADIR
*** Quản lý Target Objects
*** Đối soát Matrix (Compare)
** Quản lý Transport Request (TR)
*** Cây phả hệ TR (Hierarchy Tree)
*** Tìm kiếm đối tượng trong TR
*** Phát hành TR (Release Service)
** Tiện ích & Trợ lý AI
*** So sánh trực quan Monaco Diff
*** Tối ưu & Gợi ý TR qua Gemini
*** GZIP Compression Utility
@endmindmap
```

---

## 🎯 Standardized Diagram Language & Action Formatting Rules

> **MANDATORY**: Technical diagrams must maintain international technical standards while faithfully representing the codebase implementation.

1. **Object / Screen Box Names & Metadata — 100% Standardized English**:
   - Every node box label MUST be in standardized technical English (e.g., `Login Screen`, `Register Screen`, `Home Dashboard`, `Cart Screen`, `Product Detail Screen`, `Navigation Map 2D`).
   - Applies to ALL diagram entities:
     - Group / Cluster titles (`Authentication Flow`, `Main Operations`, `Warehouse Staff Area`).
     - Container boxes, Subtitles, Badges & Role tags (`[Authorized Staff Only]`, `Route: /login`).
   - NEVER place Vietnamese titles or redundant bilingual strings (`Đăng nhập (Login Screen)`) inside node boxes.

2. **Automated i18n Codebase Detection (AI Heuristic)**:
   - Before drafting the spec, AI scans the target codebase for internationalization resources:
     - **Android**: `res/values-*/strings.xml` (presence of `values-en/` alongside `values-vi/` or default `values/`).
     - **Web/FE**: `locales/`, `messages/`, `i18n.ts/js`, or pairs like `en.json` and `vi.json`.
     - **Flutter/Cross-platform**: `l10n/` or `.arb` resource files.
   - **Multi-language (i18n) Mode** (>= 2 languages found): Default 100% of all diagram text, including action button labels, to English (`Tap "Login"`, `Click "View Cart"`, `Select "Settings"`).
   - **Single-language Native Mode** (only 1 native locale found, e.g. Vietnamese-only FE): Action verbs in English + Quoted native UI string directly from codebase.

3. **Action Button Phrasing on Arrows**:
   - **Standardized English Action Verbs**:
     - `Tap`: For Mobile / Touchscreen interactions (`Tap "Đăng nhập"`).
     - `Click`: For Web / Desktop / Mouse interactions (`Click "Submit"`).
     - `Select`: For Tabs, Radio buttons, Dropdown menus, List items (`Select "Cài đặt"`).
     - `Scan`: For Camera, Barcode, QR scanning (`Scan "Mã vạch sản phẩm"`).
     - `Swipe`: For Gesture-based transitions (`Swipe Down to Refresh`).
     - `Auto`: For System-triggered redirects and timer expirations (`Auto Redirect (3s)`).
   - **Quoted Native Button UI String**:
     - When a real UI button exists in single-language mode: `Click "Đăng nhập"`, `Tap "Xem lộ trình\n& Chỉ đường"`, `Click "Đăng xuất"`.

---

## 💻 CLI Usage & Visual Tools

```bash
# 1. Unified Dispatcher (Tự động chọn Canvas, Mermaid, hoặc PlantUML theo field "engine"):
python ai_tools_cli.py diagram-render your_spec.json -o output.png

# 2. Render trực tiếp từng engine:
python ai_tools_cli.py plantuml-render erd_spec.json -o erd.png --dpi 300
python ai_tools_cli.py mermaid-render sequence_spec.json -o seq.png
python ai_tools_cli.py spec-render screen_flow_spec.json -o flow.png --scale 3

# 3. Chạy Interactive Canvas Editor kéo thả cho Screen Flow:
python ai_tools_cli.py diagram-editor screen_flow_spec.json
```
