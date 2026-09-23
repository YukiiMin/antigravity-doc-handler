import json
import docx
import sys
sys.stdout.reconfigure(encoding='utf-8')


doc_path = r'e:\Do_an_SU26\SuperMarketBot-Android-Robot\src\Report3_Software Requirement Specification.docx'
doc = docx.Document(doc_path)

with open('scratch_structure.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Find all items under section 3, especially 3.2 and images
images = [d for d in data if d['has_image']]
print(f'Total images found in paragraphs: {len(images)}')

for img in images:
    # check nearby paragraphs for caption
    idx = img['idx']
    nearby_texts = []
    for offset in range(-2, 3):
        n_idx = idx + offset
        if 0 <= n_idx < len(doc.paragraphs):
            t = doc.paragraphs[n_idx].text.strip()
            if t:
                nearby_texts.append(f"({offset}) {t[:80]}")
    print(f"Image at paragraph {idx}:")
    for nt in nearby_texts:
        print(f"   {nt}")

print('\n--- Major Headings ---')
for d in data:
    txt = d['text']
    if any(txt.startswith(prefix) for prefix in ['1.', '2.', '3.', '4.', '5.']):
        print(f"[{d['idx']}] ({d['style']}) {txt}")
