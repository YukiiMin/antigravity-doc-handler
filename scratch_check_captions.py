import docx
import json
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')

# Let's inspect paragraphs in 3.1, 3.2, 3.3, 3.4, 3.5 to check all figures/captions
doc = docx.Document(r'e:\Do_an_SU26\SuperMarketBot-Android-Robot\src\Report3_Software Requirement Specification.docx')

print("=== Checking Figure / Screen Captions across the entire document ===")
captions = []
for i, p in enumerate(doc.paragraphs):
    txt = p.text.strip()
    if any(k in txt.lower() for k in ['figure', 'hình ', 'bảng ', 'table ', 'screenshot', 'màn hình']):
        if len(txt) < 150:
            captions.append((i, p.style.name, txt))

print(f"Found {len(captions)} caption candidates.")
for c in captions[:40]:
    print(f"P[{c[0]:4d}] ({c[1]}): {c[2]}")
if len(captions) > 40:
    print("...")
    for c in captions[40:80]:
        print(f"P[{c[0]:4d}] ({c[1]}): {c[2]}")
