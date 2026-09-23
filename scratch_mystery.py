import os
from PIL import Image
import sys
sys.stdout.reconfigure(encoding='utf-8')

media_dir = r'e:\Do_an_SU26\antigravity-doc-handler\extracted_docx_media'

mystery_images = [
    'image148.jpg', 'image25.jpg', 'image58.jpg', 'image31.jpg',
    'image1.png', 'image7.jpg', 'image63.jpg', 'image65.jpg',
    'image61.png', 'image6.png', 'image36.png', 'image42.png'
]

print("=== Inspect Mystery Images in Section 3.2 ===")
for m in mystery_images:
    p = os.path.join(media_dir, m)
    if os.path.exists(p):
        with Image.open(p) as im:
            print(f"{m:15s}: size={im.size} mode={im.mode} format={im.format}")
