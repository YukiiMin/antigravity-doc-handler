import os
from PIL import Image
import sys
sys.stdout.reconfigure(encoding='utf-8')

screenshot_dir = r'e:\Do_an_SU26\SuperMarketBot-Android-Robot\screenShot'
media_dir = r'e:\Do_an_SU26\antigravity-doc-handler\extracted_docx_media'

print("--- Files in screenShot/ ---")
for f in sorted(os.listdir(screenshot_dir)):
    p = os.path.join(screenshot_dir, f)
    if os.path.isfile(p) and not f.endswith('.docx') and not f.startswith('~$'):
        with Image.open(p) as im:
            print(f"{f:35s}: {im.size} mode={im.mode}")

print("\n--- Media files in Section 3.2 docx ---")
sec32_media = [
    'image148.jpg', 'image25.jpg', 'image60.jpg', 'image58.jpg', 'image29.jpg',
    'image31.jpg', 'image70.jpg', 'image78.jpg', 'image1.png', 'image37.jpg',
    'image33.jpg', 'image54.jpg', 'image18.jpg', 'image7.jpg', 'image117.jpg',
    'image46.jpg', 'image97.jpg', 'image35.jpg', 'image63.jpg', 'image65.jpg',
    'image61.png', 'image6.png', 'image36.png', 'image42.png'
]

for m in sec32_media:
    p = os.path.join(media_dir, m)
    if os.path.exists(p):
        with Image.open(p) as im:
            print(f"{m:20s}: {im.size} mode={im.mode}")
