import json
import os
from PIL import Image
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('scratch_all_images_context.json', 'r', encoding='utf-8') as f:
    items = json.load(f)

media_dir = r'e:\Do_an_SU26\antigravity-doc-handler\extracted_docx_media'

print("=== Checking Section 3.3 and 3.4 image placements ===")
for it in items:
    p_idx = it['p_idx']
    if p_idx > 306:
        h3 = it['h3']
        target = it['target']
        fpath = os.path.join(media_dir, target)
        if os.path.exists(fpath):
            with Image.open(fpath) as im:
                w, h = im.size
        # print heading and target
        # check if heading has keywords matching target
        # or if there are multiple images in one paragraph
        print(f"P[{p_idx:4d}] | {h3[:45]:45s} | {target:15s} ({w}x{h})")
