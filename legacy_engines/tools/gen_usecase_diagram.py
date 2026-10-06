"""
tools/gen_usecase_diagram.py — Pixel-perfect Use Case Diagram Generator.

Strictly adheres to UML 2.5 standards and the reference diagram:
- Association: Plain solid line (Actor to Use Case)
- <<include>>: Dashed line with open arrowhead (-->)
- <<extend>>: Dashed line with open arrowhead (-->)
- Generalization: Solid line with hollow white triangle arrowhead (──▷)
  * Used for Actor inheritance (Customer, Admin, Staff -> Authenticated User)
  * Used for Use Case specialization (all sub-actions -> central hubs)
- Publication-grade vector SVG + 300+ DPI PNG rendering via Chromium/Edge headless.
"""

from __future__ import annotations

import html
import json
import math
import os
import shutil
import subprocess
import sys
from typing import Any
from PIL import Image

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


def get_ellipse_intersection(
    cx: float, cy: float, rx: float, ry: float, ox: float, oy: float
) -> tuple[float, float]:
    """Calculate the intersection of the line from external point (ox, oy) to ellipse center (cx, cy)."""
    dx = ox - cx
    dy = oy - cy
    if abs(dx) < 1e-6 and abs(dy) < 1e-6:
        return (cx, cy)
    theta = math.atan2(dy, dx)
    return (cx + rx * math.cos(theta), cy + ry * math.sin(theta))


def get_ellipse_to_ellipse_points(
    cx1: float, cy1: float, rx1: float, ry1: float,
    cx2: float, cy2: float, rx2: float, ry2: float
) -> tuple[tuple[float, float], tuple[float, float]]:
    """Calculate contact points on perimeter between two ellipses."""
    p1 = get_ellipse_intersection(cx1, cy1, rx1, ry1, cx2, cy2)
    p2 = get_ellipse_intersection(cx2, cy2, rx2, ry2, cx1, cy1)
    return p1, p2


