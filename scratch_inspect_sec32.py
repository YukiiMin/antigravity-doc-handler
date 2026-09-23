import docx
import sys
sys.stdout.reconfigure(encoding='utf-8')

doc_path = r'e:\Do_an_SU26\SuperMarketBot-Android-Robot\src\Report3_Software Requirement Specification.docx'
doc = docx.Document(doc_path)

print("=== Content of Section 3.2 App for Robot (paragraphs 95 to 306) ===")
for i in range(95, 307):
    p = doc.paragraphs[i]
    txt = p.text.strip()
    img_runs = [r for r in p.runs if 'graphic' in r._element.xml]
    if img_runs or p.style.name.startswith("Heading") or any(keyword in txt for keyword in ["Figure", "Table", "Image", "Screen"]):
        print(f"[{i}] ({p.style.name}) [img={len(img_runs)}]: {txt}")
    elif len(txt) > 0 and len(txt) < 80:
        print(f"[{i}] ({p.style.name}) [img={len(img_runs)}]: {txt}")
