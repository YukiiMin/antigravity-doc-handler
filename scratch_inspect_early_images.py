import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('images_info.json', 'r', encoding='utf-8') as f:
    images = json.load(f)

print("=== Images in Paragraphs 0 to 310 ===")
for img in images:
    if img['p_idx'] <= 310:
        print(f"P[{img['p_idx']}] | H2: {img['h2']} | H3: {img['h3']} | Target: {img['target']}")
