import os
import json
from PIL import Image
import numpy as np
import sys
sys.stdout.reconfigure(encoding='utf-8')

screenshot_dir = r'e:\Do_an_SU26\SuperMarketBot-Android-Robot\screenShot'
media_dir = r'e:\Do_an_SU26\antigravity-doc-handler\extracted_docx_media'

# Load all screenshots from screenShot dir
ss_dict = {}
for f in os.listdir(screenshot_dir):
    p = os.path.join(screenshot_dir, f)
    if os.path.isfile(p) and not f.endswith('.docx') and not f.startswith('~$'):
        with Image.open(p) as im:
            ss_dict[f] = im.convert('RGB')

# Also check if there are other images in SuperMarketBot-Android-Robot or Android or Web
print(f"Loaded {len(ss_dict)} screenshots from screenShot/")

sec32_media = [
    ('image148.jpg', 97, '3.2.1 System Startup & Idle Kiosk Mode'),
    ('image25.jpg', 97, '3.2.1 System Startup & Idle Kiosk Mode'),
    ('image60.jpg', 124, '3.2.2 User Onboarding & Face ID Authentication'),
    ('image58.jpg', 124, '3.2.2 User Onboarding & Face ID Authentication'),
    ('image29.jpg', 124, '3.2.2 User Onboarding & Face ID Authentication'),
    ('image31.jpg', 124, '3.2.2 User Onboarding & Face ID Authentication'),
    ('image70.jpg', 150, '3.2.3 Guest Shopping Experience & Daily Promotions'),
    ('image78.jpg', 150, '3.2.3 Guest Shopping Experience & Daily Promotions'),
    ('image1.png', 150, '3.2.3 Guest Shopping Experience & Daily Promotions'),
    ('image37.jpg', 173, '3.2.4 Member Personalization & Special Offers'),
    ('image33.jpg', 173, '3.2.4 Member Personalization & Special Offers'),
    ('image54.jpg', 174, '3.2.4 Member Personalization & Special Offers'),
    ('image1.png', 174, '3.2.4 Member Personalization & Special Offers'),
    ('image18.jpg', 199, '3.2.5 Smart Search & AI Voice Assistant'),
    ('image7.jpg', 199, '3.2.5 Smart Search & AI Voice Assistant'),
    ('image117.jpg', 200, '3.2.5 Smart Search & AI Voice Assistant'),
    ('image46.jpg', 226, '3.2.6 Product Detail & Instant Cart Operations'),
    ('image97.jpg', 250, '3.2.7 Smart Cart & Autonomous Robot Navigation Guide'),
    ('image35.jpg', 250, '3.2.7 Smart Cart & Autonomous Robot Navigation Guide'),
    ('image63.jpg', 250, '3.2.7 Smart Cart & Autonomous Robot Navigation Guide'),
    ('image65.jpg', 250, '3.2.7 Smart Cart & Autonomous Robot Navigation Guide'),
    ('image61.png', 250, '3.2.7 Smart Cart & Autonomous Robot Navigation Guide'),
    ('image6.png', 250, '3.2.7 Smart Cart & Autonomous Robot Navigation Guide'),
    ('image36.png', 279, '3.2.8 Contextual Overlays & Autonomous Advertising'),
    ('image42.png', 279, '3.2.8 Contextual Overlays & Autonomous Advertising'),
]

for m, p_idx, sec in sec32_media:
    mpath = os.path.join(media_dir, m)
    if not os.path.exists(mpath):
        continue
    with Image.open(mpath) as im:
        im_rgb = im.convert('RGB')
        # find closest match in ss_dict
        im_resized = im_rgb.resize((100, 200), Image.Resampling.BILINEAR)
        arr = np.array(im_resized, dtype=np.float32)
        
        best_diff = 999999
        best_name = None
        for sname, sim in ss_dict.items():
            s_resized = sim.resize((100, 200), Image.Resampling.BILINEAR)
            sarr = np.array(s_resized, dtype=np.float32)
            diff = np.mean(np.abs(arr - sarr))
            if diff < best_diff:
                best_diff = diff
                best_name = sname
        print(f"P[{p_idx:3d}] {sec[:30]:30s} | {m:12s} ({im.size[0]:4d}x{im.size[1]:4d}) -> Best: {best_name:32s} (diff={best_diff:5.2f})")
