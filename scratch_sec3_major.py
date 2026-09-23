import docx
import sys
sys.stdout.reconfigure(encoding='utf-8')

doc_path = r'e:\Do_an_SU26\SuperMarketBot-Android-Robot\src\Report3_Software Requirement Specification.docx'
doc = docx.Document(doc_path)

print("=== Major Sections under 3. Functional Requirements ===")
for i, p in enumerate(doc.paragraphs):
    txt = p.text.strip()
    if p.style.name in ["Heading 2", "Heading 3"] and (i >= 66 and i <= 4190):
        # check if there are images
        img_count = sum(1 for r in p.runs if 'graphic' in r._element.xml)
        print(f"[{i}] {p.style.name}: {txt} (img: {img_count})")
