---
name: xlsx-engine-operator
description: How to operate the doctools xlsx.* MCP tools (preflight, inspect, mutate, recalc, validate, diff, build, lint_template, register_template) correctly when you have never used them before. Use whenever the task involves reading, editing, extending, repairing, auditing or generating an Excel .xlsx/.xlsm workbook in this workspace, including requests like "add 2 test-case sheets and a summary", "expand this table", "fix #REF!", "why is this KPI wrong", "check this spreadsheet", or any mention of xlsx, Excel, template rows, formulas or UG gates. Also use when a diagnostic code such as W-FORMULA-*, W-DEV-*, W-PKG-*, W-CALC-*, E-SHIFT-*, E-LOCK-*, E-DIFF-* or E-XLSX-UG* appears. Do not hand-write openpyxl/pandas scripts to modify a workbook before reading this skill.
---

# Operating the xlsx.* tools

The xlsx engine is deterministic and fail-closed: it checks things you would otherwise forget (formula shifting across sheets, dropped dropdowns, lost logos, stripped KPI formulas). It cannot check *intent*. That part is yours. This skill covers both: the order of operations that lets the engine protect you, and the judgment the engine cannot supply.

## Why this order matters

A fresh agent's instinct is to open the file and edit it. That instinct is the main source of failures, for three reasons:

1. **Blind edits.** Without looking first you do not know which row is the prototype row, which columns must stay text (`@`), what is locked, or what a template contains that a plain library save would silently destroy (logos, charts, dropdowns, conditional formats).
2. **Surface fixes.** A warning or `#REF!` is a symptom. Deleting the formula or typing `0` makes the symptom vanish and the workbook wrong.
3. **Self-grading.** If you patch around a missing tool feature with Python and then report success, nobody learns the tool has a gap, and the result was never verified by the engine's gates.

## The loop (follow in order)

