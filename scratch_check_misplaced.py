import docx
import os
import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

doc_path = r'e:\Do_an_SU26\SuperMarketBot-Android-Robot\src\Report3_Software Requirement Specification.docx'
doc = docx.Document(doc_path)

with open('images_info.json', 'r', encoding='utf-8') as f:
    images = json.load(f)

print(f"Total images: {len(images)}")

# Check text surrounding each image
findings = []
for idx, img in enumerate(images):
    p_idx = img['p_idx']
    target = os.path.basename(img['target'])
    
    # surrounding text
    before = [doc.paragraphs[p_idx + o].text.strip() for o in range(-2, 0) if 0 <= p_idx + o < len(doc.paragraphs)]
    current = doc.paragraphs[p_idx].text.strip()
    after = [doc.paragraphs[p_idx + o].text.strip() for o in range(1, 3) if 0 <= p_idx + o < len(doc.paragraphs)]
    
    # Check for keywords
    surrounding = " | ".join(before + [current] + after)
    findings.append({
        'num': idx + 1,
        'p_idx': p_idx,
        'h1': img['h1'],
        'h2': img['h2'],
        'h3': img['h3'],
        'target': target,
        'surrounding': surrounding[:200]
    })

with open('scratch_all_images_context.json', 'w', encoding='utf-8') as f:
    json.dump(findings, f, ensure_ascii=False, indent=2)

print("Saved scratch_all_images_context.json")
