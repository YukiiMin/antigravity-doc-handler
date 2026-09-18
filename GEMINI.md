# ZSCORT Project — Critical Rules Quickref

> **Auto-loaded every session. Read this FIRST after any `{{ CHECKPOINT N }}` signal.**
> Full rules: `.agents/rules/` | Architecture: `ARCHITECTURE.md` | Task state: `.agent_scratchpad.md`

---

## CHECKPOINT Recovery Protocol (BẮT BUỘC)

Khi nhận `{{ CHECKPOINT N }}` signal:
1. **Đọc file này** (GEMINI.md) trước tiên — xác nhận invariants đã nạp.
2. **Đọc `.agent_scratchpad.md`** — lấy current goal + remaining TODOs.
3. Không action ngay — xác nhận xong mới trả lời user.

---

## KEYWORD TRIGGER PROTOCOL

Khi bắt đầu làm bất kỳ tác vụ nào thuộc domain dưới đây, **BẮT BUỘC đọc rule chi tiết tương ứng TRƯỚC KHI viết code**:

| Khi bạn đụng đến... | Doc đọc trước |
|---|---|
| ABAP SQL, SELECT, FOR ALL ENTRIES, Buffer tables | `rule_abap_atc_and_clean_code_standards.md` |
| RAP Message, T100, i18n ABAP, String template | `rule_abap_rap_messages_standards.md` |
| RAP Query Provider (`IF_RAP_QUERY_PROVIDER`), Custom Entity | `rule_abap_rap_query_standards.md` |
| CDS View Entity, BDEF, SRVD, DCLS, DDLX | `rule_cds_data_definitions.md` |
| SAP object types, TADIR whitelist, Compare/Source view | `rule_dev_objects_classification.md` |
| AI Review, Gemini model, SICF handler, API key | `rule_ai_review_standards.md` + `rule_ai_integration_resilience.md` |
| Monaco Editor, Diff view, iframe | `rule_monaco_iframe.md` |
| Fiori deploy, PFCG, FLP, UI5 compatibility | `rule_sap_fiori_deploy_and_flp_security.md` |
| i18n, `.properties` file, Unicode escape | `rule_ui5_i18n.md` |
| UI5 Controller, OData call, fetchJson, JSONModel | `rule_ui5_controller_linter_standards.md` |
| TR Tree, CTS hierarchy, SE09, TADIR object resolution | `rule_sap_cts_tr_hierarchy.md` |
| Search screen, empty query validation | `rule_search_validation.md` |
| Technical diagram, ERD, DB schema | `rule_technical_diagram_standards.md` + `rule_database_erd_standards.md` |
| Document converter, PDF export | `rule_decoupled_document_converter.md` |
| Excel Template, openpyxl, Spreadsheet Data Injection, Matrix UX | `rule_excel_template_preservation_and_ux.md` |
| Docx/Excel QA, unified_qa_diagnostic, OpenXML, DrawingML, Table borders | `rule_enterprise_document_and_spreadsheet_qa.md` |
| `/learn` invoked, writing new Rule, writing new Skill | `rule_learning_and_skill_authoring.md` |
| git commit, git push | `rule_git_workflow.md` |

---

## ABAP Critical Invariants