1. **`xlsx.preflight`**: what is inside the package, which fidelity tier applies. If it reports a tier or component that cannot be preserved (shapes, slicers, macros, external links), stop and ask the user. Do not proceed on your own: the answer may be "accept the loss", and that is their call.
2. **`xlsx.inspect` with `level="summary"`, then `level="structure"`** for the sheets you will touch. Add `formulas` or `formats` only when the task needs them; drill into a single anchor with `cells`. Output is grouped (formulas by R1C1 pattern, formats by style id) and paginated. If it says `truncated: true`, that is real: page on or narrow the range, do not assume you saw everything.
3. **Plan before you mutate.** Write the MutationSpec in your head (or to the user for large changes): which sheet, which anchor (by header text or keyword, never a hardcoded row number), which prototype row, which columns are identifiers. State what you expect to change so you can compare with what actually changed.
4. **`xlsx.mutate`** with a MutationSpec (JSON). Never craft XML or openpyxl code. Pass `calc_policy` explicitly if the task cares about cached values. Mutate always produces a new file; the original is untouched.
5. **`xlsx.recalc`** unless mutate already ran it. Look at `values_status` and its `origin` before quoting any number to the user. A LibreOffice-computed cache is not Excel's number.
6. **`xlsx.validate`** (universal gates, plus the template's profile) and **`xlsx.diff`** between the input and the output. Every `undeclared` difference is a bug until proven intended.
7. **Deliver** only when no error remains and every warning has been dealt with as described below.

For a read-only question ("what does this workbook contain?", "why is this cell wrong?") steps 1-2 are the whole job; you do not need to mutate anything.

## Do not leave the tools

Do not open the workbook with openpyxl, pandas, xlwings or a zip editor to **modify** it. Computing statistics over data you already extracted with `inspect` is fine. Editing the file is not, even "just this once".

If the tools genuinely cannot do what the user asked, say so:

> "The xlsx tools have no operation for X. I could do it with a Python script, but that would bypass the engine's gates, so I have not. Gap: <one line>. Options: ..."

Then let the user decide. Record it as a tool gap in your final report. A visible gap is useful to the person improving the tools; a hidden workaround is not. The engine also detects files that came back from outside the tool chain (`W-PROV-EXTERNAL`), so a workaround tends to surface anyway.

## Handling diagnostics

Every issue carries `code`, `location`, `evidence`, `fixable_by` and (often) `suggested_action`. Read `fixable_by` first:

| `fixable_by` | What you do |
|---|---|
| `engine` | Re-run with the policy or `repair` the engine suggests. |
| `ai` | Fix your spec using the `evidence` and call again. Cap this at 2 attempts. If two consecutive attempts do not reduce the errors, stop and report; do not keep guessing. |
| `human` | Stop and ask the user. Show before/after from `evidence`. Applies to `W-DEV-*` (deviation from template), `W-PKG-UNSUPPORTED-*` (something may be lost), and `E-LOCK-*` (write into a locked zone). Only pass `approved_deviations` after the user said yes. |

Severity does not decide whether to act. **A warning is not permission to ignore.** `W-*` does not block the build, which is exactly why they get ignored and why the wrong number ships. Either fix it, or tell the user in the final report what it is and why you left it.

Never make a diagnostic disappear by removing what it points at. Deleting a formula, clearing a cell, or writing `0` over an error silences the check while destroying the logic. If you catch yourself thinking "this makes the warning go away", that is the cue to look at what the cell is *for*.

Details and worked examples for the most common codes are in [references/diagnostics.md](references/diagnostics.md). Read it when you meet `W-FORMULA-EMPTY-CELL-REF`, `#REF!`/`E-SHIFT-*`, `E-DIFF-*`, or any `W-CALC-*`.

## Reading a formula warning properly (the `-AA7` lesson)

A formula that subtracts or references an empty cell, e.g. `=O8-AA7` where `AA7` is empty, evaluates without error to a wrong number. The engine flags it; it cannot say what was meant. Do this:

1. `inspect` (or `trace_cell`) the formula and the cells around its target. Compare neighbouring rows' formulas in the same column: do they reference a column that holds data?
2. Work out what the formula *means* in the sheet's own vocabulary (e.g. "lack of test cases = quota − actual", so the subtrahend should be the actual-count cell).
3. If one candidate fits clearly (here `O7`, same row pattern as its siblings), fix the reference through `mutate`, and say so in your report. If two readings are plausible, ask the user.

## Tables, anchors and identifiers

- Locate the table by header text or keyword (`anchor.kind = header|keyword`). If the engine answers `E-TPL-ANCHOR-AMBIGUOUS` or `-MISSING`, pick a more specific anchor or ask; do not substitute a row number.
- Identifier columns (IDs, codes with leading zeros) are text. Pass them as strings and list them in `id_columns`.
- Strings starting with `=` are text unless you mark them `formula`. Do not rely on this by accident: say which you mean.
- Summary/KPI cells stay formulas (`COUNTIF`, `SUM`). Never overwrite them with a number to "fix" a total.
- Write only to the top-left cell of a merged range.
- Never create a blank workbook in place of a template. If the template path fails, that is `E-TPL-*`: report it.

## Reporting back

Be exact about what was and was not verified. A good final message has:

- what changed (sheets, row counts, formulas shifted) in two or three lines,
- the gate/diff result (all passed, or which warnings remain and why),
- where the numbers came from (`values_status` and `origin`: recalculated by LibreOffice vs cached from the source file),
- anything you could not do or did not test, said plainly,
- any tool gap you hit.

Do not write "all tests passed" for checks you did not run. "Not verified: <what>" is a correct and useful sentence.

## Quick reference: tool names

Names follow the registry (`xlsx.preflight`, `xlsx.inspect`, `xlsx.lint_template`, `xlsx.register_template`, `xlsx.mutate`, `xlsx.recalc`, `xlsx.validate`, `xlsx.diff`, `xlsx.build`, `xlsx.analyze_formulas`, `xlsx.describe_formats`, `xlsx.function_catalog`, `xlsx.coverage_report`, `xlsx.set_format`, `xlsx.set_validation`, `xlsx.set_conditional_format`, `xlsx.copy_sheet`). If your host exposes them with a different spelling (for example `preflight_xlsx`), the meaning is the same. Treat missing tools as a tool gap, not a licence to script.
