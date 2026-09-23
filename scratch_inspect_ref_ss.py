import os
from PIL import Image
import numpy as np
import sys
sys.stdout.reconfigure(encoding='utf-8')

screenshot_dir = r'e:\Do_an_SU26\SuperMarketBot-Android-Robot\screenShot'
media_dir = r'e:\Do_an_SU26\antigravity-doc-handler\extracted_docx_media'

# Let's inspect all files in screenshot_dir
print("=== Files in screenShot/ ===")
for f in sorted(os.listdir(screenshot_dir)):
    p = os.path.join(screenshot_dir, f)
    if os.path.isfile(p) and not f.endswith('.docx') and not f.startswith('~$'):
        with Image.open(p) as im:
            print(f"{f:35s}: {im.size} mode={im.mode}")
