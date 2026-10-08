# Kế hoạch Kiến trúc Mô-đun hóa Bộ công cụ AI-Native (`pdf_to_docx_converter`)

> **Phiên bản Plan: 6 — Master Baseline Toàn Diện (Final Approved Architecture)**
> - **Căn cứ đặc tả**: [Docx Foundation Plan v1.1](docs/update-spec/docx-engine-mcp-plan.md), [Xlsx Foundation Plan v1.1](docs/update-spec/xlsx-engine-mcp-plan-v1.1.md), [Diagram Foundation Plan v1.0](docs/update-spec/diagram-engine-mcp-plan.md).
> - **Nguyên tắc định danh**: Áp dụng hệ thống tiền tố tường minh cho Tools (`docx.*`, `xlsx.*`, `diagram.*`), Mã lỗi (`E-DOCX-*`, `E-XLSX-*`, `E-DGM-*`), Quyết định (`DOCX-D-*`, `XLSX-D-*`, `DGM-D-*`), và Ca kiểm thử (`DOCX-TC-*`, `XLSX-TC-*`, `DGM-TC-*`).
> - **Chiến lược phân kỳ**: "Làm đến đâu xong đến đó" — Mỗi Module được chia thành 2 phân đoạn chuẩn: **MVP (a)** và **P1 (b)**. Giữ song song khả năng chạy của legacy engines cho đến khi nghiệm thu hoàn tất.
> - **Trạng thái quyết định**: Toàn bộ 16 câu hỏi kỹ thuật và 5 quyết định nền tảng Phase 0 đã được **CHỐT 100%**.

---

## 1. Goal Description & Scope Boundaries

Chuyển đổi toàn bộ mã nguồn tại `tool/pdf_to_docx_converter` thành bộ công cụ AI-Native Toolkit mô-đun hóa (`doctools`), tuân thủ triệt để nguyên tắc đơn trách nhiệm và kỷ luật nghiêm ngặt **< 300 dòng mã nguồn/file**.

### Bốn Trụ Cột Kỹ Thuật
1. **Tránh phình to file & Cưỡng chế bằng Code**:
   - Sử dụng `import-linter` để cưỡng chế Dependency Rule giữa các tầng (chống circular import).
   - Test tự động `test_file_size_limits.py` quét toàn bộ codebase trong CI, fail ngay nếu bất kỳ file logic nào $\ge 300$ dòng.
2. **AI-Native Plumbing & Tiền tố Namespace**:
   - Mọi công cụ đăng ký vào Registry tập trung (`doctools/registry.py`) theo namespace phân định: `docx.<tool>`, `xlsx.<tool>`, `diagram.<tool>`.
   - Giao tiếp thuần túy qua hợp đồng chuẩn `FileRef`: `{uri, sha256, size, mime, expires_at}` với URI mờ `resource://<engine>/files/{opaque_id}` và chiều vào `file://` kiểm tra trong allow-list roots (`core/guards.py`).
   - Phong bì trả về chuẩn `Result` + danh mục `Issue` có cấu trúc: `engine` (`docx` | `xlsx` | `diagram` | `infra`), `location` (mở rộng theo engine), `severity`, `fixable_by`, `evidence`, `suggested_action`.
3. **Template là Chân lý & Không Phá hủy (Word & Excel)**:
   - **Word**: Tag Order Registry cưỡng chế thứ tự thẻ XML ECMA-376 qua `lxml`, Dual-path builder (Path A Jinja render + Path B DocSpec generator), Run Consolidator giải quyết Run Splitting.
   - **Excel**: Preflight Package Inventory (T1..T4), Shift Manager phân tích AST qua `openpyxl.formula.Tokenizer` cập nhật công thức toàn workbook, Recalc Backend (`excel_com` ưu tiên, `libreoffice` fallback) + Cache Writer (`write_cached` bằng `lxml`, EV-13) tiêm `<v>`, bảo toàn công thức sống. Kiểm định qua **13 Universal Gates (UG-01..13)** và PG Profiles.
4. **Ngữ nghĩa Trước Hình học & Tách biệt Render (Diagram)**:
   - Sơ đồ kỹ thuật Nhóm 4 (ERD, Architecture, Sequence ở MVP; DFD, Class, Radial ở P1; Schematic ở P2): AI chỉ khai báo `DiagramSpec` JSON + gợi ý bố cục (`layout_hints`); không viết XML, không đưa tọa độ.
   - **Gate Ngữ nghĩa DG-00** chạy fail-closed trên spec trước khi tính hình học.
   - Tách biệt tuyệt đối **Pha 1 (sinh XML `mxGraphModel` tất định, không cần trình duyệt)** và **Pha 2 (Render PNG/SVG)**.
   - Runtime phối hợp: Python chủ quản + Node sidecar (`elk_worker.mjs` qua stdin/stdout cho layered layout) + Python layouts thuần (Sequence, DFD 5 cột, Radial, Schematic).
   - Đo chữ bằng font ghim đóng gói (`Pillow` advance length `font.getlength(text)`, NFC Unicode, ghim pixel size; **hủy bỏ hệ số `K_adj = 0.78`** bị lỗi đơn vị).

> [!WARNING]
> **Ranh giới Phân định Rõ Ràng Giữa Các Engine**:
> - **Biểu đồ số liệu / Chart (DrawingML)**: `xlsx.build` (P1) chịu trách nhiệm chính về tạo mới Chart DrawingML native; `xlsx.mutate`/`xlsx.recalc` (FR-17, MVP) chịu trách nhiệm relink dải tham chiếu chart có sẵn trong template. Docx Engine **chỉ chèn ảnh hoặc nhúng chart qua `FileRef`**, không tự sinh chart. Diagram Engine **kiên quyết không ghi OOXML và không sinh chart**.
> - **Sơ đồ Mạch điện (Schematic)**: Được giữ lại trong Diagram Engine vì cùng định dạng xuất bản `.drawio` (`MX_INV_10`, `MX_INV_13`, `MX_INV_17`), nhưng được quy hoạch vào **Phase 3b (P2)** đi kèm một tài liệu đặc tả riêng (**Diagram Spec v1.1**) và layout `schematic_layout.py` chuyên biệt.
> - **Chuyển giao Sơ đồ sang Văn bản/Bảng tính**: Diagram Engine xuất ảnh qua `FileRef` + `render_info` (width_px, height_px, dpi); Docx/Xlsx Engine nhận `FileRef` để đặt vào đúng placeholder mà không méo tỷ lệ.

---

## 2. Core Principles & Design Decisions (Tham chiếu Đối chiếu)

Chi tiết đầy đủ về bối cảnh, phân tích trade-off và cơ sở thực nghiệm được lưu trữ tại các tài liệu nền tảng:
- Tham chiếu Quyết định & Ranh giới Cam kết Word: [Docx Plan v1.1 (Mục 3 & 4)](docs/update-spec/docx-engine-mcp-plan.md).
- Tham chiếu Quyết định & Invariants E1–E14 Excel: [Xlsx Plan v1.1 (Mục 3 & 4)](docs/update-spec/xlsx-engine-mcp-plan-v1.1.md).
- Tham chiếu Quyết định & Đính chính Thực nghiệm Diagram: [Diagram Plan v1.0 (Mục 3, Phụ lục D & E)](docs/update-spec/diagram-engine-mcp-plan.md).

### Bảng Tổng Hợp Tiền Tố Định Danh Kỹ Thuật

| Hạng mục | Quy ước tiền tố | Ví dụ |
|---|---|---|
| **MCP Tools** | `<module>.<verb>_<noun>` | `docx.lint_template`, `xlsx.mutate`, `diagram.build` |
| **Mã lỗi / Cảnh báo** | `E-<MODULE>-*`, `W-<MODULE>-*`, `I-<MODULE>-*` | `E-DOCX-SCHEMA-001`, `E-XLSX-SHIFT-002`, `E-DGM-SEM-ERD-001` |
| **Quyết định Thiết kế** | `<MODULE>-D-<NN>` | `DOCX-D-06` (Tag Order), `XLSX-D-03` (Tokenizer), `DGM-D-03` (Tách Pha 1 & 2) |
| **Câu hỏi Mở / Quyết định** | `<MODULE>-Q-<NN>` | `DOCX-Q-01`, `XLSX-Q-04`, `DGM-Q-06` |
| **Ca kiểm thử** | `<MODULE>-TC-<NN>` | `DOCX-TC-01`, `XLSX-TC-04`, `DGM-TC-16` |