| # | Rule | Vi phạm phổ biến |
|---|---|---|
| A1 | **FOR ALL ENTRIES driver table type = bảng ĐÍCH** | Dùng `e071-obj_name` (CHAR120) drive TADIR → type mismatch. Tạo `ty_tadir_fae` với `TYPE tadir-obj_name` (CHAR40) |
| A2 | **FOR ALL ENTRIES: NO ORDER BY** | Sort internal table sau SELECT: `SORT lt_... BY ...` |
| A3 | **SELECT partial columns vào full DB type** | Dùng `INTO CORRESPONDING FIELDS OF TABLE`, không phải `INTO TABLE` |
| A4 | **Inline `@(\|...\|)` trong SQL WHERE không hợp lệ** | Tính sẵn: `DATA lv_like TYPE vrsd-objname. lv_like = |{ name }%|.` rồi `WHERE field LIKE @lv_like` |
| A5 | **NO explanatory comments trong ABAP class** | Chỉ cho phép `"#EC CI_SGLSELECT`, `"#EC CI_BUFFJOIN`, `"#EC NEEDED`, section label không giải thích |
| A6 | **Buffered tables (TADIR, T100, TDEVC, USR02, ENLFDIR)** | SELECT SINGLE với full PK → tận dụng buffer. Fuzzy/multi-row → `"#EC CI_SGLSELECT` |
| A7 | **Thay FOR ALL ENTRIES bằng INNER JOIN** | Khi E070+E071 (không bị buffer) → `FROM e070 AS h INNER JOIN e071 AS o ON ...` |
| A8 | **Nghiêm cấm SELECT \*** | Luôn liệt kê trường tường minh |
| A9 | **Inline `DATA()` không visible qua nested SELECT scope** | Khai báo explicit ở đầu method: `DATA lt_... TYPE STANDARD TABLE OF e071 WITH DEFAULT KEY.` |
| A10 | **RAP Query: `IF_RAP_QUERY_PROVIDER`** | Không ORDER BY trong FAE; tách inline DATA() ra explicit; CLEAR table trước khi dùng lại |
| A11 | **ABAP Comments: English only, no Vietnamese, no explanatory, no numbered steps** | Chỉ comment khi documenting non-obvious architectural workarounds |
| A12 | **String template không được multiline** | Không span `|...|` qua nhiều dòng. Dùng `&&` để nối |
| A13 | **CDS View Entity: không dùng `IN (...)` literal list** | Dùng chained `OR`: `where (object = 'PROG' or object = 'CLAS')` |
| A14 | **CDS/BDEF: KHÔNG dùng `"` làm comment** | Chỉ dùng `/* ... */` trong CDS. `"` là invalid trong CDS grammar |
| A15 | **TADIR: luôn filter `delflag`** | `AND ( delflag IS NULL OR delflag = ' ' )` khi query tadir |
| A16 | **RAP UNION ALL: phải khai báo association ở MỌI branch** | Thiếu 1 branch → compiler báo `_Assoc is unknown column` |
| A17 | **Kernel deep struct: dùng dynamic component lookup** | `ASSIGN COMPONENT 'ABAPTXT255' OF STRUCTURE ... TO ...` với fallback candidates |
| A18 | **MSAG Companion File** | Khi tạo/sửa `<NAME>.msag.xml`, BẮT BUỘC tạo/cập nhật `<NAME>.md` kèm format TSV để copy nhanh vào SE91/ADT (hỗ trợ placeholder `&1`-`&4` và version <=39 chars) |

---

## UI5 Critical Invariants

| # | Rule | Vi phạm phổ biến |
|---|---|---|
| U1 | **`fetchJson()` LUÔN trả về array** | `oData.As4date` → undefined. Phải `aData[0]` hoặc `.find(n => n.NodeType === 'TR')` |
| U2 | **Custom RAP Entity (ZCE_\*): dùng `$filter`** | Không dùng read-by-key `EntitySet('KEY')`. Dùng `?$filter=Trkorr eq '...'&$top=50` |
| U3 | **OData filter: KHÔNG `encodeURIComponent()`** | Encode `'` → `%27`, phá syntax. Chỉ `.replace(/'/g, "''")` |
| U4 | **JSONModel `onInit`: khai báo ĐỦ properties** | `activeTasks: []`, `activeTasksCount: 0`, `parentObjects: []`, `isUnreleased: true`, `as4date: ""` phải có sẵn |
| U5 | **WrongOverrideLinter** | Child controller KHÔNG override private methods của BaseController |
| U6 | **Service routing tường minh** | `_trServiceUri()` cho TrTree/TrSearch; `_objServiceUri()` cho LocalObjects; `_mainServiceUri()` cho Compare/Version |
| U7 | **Search screens: validate input trước khi query** | ObjSearch: cần Object Name, Package, hoặc Person Responsible. TrSearch: cần TR hoặc Owner |
| U8 | **i18n `.properties`: Unicode escape `\uXXXX` 4 hex** | `\u305` (3 hex) → crash UI5 boot |
| U9 | **UI5 >=1.118: dùng `sap/base/i18n/Localization`** | Không dùng `sap.ui.getCore().getConfiguration().setLanguage()` (deprecated) |
| U10 | **Monaco Editor: iframe sandbox bắt buộc** | AMD loader conflict. Giao tiếp qua `postMessage`. Không dùng VBox height="100%" trong IconTabFilter |
| U11 | **Monaco Diff missing side: pass `""`** | Không insert dummy comment. Dùng CSS `.no-diff` class và status tag |
| U12 | **AI calls: 100% qua SICF `/sap/bc/zscort_ai`** | KHÔNG gọi `generativelanguage.googleapis.com` từ FE. KHÔNG lưu API key trong JS |

