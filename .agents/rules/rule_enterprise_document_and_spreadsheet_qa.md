---
trigger: model_decision
description: Enterprise Document & Spreadsheet QA and static diagnostic standards for DOCX, XLSX, Diagrams, and zombie locks cleanup. Kiểm toán chất lượng tài liệu văn phòng, soát lỗi định dạng, rách bảng, chẻ đôi hàng, băm run Jinja, ngắt trang, dọn dẹp file khóa zombie.
---

# Rule: Enterprise Document & Spreadsheet QA / Diagnostics Standard

> **Scope**: Mandatory for reading, mutating, creating, diagnosing, and converting enterprise documents (`.docx`, `.xlsx`, `.pdf`, `.md`) and technical diagram assets (Draw.io, charts).

---

## 1. Core Philosophy: Template-First & Non-Destructive Mutation

1. **Never Hardcode Styles**: Never hardcode hex colors, font families, or cell dimensions without referencing the template.
2. **Prototype Row Style Cloning**: Always extract styling from a representative prototype data row in the template and clone 100% of its attributes onto new rows.
3. **Zero-Destruction Invariant**: Never overwrite original files without a backup (`.bak`). Default to writing remediated output to `[name]_repaired.[ext]`.
4. **Semantic Anchor Discovery**: Locate Header, Data Start, and Summary/Total rows dynamically via keywords and formulas rather than hardcoding static row indices.

---

## 2. Invariants Across 4 Technical Domains

### A. EXCEL (XLSX) Domain — Spreadsheet Structure & Formatting
* **`ERR_XLSX_001` (Prototype Row Style Cloning)**: When appending rows, clone all cell properties (`font`, `fill`, `border`, `alignment`, `number_format`) from the first data row directly under the header.
* **`ERR_XLSX_002` (Dynamic Formula Range Expansion)**: Scan template formulas, extract reference ranges via regex/AST (e.g., `F10:F25`), and expand dynamically to `F10:F{25 + \Delta K}` when inserting rows.
* **`ERR_XLSX_003` (Semantic Anchor Discovery)**: New records MUST ONLY be inserted between Data Start (row below header) and Summary Sentinel (row containing `Total`, `Summary`, or `=SUM`).
* **`ERR_XLSX_004` (Safe Merged-Cell Introspection)**: Maintain helper `get_effective_cell()`. Write values exclusively to the Top-Left cell; synchronize borders across the entire merged range to avoid border clipping.
* **`ERR_XLSX_005` (Adaptive 2D Freeze Panes & Auto-scaling)**: Set Freeze Panes at the intersection of `(Header Row + 1, First Data Column)`. Compute dynamic row height:
  $$\text{Row Height} = \max(\text{min\_h}, \text{total\_lines} \times \text{line\_h}) \quad \text{with} \quad \text{wrap\_text=True}$$
* **`ERR_XLSX_006` (DrawingML & Package Integrity)**: Always load existing templates directly (`load_workbook(..., data_only=False)`). Never instantiate empty `Workbook()` objects, which strips Cover logos and shapes.
* **`ERR_XLSX_007` (Identifier Format & Leading Zeros)**: Columns containing semantic codes or IDs must explicitly set `number_format = '@'` and store string types.

### B. WORD (DOCX) Domain — OpenXML Integrity & Tables
* **`ERR_DOCX_001` (The Last Paragraph Rule)**: Every table cell (`<w:tc>`) MUST terminate with at least one paragraph (`<w:p>`). Never leave empty cells that cause Word repair warnings.
* **`ERR_DOCX_002` (Run Text Overwrite)**: Never assign `cell.text = "..."`. Mutate via `cell.paragraphs[0].runs` to preserve template typography, size, and color.
* **`ERR_DOCX_003` (Multi-Page Table Pagination Rupture)**: Multi-page tables require `<w:cantSplit/>` on each row and `<w:tblHeader/>` on header rows.
* **`ERR_DOCX_004` (Table Shading & XML Namespace)**: Use fully qualified namespace syntax (`parse_xml(f'<w:shd {nsdecls("w")} .../>')`) for raw table XML operations.
* **`ERR_DOCX_005` (Image Margins & Aspect Ratio)**: Lock aspect ratio and ensure image width does not exceed printable margins:
  $$\text{Max Image Width} = \text{page\_width} - \text{left\_margin} - \text{right\_margin}$$
