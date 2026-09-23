import sys
import docx

sys.stdout.reconfigure(encoding='utf-8')

DOCX_PATH = r"e:\Do_an_SU26\SuperMarketBot-Android-Robot\screenShot\Report3_Software Requirement Specification.docx"

doc = docx.Document(DOCX_PATH)
print(f"Total Paragraphs: {len(doc.paragraphs)}")
print(f"Total Tables: {len(doc.tables)}")

# Check Section 3.2 and 3.3 positions
idx_3_2 = -1
idx_3_3 = -1
for i, p in enumerate(doc.paragraphs):
    if p.text.strip() == "3.2 App for Robot":
        idx_3_2 = i
    elif p.text.strip() == "3.3 Android Customer App":
        idx_3_3 = i
        break

print(f"Index 3.2: {idx_3_2}")
print(f"Index 3.3: {idx_3_3}")
print(f"Paragraphs in 3.2: {idx_3_3 - idx_3_2}")

# Check headings inside 3.2
h4_titles = []
images_count = 0
todos = []

for i in range(idx_3_2, idx_3_3):
    p = doc.paragraphs[i]
    if p.style.name == 'Heading 4' and p.text.startswith("3.2."):
        h4_titles.append(p.text)
    
    # Check images (blip tags in xml)
    if 'graphicData' in p._p.xml:
        pic_count = p._p.xml.count('<a:blip')
        images_count += pic_count
        
    # Check TODO markers
    for run in p.runs:
        if "[TODO:" in run.text:
            color = run.font.color.rgb if run.font.color else None
            todos.append((run.text, run.bold, color))

print("\n--- Summary of Verification ---")
print(f"Sub-sections found ({len(h4_titles)}): {h4_titles}")
print(f"Embedded images count: {images_count}")
print(f"TODO markers count: {len(todos)}")
for t in todos:
    print(f"  {t[0][:65]}... | Bold: {t[1]} | Color: {t[2]}")

# Check TOC (first 50 paragraphs)
print("\n--- TOC Check (Paragraphs 25 to 45) ---")
for idx in range(25, min(45, len(doc.paragraphs))):
    txt = doc.paragraphs[idx].text.strip()
    if txt and ("3." in txt or "4." in txt):
        print(f"P{idx}: {txt}")
