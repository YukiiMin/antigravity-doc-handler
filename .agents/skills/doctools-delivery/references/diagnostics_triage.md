# Reference: Diagnostics Triage & Issue Classification

## 1. Standard Issue Schema
All diagnostics emitted by domain engines (DOCX, XLSX, DIAGRAM, INFRA) wrap inside `Diagnostics` containing `errors`, `warnings`, and `info`:
- `code`: Standard identifier (`E-...`, `W-...`, `I-...`).
- `severity`: `error` (blocks delivery), `warning` (conditionally accepted), `info` (telemetry/observability).
- `fixable_by`: `engine`, `ai`, or `human`.
- `suggested_action`: Actionable remediation guidance.
- `evidence`: Empirical diagnostic measurements.

## 2. Failure Handling Protocol (Fail-Fast Rule)
- When `errors` are present:
  - `fixable_by="ai"`: Maximum 2 automated fix attempts. If errors persist after attempt 2 $\rightarrow$ HALT immediately and report root cause.
  - `fixable_by="human"`: Never guess or force changes; print clear evidence and request user intervention.
  - `fixable_by="engine"`: Rerun the automated engine repair tool (e.g., `docx.normalize_template`).

## 3. Template Deviation Warnings (`W-DEV-*`)
- When encountering `W-DEV-*` warnings (visual or structural deviations from template standards):
  - The Agent MUST NOT arbitrarily apply changes that alter the template design.
  - The Agent MUST halt, present before-and-after evidence, and seek user confirmation via `/grill-me`.