---

## CTS / TR Workflow Invariants

| # | Rule |
|---|---|
| C1 | **Release TR**: chỉ chốt status 'R' + VRSD snapshot. TUYỆT ĐỐI không auto-apply sang Target |
| C2 | **Apply to Target**: người dùng chủ động trigger → modal confirm → proceed |
| C3 | **Active Tasks**: query `E070 WHERE strkorr = parent_trkorr` + `E07T` (description) + `E071`/`TADIR` |
| C4 | **Version Roll-Forward**: đọc từ `VRSD` (không đọc local active), ghi `MAX(version_no)+1` vào `za05_scort_t_src`, cập nhật `current_version` |
| C5 | **Compare Status**: object trên Target chưa có status `ACTIVE` → không hiển thị diff |
| C6 | **TADIR Function Module**: FUNC không có trong TADIR, chỉ có FUGR. Query `ENLFDIR JOIN TADIR` khi tìm FUNC |
| C7 | **SE09 NodeId**: phải unique = concat(trkorr + obj_type + obj_name + suffix) |
| C8 | **Source retrieval theo object type**: DCLS→`ACMDCLSRC`; DDLX→`DDLXSRC_SRC`; BDEF→`RSBDEFSRC`; SRVD→`SRVD_SOURCE`; DDLS→`DDDDLSRC` |

---

## SAP Deployment Invariants

| # | Rule |
|---|---|
| D1 | **`fiori deploy`: bắt buộc `--yes`** để tránh interactive prompt treo agent |
| D2 | **PFCG User tab: không wildcard** — dùng `SU10` cho mass assignment |
| D3 | **PFCG + OData V4 (`G4BA`)**: phải Generate Authorization Profile (`Shift+F5`) sau khi gán service → không thì HTTP 403 |
| D4 | **FLP cache**: chạy `/UI2/INVAL_CACHES` hoặc `&sap-cache=false` sau deploy |

---

## Spreadsheet / Document Generation Invariants (E1–E14)

| # | Invariant | Quy định cốt lõi |
|---|---|---|
| E1 | **Template-Driven Token Extraction** | 100% tokens (font, fill, border, alignment) lấy từ reference sheet (`Example`/`Template`). Không đoán mò. |
| E2 | **Grill-Before-Deviate** | Đề xuất cải tiến UX lệch template -> Dừng lại, hỏi user qua `/grill-me` trước khi áp dụng. |
| E3 | **Live KPI Formulas** | Row 7 và Summary cells phải dùng công thức động (`=COUNTIF`, `=SUM`, `='Sheet'!Cell`), không hardcode số. |
| E4 | **Era-Appropriate Data** | Dữ liệu mock/test phải khớp niên đại dự án (2026+), loại bỏ placeholder cũ 2000-2009. |
| E5 | **Sibling Symmetry** | Toàn bộ 20 function sheets phải đồng nhất 100% về kích thước cột, dòng, freeze panes, và styles. |
| E6 | **Automated 12-Gate Diff** | Bắt buộc chạy script format diff 12 cổng trước khi bàn giao. Nghiêm cấm `exit code 0 = Done`. |
| E7 | **Unified 3-Column Box (B-C-D)** | Khởi tạo đầy đủ khối B-C-D cho mọi hàng dữ liệu: B (`left=thin`), C (no vertical), D (`right=thin`), fill white. |
| E8 | **Strict Group Hierarchy** | Tên nhóm (e.g. `Precondition`) chỉ xuất hiện ở Col B dòng đầu tiên. Các dòng con Col B để trống, text ở Col D. |
| E9 | **Cross-Zone Token Isolation** | Trích xuất token theo từng vùng (Header, Condition, Confirm, Result footer). Không dùng chung style giữa các vùng. |
| E10 | **Multi-Tier Hierarchy** | Giữ nguyên 3 cấp phân cấp: Level 1 (Precondition), Level 2 (Input Parameters/ParamName), Level 3 (Value). |
| E11 | **Untrusted Input Style Isolation** | File input chỉ dùng lấy raw value. Tuyệt đối KHÔNG copy font size/style từ input (tránh lỗi Arial 8.5pt). |
| E12 | **Dynamic Chart Re-Anchoring** | OpenPyXL không tự relink chart -> Bắt buộc script duyệt `chart.series` cập nhật formula `$F$34:$H$34` và anchor row. |
| E13 | **UX Dynamic Text Auto-Scaling** | `Row Height = max(min_h, total_lines * line_h)` + `wrap_text=True` cho các ô text dài, chống tràn/cắt chữ. |
| E14 | **Summary & Subtotal Parity** | Subtotal: Navy endpoints (A/B & Total), nền trắng giữa (C..H). Đủ 5 dòng KPI (Coverage, Success, Normal, Abnormal, Boundary). |

