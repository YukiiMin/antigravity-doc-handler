# doctools — khung mẫu "bộ công cụ cho AI"

Mục tiêu: cho thấy kiến trúc tối thiểu để một bộ công cụ (tất định, lặp lại nhiều) được **AI quản lý và sử dụng**.
Chỉ có 3 công cụ Excel (`preflight_xlsx`, `set_cells_xlsx`, `diff_inventory_xlsx`) để bạn thấy khung, không phải sản phẩm hoàn chỉnh.

## Kiến trúc: Core -> Contract -> Registry -> Adapters

```
 AI (Antigravity / Claude Code / host MCP bất kỳ)
        │  đọc .agent/ (KHI NÀO dùng công cụ nào)         ← mỏng, có test chống lệch
        ▼
 ┌─ ADAPTERS (mỏng, không logic) ──────────────────────────────┐
 │  cli.py        mcp_server.py        (http.py, thư viện)     │
 └───────────────┬─────────────────────────────────────────────┘
                 ▼  tất cả đi qua MỘT điểm vào: registry.run(tên, json) -> Result
 ┌─ REGISTRY: tên + mô tả cho AI + schema + (đọc/ghi, idempotent) ─┐   ← một nguồn sự thật
 └───────────────┬─────────────────────────────────────────────┘
                 ▼
 ┌─ CONTRACT (Pydantic): đầu vào JSON có schema, đầu ra Result{success,data,file_ref,issues[]} ─┐
 └───────────────┬─────────────────────────────────────────────┘
                 ▼
 ┌─ CORE: logic thuần + rào chắn (roots, vùng khóa, không ghi đè, all-or-nothing, tự đối chiếu) ─┐
 └─────────────────────────────────────────────────────────────┘
```

## Thử nhanh

```bash
pip install openpyxl pydantic pillow            # (+ pip install "mcp>=2.3,<3" nếu muốn thử MCP)
export PYTHONPATH=.                             # hoặc: pip install -e .
python -m unittest discover -s tests -v         # 18 test, mỗi test tự dựng dữ liệu, không phụ thuộc thứ tự

python -m doctools list
python -m doctools schema set_cells_xlsx
python -m doctools check-docs                   # .agent/ có khớp registry không
python -m doctools run preflight_xlsx --input '{"path": "file.xlsx"}'     # exit code 0/1/2

python scripts/try_mcp.py                       # khởi động server MCP qua stdio và gọi thử (cần gói mcp)
```

`DOCTOOLS_ROOTS` (danh sách thư mục, ngăn bằng `:` hoặc `;`) giới hạn nơi công cụ được đọc/ghi; mặc định là thư mục hiện tại.

## Thêm một công cụ mới (5 bước)

1. Logic thuần trong `core/` (không import MCP/CLI).
2. Model đầu vào trong `contract/inputs.py`, mỗi trường có `description` (AI đọc nó).
3. Hàm trong `operations.py` với `@operation(...)`, trả `Result`; lỗi dự kiến dùng `DocToolsError(code=...)`.
4. Nhắc `tool:<tên>` trong một skill/workflow ở `.agent/` (nói KHI NÀO dùng) — `check-docs` sẽ bắt nếu quên.
5. Viết test: ca đúng, ca bị rào chắn chặn, ca sai schema.

## Giới hạn của bản mẫu

- Quét XML bằng `xml.etree` (có giới hạn kích thước); bản production nên dùng `defusedxml`/`lxml` cấu hình an toàn và thêm giới hạn tỷ lệ nén.
- Chưa có tính lại công thức, Shift Manager, validator theo profile (xem spec Xlsx Engine).
- Adapter MCP mới chạy thử với `mcp 2.3.0`; API SDK đổi giữa các bản lớn nên được cô lập trong một file.
