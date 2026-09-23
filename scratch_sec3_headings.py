import docx
import sys
sys.stdout.reconfigure(encoding='utf-8')

doc_path = r'e:\Do_an_SU26\SuperMarketBot-Android-Robot\src\Report3_Software Requirement Specification.docx'
doc = docx.Document(doc_path)

print("=== Subsections of Section 3 ===")
in_sec_3 = False
for i, p in enumerate(doc.paragraphs):
    txt = p.text.strip()
    if txt.startswith("3. Functional Requirements"):
        in_sec_3 = True
    elif txt.startswith("4. Non-Functional Requirements"):
        in_sec_3 = False
    
    if in_sec_3 and p.style.name.startswith("Heading"):
        # count images in this paragraph or following paragraphs before next heading
        print(f"[{i}] {p.style.name}: {txt}")