# ==============================================================================
# 1. NODE SPECIFICATION (48 Use Cases)
# ==============================================================================
USE_CASES = {
    # Hub: Manage Ad Campaign & Sub-actions (Top Hub)
    "cancel_campaign": {"cx": 400.0, "cy": 79.5, "rx": 37.0, "ry": 24.0, "text": "Cancel\nCampaign"},
    "resume_campaign": {"cx": 484.5, "cy": 70.5, "rx": 37.0, "ry": 24.0, "text": "Resume\nCampaign"},
    "pause_campaign": {"cx": 607.5, "cy": 75.5, "rx": 38.0, "ry": 23.0, "text": "Pause Campaign"},
    "update_campaign": {"cx": 704.5, "cy": 77.5, "rx": 37.0, "ry": 24.0, "text": "Update\nCampaign"},
    "create_campaign": {"cx": 797.0, "cy": 82.5, "rx": 41.0, "ry": 23.0, "text": "Create Campaign"},
    "config_ad_params": {"cx": 387.0, "cy": 138.5, "rx": 43.0, "ry": 25.0, "text": "Configure Ad\nParameters"},
    "manage_ad_campaign": {"cx": 591.5, "cy": 151.0, "rx": 43.0, "ry": 25.0, "text": "Manage Ad\nCampaign"},
    "view_campaign_log": {"cx": 453.0, "cy": 182.5, "rx": 42.0, "ry": 24.0, "text": "View Campaign\nLog"},
    "view_campaign_dash": {"cx": 528.0, "cy": 223.5, "rx": 43.0, "ry": 25.0, "text": "View Campaign\nDashboard"},

    # Top-Left Authentication (Connected to Authenticated User)
    "login": {"cx": 283.0, "cy": 112.5, "rx": 38.0, "ry": 24.0, "text": "Login"},
    "logout": {"cx": 283.0, "cy": 177.5, "rx": 38.0, "ry": 24.0, "text": "Logout"},
    "forgot_password": {"cx": 283.0, "cy": 246.5, "rx": 43.0, "ry": 24.0, "text": "ForgotPassword"},

    # Hub: Manage Account & Sub-actions
    "create_account": {"cx": 682.5, "cy": 174.5, "rx": 38.0, "ry": 24.0, "text": "Create Account"},
    "manage_account": {"cx": 822.5, "cy": 167.5, "rx": 43.0, "ry": 25.0, "text": "Manage Account"},
    "update_account": {"cx": 611.5, "cy": 217.5, "rx": 38.0, "ry": 24.0, "text": "Update Account"},
    "delete_account": {"cx": 695.0, "cy": 239.5, "rx": 38.0, "ry": 24.0, "text": "Delete Account"},

    # Hub: Manage Map & Waypoints & Sub-actions
    "create_map": {"cx": 404.0, "cy": 232.5, "rx": 42.0, "ry": 24.0, "text": "Create Map &\nWaypoints"},
    "delete_map": {"cx": 481.5, "cy": 288.5, "rx": 41.0, "ry": 24.0, "text": "Delete Map &\nWaypoints"},
    "update_map": {"cx": 401.5, "cy": 299.5, "rx": 42.0, "ry": 24.0, "text": "Update Map &\nWaypoints"},
    "manage_map": {"cx": 649.5, "cy": 302.0, "rx": 48.0, "ry": 27.0, "text": "Manage Map &\nWaypoints"},

    # Robot Management
    "manage_robot": {"cx": 767.0, "cy": 327.5, "rx": 42.0, "ry": 25.0, "text": "Manage Robot"},
    "manage_auto_ad": {"cx": 530.0, "cy": 369.0, "rx": 48.0, "ry": 27.0, "text": "Manage\nAutonomous\nAdvertisement"},
    "set_ad_path": {"cx": 424.0, "cy": 357.5, "rx": 41.0, "ry": 24.0, "text": "Set Advertise\nPath"},
    "cancel_ad": {"cx": 423.5, "cy": 427.0, "rx": 42.0, "ry": 25.0, "text": "Cancel\nAdvertisement"},

    # Customer Personal Functions (Mid Left)
    "set_budget": {"cx": 314.0, "cy": 368.5, "rx": 38.0, "ry": 24.0, "text": "Set Budget"},
    "view_invoice_hist": {"cx": 314.0, "cy": 426.5, "rx": 39.0, "ry": 24.0, "text": "View Invoice\nHistory"},
    "set_allergic": {"cx": 312.0, "cy": 492.5, "rx": 41.0, "ry": 24.0, "text": "Set Allergic Items"},

    # Master Data: Import Supermarket, Brand, Product Trees
    "import_supermarket": {"cx": 851.5, "cy": 352.5, "rx": 42.0, "ry": 26.0, "text": "Import\nSupermarket\nData"},
    "import_brand": {"cx": 657.0, "cy": 417.5, "rx": 42.0, "ry": 25.0, "text": "Import Brand\nData"},
    "create_brand": {"cx": 518.0, "cy": 436.5, "rx": 40.0, "ry": 24.0, "text": "Create Brand"},
    "update_brand": {"cx": 495.5, "cy": 516.5, "rx": 40.0, "ry": 24.0, "text": "Update Brand"},
    "delete_brand": {"cx": 619.0, "cy": 511.0, "rx": 41.0, "ry": 24.0, "text": "Delete Brand"},

    "import_product": {"cx": 816.0, "cy": 439.5, "rx": 42.0, "ry": 25.0, "text": "Import Product\nData"},
    "create_product": {"cx": 689.5, "cy": 531.5, "rx": 40.0, "ry": 24.0, "text": "Create Product"},
    "update_product": {"cx": 774.0, "cy": 531.5, "rx": 40.0, "ry": 24.0, "text": "Update Product"},
    "delete_product": {"cx": 868.5, "cy": 534.5, "rx": 40.0, "ry": 24.0, "text": "Delete Product"},

    # Staff Store Operations
    "view_map": {"cx": 578.0, "cy": 567.5, "rx": 39.0, "ry": 24.0, "text": "View Map"},
    "view_robot_status": {"cx": 503.0, "cy": 609.5, "rx": 41.0, "ry": 24.0, "text": "View Robot\nStatus"},
    "update_refill": {"cx": 626.0, "cy": 647.5, "rx": 45.0, "ry": 24.0, "text": "Update Refill Status"},
    "view_shelf_status": {"cx": 562.5, "cy": 699.5, "rx": 44.0, "ry": 24.0, "text": "View Shelf Status"},
    "stock_alert": {"cx": 741.5, "cy": 703.0, "rx": 44.0, "ry": 24.0, "text": "Receive Out-of-\nStock Alert"},

    # Route Guidance & Item Search
    "route_guidance": {"cx": 228.5, "cy": 612.5, "rx": 45.0, "ry": 24.0, "text": "Request Route\nGuidance"},
    "search_item": {"cx": 230.0, "cy": 689.5, "rx": 39.0, "ry": 24.0, "text": "Search Item"},

    # Guest Registration & Customer Interaction
    "register": {"cx": 251.5, "cy": 827.5, "rx": 40.0, "ry": 24.0, "text": "Register"},
    "interact_ad": {"cx": 413.0, "cy": 690.0, "rx": 45.0, "ry": 28.0, "text": "Interact with\nAdvertisement"},

    # Robot Bottom Tasks
    "scan_shelf": {"cx": 668.5, "cy": 789.5, "rx": 41.0, "ry": 24.0, "text": "Scan Shelf\nInventory"},
    "broadcast_ad": {"cx": 611.5, "cy": 839.5, "rx": 42.0, "ry": 24.0, "text": "Broadcast\nAdvertisement"},
    "patrol": {"cx": 733.0, "cy": 872.0, "rx": 42.0, "ry": 24.0, "text": "Execute\nAutonomous\nPatrol"},
}

