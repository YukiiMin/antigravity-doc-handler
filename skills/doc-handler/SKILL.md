---
name: doc-handler
description: High-fidelity office document processing, conversion (PDF <-> DOCX <-> Markdown), OpenXML table repair, and decoupled styling.
---

# Antigravity Skill: Office Document Handler (`doc-handler`)

Use this skill whenever you need to convert, inspect, format, or repair office documents (PDF, Word `.docx`, Excel `.xlsx`, and Markdown `.md`) with 100% layout and data fidelity.

---

## 🚀 Quick CLI Reference for AI Agents

All commands can be invoked directly from the command line:

```bash
# 1. Convert PDF to DOCX with Smart Post-Processor v6:
python -m ai_tools_cli convert input.pdf -o output.docx

# 2. Convert DOCX to decoupled Markdown + Style YAML:
python -m ai_tools_cli convert document.docx -t md

# 3. Convert Markdown back to DOCX (using style tokens):
python -m ai_tools_cli convert document.md -t docx --style document.style.yaml

# 4. Inspect document structure, headings, and table properties:
python -m ai_tools_cli inspect-doc document.docx

# 5. Insert an image or diagram under a specific section heading:
python -m ai_tools_cli insert-diagram document.docx diagram.png -s "3.1.2 Android User Screen Flow" -c "Figure 3.1: Screen Flow" -w 14.0
```

---

## 📋 OpenXML Table Invariants (Mandatory Standards)

When generating or editing tables in Word (`.docx`) documents, you MUST enforce the following 4 rules:

1. **Anti-Row-Split (`<w:cantSplit/>`)**:
   - Every table row (`trPr`) must contain `<w:cantSplit/>` to prevent ugly page-boundary splits.
2. **Repeating Header (`<w:tblHeader/>`)**:
   - Row 0 of every table must have `<w:tblHeader/>` so column titles repeat when tables span across pages.
3. **Vertical Centering (`<w:vAlign w:val="center"/>`)**:
   - Every cell (`tcPr`) must have vertical alignment set to center.
4. **Header Shading**:
   - Header row must have peach background `#FFE8E0` (`<w:shd w:fill="FFE8E0"/>`).

### Python OpenXML Helper Pattern:

```python
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH

def format_table_openxml(table):
    # Repeat header & cantSplit
    for idx, row in enumerate(table.rows):
        trPr = row._tr.get_or_add_trPr()
        trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))
        if idx == 0:
            trPr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))
            for cell in row.cells:
                tcPr = cell._tc.get_or_add_tcPr()
                tcPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="FFE8E0"/>'))
        
        # Vertical center all cells
        for cell in row.cells:
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
```

---

## 🎨 Decoupled Document Architecture (Markdown + Style YAML)

Do NOT embed inline CSS or YAML frontmatter directly inside Markdown content if decoupling is requested.
Instead, use the two-layer model:

1. `document.md`: Pure GitHub-Flavored Markdown (Headings, bullet lists, tables, text).
2. `document.style.yaml`: Presentation tokens (margins, typography, heading colors, table shading).
