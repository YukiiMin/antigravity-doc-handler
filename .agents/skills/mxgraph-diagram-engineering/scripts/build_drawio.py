"""
Draw.io (mxGraphModel) Native Diagram Builder
Generates pure native Draw.io XML/drawio files adhering to rule_mxgraph_drawio_diagram_standards.md.
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional

TABLE_STYLE = (
    "shape=table;startSize=43;container=1;collapsible=0;childLayout=tableLayout;"
    "fixedRows=1;rowLines=1;fontSize=16;fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;"
    "strokeWidth=1;align=center;resizeLast=1;html=1;"
)

ROW_STYLE = (
    "shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=1;"
    "strokeWidth=1;collapsible=0;dropTarget=0;points=[[0,0.5],[1,0.5]];"
    "portConstraint=eastwest;top=0;left=0;right=0;bottom=0;"
)

CELL_STYLE = (
    "shape=partialRectangle;connectable=0;strokeWidth=1;"
    "fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;top=1;left=1;bottom=1;right=1;"
    "align=left;spacingLeft=8;overflow=hidden;fontSize=16;"
)

EDGE_BASE_STYLE = (
    "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;"
    "strokeColor=light-dark(#9370DB,#cccccc);strokeWidth=1;"
)

def create_native_drawio_tree(
    entities: Dict[str, List[Dict[str, str]]],
    positions: Dict[str, Dict[str, float]],
    edges: List[Dict[str, Any]],
    canvas_w: int = 850,
    canvas_h: int = 1100
) -> ET.Element:
    """
    Builds a pure native mxGraphModel XML tree.
    entities: { 'TABLE_NAME': [{'name': 'ID', 'type': 'int', 'key': 'PK'}, ...] }
    positions: { 'TABLE_NAME': {'x': 100.0, 'y': 200.0} }
    edges: [ {'source': 'table_A', 'target': 'table_B', 'style': '...'} ]
    """
    out_root = ET.Element('mxGraphModel', {
        'dx': '2060',
        'dy': '1124',
        'grid': '1',
        'gridSize': '10',
        'guides': '1',
        'tooltips': '1',
        'connect': '1',
        'arrows': '1',
        'fold': '1',
        'page': '1',
        'pageScale': '1',
        'pageWidth': str(canvas_w),
        'pageHeight': str(canvas_h),
        'math': '0',
        'shadow': '0'
    })

    root_tag = ET.SubElement(out_root, 'root')
    ET.SubElement(root_tag, 'mxCell', {'id': '0'})
    ET.SubElement(root_tag, 'mxCell', {'id': '1', 'parent': '0'})

    # Build Tables
    for tname, fields in entities.items():
        pos = positions.get(tname, {'x': 100.0, 'y': 100.0})
        x_val = str(pos['x'])
        y_val = str(pos['y'])
        row_count = len(fields)
        t_height = str(43 * (row_count + 1))
        t_width = "278"

        tid = f"table_{tname}"
        tcell = ET.SubElement(root_tag, 'mxCell', {
            'id': tid,
            'value': tname,
            'style': TABLE_STYLE,
            'vertex': '1',
            'parent': '1'
        })
        ET.SubElement(tcell, 'mxGeometry', {
            'x': x_val,
            'y': y_val,
            'width': t_width,
            'height': t_height,
            'as': 'geometry'
        })

        # Rows
        for i, f in enumerate(fields, 1):
            rid = f"row_{tname}_{i}"
            rcell = ET.SubElement(root_tag, 'mxCell', {
                'id': rid,
                'style': ROW_STYLE,
                'vertex': '1',
                'parent': tid
            })
            ET.SubElement(rcell, 'mxGeometry', {
                'y': str(43 * i),
                'width': t_width,
                'height': '43',
                'as': 'geometry'
            })

            # Column 1: Type (82px)
            c1 = ET.SubElement(root_tag, 'mxCell', {
                'id': f"{rid}_c1",
                'value': f.get('type', ''),
                'style': CELL_STYLE,
                'vertex': '1',
                'parent': rid
            })
            ET.SubElement(c1, 'mxGeometry', {'width': '82', 'height': '43', 'as': 'geometry'})

            # Column 2: Name (153px)
            c2 = ET.SubElement(root_tag, 'mxCell', {
                'id': f"{rid}_c2",
                'value': f.get('name', ''),
                'style': CELL_STYLE,
                'vertex': '1',
                'parent': rid
            })
            ET.SubElement(c2, 'mxGeometry', {'x': '82', 'width': '153', 'height': '43', 'as': 'geometry'})

            # Column 3: Key (43px)
            c3 = ET.SubElement(root_tag, 'mxCell', {
                'id': f"{rid}_c3",
                'value': f.get('key', ''),
                'style': CELL_STYLE,
                'vertex': '1',
                'parent': rid
            })
            ET.SubElement(c3, 'mxGeometry', {'x': '235', 'width': '43', 'height': '43', 'as': 'geometry'})

    # Build Edges
    for idx, e in enumerate(edges, 1):
        eid = f"edge_{idx}"
        style = e.get('style', EDGE_BASE_STYLE)
        ecell = ET.SubElement(root_tag, 'mxCell', {
            'id': eid,
            'edge': '1',
            'parent': '1',
            'source': e['source'],
            'target': e['target'],
            'style': style
        })
        ET.SubElement(ecell, 'mxGeometry', {'relative': '1', 'as': 'geometry'})

    return out_root

def write_drawio_files(out_root: ET.Element, base_path_no_ext: str):
    """
    Saves dual files (.xml and .drawio) for seamless compatibility.
    """
    ET.indent(out_root, space='  ')
    xml_bytes = ET.tostring(out_root, encoding='utf-8', xml_declaration=False)
    xml_str = xml_bytes.decode('utf-8')

    for ext in ['.xml', '.drawio']:
        target = f"{base_path_no_ext}{ext}"
        with open(target, 'w', encoding='utf-8') as f:
            f.write(xml_str)
        print(f"Exported: {target} ({len(xml_str):,} bytes)")

if __name__ == '__main__':
    print("mxGraphModel Native Diagram Builder module loaded successfully.")