# ==============================================================================
# 2. ACTORS SPECIFICATION (Stickmen Outside Rectangle)
# ==============================================================================
ACTORS = {
    "auth_user": {
        "head_cx": 93.0, "head_cy": 190.0, "label": "Authenticated User", "label_y": 258.0,
        "anchor": (93.0, 210.0), "side": "left"
    },
    "customer": {
        "head_cx": 90.0, "head_cy": 467.0, "label": "Customer", "label_y": 535.0,
        "anchor": (90.0, 487.0), "side": "left"
    },
    "guest": {
        "head_cx": 90.0, "head_cy": 772.0, "label": "Guest", "label_y": 840.0,
        "anchor": (90.0, 792.0), "side": "left"
    },
    "admin": {
        "head_cx": 948.0, "head_cy": 133.0, "label": "Admin", "label_y": 201.0,
        "anchor": (948.0, 153.0), "side": "right"
    },
    "staff": {
        "head_cx": 955.0, "head_cy": 600.0, "label": "Staff", "label_y": 668.0,
        "anchor": (955.0, 620.0), "side": "right"
    },
    "robot": {
        "head_cx": 955.0, "head_cy": 792.0, "label": "Robot", "label_y": 860.0,
        "anchor": (955.0, 812.0), "side": "right"
    },
}

# Actor Associations: Solid line, NO arrowhead (Standard UML Association)
ACTOR_ASSOCIATIONS = [
    # Authenticated User
    ("auth_user", "login", (93.0, 206.0)),
    ("auth_user", "logout", (93.0, 214.0)),
    ("auth_user", "forgot_password", (93.0, 224.0)),

    # Customer
    ("customer", "set_budget", (90.0, 475.0)),
    ("customer", "view_invoice_hist", (90.0, 485.0)),
    ("customer", "set_allergic", (90.0, 495.0)),
    ("customer", "search_item", (90.0, 515.0)),     # Starts lower to cleanly avoid route_guidance
    ("customer", "interact_ad", (90.0, 502.0)),

    # Guest
    ("guest", "search_item", (90.0, 790.0)),
    ("guest", "register", (90.0, 804.0)),

    # Admin
    ("admin", "manage_ad_campaign", (948.0, 140.0)),
    ("admin", "manage_account", (948.0, 148.0)),
    ("admin", "manage_map", (948.0, 154.0)),
    ("admin", "manage_robot", (948.0, 160.0)),
    ("admin", "import_supermarket", (948.0, 166.0)),

    # Staff
    ("staff", "view_map", (945.0, 610.0)),
    ("staff", "view_robot_status", (945.0, 614.0)),
    ("staff", "update_refill", (945.0, 618.0)),
    ("staff", "view_shelf_status", (945.0, 622.0)),
    ("staff", "stock_alert", (945.0, 626.0)),

    # Robot
    ("robot", "scan_shelf", (945.0, 802.0)),
    ("robot", "broadcast_ad", (945.0, 808.0)),
    ("robot", "patrol", (945.0, 814.0)),
]

