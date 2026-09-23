import os
import sys

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if _CURRENT_DIR not in sys.path:
    sys.path.insert(0, _CURRENT_DIR)

from gen_master_erd import TABLES, RELATIONSHIPS

lines = ['@startuml', 'hide circle', 'skinparam linetype ortho', '']

for t in TABLES:
    lines.append(f'entity "{t["name"]}" as {t["name"]} {{')
    pks = [c for c in t['columns'] if c[2]]
    non_pks = [c for c in t['columns'] if not c[2]]
    for col in pks:
        fk_str = ', FK' if col[3] else ''
        lines.append(f'    * {col[0]} : {col[1]} <<PK{fk_str}>>')
    if pks and non_pks:
        lines.append('    --')
    for col in non_pks:
        req = '* ' if not col[4] else ''
        fk_str = ' <<FK>>' if col[3] else ''
        lines.append(f'    {req}{col[0]} : {col[1]}{fk_str}')
    lines.append('}')
    lines.append('')

for src, rel, tgt in RELATIONSHIPS:
    lines.append(f'{src} {rel} {tgt}')

lines.append('')
lines.append('@enduml')

content = '\n'.join(lines)
out_path = os.path.abspath(os.path.join(_CURRENT_DIR, "..", "diagram_assets", "master_erd_drawio_friendly.puml"))
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Generated draw.io friendly PUML: {out_path} ({len(content)} bytes)")