---

## 3. Dependency Rules & Cơ Chế Cưỡng Chế Bằng Code

```
adapters  →  registry  →  operations  →  gates  →  core  →  contract
                               │                      ▲
                               └──────►  infra  ──────┘ (infra chỉ phụ thuộc contract)
```

### Cơ Chế Cưỡng Chế Kỹ Thuật (Automated Enforcement)
1. **Cưỡng chế Phụ thuộc (`import-linter`)**:
   File cấu hình `.importlinter` tại gốc dự án kiểm tra cấu trúc 5 tầng:
   - `core` không được import `gates` (tránh circular dependency).
   - `gates` chỉ đọc, không import `operations`.
   - `contract` không import bất kỳ module nội bộ nào khác.
   - `infra` chỉ được phép import `contract`.
   - Vi phạm import làm fail ngay lập tức lệnh `lint` trong CI.
2. **Cưỡng chế Giới hạn Kích thước File (`test_file_size_limits.py`)**:
   Bộ test tự động duyệt qua 100% file trong gói `doctools/`. Bất kỳ file nào có số dòng thực tế $\ge 300$ sẽ gây lỗi build:
   `AssertionError: File doctools/... exceeds 300 lines limit (current: N lines). Please decompose.`
3. **Một Điểm Ghi Duy Nhất cho Mỗi Định Dạng**:
   - Ghi OOXML Word: Duy nhất qua `core/docx/schema/` (ECMA-376 Tag Order Registry).
   - Ghi Cache XML Excel: Duy nhất qua `core/xlsx/recalc/cache_writer.py` (`lxml`, tiêm `<v>`, tự kiểm lại bằng UG-13).
   - Ghi XML Diagram: Duy nhất qua `core/diagram/serializer/xml_serializer.py` (`lxml`, một đường ghi tuần tự).

---

## 4. Target Project Tree & Danh Mục File Kiểm Chứng Được

### 4.1. Cấu Trúc Tổng Thể

```
pdf_to_docx_converter/
├── .agents/                                # Rules, Skills, Workflows
├── docs/update-spec/                       # 3 Foundation Plans gốc
├── legacy_engines/                         # Các script đơn khối cũ (bảo toàn dual-run)
├── doctools/                               # Gói AI-Native chính thức (< 300 dòng/file)
│   ├── contract/                           # Tầng 1: Models, Codes, Specs
│   ├── infra/                              # Tầng hạ tầng dùng chung (Sandbox, FileStore, Audit)
│   ├── core/                               # Tầng 2 & 3: Lõi thực thi (docx, xlsx, diagram)
│   ├── gates/                              # Tầng 4: Gates kiểm định & diff (docx, xlsx, diagram)
│   ├── operations/                         # Khai báo công cụ MCP & pipelines (docx, xlsx, diagram)
│   ├── resources/                          # Schemas, XSD, Fonts, Sidecars, Profiles
│   ├── adapters/                           # CLI & MCP stdio server
│   ├── registry.py                         # Tool Registry tập trung
│   └── agent_docs.py                       # Anti-drift tool
├── scripts/                                # Oracle runners (Word COM, Excel COM, Draw.io CLI)
├── tests/                                  # Tests độc lập (docx, xlsx, diagram, infra)
├── .importlinter                            # Cấu hình kiểm tra kiến trúc phụ thuộc
└── pyproject.toml
```

---

### 4.2. `contract/` và `infra/` (Dùng Chung Cả 3 Module)

#### Gói `doctools/contract/` (15 files)
- `__init__.py`
- `models.py`: Khai báo `FileRef` (URI mờ, sha256, TTL), `Result`, và `Issue` (chứa trường `engine: Literal["docx", "xlsx", "diagram", "infra"]` và `location: Dict[str, Any]` mở rộng).
- `codes/__init__.py`
- `codes/docx_codes.py`: Họ mã lỗi `E-DOCX-SCHEMA-*`, `E-DOCX-TPL-*`, `E-DOCX-IMMUT-*`, `W-DOCX-LAYOUT-*`.
- `codes/xlsx_codes.py`: Họ mã lỗi `E-XLSX-PKG-*`, `E-XLSX-SHIFT-*`, `E-XLSX-LOCK-*`, `E-XLSX-CACHE-*`, `W-XLSX-CALC-*`.
- `codes/diagram_codes.py`: Họ mã lỗi `E-DGM-SPEC-*`, `E-DGM-SEM-*`, `E-DGM-STYLE-*`, `E-DGM-LAYOUT-*`, `E-DGM-ROUTE-*`, `E-DGM-XML-*`, `E-DGM-RENDER-*`, `W-DGM-SEM-*`, `W-DGM-LAYOUT-*`, `W-DGM-ROUTE-*`, `W-DGM-TEXT-*`.
- `docx/`: `__init__.py`, `inputs.py`, `docspec.py`, `manifest.py`, `outputs.py`.
- `xlsx/`: `__init__.py`, `inputs.py`, `manifest.py`, `tokens.py`, `outputs.py`.
- `diagram/`: `__init__.py`, `inputs.py`, `specs.py`, `tokens.py`, `outputs.py`.

#### Gói `doctools/infra/` (Tách nhỏ Sandbox, 10 files)
- `__init__.py`
- `file_store.py`: Quản lý cấp phát `FileRef`, giải mã URI mờ, dọn dẹp TTL 24h, cô lập theo tenant.
- `audit_log.py`: Logger JSONL che thông tin nhạy cảm, chính sách lưu trữ retention 90 ngày.
- `resource_limits.py`: Cưỡng chế giới hạn dung lượng file, timeout, RAM theo NFR-02.
- `request_context.py`: Trace context chứa `request_id`, `tenant_id`.
- `sandbox/__init__.py`
- `sandbox/base.py`: Lớp cơ sở điều khiển tiến trình con an toàn (cách ly, timeout, tắt mạng, dọn tài nguyên).
- `sandbox/jinja_sandbox.py`: Cô lập môi trường biên dịch template Jinja2 của Word.
- `sandbox/libreoffice_sandbox.py`: Điều khiển tiến trình headless LibreOffice tính toán lại Excel.
- `sandbox/node_sidecar.py`: Điều phối Node.js sidecar `elk_worker.mjs` qua stdin/stdout JSON.
- `sandbox/browser_pool.py`: Bể tiến trình headless browser Edge/Chrome render sơ đồ Draw.io.

---

### 4.3. Module DOCX — Danh Mục 74 Files Logic Kiểm Chứng Được

```
doctools/core/docx/                         # 45 files
├── __init__.py
├── package_io/                             # (4 files)
│   ├── __init__.py, package_reader.py, package_writer.py, part_manager.py
├── schema/                                 # (4 files)
│   ├── __init__.py, schema_helper.py, tag_order_registry.py, element_builder.py
├── template/                               # (8 files)
│   ├── __init__.py, template_linter.py, jinja_normalizer.py, manifest_parser.py
│   ├── style_registry.py, slot_manager.py, variable_extractor.py, validator.py
├── build/                                  # (18 files)
│   ├── __init__.py, jinja_renderer.py, docspec_generator.py, run_consolidator.py
│   ├── paragraph_builder.py, table_builder.py, list_builder.py, section_builder.py
│   ├── image_injector.py, header_footer_builder.py, numbering_manager.py
│   ├── hyperlink_builder.py, bookmark_builder.py, style_applicator.py
│   ├── footnote_builder.py, comment_builder.py, table_styler.py, xml_postprocessor.py
├── merge/                                  # [P1] (5 files)
│   ├── __init__.py, document_merger.py, style_conflict_resolver.py
│   ├── section_break_handler.py, rels_merger.py
├── guards/                                 # (4 files)
│   ├── __init__.py, semantic_guard.py, style_leak_guard.py, namespace_guard.py
├── fields/                                 # [P1] (3 files)
│   ├── __init__.py, field_updater.py, toc_generator.py
├── hygiene/                                # (1 file) xml_cleaner.py
├── text/                                   # (2 files) typography_fixer.py, space_normalizer.py
├── inspect/                                # (2 files) structure_inspector.py, diff_inspector.py
└── patch/                                  # [P1] (3 files) patch_applier.py, block_locator.py, block_replacer.py

doctools/gates/docx/                        # (6 files)
├── __init__.py, dg_01_xml_schema_gate.py, dg_02_tag_order_gate.py
├── dg_03_style_hygiene_gate.py, dg_04_layout_fidelity_gate.py, structural_diff.py

doctools/operations/docx/                   # (4 files)
├── __init__.py, template_ops.py, build_ops.py, inspect_ops.py, pipeline.py

doctools/resources/docx/                    # (5 files)
├── tag_order.generated.json, jinja_allowlist.yaml, builtin_styles.yaml
├── NOTICE, xsd/ecma-376/wml.xsd
```