# Use Case Specialization (Generalization): Solid line with hollow white triangle arrowhead (──▷)
# Pointing INTO the generalized hub use cases!
GENERALIZATION_ARROWS = [
    # Hub: manage_ad_campaign
    ("cancel_campaign", "manage_ad_campaign"),
    ("resume_campaign", "manage_ad_campaign"),
    ("pause_campaign", "manage_ad_campaign"),
    ("update_campaign", "manage_ad_campaign"),
    ("create_campaign", "manage_ad_campaign"),
    ("config_ad_params", "manage_ad_campaign"),
    ("view_campaign_log", "manage_ad_campaign"),
    ("view_campaign_dash", "manage_ad_campaign"),

    # Hub: manage_account
    ("create_account", "manage_account"),
    ("update_account", "manage_account"),
    ("delete_account", "manage_account"),

    # Hub: manage_map
    ("create_map", "manage_map"),
    ("update_map", "manage_map"),
    ("delete_map", "manage_map"),

    # Hub: manage_auto_ad
    ("set_ad_path", "manage_auto_ad"),
    ("cancel_ad", "manage_auto_ad"),

    # Link: manage_auto_ad -> manage_robot
    ("manage_auto_ad", "manage_robot"),

    # Hub: import_brand
    ("create_brand", "import_brand"),
    ("update_brand", "import_brand"),
    ("delete_brand", "import_brand"),

    # Hub: import_product
    ("create_product", "import_product"),
    ("update_product", "import_product"),
    ("delete_product", "import_product"),

    # Hub: import_supermarket
    ("import_brand", "import_supermarket"),
    ("import_product", "import_supermarket"),
]

# Stereotypes: Dashed line with open arrowhead (-->) and <<label>>
STEREOTYPE_ARROWS = [
    ("search_item", "route_guidance", "<<include>>", (0.0, 0.0)),
    ("scan_shelf", "stock_alert", "<<include>>", (-8.0, -8.0)),
    ("broadcast_ad", "interact_ad", "<<extend>>", (0.0, 0.0)),
]


