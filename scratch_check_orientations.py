import os
import json
from PIL import Image
import sys
sys.stdout.reconfigure(encoding='utf-8')

media_dir = r'e:\Do_an_SU26\antigravity-doc-handler\extracted_docx_media'

with open('images_info.json', 'r', encoding='utf-8') as f:
    images = json.load(f)

print("=== Check Image Dimensions & Orientation in Section 3.2 ===")
for img in images:
    if img['p_idx'] <= 310:
        filename = os.path.basename(img['target'])
        filepath = os.path.join(media_dir, filename)
        if os.path.exists(filepath):
            with Image.open(filepath) as im:
                w, h = im.size
                aspect = w / h
                orientation = "LANDSCAPE (Tablet/Web)" if aspect > 1.2 else ("PORTRAIT (Mobile Phone)" if aspect < 0.8 else "SQUARE/OTHER")
                print(f"P[{img['p_idx']:4d}] | {img['h3'][:35]:35s} | {filename:15s} | {w}x{h} ({orientation})")
