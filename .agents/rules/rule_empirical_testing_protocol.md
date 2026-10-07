---
trigger: model_decision
description: Mandatory Empirical Testing and Tool Verification Protocol. Bắt buộc áp dụng khi người dùng yêu cầu testing, kiểm thử thực nghiệm trên file tài liệu/bảng tính thực tế, chạy test bài toán doanh nghiệp, đánh giá năng lực tools, phục hồi sheet, kiểm tra lỗi #REF!, soát file output.
---

# Rule: Empirical Testing & Tool Verification Protocol

> **Scope**: Mandatory whenever executing empirical tests on live document files (DOCX, XLSX, DIAGRAM), evaluating toolkit capabilities, or restoring corrupted datasets.

---

## 1. Core Ethos: "Testing Tools, Not Just Solving Documents"

1. **Zero Evasion Rule**: Never solve document tasks using raw, ad-hoc Python libraries to deliver a file while bypassing or obscuring the role of `doctools`.
2. **Mandatory Responsibility Matrix**:
   Before executing modifications, the AI MUST explicitly publish a Responsibility Matrix:
   - **`doctools` Core Operations**: Which specific MCP tools are dispatched (`preflight`, `inspect`, `mutate`, `recalc`, `diff`, `validate`).
   - **AI Semantic & Auxiliary Logic**: Scope of prompt analysis, schema preparation, or temporary glue script.
   - **Justification for Auxiliary Code**: Explicitly state if an auxiliary script is used due to an unbuilt feature or pipeline gap. Never conceal raw Python fallbacks.

---

## 2. Invariants for Empirical Verification

### Invariant 1: Global Workbook Audit (`Cover` & Summary Invariant)
When testing, repairing, or mutating spreadsheets, NEVER focus solely on leaf data sheets. The AI MUST verify all global context sheets:
1. **Cover / Title Sheets**: Audit project metadata tables, author, dates, and version tracking blocks.
2. **Rollup & KPI Sheets (`Summary`, `Statistics`, `Dashboard`)**: Must retain dynamic cross-sheet formulas (`=COUNTIF`, `=SUM`, `=AVERAGE`). Hardcoding static aggregate figures is strictly forbidden.
3. **Index / Catalog Sheets (`Functions`, `TOC`)**: Must synchronize catalog entries when new sheets are introduced.

### Invariant 2: Dataset Immutability & File Output Routing
- Input files located in `data-set/input-data/` are strictly **READ-ONLY**.
- All empirical test outputs MUST be written to `data-set/output-data/<name>_tested.<ext>`.
- Never overwrite the reference or input file during tests.

### Invariant 3: Zombie Lock Guard
- Check for temporary lock files (`~$<filename>` or `.~lock.*`).
- If an active desktop application holds the target file open, write to an isolated unique filename to prevent `PermissionError` failures.

---

## 3. Mandatory 5-Stage Verification Lifecycle

1. **Stage 1 (Pre-Audit Baseline)**: Measure baseline metrics via `xlsx.preflight` / `xlsx.inspect` (sheet count, formula count, `#REF!` count, Tier T1..T4, DrawingML/Images).
2. **Stage 2 (Plan & Responsibility Matrix)**: Outline tool chain and publish the Responsibility Matrix.
3. **Stage 3 (Execution via Tools)**: Apply mutations using `xlsx.mutate`, `xlsx.build`, or `xlsx.recalc`.
4. **Stage 4 (Post-Audit Diff & Gates)**: Run `xlsx.diff` and `xlsx.validate` (13 Universal Gates UG-01..13). Report Delta (sheets $\pm$, formulas $\pm$, `#REF!` eliminated).
5. **Stage 5 (Visual & Parity Audit)**: Compare visual rendering against template expectations; inspect `Cover`, frozen panes, headers, and report match percentage.
