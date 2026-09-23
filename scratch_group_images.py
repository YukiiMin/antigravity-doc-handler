import json
import os
import zipfile
import docx
from collections import defaultdict
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('images_info.json', 'r', encoding='utf-8') as f:
    images = json.load(f)

print(f"Total image references: {len(images)}")

# Group by section
by_sec = defaultdict(list)
for img in images:
    sec = f"{img['h2']} -> {img['h3']}"
    by_sec[sec].append(img)

for sec, imgs in by_sec.items():
    print(f"\n[{sec}] : {len(imgs)} images")
    p_indices = sorted(list(set(img['p_idx'] for img in imgs)))
    print(f"   Paragraphs: {p_indices}")
    # targets
    targets = [img['target'] for img in imgs]
    print(f"   Media targets: {targets}")