---

### 4.4. Module XLSX — Danh Mục 63 Files Logic Kiểm Chứng Được

`
doctools/core/xlsx/                         # 37 files (+4 files inspect & template)
├── __init__.py
├── preflight/                              # (3 files)
│   ├── __init__.py, package_inventory.py, tier_classifier.py
├── template/                               # (4 files)
│   ├── __init__.py, template_inspector.py, token_extractor.py
│   └── function_registry.py                # [2.3d] Registry hàm phiên bản độc lập (D-27, FR-32)
├── shift/                                  # (8 files)
│   ├── __init__.py, shift_manager.py, formula_tokenizer.py, range_translator.py
│   ├── named_range_updater.py, conditional_formatting_shifter.py
│   ├── data_validation_shifter.py, table_range_shifter.py
├── mutate/                                 # (6 files)
│   ├── __init__.py, table_expander.py, row_consumer.py, style_cloner.py
│   ├── merge_cell_handler.py, anchor_discoverer.py
├── recalc/                                 # (5 files)
│   ├── __init__.py, recalc_backend.py, cache_writer.py, formula_verifier.py, dep_graph.py
├── build_spec/                             # [P1] (2 files)
│   ├── __init__.py, sheet_generator.py, chart_generator.py (Chịu trách nhiệm tạo Chart DrawingML)
├── inspect/                                # (5 files)
│   ├── __init__.py, sheet_inspector.py, formula_inspector.py
│   ├── formula_profiler.py                 # [2.3b] Phân tích công thức R1C1 & rủi ro tham chiếu
│   ├── format_profiler.py                  # [2.3c] 12 lớp số, Font, viền 4 cạnh, CF, DV, theme color
│   └── coverage_analyzer.py                # [2.3a] Coverage Matrix 5 trạng thái theo Phụ lục I
├── repair/                                 # [P1] (1 file) package_repairer.py
└── hygiene/                                # (1 file) drawingml_sanitizer.py

doctools/gates/xlsx/                        # (18 files) (+3 cổng mở rộng UG-14..16)
├── __init__.py
├── ug_01_drawingml_gate.py, ug_02_formula_syntax_gate.py, ug_03_ref_error_gate.py
├── ug_04_merged_border_gate.py, ug_05_format_leak_gate.py, ug_06_style_parity_gate.py
├── ug_07_content_presence_gate.py, ug_08_semantic_cell_gate.py, ug_09_freeze_panes_gate.py
├── ug_10_print_area_gate.py, ug_11_calc_chain_gate.py, ug_12_package_integrity_gate.py
├── ug_13_cache_value_gate.py               # (Đủ 13 Universal Gates UG-01..13)
├── ug_14_validation_parity_gate.py         # [2.4.3] Phát hiện rơi Data Validation / CF khi clone sheet
├── ug_15_border_consistency_gate.py        # [2.4.3] Phát hiện ô khuyết viền trong khối bảng
├── ug_16_formula_deterministic_anomaly_gate.py # [2.4.3] Bắt lỗi xác định tham chiếu ô rỗng
├── structural_diff.py
└── pg_profiles/unit_test_matrix.py

doctools/operations/xlsx/                   # (5 files)
├── __init__.py, inspect_ops.py, template_ops.py, mutate_ops.py, validate_ops.py, pipeline.py
`

---

### 4.5. Module DIAGRAM — Danh Mục 56 Files Logic Kiểm Chứng Được

```
doctools/core/diagram/                      # 37 files logic
├── __init__.py
├── spec/                                   # (2 files) spec_registry.py, spec_validator.py
├── semantic/                               # (8 files)
│   ├── __init__.py, semantic_linter.py, erd_rules.py, arc_rules.py, seq_rules.py
│   ├── class_rules.py [P1], dfd_rules.py [P1], cross_rules.py, schematic_rules.py [P2]
├── text/                                   # (2 files) text_measurer.py, font_registry.py
├── layout/                                 # (7 files)
│   ├── __init__.py, layout_dispatcher.py, elk_client.py
│   ├── python_layouts/sequence_layout.py, dfd_layout.py [P1], radial_layout.py [P1]
│   ├── python_layouts/schematic_layout.py [P2], python_layouts/fallback_layout.py [P1]
├── router/                                 # (3 files)
│   ├── __init__.py, manhattan_router.py, port_calculator.py, corridor_manager.py [P1]
├── serializer/                             # (3 files)
│   ├── __init__.py, xml_serializer.py, page_manager.py, page_splitter.py [P1]
├── render/                                 # (3 files)
│   ├── __init__.py, render_service.py, browser_pool.py, cli_renderer.py
├── inspect/                                # (1 file) drawio_inspector.py
├── patch/                                  # [P1] (1 file) drawio_patcher.py
└── importers/                              # [P1] (2 files) sql_ddl_importer.py, dbml_importer.py

doctools/gates/diagram/                     # (15 files)
├── __init__.py
├── dg_00_semantic_gate.py, dg_01_xml_gate.py, dg_02_hierarchy_gate.py
├── dg_03_collision_gate.py, dg_04_docking_gate.py, dg_05_label_gate.py
├── dg_06_viewport_gate.py, dg_07_routing_gate.py, dg_08_oracle_gate.py
├── quality_metrics.py
└── pg_profiles/
    ├── __init__.py, pg_erd.py, pg_arc.py, pg_seq.py, pg_dfd.py [P1], pg_schematic.py [P2]

doctools/operations/diagram/                # (4 files)
├── __init__.py, spec_ops.py, build_ops.py, inspect_ops.py, pipeline.py

doctools/resources/diagram/                 # Tài nguyên & Sidecar (1 sidecar script)
├── sidecars/elk_worker.mjs                 # Node.js sidecar chạy elkjs
├── fonts/LiberationSans-Regular.ttf, LiberationSans-Bold.ttf, BeVietnamPro-Regular.ttf
└── style_registry/diagram_tokens.yaml, icon_allowlist.yaml
```

---

### 4.6. Bảng Thuật Toán Bố Cục theo `diagram_type`

| `diagram_type` | Thuật toán bố cục | Đơn vị tính | Cơ chế cổng neo (Port) | Phân tầng thực hiện |
|---|---|---|---|---|
| `erd` | ELK layered / orthogonal | Node sidecar | Cổng cố định theo dòng FK (`FIXED_POS`) | **Phase 3a (MVP)** |
| `architecture` / `network` | ELK phân cấp (`hierarchyHandling=INCLUDE_CHILDREN`) | Node sidecar | Cổng theo hướng cạnh | **Phase 3a (MVP)** |
| `sequence` | **Bố cục Lifeline Python thuần** | Python lõi | Trục Y đơn điệu theo index thông điệp | **Phase 3a (MVP)** |
| `dfd` | **Lưới 5 cột Python thuần (`MX_INV_14`)** | Python lõi | Hướng cố định Ext -> Ingest -> Proc -> Comm -> Cloud | **Phase 3b (P1)** |
| `class` | ELK layered, hướng DOWN | Node sidecar | Cạnh node, ký hiệu UML chuẩn | **Phase 3b (P1)** |
| `radial` | **Bố cục bán kính Python thuần** | Python lõi | Phân số 4 hướng quanh Core Hub | **Phase 3b (P1)** |
| `schematic` | **Bố cục dải ngang Python thuần (`MX_INV_13`)** | Python lõi | Rail nguồn trên đỉnh, GND dưới đáy | **Phase 3b (P2)** |

