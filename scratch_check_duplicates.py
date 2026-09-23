import os
import json
from PIL import Image
import numpy as np
import sys
sys.stdout.reconfigure(encoding='utf-8')

screenshot_dir = r'e:\Do_an_SU26\SuperMarketBot-Android-Robot\screenShot'
media_dir = r'e:\Do_an_SU26\antigravity-doc-handler\extracted_docx_media'

with open('images_info.json', 'r', encoding='utf-8') as f:
    images = json.load(f)

# Let's inspect where all 152 images in extracted_docx_media appear across the doc
print(f"Total entries in images_info: {len(images)}")

# Map each media file to all paragraphs and sections it appears in
media_usage = {}
for img in images:
    target = os.path.basename(img['target'])
    if target not in media_usage:
        media_usage[target] = []
    media_usage[target].append(f"P[{img['p_idx']}] {img['h2']} -> {img['h3']}")

print(f"Total unique media targets in doc: {len(media_usage)}")
for target, places in sorted(media_usage.items()):
    if len(places) > 1:
        print(f"{target} is used in MULTIPLE places ({len(places)}):")
        for p in places:
            print(f"   {p}")

