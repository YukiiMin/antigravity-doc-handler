---
name: empirical-testing
description: Operational playbook and reporting standards for Empirical Testing on documents and spreadsheets using doctools. Hướng dẫn quy trình 5 giai đoạn kiểm thử thực nghiệm, lập ma trận phân định trách nhiệm, đo lường baseline, chạy diff và universal gates, đối soát visual parity.
---

# Empirical Document & Spreadsheet Testing Playbook

## Trigger Conditions
Activate this skill whenever:
- User provides a live file in `data-set/` and commands testing or verification.
- Recreating, repairing, or mutating workbook sheets against real business scenarios.
- Benchmarking `doctools` capability and fidelity against baseline documents.

---

## Standard 5-Stage Execution Protocol

### Stage 1: Pre-Audit Baseline Establishment
Run preflight diagnostics to establish the reference baseline:
```python
# XLSX Example via MCP Registry:
res_pre = registry.execute("xlsx.preflight", {"file_ref": input_file_path})
res_insp = registry.execute("xlsx.inspect", {"file_ref": input_file_path})
```
Log baseline metrics:
- Sheet Count & Names
- Formula Count & Existing Error Count (`#REF!`, `#NAME?`)
- Fidelity Tier (T1..T4)
- DrawingML, Charts, Images, Macros Presence
- Active Lock Detection (`~$*`)

### Stage 2: Publish Responsibility Matrix
Present the explicit boundary between toolkit operations and AI logic before modifying files:

| Pipeline Step | `doctools` Operation | AI / Auxiliary Scope | Rationale / Note |
|---|---|---|---|
| 1. Baseline Audit | `xlsx.preflight`, `xlsx.inspect` | Parameter selection | Opaque package parsing |
| 2. Spec Definition | Schema validation | Domain logic mapping | AI translates prompt to JSON Spec |
| 3. Table Expansion | `xlsx.mutate` | Row payload assembly | Prototype cloning & style inheritance |
| 4. Recalculation | `xlsx.recalc` | Cache value verification | Headless COM / lxml cache injection |
| 5. Quality Gate | `xlsx.validate`, `xlsx.diff` | Regression inspection | 13 Universal Gates UG-01..13 |

### Stage 3: Tool-Driven Transformation
Execute document modifications strictly through toolkit interfaces:
- Never overwrite `data-set/input-data/`.
- Direct outputs to `data-set/output-data/<basename>_tested.<ext>`.

### Stage 4: Post-Audit & Delta Verification
Run structural diff and quality gates:
```python
res_diff = registry.execute("xlsx.diff", {"original_ref": input_file, "modified_ref": output_file})
res_gates = registry.execute("xlsx.validate", {"file_ref": output_file})
```
Compute structural delta:
- $\Delta$ Sheets: Expected vs Actual
- $\Delta$ Formulas: New formulas introduced vs Orphan formulas resolved
- $\Delta$ Errors: Count of `#REF!` eliminated (must strictly be $\le$ baseline)
- DrawingML Status: 100% Preserved

### Stage 5: Global Parity & Visual Audit Report
Conduct full-surface inspection including `Cover`, `Summary`, and `KPIs`. Report results using the standardized delivery template:

```markdown
### Empirical Testing Audit Report — [Filename]

#### 1. Responsibility Matrix Fulfillment
- `doctools` Tools Dispatched: [List tools]
- AI / Auxiliary Scripts: [List and justify]

#### 2. Quantitative Structural Delta
| Metric | Baseline (Pre-Audit) | Post-Audit Result | Delta ($\Delta$) | Status |
|---|---|---|---|---|
| Sheet Count | X | Y | +Z | PASS |
| Total Formulas | X | Y | +Z | PASS |
| #REF! Errors | N | 0 | -N | RESOLVED |
| DrawingML/Charts | True | True | Preserved | PASS |

#### 3. Global Workbook & Surface Verification
- [ ] Cover Sheet Audit: Project summary, dates, author updated.
- [ ] Summary / Rollup Audit: Dynamic cross-sheet formulas verified.
- [ ] Universal Gates: UG-01..13 passed (0 Errors).
- [ ] Visual Rendering Parity: Match score against template.
```