---

### 4.7. Danh Mục Luật Ngữ Nghĩa DG-00 (`SEM-*`)

| Nhóm | Mã luật | Nội dung kiểm định | Mức độ |
|---|---|---|---|
| **ERD** (MVP) | `SEM-ERD-01` | Khóa ngoại phải trỏ tới (bảng, cột) thực sự tồn tại trong spec | `error` |
| | `SEM-ERD-02` | Kiểu dữ liệu cột FK tương thích kiểu cột đích (cùng họ kiểu) | `error` / `warning` |
| | `SEM-ERD-04` | Không trùng tên bảng; không trùng tên cột trong cùng bảng | `error` |
| | `SEM-ERD-08` | Cột `key=PK` không được `nullable` | `error` |
| **Architecture** (MVP) | `SEM-ARC-01` | Cây lồng nhau không có chu trình; `parent` tồn tại | `error` |
| | `SEM-ARC-02` | Phân cấp hợp lệ (Subnet trong VPC, Pod trong Node/Namespace) | `error` |
| | `SEM-ARC-03..04` | CIDR con nằm trong CIDR cha; các CIDR anh em không chồng lấn | `error` |
| **Sequence** (MVP) | `SEM-SEQ-01..02` | Lifelines tồn tại; message tăng đơn điệu; `reply` sau `call` | `error` |
| | `SEM-SEQ-03..05` | Không gửi tin nhắn trước `create` hoặc sau `destroy`; activation cân bằng | `error` |
| **DFD** [P1] | `SEM-DFD-01..02` | Cấm Store ↔ Store, Ext ↔ Ext; mỗi Process có $\ge 1$ in và $\ge 1$ out | `error` |
| **Schematic** [P2] | `SEM-SCH-01..03` | Dây nguồn cắm đúng rail (+12V, +5V, +3V3, GND); không gắn nhãn text đè dây | `error` |
| **Xuyên loại** (MVP) | `SEM-X-01..04` | 100% ID duy nhất; icon thuộc allow-list; nhãn không chứa payload XSS | `error` |

---

### 4.8. Ánh Xạ Chuẩn Xác 21 Bất Biến `MX_INV_01..21` Sang Gates & Tests (Tuân thủ D-10)

| Mã Bất biến | Tên nguyên tắc / Quy định | Cưỡng chế bởi Gate | Ca kiểm thử Conformance |
|---|---|---|---|
| `MX_INV_01` | **Pure Native Hierarchy**: Cấm UserObject Mermaid/PlantUML thô | `DG-01` (XML Gate) | `DGM-TC-19` |
| `MX_INV_02` | **Minimalist XML**: Thẻ đóng hoàn chỉnh, kết thúc `</root></mxGraphModel>` | `DG-01` (XML Gate) | `DGM-TC-19` |
| `MX_INV_03` | **Container-Level Docking**: Edge chỉ trỏ node cha, cấm cell con | `DG-04` (Docking Gate) | `DGM-TC-17` |
| `MX_INV_04` | **Orthogonal Perimeter Routing**: Dây trực giao, cổng viền chuẩn | `DG-07` (Routing Gate) | `DGM-TC-15` |
| `MX_INV_05` | **Dynamic Geometry Scaling**: Khoảng cách an toàn `min_node_gap >= 60px` | `DG-03` (Collision Gate) | `DGM-TC-12` |
| `MX_INV_06` | **Dual Delivery**: Xuất file gốc `.drawio` và ảnh render PNG/SVG | — (Quy trình Render) | `DGM-TC-22` |
| `MX_INV_07` | **Monochrome Academic Line-Art**: Style đơn sắc nền trắng, viền đen | `DG-01` / Token Registry | `DGM-TC-28` |
| `MX_INV_08` | **Collision-Free Labels & Masks**: Nền trắng ôm khít, hành lang bus $\ge 40$px | `DG-05`, `DG-07` | `DGM-TC-09` |
| `MX_INV_09` | **Multi-Page Single-File**: Đa tab `<diagram name="...">` trong 1 file | `DG-01` (XML Gate) | `DGM-TC-24` |
| `MX_INV_10` | **Schematic Direct Taps**: Dây nguồn đi thẳng từ rail (+12V, +5V, +3V3, GND) | `PG-SCH-01` [Phase 3b] | `DGM-TC-SCH-01` |
| `MX_INV_11` | **Fractional Perimeter Port Anchoring**: Neo phân số khớp tâm đích | `DG-07` (Routing Gate) | `DGM-TC-15` |
| `MX_INV_12` | **Discrete Highway Corridors**: Tuyến bus đi trên trục rời rạc $\ge 30$–$50$px | `DG-07` (Routing Gate) | `DGM-TC-18` |
| `MX_INV_13` | **Schematic Horizontal Strip**: Module xếp dải ngang, rail đỉnh, GND đáy | `PG-SCH-02` [Phase 3b] | `DGM-TC-SCH-02` |
| `MX_INV_14` | **DFD 5-Column Flow**: Luồng trực giao qua 5 cột cố định | `PG-DFD-01` [Phase 3b] | `DGM-TC-06` |
| `MX_INV_15` | **Dynamic Edge Label Width**: Cấm ngắt dòng thủ công, tự wrap theo `labelWidth` | `DG-05` (Label Gate) | `DGM-TC-09` |
| `MX_INV_16` | **4-Tier Stroke Depth Hierarchy**: Khung lớn 3px > IC 2px > Ngoại vi 1.2px > Dây 1px | `PG-ARC-01` | `DGM-TC-13` |
| `MX_INV_17` | **Dedicated Rail Header Legend**: Tách cột Header riêng cho tên rail | `PG-SCH-02` [Phase 3b] | `DGM-TC-SCH-03` |
| `MX_INV_18` | **MCU Egress Waterfall**: Bus từ MCU đi vào hành lang riêng rồi đổ thác | `DG-07` (Routing Gate) | `DGM-TC-18` |
| `MX_INV_19` | **Complete 4-Sided Data Store Enclosure**: Kho dữ liệu DFD đóng kín 4 cạnh | `PG-DFD-01` [Phase 3b] | `DGM-TC-06` |
| `MX_INV_20` | **Snug Mask Bounding**: `labelWidth` tính động ôm sát chữ | `DG-05` (Label Gate) | `DGM-TC-09` |
| `MX_INV_21` | **Zero-Clipping Viewport**: Viewport $\ge \max + 160$px, padding cắt biên đều 25px | `DG-06` (Viewport Gate) | `DGM-TC-21` |

---

### 4.9. Bảng Parity Chuyển Tiếp Từ Legacy (Dual-Run Table)

Để không làm đứt gãy quy trình đang vận hành (`gui.py`, `process_both_reports.py`, `format_reports_pipeline.py`), các script cũ được bảo toàn trong `legacy_engines/` và giữ song song khả năng chạy (Dual-Run) cho đến khi module mới tương ứng đạt 100% acceptance test:

