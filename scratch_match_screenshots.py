import os
import hashlib
import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

screenshot_dir = r'e:\Do_an_SU26\SuperMarketBot-Android-Robot\screenShot'
media_dir = r'e:\Do_an_SU26\antigravity-doc-handler\extracted_docx_media'

def get_hash(filepath):
    h = hashlib.md5()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

# Hash all screenshots
ss_hashes = {}
for fname in os.listdir(screenshot_dir):
    fpath = os.path.join(screenshot_dir, fname)
    if os.path.isfile(fpath) and not fname.endswith('.docx') and not fname.startswith('~$'):
        ss_hashes[get_hash(fpath)] = fname

print(f"Hashed {len(ss_hashes)} screenshots in screenShot/")

# Compare with extracted media
matched = {}
for mname in os.listdir(media_dir):
    mpath = os.path.join(media_dir, mname)
    mhash = get_hash(mpath)
    if mhash in ss_hashes:
        matched[mname] = ss_hashes[mhash]

print(f"Matched {len(matched)} media files to screenShot/ files:")
for mname, ssname in sorted(matched.items()):
    print(f"  {mname} <==> {ssname}")

with open('images_info.json', 'r', encoding='utf-8') as f:
    images = json.load(f)

print("\n=== Placement of matched screenshots in document ===")
for img in images:
    t = os.path.basename(img['target'])
    if t in matched:
        print(f"P[{img['p_idx']:4d}] | {img['h2'][:25]} -> {img['h3'][:35]} | {t} ({matched[t]})")
    elif img['p_idx'] <= 310:
        print(f"P[{img['p_idx']:4d}] | {img['h2'][:25]} -> {img['h3'][:35]} | {t} (UNMATCHED TO SCREENSHOT DIR)")
