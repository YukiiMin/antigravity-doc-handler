"""
Draw.io (mxGraphModel) 4-Gate Automated Quality Assurance Script
Validates:
  Gate 1: XML Well-Formedness & Closing Tags
  Gate 2: Unique IDs & Valid Parent Hierarchy
  Gate 3: Zero AABB Bounding Box Collisions
  Gate 4: Clean Edge Connections (No Dangling Edges)
"""

import sys
import argparse
import xml.etree.ElementTree as ET
from typing import List, Dict, Tuple, Set

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def run_4gate_validation(file_path: str, safety_margin: float = 8.0) -> bool:
    print(f"\n{'='*60}")
    print(f"RUNNING 4-GATE QA ON: {file_path}")
    print(f"{'='*60}")

    # --- GATE 1: XML Well-Formedness ---
    print("\n[GATE 1] XML Well-Formedness & Closing Tags...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        if not (content.endswith('</root></mxGraphModel>') or content.endswith('</mxGraphModel>')):
            print("  [FAIL] GATE 1 FAILED: Missing valid root closing tag </mxGraphModel>!")
            return False

        tree = ET.parse(file_path)
        root = tree.getroot()
        print("  [PASS] GATE 1 PASSED: XML is completely well-formed with clean closing tags.")
    except Exception as e:
        print(f"  [FAIL] GATE 1 FAILED: XML Parse Error: {e}")
        return False

    # Check for forbidden dynamic tags (MX_INV_01)
    user_objects = list(root.iter('UserObject'))
    for uo in user_objects:
        if 'mermaidData' in uo.attrib or 'plantUmlData' in uo.attrib:
            print("  [FAIL] GATE 1 FAILED (MX_INV_01 Violation): Found dynamic UserObject with mermaidData/plantUmlData!")
            return False

    # --- GATE 2: Unique IDs & Valid Parents ---
    print("\n[GATE 2] Unique Element IDs & Parent Hierarchy...")
    all_ids: Set[str] = set()
    duplicate_ids: List[str] = []
    
    for elem in root.iter():
        eid = elem.get('id')
        if eid is not None:
            if eid in all_ids:
                duplicate_ids.append(eid)
            all_ids.add(eid)

    if duplicate_ids:
        print(f"  [FAIL] GATE 2 FAILED: Duplicate IDs found: {duplicate_ids}")
        return False

    missing_parents: List[Tuple[str, str]] = []
    for cell in root.iter('mxCell'):
        parent = cell.get('parent')
        if parent is not None and parent not in all_ids:
            missing_parents.append((cell.get('id', ''), parent))

    if missing_parents:
        print(f"  [FAIL] GATE 2 FAILED: Elements reference non-existent parents: {missing_parents}")
        return False

    print(f"  [PASS] GATE 2 PASSED: {len(all_ids)} elements validated. Zero duplicates, all parents valid.")

    # --- GATE 3: AABB Collision Check ---
    print(f"\n[GATE 3] Table Collision Check (Safety Margin: {safety_margin}px)...")
    tables: Dict[str, Dict[str, float]] = {}
    for cell in root.iter('mxCell'):
        style = cell.get('style', '')
        if 'shape=table;' in style:
            name = cell.get('value', cell.get('id'))
            geo = cell.find('mxGeometry')
            if geo is not None:
                tables[name] = {
                    'x': float(geo.get('x', 0)),
                    'y': float(geo.get('y', 0)),
                    'w': float(geo.get('width', 0)),
                    'h': float(geo.get('height', 0))
                }

    print(f"  Detected {len(tables)} tables on canvas.")
    collisions: List[Tuple[str, str]] = []
    tnames = list(tables.keys())

    for i in range(len(tnames)):
        for j in range(i + 1, len(tnames)):
            t1 = tables[tnames[i]]
            t2 = tables[tnames[j]]
            # AABB overlap test with margin
            if not (t1['x'] + t1['w'] + safety_margin <= t2['x'] or
                    t2['x'] + t2['w'] + safety_margin <= t1['x'] or
                    t1['y'] + t1['h'] + safety_margin <= t2['y'] or
                    t2['y'] + t2['h'] + safety_margin <= t1['y']):
                collisions.append((tnames[i], tnames[j]))

    if collisions:
        print(f"  [FAIL] GATE 3 FAILED: Table bounding box collisions detected: {collisions}")
        return False

    print(f"  [PASS] GATE 3 PASSED: Zero collisions across {len(tables)} tables.")

    # --- GATE 4: Clean Edge Connections ---
    print("\n[GATE 4] Edge Routing & Endpoint Integrity...")
    edges = [c for c in root.iter('mxCell') if c.get('edge') == '1']
    broken_edges: List[Tuple[str, str, str]] = []
    inner_docking_edges: List[str] = []

    for e in edges:
        eid = e.get('id', '')
        src = e.get('source')
        tgt = e.get('target')

        if not src or not tgt or src not in all_ids or tgt not in all_ids:
            broken_edges.append((eid, str(src), str(tgt)))

        # MX_INV_03 check: Ensure edge connects to table container, not inner cell
        if src and not src.startswith('table_'):
            inner_docking_edges.append(f"{eid} source ({src})")
        if tgt and not tgt.startswith('table_'):
            inner_docking_edges.append(f"{eid} target ({tgt})")

    if broken_edges:
        print(f"  [FAIL] GATE 4 FAILED: Broken/Dangling edges found: {broken_edges}")
        return False

    if inner_docking_edges:
        print(f"  [FAIL] GATE 4 FAILED (MX_INV_03 Violation): Edges docked to inner cells instead of tables: {inner_docking_edges[:5]}")
        return False

    print(f"  [PASS] GATE 4 PASSED: All {len(edges)} edges connect valid table containers directly.")

    print(f"\n{'='*60}")
    print("[SUCCESS] ALL 4 GATES PASSED CLEANLY (100% DRAW.IO COMPATIBLE)")
    print(f"{'='*60}\n")
    return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Validate Draw.io XML / drawio files.")
    parser.add_argument('file', nargs='?', default='Docs/output/ERD-Data-position.xml', help="Path to XML or drawio file")
    parser.add_argument('--margin', type=float, default=8.0, help="Safety margin for collision check in px")
    args = parser.parse_args()

    success = run_4gate_validation(args.file, safety_margin=args.margin)
    sys.exit(0 if success else 1)