| Script / Chức năng Legacy | Trạng thái chuyển tiếp | Thành phần mới thay thế tương đương | Điều kiện ngắt bỏ Legacy |
|---|---|---|---|
| `process_both_reports.py` (Excel reports) | Giữ nguyên chạy song song | `xlsx.mutate` + `xlsx.recalc` + pipeline | Nghiệm thu xong Phase 2a (đạt 13 UG Gates) |
| `format_reports_pipeline.py` (Excel formatting) | Giữ nguyên chạy song song | `xlsx.mutate` (Row Consumer, Style Cloner) | Nghiệm thu xong Phase 2a |
| `docx_writer.py` (Word document generator) | Giữ nguyên chạy song song | `docx.build_document` (Path A Jinja / Path B DocSpec) | Nghiệm thu xong Phase 1a (đạt 6 DG Gates) |
| `mxgraph_engine.py` (Draw.io XML generator) | Giữ nguyên chạy song song | `diagram.build` + `diagram.validate_drawio` | Nghiệm thu xong Phase 3a (đạt DG-00..08) |
| `gui.py` (Giao diện desktop) | Giữ wrapper gọi legacy | Cung cấp adapter gọi MCP CLI mới | Sau khi hoàn thành toàn bộ Phase 3 |

---

### 4.10. Tests: Danh Mục Đầy Đủ 44 Ca Kiểm Thử DIAGRAM (`DGM-TC-01..44`)

```
tests/diagram/
├── conftest.py
├── unit/                                   # (15 files)
│   ├── test_spec_validator.py              # DGM-TC-01: Schema validation & limits
│   ├── test_semantic_erd.py                # DGM-TC-02: SEM-ERD-01..08
│   ├── test_semantic_class.py              # DGM-TC-03: SEM-CLS-01..06 [P1]
│   ├── test_semantic_sequence.py           # DGM-TC-04: SEM-SEQ-01..08
│   ├── test_semantic_architecture.py       # DGM-TC-05: SEM-ARC-01..08
│   ├── test_semantic_dfd.py                # DGM-TC-06: SEM-DFD-01..04 [P1]
│   ├── test_cross_semantic.py              # DGM-TC-07: SEM-X-01..05
│   ├── test_text_measurer.py               # DGM-TC-08: Pillow advance length & NFC
│   ├── test_snug_label_masks.py            # DGM-TC-09: Snug label bounds (MX_INV_15, 20)
│   ├── test_layout_dispatcher.py           # DGM-TC-11: Dispatcher & fallback
│   ├── test_manhattan_router.py            # DGM-TC-15: Direct taps & fractional ports (MX_INV_11)
│   ├── test_corridor_manager.py            # DGM-TC-18: Discrete corridors & waterfall (MX_INV_12, 18) [P1]
│   ├── test_xml_serializer.py              # DGM-TC-19: Native XML serializer (MX_INV_01, 02)
│   ├── test_monochrome_tokens.py           # DGM-TC-28: Academic line-art style (MX_INV_07)
│   └── test_diagnostics_issues.py          # DGM-TC-34: Issue structure, evidence & suggested_action
├── integration/                            # (10 files)
│   ├── test_build_erd_pipeline.py          # DGM-TC-12: ERD end-to-end (10/50/100 tables)
│   ├── test_build_architecture_pipeline.py # DGM-TC-13: Nested containers & stroke depth (MX_INV_16)
│   ├── test_build_sequence_pipeline.py     # DGM-TC-14: Sequence pipeline & lifelines
│   ├── test_render_dual_delivery.py        # DGM-TC-22: Dual delivery .drawio & PNG (MX_INV_06)
│   ├── test_multi_page_diagram.py          # DGM-TC-24: Multi-page packaging (MX_INV_09)
│   ├── test_inspect_roundtrip.py           # DGM-TC-25: Inspect & anchor stability
│   ├── test_patch_diagram.py               # DGM-TC-26: Incremental patch & pinned nodes [P1]
│   ├── test_importers.py                   # DGM-TC-27: SQL DDL & DBML importers [P1]
│   ├── test_cross_engine_fileref.py        # DGM-TC-39: Handoff FileRef ảnh sang Docx/Xlsx Engine
│   └── test_large_spec_multi_page.py       # DGM-TC-42: Spec lớn tự chia trang theo bounded context [P1]
├── differential/                           # (3 files)
│   ├── test_elk_determinism.py             # DGM-TC-10: ELK determinism (đa tiến trình, đa nền tảng)
│   ├── test_drawio_oracle.py               # DGM-TC-23: Headless runner vs Draw.io CLI Oracle (DG-08)
│   └── test_end_to_end_determinism.py      # DGM-TC-32: Determinism toàn pipeline với golden XML
├── conformance/                            # (5 files)
│   ├── test_docking_invariants.py          # DGM-TC-17: Container-level docking (MX_INV_03)
│   ├── test_all_dg_gates.py                # DGM-TC-20: Kiểm thử độc lập từng cổng DG-01..DG-07
│   ├── test_viewport_clipping.py           # DGM-TC-21: Zero-clipping viewport & padding (MX_INV_21)
│   ├── test_resource_limits.py             # DGM-TC-33: NFR-02 limits & CI exit codes
│   └── test_invariant_meta_coverage.py     # DGM-TC-43: Meta-test bảo đảm 100% MX_INV có gate/test
├── security/                               # (3 files)
│   ├── test_label_xss_injection.py         # DGM-TC-29: Chặn script, iframe, javascript: trong nhãn
│   ├── test_sidecar_sandbox.py             # DGM-TC-30: Cách ly Node sidecar & browser pool
│   └── test_fileref_and_roots.py           # DGM-TC-31: Cô lập tenant, chặn path traversal ngoài roots
├── property/                               # (1 file)
│   └── test_spec_fuzzing.py                # DGM-TC-41: Fuzzing DiagramSpec ngẫu nhiên bằng Hypothesis
├── oracle/                                 # (2 files)
│   ├── test_desktop_waypoint_freeze.py     # DGM-TC-16: Mở trên Draw.io thật, kiểm tra waypoint freeze
│   └── test_consumer_matrix.py             # DGM-TC-44: Mở trên Draw.io Desktop, diagrams.net, VS Code
└── quality/                                # (5 files)
    ├── test_perf_benchmark.py              # DGM-TC-35: Đo lường p95 (<1s cho 50 node)
    ├── test_audit_masking.py               # DGM-TC-36: Kiểm tra che thông tin nhạy cảm trong log
    ├── test_vietnamese_typography.py       # DGM-TC-37: Hiển thị đúng 100% glyph dấu tiếng Việt
    ├── test_quality_metrics_reporting.py   # DGM-TC-38: Báo cáo trung thực số giao cắt (không zero-crossing)
    └── test_business_uat_corpus.py         # DGM-TC-40: UAT trên corpus sơ đồ nghiệp vụ thực tế
```

---

## 5. Bảng Công Cụ MCP Chính Thức (Chuẩn Tiền Tố Namespace)

### 5.1. Module DOCX (`docx.*`, 8 MVP + 2 P1)

| Tên công cụ MCP | Ưu tiên | File khai báo | Mục đích |
|---|---|---|---|
| `docx.lint_template` | MVP | `operations/docx/template_ops.py` | Kiểm định template, phát hiện tag vỡ, unclosed tags, style rác |
| `docx.normalize_template` | MVP | `operations/docx/template_ops.py` | Ghép các run rời rạc, làm sạch XML Jinja |
| `docx.register_template` | MVP | `operations/docx/template_ops.py` | Đăng ký template vào kho kèm manifest |
| `docx.list_templates` | MVP | `operations/docx/template_ops.py` | Liệt kê danh mục template hợp lệ |
| `docx.get_template_manifest` | MVP | `operations/docx/template_ops.py` | Lấy chi tiết slot, biến và ràng buộc của template |
| `docx.build_document` | MVP | `operations/docx/build_ops.py` | Dual-path builder: Path A (Jinja) hoặc Path B (DocSpec) sinh file `.docx` |
| `docx.inspect_structure` | MVP | `operations/docx/inspect_ops.py` | Trích xuất cây cấu trúc (đoạn, bảng, run) kèm anchor |
| `docx.validate` | MVP | `operations/docx/inspect_ops.py` | Chạy 6 Gates kiểm tra tính hợp lệ OOXML và layout |
| `docx.merge` | P1 | `operations/docx/build_ops.py` | Trộn nhiều tài liệu DOCX, giải quyết xung đột style và section break |
| `docx.patch` | P1 | `operations/docx/inspect_ops.py` | Thay thế các khối nội dung theo anchor mà không sửa toàn file |

