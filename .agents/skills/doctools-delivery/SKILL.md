---
name: doctools-delivery
description: Quy trình phân phối và nghiệm thu mã nguồn doctools: Micro-Commit Cadence (X.Y.Z), Git Workflow Gates, Triage Diagnostics và quy trình chuyển đổi liên module.
---

# Skill: doctools-delivery

> **Purpose**: Chuẩn hóa toàn bộ quy trình phát triển, kiểm thử, phân phối (delivery) và nghiệm thu mã nguồn giữa Solo Dev và AI Agent trong dự án `doctools`.

---

## 1. When to Use
Kích hoạt khi:
- Bắt đầu triển khai hoặc nghiệm thu một Phase / Sub-step trong Master Plan (`X.Y.Z`).
- Cần thực hiện kiểm định chất lượng, chạy test suite, và đóng gói commit Git.
- Cần điều phối luồng xử lý liên module (Cross-Module: XLSX $\rightarrow$ DOCX, DIAGRAM $\rightarrow$ DOCX).
- Xử lý và phân loại lỗi / cảnh báo chẩn đoán (`Diagnostics` triage).

---

## 2. Micro-Commit Cadence (`X.Y.Z`) & Git Gate

Quy tắc bất biến cho mọi Phase phát triển:
1. **Phân rã mã số vi mô**:
   - `X`: Phase lớn (`1`: DOCX, `2`: XLSX, `3`: DIAGRAM).
   - `Y`: Nhóm tính năng theo ưu tiên (`1`: MVP, `2`: P1, `3`: P2).
   - `Z`: Tiểu bước kiểm chứng được (`0`, `1`, `2`...).
2. **Kỷ luật Verifiable Gate**:
   - Mỗi tiểu bước `X.Y.Z` phải có unit test độc lập.
   - Chạy toàn bộ test suite đạt **100% PASS**.
   - Agent dừng lại, in bằng chứng pass test và đề xuất lệnh commit.
   - **BẮT BUỘC có phê duyệt tường minh của User mới được commit và push**.
   - Chi tiết: Xem [references/micro_commit_cadence.md](references/micro_commit_cadence.md).

---

## 3. Decision Tree: Triage & Delivery Flow

```
                      [Triển khai Tiểu bước X.Y.Z]
                                   │
                                   ▼
                       [Chạy Test Suite Toàn Diện]
                                   │
            ┌──────────────────────┴──────────────────────┐
            ▼                                             ▼
       [Có Tests Thất Bại]                           [100% Tests PASS]
            │                                             │
      [Max 1 Fix Attempt]                                 ▼
      Thử sửa 1 lần duy nhất                     [Đề xuất Git Commit]
            │                                 Format: feat(scope): ... [Gate]
     ┌──────┴──────┐                                      │
     ▼             ▼                                      ▼
[Pass 100%]    [Vẫn Lỗi]                         [User Duyệt Tường Minh]
     │             │                                      │
     │       DỪNG LẠI NGAY!                               ▼
     │       Giải thích root cause,              [Thực thi Commit & Push]
     │       chờ phản hồi của User                        │
     │                                                    ▼
     └───────────────────────────────────────► [Chuyển sang X.Y.(Z+1)]
```

---

## 4. Diagnostics Triage & Cross-Module References

- **Xử lý chẩn đoán**: Xem [references/diagnostics_triage.md](references/diagnostics_triage.md) để phân loại `errors` vs `warnings` (`W-DEV-*` kích hoạt `/grill-me`).
- **Quy trình liên module**: Xem [references/cross_module_pipelines.md](references/cross_module_pipelines.md) cho các pipeline tích hợp DOCX + XLSX + DIAGRAM.
