import json
import os
from PIL import Image
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('scratch_all_images_context.json', 'r', encoding='utf-8') as f:
    items = json.load(f)

media_dir = r'e:\Do_an_SU26\antigravity-doc-handler\extracted_docx_media'

print("=== Analyzing Image Placements Across Sections ===")
for it in items:
    fname = it['target']
    fpath = os.path.join(media_dir, fname)
    if not os.path.exists(fpath):
        continue
    with Image.open(fpath) as im:
        w, h = im.size
        aspect = w / h
    
    sec = it['h3'] if it['h3'] else it['h2']
    # Check for obvious mismatches:
    # 1. Web Admin having portrait mobile screenshots (aspect < 0.8)
    if 'Web Admin' in it['h2'] and aspect < 0.8:
        print(f"[MISMATCH - Web Admin has mobile portrait image]: {sec} -> {fname} ({w}x{h}, aspect={aspect:.2f})")
    # 2. Customer App / Staff App having widescreen desktop images (aspect > 1.4)
    if ('Android Customer App' in it['h2'] or 'Staff Mobile' in it['h2']) and aspect > 1.4:
        print(f"[MISMATCH - Mobile App has widescreen desktop image]: {sec} -> {fname} ({w}x{h}, aspect={aspect:.2f})")
    # 3. Section 3.2 App for Robot
    if '3.2 App for Robot' in it['h2'] or (it['h3'] and it['h3'].startswith('3.2.')):
        print(f"[Section 3.2 Image]: {sec} (P[{it['p_idx']}]) -> {fname} ({w}x{h})")

