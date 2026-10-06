# Reference: 5-Layer Context Model & Walk-Up Scoping

> **Module**: `agent-context-architecture`
> **Mục tiêu**: Phân tích chi tiết mô hình 5 tầng ngữ cảnh và cơ chế kế thừa thư mục (Walk-Up Scoping) trong hệ sinh thái AI-Native.

---

## 1. Bản Chất 5 Tầng Ngữ Cảnh (The 5 Layers)

Khi AI làm việc trên một dự án lớn, việc nhồi nhét toàn bộ tài liệu vào ngữ cảnh cùng một lúc sẽ dẫn tới **Context Saturation** và hiện tượng **Lost in the Middle** (AI quên mất luật ở giữa tài liệu dài). Hệ thống phân tầng ngữ cảnh chia thông tin thành 5 cấp bậc:

```
┌─────────────────────────────────────────────────────────────────┐
│ Layer 1: GEMINI.md / AGENTS.md (Root & Sub-directories)        │
│          - Always-on theo phạm vi thư mục                       │
│          - Định vị module, routing, bất biến cốt lõi           │
├─────────────────────────────────────────────────────────────────┤
│ Layer 2: .agents/rules/*.md                                    │
│          - Quy chuẩn code, rào chắn bảo vệ, ATC standards       │
│          - Kích hoạt qua Glob, Model Decision, Always-on        │
├─────────────────────────────────────────────────────────────────┤
│ Layer 3: .agents/skills/<skill-name>/                          │
│          - Năng lực thao tác (Capabilities & Workflows)         │
│          - Kích hoạt On-Demand qua Progressive Disclosure       │
├─────────────────────────────────────────────────────────────────┤
│ Layer 4: Specs & Architecture Documents (docs/, specs/)        │
│          - Nguồn chân lý kỹ thuật (Source of Truth)             │
│          - Chỉ đọc khi Agent thực sự cần thông tin chi tiết     │
├─────────────────────────────────────────────────────────────────┤
│ Layer 5: Deterministic Execution Scripts (scripts/, tools/)    │
│          - Thuật toán tính toán nặng, CLI, format diff, đo pixel│
│          - Thực thi hộp đen (Black-box Execution)               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Cơ Chế Walk-Up Scoping Của GEMINI.md / AGENTS.md

### 2.1. Nguyên lý hoạt động
Khi AI Agent thao tác trên một file tại đường dẫn:
`/project/services/order_service/handlers/create_order.py`

Hệ thống sẽ tự động quét ngược (Walk-up) từ thư mục hiện tại lên đến thư mục gốc:
1. `services/order_service/handlers/GEMINI.md` (nếu có)
2. `services/order_service/GEMINI.md` (nếu có)
3. `services/GEMINI.md` (nếu có)
4. `/project/GEMINI.md` (Root project context)

### 2.2. Quy tắc kế thừa và cô lập
- **Root `GEMINI.md`**: Chứa bản đồ toàn dự án, danh mục module, các nguyên tắc tối thượng áp dụng cho toàn bộ repo. Chiều dài lý tưởng: $\le 80$ dòng (tối đa 100 dòng).
- **Sub-directory `GEMINI.md`**: Chỉ chứa bất biến và ranh giới trách nhiệm riêng của package/module đó. Chiều dài lý tưởng: $\le 20$–$30$ dòng.
- **Không lặp lại**: Sub-directory không lặp lại các luật đã có ở Root. Root không đi sâu vào chi tiết nội bộ của một module.

---

## 3. Ranh Giới Giữa Rule và Skill

Một sai lầm phổ biến là biến Rule thành hướng dẫn làm bài tập (Tutorial) hoặc biến Skill thành danh sách cấm đoán (Invariants).

| Tiêu Chí | Rules (`.agents/rules/`) | Skills (`.agents/skills/`) |
|---|---|---|
| **Mục đích** | Rào chắn bảo vệ, chuẩn mực code, điều kiện cấm kỵ | Quy trình thực thi, phương pháp luận giải quyết vấn đề |
| **Câu hỏi cốt lõi** | "Tôi PHẢI tuân thủ gì? Tôi KHÔNG ĐƯỢC làm gì?" | "Tôi LÀM thế nào để hoàn thành tác vụ này?" |
| **Tính chất** | Bắt buộc, thụ động (Passive Guardrails) | Chủ động, năng động (Active Capabilities) |
| **Cơ chế nạp** | Tự động qua file match (Glob) hoặc AI match (Model) | Đọc `SKILL.md` khi phát hiện intent khớp description |
| **Ngân sách** | Tính vào tổng 20k token active rules | Tách biệt, tải từng file qua Progressive Disclosure |

---

## 4. Specs vs Scripts: Giảm Tải Cho AI

- **Specs (Layer 4)**: Cung cấp API schema, cấu trúc bảng DB, sơ đồ khối logic. AI chỉ cần tham chiếu (view_file) phần nó đang làm, không đọc lướt cả tập spec 50 trang.
- **Scripts (Layer 5)**: AI là người ra quyết định logic nghiệp vụ, máy tính là người tính toán hình học, đo đạc toạ độ và chạy regression test. Tuyệt đối không để AI nhẩm toạ độ pixel trong đầu.
