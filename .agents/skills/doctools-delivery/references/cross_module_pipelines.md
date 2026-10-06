# Reference: Cross-Module Pipelines & Hand-off Protocol

## 1. Analytics to Document (`WF-CROSS-01`)
1. XLSX Engine runs `xlsx.mutate` to inject data into template $\rightarrow$ `xlsx.recalc` updates dynamic formulas $\rightarrow$ outputs `file_ref_xlsx`.
2. Extract summary metrics table via `xlsx.inspect`.
3. DOCX Engine runs `docx.build_document` embedding summary tables into Word report (`.docx`).
4. Deliver dual artifacts: Final Word report + 100% dynamic formula Excel spreadsheet.

## 2. Visual Diagram to Document (`WF-CROSS-02`)
1. DIAGRAM Engine runs `diagram.build` generating `.drawio` XML $\rightarrow$ `diagram.render` exports high-DPI PNG/SVG ($\ge 300\text{ DPI}$).
2. DOCX Engine embeds the image into a document `image` block, auto-scaled to printable width $\le 15.92\text{ cm}$.
3. XLSX Engine embeds the image into the Cover Sheet via Two-Cell Anchor.

## 3. File Lifecycle & Security (`WF-CROSS-03`)
- **Opaque FileRef Handles**: `resource://<engine>/files/<id>` with SHA-256 integrity hash. Never pass raw inline base64 strings across tools.
- **TTL & Cleanup**: `FileStore` automatically purges expired artifacts and sweeps zombie system locks (`.~lock.*`, `~$*`).
- **Sandbox Isolation**: Resource-intensive operations (Jinja rendering, LibreOffice recalculation, headless Chromium) execute in isolated subprocesses (timeout $\le 60\text{s}$, RAM limit $\le 2\text{GB}$).
