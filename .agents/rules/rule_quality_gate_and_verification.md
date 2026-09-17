# Rule: Automated Quality Gate, Fidelity Verification & Multi-Format Validation

> **Scope**: Mandatory automated validation checks before delivering any generated or patched document (`.docx`, `.xlsx`, `.xls`, `.pdf`, `.png`, `.svg`).

---

## 1. Quality Gate Invariants

| # | Gate | Requirement | Automated Verification Check |
|---|---|---|---|
| **Q1** | **Zero Unreplaced Placeholders** | No placeholder artifacts like `<Author Name>`, `<Developer Name>`, `<TODO>`, `{{...}}` remain in the output. | Regex scan across all cells / paragraphs: `re.search(r"<[A-Za-z\s_-]{3,}>", text)` must return 0 matches. |
| **Q2** | **DrawingML & Embedded Image Fidelity** | Logos, diagrams, and figures in base templates must NEVER be dropped or corrupted during mutation. | Check `len(ws._images) > 0` for worksheets and `len(doc.inline_shapes) > 0` for documents. |
| **Q3** | **Live Formula Integrity** | Formulas must be valid OpenXML formulas, never evaluate to `#REF!`, `#NAME?`, or `#VALUE!`, and must not be saved as literal static text. | Iterate over formula cells: ensure formula starts with `=` and contains valid uppercase function names (`COUNTIF`, `SUM`, `IF`, `COUNTA`). |
| **Q4** | **OpenXML Table Invariants** | Tables inside Word documents must enforce pagination stability. | Ensure every `<w:tr>` contains `<w:cantSplit/>`, table header contains `<w:tblHeader/>`, and cells have `<w:vAlign w:val="center"/>`. |
| **Q5** | **Legacy Dual-Format Delivery** | When Excel deliverables are required, provide both modern `.xlsx` and legacy binary `.xls` (via headless LibreOffice export). | Verify both `.xlsx` and `.xls` exist in the target output directory and have non-zero byte size. |

---

## 2. Automated Quality Gate Script Template

```python
import re
import openpyxl

def run_excel_quality_gate(xlsx_path: str):
    wb = openpyxl.load_workbook(xlsx_path, data_only=False)
    
    # 1. Zero Placeholders
    placeholder_errors = []
    for sheetname in wb.sheetnames:
        ws = wb[sheetname]
        for r in range(1, ws.max_row + 1):
            for c in range(1, ws.max_column + 1):
                val = str(ws.cell(r, c).value or "")
                if not val.startswith("=") and re.search(r"<[A-Za-z\s_-]{3,}>", val):
                    placeholder_errors.append((sheetname, r, c, val))
    assert len(placeholder_errors) == 0, f"Found placeholders: {placeholder_errors}"

    # 2. DrawingML Images
    ws_cover = wb.worksheets[1] if len(wb.worksheets) > 1 else wb.worksheets[0]
    images_count = len(getattr(ws_cover, "_images", []))
    assert images_count > 0, "DrawingML images lost on Cover sheet!"

    # 3. Dynamic Formula Validation
    ws_stat = wb["Statistics"] if "Statistics" in wb.sheetnames else None
    if ws_stat:
        assert str(ws_stat["C12"].value).startswith("="), "Statistics C12 is not a live formula!"
        assert str(ws_stat["C17"].value).startswith("=SUM"), "Statistics C17 is not a SUM formula!"

    print(">>> 100% QUALITY GATE PASSED <<<")
```