def generate_usecase_svg() -> str:
    """Generate pixel-perfect SVG string matching reference image and UML standards."""
    svg: list[str] = []

    width = 1024
    height = 901

    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">')
    svg.append("""  <defs>
    <!-- Open arrowhead for <<include>> / <<extend>> dashed dependencies -->
    <marker id="arrow-open" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse">
      <polyline points="1,1 9,5 1,9" fill="none" stroke="#000000" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
    </marker>
    <!-- Closed hollow triangle for UML Generalization (white fill, black stroke) -->
    <marker id="arrow-generalization" viewBox="0 0 14 14" refX="13" refY="7" markerWidth="9.5" markerHeight="9.5" orient="auto-start-reverse">
      <polygon points="1,2 13,7 1,12" fill="#FFFFFF" stroke="#000000" stroke-width="1.3" stroke-linejoin="round"/>
    </marker>
  </defs>""")

    # Background
    svg.append(f'  <rect x="0" y="0" width="{width}" height="{height}" fill="#FFFFFF"/>')

    # System boundary box
    box_x = 138.0
    box_y = 45.0
    box_w = 775.0
    box_h = 848.0
    svg.append(f'  <rect x="{box_x:.1f}" y="{box_y:.1f}" width="{box_w:.1f}" height="{box_h:.1f}" fill="none" stroke="#000000" stroke-width="1.3"/>')

    # =========================================================================
    # Actor Generalization Paths (Orthogonal around frame with Generalization hollow triangle)
    # =========================================================================
    svg.append("  <!-- Actor Generalization Paths (hollow triangle arrowhead) -->")
    # 1. Customer -> Authenticated User (Left margin, into chest/neck)
    svg.append('  <path d="M 90 480 L 13 480 L 13 208 L 83 208" fill="none" stroke="#000000" stroke-width="1.2" marker-end="url(#arrow-generalization)"/>')

    # 2. Admin -> Authenticated User (Top inner loop, into top of head)
    svg.append('  <path d="M 955 138 L 972 138 L 972 28 L 93 28 L 93 182" fill="none" stroke="#000000" stroke-width="1.2" marker-end="url(#arrow-generalization)"/>')

    # 3. Staff -> Authenticated User (Top outer loop, into left of head)
    svg.append('  <path d="M 955 608 L 985 608 L 985 14 L 78 14 L 78 197 L 85 197" fill="none" stroke="#000000" stroke-width="1.2" marker-end="url(#arrow-generalization)"/>')

    # =========================================================================
    # Actor Associations (Solid straight lines, NO arrowheads)
    # =========================================================================
    svg.append("  <!-- Actor Associations (Plain solid lines) -->")
    for act_id, uc_id, anchor in ACTOR_ASSOCIATIONS:
        uc = USE_CASES[uc_id]
        ax, ay = anchor
        px, py = get_ellipse_intersection(uc["cx"], uc["cy"], uc["rx"], uc["ry"], ax, ay)
        svg.append(f'  <line x1="{ax:.1f}" y1="{ay:.1f}" x2="{px:.1f}" y2="{py:.1f}" stroke="#000000" stroke-width="1.1"/>')

    # =========================================================================
    # Use Case Generalization (Solid line with Generalization HOLLOW TRIANGLE arrowhead)
    # =========================================================================
    svg.append("  <!-- Use Case Generalization Sub-actions (Hollow Triangle Arrowhead) -->")
    for src_id, dst_id in GENERALIZATION_ARROWS:
        src = USE_CASES[src_id]
        dst = USE_CASES[dst_id]
        p1, p2 = get_ellipse_to_ellipse_points(
            src["cx"], src["cy"], src["rx"], src["ry"],
            dst["cx"], dst["cy"], dst["rx"], dst["ry"]
        )
        svg.append(
            f'  <line x1="{p1[0]:.1f}" y1="{p1[1]:.1f}" x2="{p2[0]:.1f}" y2="{p2[1]:.1f}" '
            f'stroke="#000000" stroke-width="1.1" marker-end="url(#arrow-generalization)"/>'
        )

    # =========================================================================
    # Stereotype Arrows (Dashed with OPEN arrowhead & label)
    # =========================================================================
    svg.append("  <!-- Stereotypes: <<include>> / <<extend>> (Dashed with Open Arrowhead) -->")
    for src_id, dst_id, label, offset in STEREOTYPE_ARROWS:
        src = USE_CASES[src_id]
        dst = USE_CASES[dst_id]
        p1, p2 = get_ellipse_to_ellipse_points(
            src["cx"], src["cy"], src["rx"], src["ry"],
            dst["cx"], dst["cy"], dst["rx"], dst["ry"]
        )
        svg.append(
            f'  <line x1="{p1[0]:.1f}" y1="{p1[1]:.1f}" x2="{p2[0]:.1f}" y2="{p2[1]:.1f}" '
            f'stroke="#000000" stroke-width="1.1" stroke-dasharray="3,3" marker-end="url(#arrow-open)"/>'
        )
        mid_x = (p1[0] + p2[0]) / 2.0 + offset[0]
        mid_y = (p1[1] + p2[1]) / 2.0 + offset[1]
        esc_label = html.escape(label)
        svg.append(
            f'  <text x="{mid_x:.1f}" y="{mid_y:.1f}" font-family="Segoe UI, -apple-system, Arial, sans-serif" '
            f'font-size="8.5px" font-style="italic" fill="#000000" text-anchor="middle" '
            f'paint-order="stroke fill" stroke="#FFFFFF" stroke-width="3.5px" stroke-linejoin="round">{esc_label}</text>'
        )

    # =========================================================================
    # Use Case Ovals (White fill, Black stroke, Centered Text)
    # =========================================================================
    svg.append("  <!-- Use Case Ellipses -->")
    for uc_id, uc in USE_CASES.items():
        cx, cy, rx, ry = uc["cx"], uc["cy"], uc["rx"], uc["ry"]
        svg.append(f'  <g id="uc-{uc_id}">')
        svg.append(f'    <ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="#FFFFFF" stroke="#000000" stroke-width="1.2"/>')

        lines = uc["text"].split("\n")
        line_h = 11.5
        start_y = cy - ((len(lines) - 1) * line_h) / 2.0 + 3.8
        for idx, line in enumerate(lines):
            ly = start_y + idx * line_h
            esc = html.escape(line, quote=True)
            svg.append(
                f'    <text x="{cx:.1f}" y="{ly:.1f}" font-family="Segoe UI, -apple-system, Arial, sans-serif" '
                f'font-size="10px" fill="#000000" text-anchor="middle">{esc}</text>'
            )
        svg.append('  </g>')

    # =========================================================================
    # Actors (Stickman Vector Rendering)
    # =========================================================================
    svg.append("  <!-- Actors -->")
    for act_id, act in ACTORS.items():
        hcx = act["head_cx"]
        hcy = act["head_cy"]
        r = 7.5
        svg.append(f'  <g id="actor-{act_id}">')
        # Head
        svg.append(f'    <circle cx="{hcx:.1f}" cy="{hcy:.1f}" r="{r:.1f}" fill="#FFFFFF" stroke="#000000" stroke-width="1.3"/>')
        # Spine
        spine_top = hcy + r
        spine_bot = spine_top + 20.0
        svg.append(f'    <line x1="{hcx:.1f}" y1="{spine_top:.1f}" x2="{hcx:.1f}" y2="{spine_bot:.1f}" stroke="#000000" stroke-width="1.3"/>')
        # Arms
        arm_y = spine_top + 7.0
        svg.append(f'    <line x1="{hcx - 13.0:.1f}" y1="{arm_y:.1f}" x2="{hcx + 13.0:.1f}" y2="{arm_y:.1f}" stroke="#000000" stroke-width="1.3"/>')
        # Legs
        leg_bot_y = spine_bot + 18.0
        svg.append(f'    <line x1="{hcx:.1f}" y1="{spine_bot:.1f}" x2="{hcx - 11.0:.1f}" y2="{leg_bot_y:.1f}" stroke="#000000" stroke-width="1.3"/>')
        svg.append(f'    <line x1="{hcx:.1f}" y1="{spine_bot:.1f}" x2="{hcx + 11.0:.1f}" y2="{leg_bot_y:.1f}" stroke="#000000" stroke-width="1.3"/>')
        # Label
        lbl_y = act["label_y"]
        esc_lbl = html.escape(act["label"], quote=True)
        svg.append(
            f'    <text x="{hcx:.1f}" y="{lbl_y:.1f}" font-family="Segoe UI, -apple-system, Arial, sans-serif" '
            f'font-size="11px" font-weight="500" fill="#000000" text-anchor="middle">{esc_lbl}</text>'
        )
        svg.append('  </g>')

    svg.append("</svg>")
    return "\n".join(svg)


