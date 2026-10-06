# Reference: Ready-to-Use Templates & Boilerplates

> **Module**: `agent-context-architecture`
> **Mục tiêu**: Cung cấp các mẫu khung chuẩn (Boilerplates) sẵn sàng sao chép cho Root GEMINI, Sub-directory GEMINI, Glob Rule, Model-Decision Rule và Skill Package.

---

## 1. Mẫu Root `GEMINI.md` (Cho Gốc Repo - Dưới 80 Dòng)

```markdown
# [Tên Dự Án] — Core Architecture & Invariants Quickref

> **Vai trò**: Cung cấp bản đồ tổng thể dự án và các bất biến cốt lõi cho AI Agent.
> **Quy tắc**: File này ALWAYS-ON. Giữ ngắn gọn, không giải thích dài dòng.

---

## 1. Bản Đồ Module Dự Án (Project Module Map)

| Module | Đường Dẫn | Vai Trò & Ranh Giới | Rule Kích Hoạt Tương Ứng |
|---|---|---|---|
| **Core Service** | `src/core/` | Logic kinh doanh lõi, thuật toán chính | `rule_core_standards.md` (`src/core/**`) |
| **API / Transport** | `src/api/` | FastAPI/Express handlers, routing | `rule_api_standards.md` (`src/api/**`) |
| **Infra / Database** | `src/infra/` | Kết nối DB, ORM, adapter bên ngoài | `rule_infra_standards.md` (`src/infra/**`) |

---

## 2. Bất Biến Cốt Lõi Tối Thượng (Top Non-Negotiable Invariants)

1. **Ranh giới công nghệ**: Chỉ sử dụng thư viện đã phê duyệt trong `pyproject.toml` / `package.json`.
2. **Tiêu chuẩn kiểm thử**: Mọi tính năng mới phải có unit test tương ứng; độ bao phủ $\ge 80\%$.
3. **An toàn dữ liệu**: Không ghi đè file của người dùng khi chưa có bản sao lưu dự phòng.
4. **Giới hạn kích thước**: Mỗi file mã nguồn $\le 300$ dòng; chia tách module khi vượt ngưỡng.

---

## 3. Điều Hướng Tác Vụ Sang Skills Chuyên Biệt

- Khi triển khai tính năng hoặc quy trình nghiệp vụ: Đọc `.agents/skills/<ten-skill>/SKILL.md`.
- Khi kiểm toán chất lượng hoặc sửa lỗi: Kích hoạt quy chuẩn kiểm định tại `.agents/rules/`.
```

---

## 2. Mẫu Sub-Directory `GEMINI.md` (Cho Module Con - Dưới 25 Dòng)

```markdown
# [Tên Sub-Module] Context & Invariants

> **Scope**: Áp dụng riêng cho thư mục `path/to/submodule/` và các thư mục con.

## Invariants Bắt Buộc Của Module:
1. **Cô lập phụ thuộc**: Module này KHÔNG ĐƯỢC import ngược từ tầng `api/` hoặc `cli/`.
2. **Không ném ngoại lệ thô**: Mọi lỗi phải được bọc trong exception nội bộ của module (`ModuleError`).
3. **Pure Functions**: Các hàm biến đổi dữ liệu phải là hàm thuần túy (không side-effect).
```

---

## 3. Mẫu Rule Kích Hoạt Theo Glob (`trigger: glob`)

```markdown
---
trigger: glob
globs: src/core/**/*.py, tests/core/**/*.py
---

# Rule: Core Service Architecture Standards

> **Phạm vi**: Tự động kích hoạt khi chỉnh sửa hoặc đọc các file trong `src/core/`.

## 1. Ràng Buộc Kiến Trúc
- Sử dụng Pydantic v2 để validate dữ liệu đầu vào.
- Không truy cập trực tiếp biến môi trường `os.environ` tại tầng này; nhận qua Config Injection.
```

---

## 4. Mẫu Rule Kích Hoạt Theo AI Model (`trigger: model_decision`)

```markdown
---
trigger: model_decision
description: Quy chuẩn kiểm toán chất lượng, bảo toàn dữ liệu và xử lý hồi quy kiểm thử
---

# Rule: Quality Audit & Regression Prevention

> **Phạm vi**: AI tự động nạp khi nhận diện tác vụ liên quan đến QA, test fail, hoặc review code.

## 1. Nguyên Tắc Sửa Lỗi
- Tối đa 1 lần thử sửa lỗi; nếu thất bại phải dừng lại phân tích nguyên nhân gốc rễ.
- Không comment tắt cảnh báo linter mà không có giải trình kỹ thuật.
```

---

## 5. Mẫu Skill Package Chuẩn (`.agents/skills/<name>/`)

### Cấu trúc thư mục:
```
.agents/skills/<ten-skill>/
├── SKILL.md                          # (Bắt buộc) Hướng dẫn quy trình chính
├── references/                       # (Tùy chọn) Tài liệu chuyên sâu lazy-load
│   └── deep_dive_topic.md
└── scripts/                          # (Tùy chọn) Script thực thi tự động
    └── automated_check.py
```

### Nội dung file `SKILL.md`:
```markdown
---
name: ten-skill
description: Mô tả rõ ràng mục tiêu của skill, các từ khóa kích hoạt, và ngữ cảnh khi nào nên dùng để AI nhận diện qua Progressive Disclosure.
---

# Skill: Tên Skill

> **Mục tiêu**: Tóm tắt 1 câu về giá trị nghiệp vụ của skill.

## 1. When to Use
- Liệt kê các kịch bản người dùng yêu cầu...

## 2. Quy Trình Thực Thi Từng Bước (Core Workflow)
1. Bước 1: Thu thập thông tin và kiểm tra tiền điều kiện...
2. Bước 2: Thực thi logic chính...
3. Bước 3: Nghiệm thu và kiểm tra kết quả...

## 3. Danh Mục References Đi Kèm
- [references/deep_dive_topic.md](references/deep_dive_topic.md): Hướng dẫn giải quyết các trường hợp biên.
```