### 5.2. Module XLSX (xlsx.*, 14 MVP + 2 P1 + 1 P2)

| Tên công cụ MCP | Ưu tiên | File khai báo | Mục đích |
|---|---|---|---|
| xlsx.preflight | MVP | operations/xlsx/inspect_ops.py | Phân tích Package Inventory, xếp hạng Fidelity Tier T1..T4 |
| xlsx.inspect | MVP | operations/xlsx/inspect_ops.py | Đọc cấu trúc bảng, công thức, merged cells kèm tọa độ (4 levels) |
| xlsx.coverage_report | MVP | operations/xlsx/inspect_ops.py | Báo cáo ma trận bao phủ 5 trạng thái (READ_WRITE, READ_ONLY, PRESERVE_ONLY, DETECT_ONLY, UNSUPPORTED) |
| xlsx.analyze_formulas | MVP | operations/xlsx/inspect_ops.py | Phân tích công thức, gom nhóm R1C1, đồ thị phụ thuộc, phát hiện rủi ro W-FORMULA-EMPTY-CELL-REF |
| xlsx.describe_formats | MVP | operations/xlsx/inspect_ops.py | Mô tả định dạng 12 lớp số, Font phân vùng, 4 cạnh viền, CF 18 loại, DV 7 loại, màu theme |
| xlsx.function_catalog | MVP | operations/xlsx/inspect_ops.py | Tra cứu registry hàm phiên bản, tra trạng thái hỗ trợ đo lường qua ma trận Fx vi sai |
| xlsx.lint_template | MVP | operations/xlsx/template_ops.py | Kiểm tra template, phát hiện thiếu dải tổng, công thức sai |
| xlsx.register_template | MVP | operations/xlsx/template_ops.py | Đăng ký template kèm manifest |
| xlsx.list_templates | MVP | operations/xlsx/template_ops.py | Liệt kê danh mục template Excel khả dụng |
| xlsx.get_template_manifest | MVP | operations/xlsx/template_ops.py | Trích xuất dải ô, quy tắc mở rộng và design tokens |
| xlsx.mutate | MVP | operations/xlsx/mutate_ops.py | Chèn dữ liệu, mở rộng bảng qua Shift Manager, đồng bộ merged-cells |
| xlsx.recalc | MVP | operations/xlsx/mutate_ops.py | Tính toán lại công thức (xcel_com / libreoffice) + tiêm cache bằng lxml |
| xlsx.validate | MVP | operations/xlsx/validate_ops.py | Chạy 16 Universal Gates (UG-01..16) + PG Profiles |
| xlsx.diff | MVP | operations/xlsx/validate_ops.py | So khớp cấu trúc XML trước và sau đột biến |
| xlsx.build | P1 | operations/xlsx/mutate_ops.py | Sinh workbook từ XlsxSpec thuần; **chịu trách nhiệm tạo mới Chart DrawingML** |
| xlsx.repair | P1 | operations/xlsx/validate_ops.py | Sửa chữa hư hỏng nhẹ trong package (thiếu <calcPr>, lỗi quan hệ) |
| xlsx.export_legacy_xls | P2 | operations/xlsx/mutate_ops.py | Chuyển đổi định dạng cổ điển .xls (Excel 97-2003) qua LibreOffice |

### 5.3. Module DIAGRAM (`diagram.*`, 6 MVP + 3 P1)

| Tên công cụ MCP | Ưu tiên | File khai báo | Mục đích |
|---|---|---|---|
| `diagram.get_schema` | MVP | `operations/diagram/spec_ops.py` | Trả JSON Schema và ví dụ theo `diagram_type` |
| `diagram.validate_spec` | MVP | `operations/diagram/spec_ops.py` | Xác thực schema Pydantic và chạy Gate Ngữ nghĩa DG-00 (fail-closed) |
| `diagram.build` | MVP | `operations/diagram/build_ops.py` | DiagramSpec → `.drawio` (Pha 1: đo chữ, bố cục ELK/Python, router, serializer) |
| `diagram.validate_drawio` | MVP | `operations/diagram/inspect_ops.py` | Chạy chuỗi cổng `DG-01..DG-07` và PG Profiles trên file `.drawio` |
| `diagram.inspect` | MVP | `operations/diagram/inspect_ops.py` | Đọc cấu trúc sơ đồ cho AI: trang, node, edge, anchor ổn định |
| `diagram.render` | MVP | `operations/diagram/build_ops.py` | Pha 2: Render PNG/SVG từ `.drawio` qua headless browser / Draw.io CLI |
| `diagram.patch` | P1 | `operations/diagram/inspect_ops.py` | Sửa file có sẵn theo thao tác khai báo, bố cục tăng dần giữ nguyên node ghim |
| `diagram.import_source` | P1 | `operations/diagram/build_ops.py` | Nguồn có cấu trúc (SQL DDL, DBML) → DiagramSpec tất định |
| `diagram.list_style_registry` | P1 | `operations/diagram/spec_ops.py` | Liệt kê token kiểu dáng và icon cloud hợp lệ |

---

## 6. Lộ Trình Triển Khai Chi Tiết ("Làm Đến Đâu Xong Đến Đó")

```
┌────────────────────────────────────────────────────────────────────────┐
│ PHASE 0: Nền tảng, Early Spikes, Hạ tầng dùng chung & Dual-Run Legacy  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼
┌─────────────────────────┬──────────────────────────────────────────────┐
│ PHASE 1a: DOCX MVP      │ 1b: DOCX P1 (Merge, Patch, Fields)           │
└─────────────────────────┴──────────────────────────────────────────────┘
                                    ▼
┌─────────────────────────┬──────────────────────────────────────────────┐
│ PHASE 2a: XLSX MVP      │ 2b: XLSX P1/P2 (Chart Generation, Repair)    │
└─────────────────────────┴──────────────────────────────────────────────┘
                                    ▼
┌─────────────────────────┬──────────────────────────────────────────────┐
│ PHASE 3a: DIAGRAM MVP   │ 3b: DIAGRAM P1/P2 (DFD, Radial, Schematic)   │
└─────────────────────────┴──────────────────────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ PHASE 4: Audit Toàn Diện, CI/CD Hardening & Release Gate (Plan Riêng)  │
└────────────────────────────────────────────────────────────────────────┘
```

### Chi Tiết Từng Giai Đoạn

- **Phase 0 — Nền Tảng, Early Spikes & Hạ Tầng Dùng Chung**:
  - **Phase 0.1 — Chốt Thiết Kế Nền Tảng**:
    - Thiết lập `doctools/infra/file_store.py` (Local filesystem, `tenant_id` abstract, TTL 24h).
    - Thiết lập `doctools/infra/audit_log.py` (JSONL che dữ liệu nhạy cảm, retention 90 ngày).
    - Cấu hình Self-hosted Windows runner cho CI hằng ngày (chạy Word COM, Excel COM, Draw.io).
    - Thiết lập `import-linter` và `test_file_size_limits.py` cưỡng chế kiến trúc.
    - Bảo toàn `legacy_engines/` chạy song song (Dual-Run) bảo vệ `gui.py` và các script báo cáo hiện hành.
  - **Phase 0.2 — Chạy Sớm Các Spikes Rủi Ro Cao (Chặn Đường)**:
    - `DGM-S5`: Mở file trên Draw.io thật làm thủ công 1 lần, kiểm tra waypoint freeze khi di chuyển node và Reset Edge, chốt `routing_mode` (ưu tiên `orthogonalEdgeStyle`, fallback `polyline_with_points`).
    - `DGM-S6`: Đo ground truth độ rộng nhãn thật trên Draw.io so với Pillow advance length ở đúng pixel, chốt biên an toàn.
    - `DGM-S7`: ELK tất định cross-process và cross-OS.
    - `DGM-S9`: So khớp stencil icon và bảng giữa `mxClient` runner vs Draw.io thật.
    - Word COM Spike: Chốt `updateFields` và đóng gói XSD ECMA-376 nguyên bản kèm NOTICE.
    - Excel COM vs LibreOffice Spike: Chốt backend tính toán và ma trận consumer đọc cache.
  - **Phase 0.3 — Khung Sườn Chung**:
    - Dựng `doctools/contract/models.py` (`FileRef`, `Result`, `Issue`), `doctools/infra/sandbox/` (tách 5 runners), `core/guards.py`, `core/errors.py`.