* **`ERR_DOCX_006` (Template Style Inheritance)**: Prefer inheriting table styles from `styles.xml` (`table.style = '...'`) over injecting verbose inline XML.
* **`ERR_DOCX_007` (Dynamic Page Numbering)**: Use dynamic OpenXML fields `<w:fldSimple w:instr="PAGE"/>` in footers rather than static hardcoded page numbers.
* **`ERR_DOCX_008` (Standard Figure Captions)**: Format captions as `Figure X.Y – <Title>` (Times New Roman 10.5pt, centered, En-dash `–`, space before 4pt / after 12pt).
* **`ERR_DOCX_009` (Quoted Entity Translation Protection)**: During technical translation, shield UI terms and quoted text via `__QUOTED_N__` placeholders.
* **`ERR_DOCX_010` (Windows File Lock Resilience)**: When saving files locked by Microsoft Word (`PermissionError: [Errno 13]`), fallback automatically to saving `[name]_updated.docx` to prevent data loss.

### C. DIAGRAMS & CHARTS Domain — Dual Mode (Template vs Zero-Template)
* **`ERR_DIAG_001` (Template-Driven Token Drift)**: When a template exists, extract 100% of style tokens (dimensions, colors, fonts, strokes) as the sole design reference.
* **`ERR_DIAG_002` (Zero-Template Layout Collision)**: When generating from scratch without a template:
  - Apply the **60-30-10** color rule (60% neutral background, 30% card surface, 10% semantic accent).
  - Position nodes on a canvas grid with minimum 40px spacing between boxes and 8px border radius.
* **`ERR_DIAG_003` (Chart Anchor Overlap)**: When expanding table rows, dynamically update chart formula references (`val.numRef.f`) and shift `chart.anchor._from.row` below the summary block.

### D. CONVERSION PIPELINE Domain — Resilient Conversion
* **`ERR_CONV_001` (Headless Conversion Layout Drift)**: Prefer LibreOffice/Stirling-PDF `writer_pdf_import` filter for PDF $\rightarrow$ DOCX conversions.
* **`ERR_CONV_002` (Font Embedding & Missing Glyphs)**: Specify robust fallback fonts: `'Segoe UI, -apple-system, BlinkMacSystemFont, Roboto, Arial, sans-serif'`.
* **`ERR_CONV_003` (Markdown-Office Roundtrip)**: Use intermediate JSON AST representations to preserve nested table structures.
* **`ERR_CONV_004` (Zombie Lock File Cleanup)**: Automatically remove orphan lock files (`.~lock.*` and `~$*`) via context managers before and after execution.

---

## 3. Quantitative Acceptance Criteria

A document is certified for delivery only when passing diagnostic evaluation with:
1. **Excel**:
   - DrawingML shapes: 100% preserved (Cover logos/shapes intact).
   - Zero MergedCell write violations (0 exceptions).
   - 100% live formulas (zero `#REF!`, `#VALUE!`, `#DIV/0!`).
2. **Word**:
   - Zero corrupt XML (100% table cells contain `<w:p>`).
   - 100% multi-page tables have `<w:tblHeader/>` and `<w:cantSplit/>`.
   - Table and image widths strictly within margins.
3. **CI/CD Exit Codes**:
   - `0`: Fully clean / ready for delivery.
   - `1`: Minor cosmetic warning (tight padding, wrap text).
   - `2`: Critical structural error (broken formula, corrupt XML, lost DrawingML).

---

## 4. CLI Diagnostic Command Reference

```bash
# Diagnose an Excel or Word document
python tool/pdf_to_docx_converter/tools/unified_qa_diagnostic.py --xlsx <path_to_file.xlsx>
python tool/pdf_to_docx_converter/tools/unified_qa_diagnostic.py --docx <path_to_file.docx>

# Diagnose directory and export JSON report for CI/CD
python tool/pdf_to_docx_converter/tools/unified_qa_diagnostic.py --all <dir_path> --format json --output report.json

# Safe auto-repair (creates _repaired output)
python tool/pdf_to_docx_converter/tools/unified_qa_diagnostic.py --xlsx <file.xlsx> --mode audit-fix

# In-place repair with .bak backup
python tool/pdf_to_docx_converter/tools/unified_qa_diagnostic.py --docx <file.docx> --mode audit-fix --in-place
```
