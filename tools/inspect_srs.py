import sys
import docx

sys.stdout.reconfigure(encoding='utf-8')
docx_path = r'e:\Do_an_SU26\SuperMarketBot-Android-Robot\screenShot\Report3_Software Requirement Specification.docx'
doc = docx.Document(docx_path)

for i in range(25, 45):
    p = doc.paragraphs[i]
    print(f"[{i}] style='{p.style.name}' | text='{p.text}'")
