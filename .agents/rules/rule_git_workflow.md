---
description: Quy chuẩn Git Workflow & Kỷ luật Commit cho Solo Dev cộng tác với AI Agent trong dự án lớn
---

# Rule: Git Workflow & Commit Protocol (Solo Dev + AI Agent)

> **Phạm vi**: Áp dụng bắt buộc cho toàn bộ chu trình phát triển của bộ công cụ `doctools` (`tool/pdf_to_docx_converter`).  
> **Mục tiêu**: Ngăn chặn 100% tình trạng mất dấu vết (lost context), ô nhiễm git log bằng mã nguồn lỗi, đồng thời bảo vệ nhánh `main` luôn tinh gọn cho người dùng cuối.

---

## 1. Mô Hình Phân Nhánh (Branching Model)

Dự án vận hành theo mô hình lai (Hybrid Phase Branching + Micro-Commit):

```
                        ┌──► [Nhánh archive/legacy-v1] (Lưu bảo tồn code cũ & bài học lên GitHub)
                        │
[Hiện trạng] ───────────┤
                        └──► [Nhánh feat/phase-0-foundation] ──► [feat/phase-1-docx] ──► [Merge vào main]
                             (Chứa các micro-commits)                                     (main sạch 100%,
                                                                                           không rác)
```

1. **Nhánh `main` (Production Baseline)**:
   - Phải luôn ở trạng thái xanh (Green), tinh gọn, không chứa file rác, log tạm hay tài sản demo nặng.
   - Người dùng cuối `git clone` nhánh `main` về máy chỉ nhận đúng bộ mã nguồn toolkit chuẩn (`doctools/`, `tests/`, `docs/`, `pyproject.toml`).
2. **Nhánh Lưu Trữ `archive/legacy-v1` (Museum Branch)**:
   - Tạo tại mốc kết thúc Phase 0.1 (sau khi gom toàn bộ engine cũ vào `legacy_engines/`).
   - Đẩy lên GitHub (`git push origin archive/legacy-v1`) để lưu trữ vĩnh viễn toàn bộ mã nguồn cũ, benchmark và bài học xương máu cho việc tra cứu lịch sử.
3. **Nhánh Phát Triển Theo Phase (`feat/phase-X-...`)**:
   - Mỗi Phase lớn mở một nhánh độc lập: `feat/phase-0-foundation`, `feat/phase-1-docx`, `feat/phase-2-xlsx`, `feat/phase-3-diagram`.
   - Mọi công việc trong phase đó được commit tuyến tính theo từng bước nhỏ (Micro-Commit).
   - Chỉ merge vào `main` khi Phase đó vượt qua 100% Quality Gates và kiểm thử Parity Dual-Run.

---

## 2. Kỷ Luật Kích Hoạt Commit (Verifiable Sub-Step Gate Cadence)

Tuyệt đối **KHÔNG** commit mù quáng, **KHÔNG** gộp cả Phase khổng lồ vào 1 commit:

1. **Điểm Dừng Kích Hoạt (Commit Trigger)**:
   - Một commit được tạo ra **NGAY KHI** một đơn vị module/tiểu phân đoạn hoàn thành và **chạy bộ test tương ứng PASS 100%**.
   - *Ví dụ*: Viết xong `file_store.py` + pass 100% `test_file_store.py` $\rightarrow$ Đạt điểm kích hoạt commit.
2. **Quyền Commit (Authority Boundary)**:
   - Agent **TUYỆT ĐỐI KHÔNG** tự ý `git commit` hay `git push` ngầm khi người dùng chưa đồng ý.
   - Khi hoàn thành sub-step, Agent:
     1. Dừng lại, in bằng chứng kiểm thử đạt yêu cầu.
     2. Đề xuất thông điệp commit chuẩn (Conventional Commits).
     3. Chờ Người dùng gõ xác nhận (ví dụ *"commit đi"*, *"ok commit"*) mới được thực thi lệnh `git commit`.

---

## 3. Quy Chuẩn Thông Điệp Commit (Commit Message Standards)

Bắt buộc tuân thủ chuẩn **Conventional Commits có Scope & Mã Cổng/TC**:

```
<type>(<scope>): <mô tả ngắn bằng tiếng Anh/tiếng Việt> [<Mã Gate/TC>]
```

### Các Tiền Tố Chuẩn (`type`):
- `feat`: Tính năng mới hoặc module mới (vd: `feat(infra): implement FileStore with TTL [UG-01, DGM-TC-01]`).
- `fix`: Sửa lỗi kỹ thuật hoặc khắc phục vi phạm gate (vd: `fix(xlsx): resolve formula AST shift offset [E-XLSX-SHIFT-FORMULA]`).
- `test`: Thêm hoặc cập nhật test cases (vd: `test(diagram): add orthogonal routing edge cases [DGM-TC-22]`).
- `refactor`: Tái cấu trúc mã nguồn không làm đổi logic (vd: `refactor(sandbox): split sandbox runner into 5 sub-modules`).
- `docs`: Cập nhật tài liệu, plan, spec, rules (vd: `docs(plan): finalize Master Plan v6 and workflows v2`).
- `chore`: Cấu hình tooling, linter, gitignore, dọn dẹp môi trường.

### Phạm Vi Hợp Lệ (`scope`):
`infra`, `contract`, `docx`, `xlsx`, `diagram`, `registry`, `tests`, `docs`, `rules`.

---

## 4. Cơ Chế Phục Hồi Khi Gặp Sự Cố (Failure & Recovery Protocol)

Khi xảy ra lỗi trong quá trình thực thi:
1. **Tuân thủ luật Max 1 Fix Attempt**: Agent chỉ được phép thử sửa tối đa 1 lần duy nhất.
2. **Keep Dirty State & In Git Diff**:
   - Nếu lần sửa thứ nhất thất bại hoặc sinh thêm lỗi mới $\rightarrow$ **DỪNG LẠI NGAY LẬP TỨC**.
   - **Giữ nguyên trạng thái dở dang (uncommitted files)**; in `git diff` tóm tắt để Người dùng và Agent cùng phân tích.
   - Tuyệt đối không tự ý `git restore .` hay `git reset --hard` ngầm làm mất dấu vết code vừa thử.
   - Người dùng là người ra quyết định cuối cùng: hướng dẫn sửa tiếp hoặc yêu cầu hoàn tác về commit xanh trước đó.

---

## 5. Ranh Giới Độc Lập Kho Mã Nguồn (Sub-Repo Isolation)

- Mọi thao tác Git (`add`, `commit`, `branch`, `push`) trong chu trình này **CHỈ ĐƯỢC PHÉP THỰC HIỆN TRÊN REPO CON**:
  `d:\Minh\For_myself\ZSCORT_GSU26_SAP05\tool\pdf_to_docx_converter` (remote `antigravity-doc-handler`).
- **NGHIÊM CẤM** đụng chạm hay commit vào kho chính SAP (`ZSCORT_GSU26SAP05_Main_Repo`) trừ khi có chỉ thị đích danh từ Người dùng.