---

## Enterprise Document & Spreadsheet QA Invariants

| Mã Lỗi | Tên Lỗi | Nguyên Tắc Bắt Buộc |
|---|---|---|
| `ERR_XLSX_001` | **Prototype Row Style Cloning** | Luôn clone 100% style từ dòng dữ liệu đại diện trong template sang dòng mới. |
| `ERR_XLSX_002` | **Dynamic Formula Shifting** | Bóc tách dải ô tham chiếu bằng Regex và tịnh tiến động khi phình to dòng. |
| `ERR_XLSX_003` | **Semantic Anchor Discovery** | Dò tìm Header, Data Start và Summary bằng từ khóa; dữ liệu chỉ chèn vào giữa. |
| `ERR_XLSX_004` | **Safe Merged-Cell Handling** | Chỉ gán giá trị vào Top-Left; đồng bộ style toàn dải merged chống rách viền. |
| `ERR_XLSX_005` | **Freeze Panes & Dynamic Height** | Freeze Panes tại giao điểm Header+1; Chiều cao tính bằng `max(min_h, lines * line_h)`. |
| `ERR_XLSX_006` | **DrawingML Preservation** | Luôn load trực tiếp template gốc; cấm tạo `Workbook()` rỗng làm mất shapes/logo. |
| `ERR_XLSX_007` | **Identifier Number Format** | Cột mã định danh (ID, Code) bắt buộc gán `number_format = '@'` và kiểu string. |
| `ERR_DOCX_001` | **The Last Paragraph Rule** | Mọi cell bảng (`<w:tc>`) bắt buộc phải kết thúc bằng tối thiểu một thẻ `<w:p>`. |
| `ERR_DOCX_002` | **Run Text Overwrite** | Thao tác nội dung qua `cell.paragraphs[0].runs`, không gán `cell.text = "..."`. |
| `ERR_DOCX_003` | **Multi-Page Table Flags** | Bảng nhiều trang bắt buộc có `<w:cantSplit/>` và `<w:tblHeader/>`. |
| `ERR_DOCX_005` | **Printable Margin Overflow** | Khóa tỉ lệ ảnh; chiều rộng hình ảnh $\le$ `page_width - left_margin - right_margin`. |
| `ERR_DIAG_002` | **Zero-Template 60-30-10** | Vẽ không có mẫu: 60% nền trung tính, 30% thẻ slate/trắng, 10% màu nhấn. Khoảng cách $\ge$ 40px. |
| `ERR_CONV_004` | **Zombie Lock Files Cleanup** | Tự động quét và thu gom sạch file rác `.~lock.*` và `~$*` trước/sau khi chạy. |
| `CLI Exit` | **CI/CD Exit Codes** | `0` = Clean 100%; `1` = Warning (Aesthetic); `2` = Critical (Corrupt XML / Break). |

---

## Git Invariant

**NGHIÊM CẤM `git commit` và `git push` tự động** — chỉ thực hiện khi user explicit ra lệnh (*"commit cho tôi"*, *"push git nhé"*). Chỉ được tự ý dùng `git status`, `git diff`, `git log`.

---

## General Dev Invariants

- **ARCHITECTURE.md**: đọc trước khi tạo file mới hoặc restructure module.
- **`.agent_scratchpad.md`**: update trước khi kết thúc mỗi response khi task > 3 steps.
- **Max 1 fix attempt per error**: nếu fix fail → STOP, giải thích root cause, chờ feedback.
- **Không truncate code** với `// rest of code unchanged` khi replace file content.
- **Guard clauses**: early return thay vì nested if.
- **Hardcoded string literals trong ABAP backend**: NGHIÊM CẤM — dùng T100 Message Class `ZCM_SCORT`.