def render_to_png(svg_content: str, output_png_path: str, scale: int = 3) -> dict[str, Any]:
    """Render SVG to high-resolution PNG using Chromium/Edge headless."""
    output_png_path = os.path.abspath(output_png_path)
    os.makedirs(os.path.dirname(output_png_path), exist_ok=True)

    svg_path = os.path.splitext(output_png_path)[0] + ".svg"
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg_content)

    candidates = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
    ]
    browser_exe = next((c for c in candidates if os.path.isfile(c)), None)
    if not browser_exe:
        browser_exe = shutil.which("msedge") or shutil.which("chrome")

    if not browser_exe:
        raise EnvironmentError("No Chromium browser (msedge.exe or chrome.exe) found on system.")

    cmd = [
        browser_exe,
        "--headless",
        "--disable-gpu",
        "--hide-scrollbars",
        f"--force-device-scale-factor={scale}",
        "--window-size=1024,901",
        f"--screenshot={output_png_path}",
        svg_path,
    ]

    res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if res.returncode != 0:
        raise RuntimeError(f"Rendering failed: {res.stderr}")

    if not os.path.isfile(output_png_path):
        raise FileNotFoundError(f"PNG not generated at {output_png_path}")

    with Image.open(output_png_path) as img:
        w_px, h_px = img.size
    file_size = os.path.getsize(output_png_path)

    return {
        "success": True,
        "svg_path": svg_path,
        "png_path": output_png_path,
        "dimensions": (w_px, h_px),
        "file_size": file_size,
        "scale": scale,
    }


def main():
    svg_content = generate_usecase_svg()
    out_png = os.path.join(ROOT_DIR, "diagram_assets", "usecase_smart_mart.png")
    res = render_to_png(svg_content, out_png, scale=3)
    print(f"Generated: {res['png_path']}")
    print(f"Dimensions: {res['dimensions']} px | Size: {res['file_size']} bytes")


if __name__ == "__main__":
    main()
