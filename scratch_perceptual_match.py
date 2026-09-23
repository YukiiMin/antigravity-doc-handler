import os
from PIL import Image
import numpy as np
import sys
sys.stdout.reconfigure(encoding='utf-8')

screenshot_dir = r'e:\Do_an_SU26\SuperMarketBot-Android-Robot\screenShot'
media_dir = r'e:\Do_an_SU26\antigravity-doc-handler\extracted_docx_media'

# Load and downscale all screenshots to 100x200 grayscale
ss_thumb = {}
for f in sorted(os.listdir(screenshot_dir)):
    p = os.path.join(screenshot_dir, f)
    if os.path.isfile(p) and not f.endswith('.docx') and not f.startswith('~$'):
        with Image.open(p) as im:
            im_gray = im.convert('L').resize((100, 200), Image.Resampling.BILINEAR)
            ss_thumb[f] = np.array(im_gray, dtype=np.float32)

print(f"Loaded {len(ss_thumb)} reference screenshots.")

sec32_media = [
    'image148.jpg', 'image25.jpg', 'image60.jpg', 'image58.jpg', 'image29.jpg',
    'image31.jpg', 'image70.jpg', 'image78.jpg', 'image1.png', 'image37.jpg',
    'image33.jpg', 'image54.jpg', 'image18.jpg', 'image7.jpg', 'image117.jpg',
    'image46.jpg', 'image97.jpg', 'image35.jpg', 'image63.jpg', 'image65.jpg',
    'image61.png', 'image6.png', 'image36.png', 'image42.png'
]

print("\n--- Matching Section 3.2 docx images to screenShot/ files ---")
for m in sec32_media:
    p = os.path.join(media_dir, m)
    if not os.path.exists(p):
        continue
    with Image.open(p) as im:
        im_gray = im.convert('L').resize((100, 200), Image.Resampling.BILINEAR)
        arr = np.array(im_gray, dtype=np.float32)
        
        best_name = None
        best_diff = 99999999
        for sname, sarr in ss_thumb.items():
            diff = np.mean(np.abs(arr - sarr))
            if diff < best_diff:
                best_diff = diff
                best_name = sname
        print(f"{m:15s} -> Best match: {best_name:32s} (diff={best_diff:6.2f})")