- **Phase 1 — Module DOCX (Word Processing Engine)**:
  - **Phase 1.1 — Module DOCX MVP (Core Builder, Template Engine & Quality Gates)**:
    + `1.1.0`: Schema Helper, Tag Order Registry ECMA-376 (`tag_order.generated.json`), và Package IO (`package_reader`, `package_writer`).
    + `1.1.1`: Template Linter & Run Consolidator (`docx.lint_template`, `docx.normalize_template`, hàn gắn run Jinja bị băm).
    + `1.1.2`: Template Registry & Inventory (`docx.register_template`, `docx.list_templates`, `docx.get_template_manifest`).
    + `1.1.3`: Path A Template Renderer (`docx.render_template`, Jinja2 sandbox, rào chắn OOXML `cantSplit`, `tblHeader`, `vAlign`).
    + `1.1.4`: Path B DocSpec Builder (`docx.build_from_spec`, JSON spec compiler, paragraph/table/image builders).
    + `1.1.5`: Structure Inspector & 6 Quality Gates (`docx.inspect_structure`, `docx.validate`: DG-01..DG-04, structural diff).
  - **Phase 1.2 — Module DOCX P1 (Merge, Patch, Fields & Sanitization)**:
    + `1.2.0`: Document Merger (`docx.merge`, style conflict resolver, section breaks).
    + `1.2.1`: Document Patcher (`docx.patch`, block locator, surgical replacement).
    + `1.2.2`: Dynamic Fields & TOC (`field_updater`, `toc_generator`).
    + `1.2.3`: Document Hygiene & Sanitization (`xml_cleaner`, macro isolation, strip tracked changes).

- **Phase 2 — Module XLSX (Spreadsheet Processing Only)**:
  - **Phase 2.1 — Module XLSX MVP (Preflight, Shift, Mutate, Gates & Recalc)**:
    + 2.1.1: Preflight Scanner & Package Inventory (xlsx.preflight, xếp hạng Fidelity Tier T1..T4, phát hiện DrawingML, macro, charts, bảng, ô gộp, công thức) [ĐÃ HOÀN THÀNH — Commit 94a7382].
    + 2.1.2: Template Registry, Manifest Parser & Static Linter (xlsx.register_template, xlsx.lint_template, xlsx.list_templates, kiểm định locked_zones, 
eference_sheet, phát hiện placeholder <...>, cảnh báo W-TPL-SAMPLE-ROW và #REF!) [ĐÃ HOÀN THÀNH — Commit 770bf62].
    + 2.1.3: AST Formula Shift Manager (ShiftManager, AST Tokenizer openpyxl.formula.Tokenizer, dịch toán hạng ô/dải liên sheet 2 chiều, bảo toàn 100% chuỗi/tên hàm, dời và mở rộng merged_cells, hỗ trợ 	able_aware vs xcel_native, bắt E-SHIFT-UNSUPPORTED-FORM) [ĐÃ HOÀN THÀNH — Commit 35d0cc4].
    + 2.1.4: Mutate Expander & Style Cloner (xlsx.mutate, MutationSpec schema, nhân bản dòng mẫu Prototype Row theo 14 bất biến E1–E14, ép kiểu chuỗi @ giữ số 0 đầu, ghi an toàn ô gộp Top-Left và đồng bộ viền 4 phía, cưỡng chế vùng khóa locked_zones E-XLSX-LOCK-001).
    + 2.1.5: 13 Universal Gates & Quality Validator (xlsx.validate, xlsx.inspect, xlsx.diff, bộ 13 cổng UG-01..UG-13, đối soát diff cấu trúc XML, bảo vệ DrawingML, báo cáo diagnostics chi tiết có location và vidence).
    + 2.1.6: Recalc Engine & Cache Writer (xlsx.recalc, điều phối headless LibreOffice / Excel COM, ghi giá trị cache <v> bằng lxml write_cached theo D-12, cờ calc_on_open uto, kiểm định UG-13).
  - **Phase 2.2 — Module XLSX P1/P2 (Path B Spec Builder, Repair & Legacy Export)**:
    + 2.2.1: Native Chart & Spec Builder (xlsx.build, sinh Chart DrawingML native từ XlsxSpec thuần, định dạng design tokens).
    + 2.2.2: Workbook Auto-Repair (xlsx.repair, sửa lỗi quan hệ package, khôi phục <calcPr>, sửa dải tham chiếu mồ côi).
    + 2.2.3: Legacy Converter (xlsx.export_legacy_xls, xuất file Excel 97-2003 .xls qua LibreOffice headless, P2).
  - **Phase 2.3 — Module XLSX Comprehensive Inspect & Knowledge Catalog (Đọc & Nhìn Toàn Diện — Tham chiếu [xlsx-engine-phase-2.3-2.4-plan.md](docs/update-spec/xlsx-engine-phase-2.3-2.4-plan.md))**:
    + 2.3a: Inspect Lõi & Coverage Report (xlsx.inspect(level) 4 cấp: summary, structure, objects, cells, RLE đối tượng, xlsx.coverage_report ma trận 5 trạng thái theo Phụ lục I). Ánh xạ: FR-30, FR-36, D-26, D-28. Tests: TC-47, TC-54, TC-58.
    + 2.3b: Formula Analyzer (xlsx.analyze_formulas, gom nhóm R1C1 chuẩn hóa, đồ thị phụ thuộc chéo sheet, chu trình W-FORMULA-CIRCULAR, cảnh báo xác định W-FORMULA-EMPTY-CELL-REF từ bài học EV-15). Ánh xạ: FR-31, D-26. Tests: TC-48, TC-49, TC-61.
    + 2.3c: Format Describer (xlsx.describe_formats, 12 lớp số, Font phân vùng, 4 cạnh Border, CF 18 loại, DV 7 loại, giải mã theme/indexed). Ánh xạ: FR-33, D-26. Tests: TC-52, TC-53, TC-60.
    + 2.3d: Function Registry & Ma Trận Fx Vi Sai (xlsx.function_catalog, registry riêng có phiên bản độc lập openpyxl, trạng thái hỗ trợ đo lường vi sai qua Excel COM vs LibreOffice runner). Ánh xạ: FR-32, D-27. Tests: TC-50, TC-51.
  - **Phase 2.4 — Module XLSX Enforcement, Parity Cloner & Controlled Mutation (Kiểm Soát & Sửa Đổi An Toàn — Tham chiếu [xlsx-engine-phase-2.3-2.4-plan.md](docs/update-spec/xlsx-engine-phase-2.3-2.4-plan.md))**:
    + 2.4.1: Bộ Test Hồi Quy Cho 3 Lỗi Thật EV-15 (Failing tests trước khi sửa: TC-59 rơi DV khi copy sheet, TC-60 khuyết viền hair, TC-61 công thức trừ ô rỗng -AA7). Ánh xạ: EV-15. Tests: TC-59, TC-60, TC-61.
    + 2.4.2: Sheet Cloner Parity Engine (Khắc phục lỗ hổng copy_worksheet: sao chép độc lập Data Validation, CF, ảnh, chart, bảng, view; tự động trỏ lại công thức tự tham chiếu sheet nguồn). Ánh xạ: D-23, FR-29, FR-35. Tests: TC-59, TC-41.
    + 2.4.3: Bộ Cổng Kiểm Định Mở Rộng — Chỉ Phát Hiện, Không Sửa Ngầm (UG-14 rơi DV/CF, UG-15 khuyết viền bảng, UG-16 công thức toán tham chiếu ô rỗng; quy tắc suy đoán ngữ nghĩa gắn nhãn stimated và non-blocking). Ánh xạ: UG-14, UG-15, UG-16. Tests: TC-59, TC-60, TC-61.
    + 2.4.4: Table Border Repair Bằng Policy Tường Minh (Tuân thủ 'Template là chân lý', chỉ vá khi có chỉ định tường minh order_policy: inherit_prototype từ Prototype Row, diff ghi declared). Ánh xạ: D-04, FR-06, FR-14. Tests: TC-60, TC-44.
    + 2.4.5: Extended Write Catalog (Schema Pydantic cho set_format, set_validation, set_conditional_format, 	able_resize, round-trip tests). Ánh xạ: FR-35. Test: TC-55.
    + 2.4.6: Benchmark A/B Framework & Thoát Khỏi Tool (Escape Rate) (Chốt Q-18 & Q-19, so sánh 	ool_only vs 	ool_plus_shell, N >= 3 lần chạy sạch, báo cáo giá trị trung bình & phương sai theo mẫu Phụ lục H). Ánh xạ: D-25, D-30, FR-37, Q-18, Q-19. Tests: TC-56, TC-57.

- **Phase 3 — Module DIAGRAM (Technical Diagram Only)**:
  - **Phase 3a (Diagram MVP)**: Spec Registry, DG-00 Semantic Linter (ERD, Architecture, Sequence), Text Measurer (Pillow advance length, NFC), Layout Dispatcher + ELK sidecar, Manhattan Router (waypoint tường minh), XML Serializer (`lxml`, đa trang), Pha 2 Render Service, DG-01..DG-08 & PG Profiles, 6 công cụ MCP `diagram.*`. Nghiệm thu sạch theo Diagram Mục 7.3.
  - **Phase 3b (Diagram P1/P2)**: DFD 5 cột (`MX_INV_14`, `19`), Class, Radial hub-and-spoke, `diagram.patch`, `diagram.import_source`, `diagram.list_style_registry`, và Sơ đồ Mạch điện Schematic (`MX_INV_10`, `13`, `17`, P2) kèm tài liệu đặc tả **Diagram Spec v1.1**.

- **Phase 4 — Audit Toàn Diện & Release Gate (Kế Hoạch Riêng)**:
  - Kế hoạch Audit chi tiết sẽ được thiết lập độc lập trong quá trình triển khai thực tế sau khi được yêu cầu và phê duyệt bởi chủ Plan.

---

## 7. Quyết Định Kỹ Thuật Đã Chốt (Approved Decisions SSOT)

Toàn bộ các câu hỏi mở đã được **CHỐT CHÍNH THỨC 100%**:

| # | Câu hỏi / Hạng mục | Quyết định đã chốt | Cơ sở kỹ thuật & Hành động triển khai |
|---|---|---|---|
| **1** | Hợp đồng `FileRef` | **ĐÃ CHỐT** | Thống nhất dùng `{uri, sha256, size, mime, expires_at}` với URI mờ `resource://<engine>/files/{id}`. Không truyền byte hay base64 nội tuyến. |
| **2** | Cấu trúc Phân tầng | **ĐÃ CHỐT** | Cưỡng chế kiến trúc 5 tầng bằng `import-linter` trong CI. |
| **3** | Phân chia Operations | **ĐÃ CHỐT** | Tách thành các file operation chuyên biệt theo cụm nghiệp vụ (< 300 dòng/file). |
| **4** | Giấy phép XSD Word | **ĐÃ CHỐT** | Đóng gói nguyên bản trong `resources/docx/xsd/` kèm file `NOTICE`. Sinh `tag_order.generated.json` bằng script và commit vào repo để build offline. |
| **5** | Ưu tiên Template Excel | **ĐÃ CHỐT** | `Report5_Unit Test-template.xlsx` là benchmark số 1 cho profile `unit_test_matrix`. Corpus Shift/Preflight sử dụng 10–20 templates đa dạng. |
| **6** | Backend Tính toán Excel | **ĐÃ CHỐT** | Ưu tiên `excel_com` khi yêu cầu rõ và làm Oracle trong CI; tự động Fallback sang `libreoffice` khi môi trường không có Microsoft Excel. |
| **7** | Thành phần lạ Preflight | **ĐÃ CHỐT** | Từ chối mặc định (Tier T3). Chỉ tiếp tục khi người dùng duyệt tường minh qua `approved_deviations`, kèm diff cảnh báo thành phần bị lược bỏ. |
| **8** | Dòng mẫu Prototype Row | **ĐÃ CHỐT** | Mặc định **consume**: ghi đè dòng mẫu bằng bản ghi đầu, nhân bản cho các bản ghi tiếp theo. Nếu $N=0$, giữ 1 dòng trống cùng kiểu để dải tổng không co về 0 (chống `#REF!`). Manifest được phép ghi đè (keep/remove). |
| **9** | Chính sách cờ `calc_on_open` | **ĐÃ CHỐT** | Áp dụng chế độ `auto` (bật `fullCalcOnLoad="1"` khi dùng LibreOffice; tắt khi dùng Excel COM). Chấp nhận thông báo nhắc lưu khi mở/đóng Excel. |
| **10** | Dual-delivery `.xls` | **ĐÃ CHỐT** | Xếp vào **P2** (`xlsx.export_legacy_xls`), chuyển đổi qua LibreOffice headless khi có yêu cầu nghiệp vụ. |
| **11** | Ranh giới Schematic | **ĐÃ CHỐT** | Giữ lại trong Diagram Engine vì cùng chung định dạng `.drawio`, nhưng xếp vào **Phase 3b (P2)** kèm một tài liệu đặc tả riêng (**Diagram Spec v1.1**). |
| **12** | Ranh giới Tạo Chart | **ĐÃ CHỐT** | `xlsx.build` (P1) chịu trách nhiệm tạo mới Chart DrawingML native; `xlsx.mutate` (MVP) chịu trách nhiệm relink dải ô. Docx chỉ chèn ảnh/chart qua `FileRef`. Diagram kiên quyết không ghi OOXML. |
| **13** | Loại Sơ đồ MVP | **ĐÃ CHỐT** | MVP tập trung 3 loại: **ERD**, **Architecture/Network**, và **Sequence**. DFD là mục đầu tiên của P1 (Python layout thuần, không cần Node). |
| **14** | Hành vi Waypoint (`routing_mode`) | **ĐÃ CHỐT** | Spike S5 thử nghiệm 3 mode trên Draw.io thật. Ưu tiên mode giữ được `orthogonalEdgeStyle`. Nếu thất bại, chuyển sang `polyline_with_points`. Router tự tính tọa độ trực giao nên polyline hiển thị đồng nhất. |
| **15** | Chính sách Icon Cloud | **ĐÃ CHỐT** | Chỉ allow-list tên shape có sẵn của Draw.io (`mxgraph.aws4.*`, `mxgraph.gcp2.*`), không tự đóng gói file SVG hãng để tránh rủi ro bản quyền. |
| **16** | Runner CI Tự Host | **ĐÃ CHỐT** | Cung cấp 1 runner Windows tự host dùng chung cho Word, Excel COM và Draw.io CLI. S5 chạy thủ công 1 lần ở Phase 0 và ghi lại kết quả. |
| **17** | Lưu trữ & Tenant (Phase 0) | **ĐÃ CHỐT** | Hệ thống file cục bộ, `tenant_id` có sẵn trong interface (mặc định `local`), `FileStore` là interface trừu tượng sẵn sàng cho object store. |
| **18** | Chính sách Retention (Phase 0) | **ĐÃ CHỐT** | `FileRef` TTL 24 giờ, audit log JSONL (đã che dữ liệu nhạy cảm) lưu trữ 90 ngày. |
| **19** | Antigravity Roots (Phase 0) | **ĐÃ CHỐT** | Chạy spike nửa ngày với MCP mẫu; phương án dự phòng là allow-list đường dẫn cục bộ trong `core/guards.py`. |
| **20** | Mô hình Phân phối & Giấy phép | **ĐÃ CHỐT** | Giữ giấy phép sạch: `elkjs` chạy tiến trình riêng cách ly (EPL-2.0), `docxtpl` import động. |
| **21** | Linux Container | **ĐÃ CHỐT** | Thiết lập container Linux ngay từ đầu cho CI hằng ngày; dev trên Windows. |
