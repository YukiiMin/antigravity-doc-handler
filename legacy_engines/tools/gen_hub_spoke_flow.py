import sys
import os
import json

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from spec_diagram_engine import PrecisionDiagram

def build_perfect_diagram() -> PrecisionDiagram:
    diag = PrecisionDiagram(
        width=1320,
        height=720,
        font_family="Segoe UI, -apple-system, BlinkMacSystemFont, Roboto, Arial, sans-serif",
        font_size=10.5,
        bg_color="#ffffff",
    )

    # ─────────────────────────────────────────────────────────────
    # 1. Center Hub
    # ─────────────────────────────────────────────────────────────
    diag.add_node("home", "Member Home Screen", x=360, y=265, width=150, height=44, type="primary")

    # ─────────────────────────────────────────────────────────────
    # 2. Top Quadrant: Discovery & Products
    # ─────────────────────────────────────────────────────────────
    diag.add_node("search", "Voice/Text Search Screen", x=470, y=45, width=155, height=36, type="standard")
    diag.add_node("empty_search", "Empty View / Retry", x=470, y=115, width=115, height=30, type="modal")
    diag.add_node("recipe", "Recipe Screen", x=480, y=170, width=125, height=36, type="standard")
    diag.add_node("suggest_alt", "Suggest Alternatives", x=480, y=230, width=135, height=30, type="modal")

    diag.add_node("health_banner", "Health Warning Banner", x=720, y=15, width=140, height=30, type="modal")
    diag.add_node("prod_detail", "Product Detail Screen", x=715, y=75, width=150, height=40, type="primary")
    diag.add_node("similar_prod", "Show Similar Products", x=740, y=145, width=135, height=30, type="modal")

    # ─────────────────────────────────────────────────────────────
    # 3. Right Quadrant: Cart & Navigation
    # ─────────────────────────────────────────────────────────────
    diag.add_node("cart", "Cart Screen", x=980, y=230, width=110, height=42, type="primary")
    diag.add_node("empty_cart", "Empty Cart View", x=980, y=315, width=110, height=30, type="modal")
    diag.add_node("nav_map", "Navigation Map Screen", x=1135, y=170, width=145, height=36, type="standard")

    # ─────────────────────────────────────────────────────────────
    # 4. Bottom-Left Quadrant: Authentication
    # ─────────────────────────────────────────────────────────────
    diag.add_node("error_toast", "Error Toast", x=35, y=385, width=85, height=30, type="modal")
    diag.add_node("face_scan", "Face Scan Screen", x=175, y=340, width=120, height=36, type="standard")
    diag.add_node("val_toast", "Validation Toast", x=205, y=405, width=105, height=30, type="modal")

    diag.add_node("login", "Login Screen", x=35, y=460, width=105, height=42, type="primary")
    diag.add_node("register", "Register Screen", x=200, y=460, width=110, height=42, type="primary")
    diag.add_node("face_reg", "Face Register Screen", x=370, y=460, width=125, height=36, type="standard")
    diag.add_node("retry_auth", "Retry / Fallback", x=375, y=565, width=115, height=32, type="modal")

    # ─────────────────────────────────────────────────────────────
    # 5. Bottom-Right Quadrant: Profile & Account
    # ─────────────────────────────────────────────────────────────
    diag.add_node("personal_info", "Personal Info Screen", x=540, y=350, width=135, height=36, type="standard")
    diag.add_node("shop_prefs", "Shopping Preferences Screen", x=750, y=350, width=160, height=40, type="primary")
    diag.add_node("profile", "Profile Screen", x=550, y=460, width=115, height=42, type="standard")

    diag.add_node("member_tier", "Member Tier Screen", x=760, y=415, width=125, height=34, type="standard")
    diag.add_node("order_history", "Order History Screen", x=760, y=470, width=125, height=34, type="standard")
    diag.add_node("face_update", "Face Update Screen", x=760, y=525, width=125, height=34, type="standard")
    diag.add_node("auto_logout", "Auto Logout -> Login", x=760, y=580, width=135, height=32, type="modal")

    # ─────────────────────────────────────────────────────────────
    # EDGES & ROUTING
    # ─────────────────────────────────────────────────────────────

    # ── Hub Connections ──
    diag.add_edge("home", "search", source_port="top", target_port="left", source_offset=-25,
                  waypoints=[(410, 63)], label="Search Bar", label_pos=0.45, label_offset_x=-15)
    diag.add_edge("home", "recipe", source_port="top", target_port="left", source_offset=25,
                  waypoints=[(460, 188)], label="Recipe Banner", label_pos=0.45, label_offset_x=-15)
    diag.add_edge("home", "cart", source_port="right", target_port="left", source_offset=-6,
                  waypoints=[(945, 281), (945, 251)], label="Bottom Nav", label_pos=0.45, label_offset_y=-8)
    diag.add_edge("home", "profile", source_port="bottom", target_port="left", source_offset=30,
                  waypoints=[(520, 309), (520, 481)], label="Bottom Nav", label_pos=0.45, label_offset_x=-16)

    # ── Discovery & Products Connections ──
    diag.add_edge("search", "empty_search", source_port="bottom", target_port="top", line_style="dashed",
                  label="No Match / Timeout", label_pos=0.5, label_offset_x=2)
    diag.add_edge("search", "prod_detail", source_port="right", target_port="left", source_offset=-5, target_offset=-8,
                  waypoints=[(670, 58), (670, 87)], label="Results Found", label_pos=0.5, label_offset_y=-8)

    diag.add_edge("recipe", "suggest_alt", source_port="bottom", target_port="top", line_style="dashed",
                  label="Ingredient OutOfStock", label_pos=0.5, label_offset_x=2)
    diag.add_edge("recipe", "prod_detail", source_port="right", target_port="left", source_offset=-5, target_offset=8,
                  waypoints=[(660, 183), (660, 103)], label="Valid Recipe", label_pos=0.5, label_offset_y=-8)
    diag.add_edge("recipe", "cart", source_port="right", target_port="left", source_offset=8, target_offset=-10,
                  waypoints=[(645, 196), (645, 241)], label="Add Ingredients", label_pos=0.6, label_offset_y=-8)

    diag.add_edge("prod_detail", "health_banner", source_port="top", target_port="bottom", line_style="dashed",
                  label="Allergy / Diet Violation", label_pos=0.5, label_offset_x=2)
    diag.add_edge("prod_detail", "similar_prod", source_port="bottom", target_port="top", line_style="dashed",
                  label="OutOfStock", label_pos=0.5, label_offset_x=2)
    diag.add_edge("prod_detail", "cart", source_port="right", target_port="top", source_offset=-6, target_offset=10,
                  waypoints=[(1045, 89)], label="Add to Cart", label_pos=0.5, label_offset_x=18)

    # ── Cart & Navigation Connections ──
    diag.add_edge("cart", "nav_map", source_port="right", target_port="left", source_offset=-8, target_offset=0,
                  waypoints=[(1115, 243), (1115, 188)], label="Calculate Route", label_pos=0.45, label_offset_y=-8)
    diag.add_edge("cart", "empty_cart", source_port="bottom", target_port="top", line_style="dashed",
                  label="Empty Cart", label_pos=0.5, label_offset_x=2)

    # ── Auth Connections ──
    diag.add_edge("login", "error_toast", source_port="top", target_port="bottom", source_offset=-25, line_style="dashed",
                  label="Invalid Creds", label_pos=0.5, label_offset_x=-15)
    diag.add_edge("login", "face_scan", source_port="top", target_port="left", source_offset=25,
                  waypoints=[(112, 358)], label="Select Face ID", label_pos=0.45, label_offset_x=18)
    diag.add_edge("login", "register", source_port="right", target_port="left",
                  label="Select Register", label_pos=0.5, label_offset_y=-8)
    diag.add_edge("login", "home", source_port="left", target_port="left", source_offset=-5, target_offset=5,
                  waypoints=[(15, 476), (15, 292)], label="Valid Creds", label_pos=0.7, label_offset_y=-8)

    diag.add_edge("face_scan", "home", source_port="right", target_port="left", source_offset=-2, target_offset=-10,
                  waypoints=[(335, 356), (335, 277)], label="Match Success", label_pos=0.45, label_offset_y=-8)
    diag.add_edge("face_scan", "retry_auth", source_port="bottom", target_port="left", source_offset=10, target_offset=0,
                  waypoints=[(245, 390), (345, 390), (345, 581)], line_style="dashed",
                  label="Match Fail", label_pos=0.25, label_offset_y=-8)

    diag.add_edge("register", "val_toast", source_port="top", target_port="bottom", line_style="dashed",
                  label="Validation Fail", label_pos=0.5, label_offset_x=2)
    diag.add_edge("register", "face_reg", source_port="right", target_port="left",
                  label="Valid Form", label_pos=0.5, label_offset_y=-8)

    # Returns to Login
    # Track 1 (Capture Success): Y = 518
    # Track 2 (Cancel):          Y = 542 (safe in gap above retry_auth at 565)
    # Track 3 (Use Password):    Y = 625 (safe below retry_auth)
    # Track 4 (User Logout):     Y = 665
    diag.add_edge("face_reg", "login", source_port="bottom", target_port="bottom", source_offset=-25, target_offset=30,
                  waypoints=[(407, 518), (117, 518)], label="Capture Success", label_pos=0.5, label_offset_y=-7)
    diag.add_edge("face_reg", "login", source_port="bottom", target_port="bottom", source_offset=20, target_offset=5,
                  waypoints=[(452, 542), (92, 542)], line_style="dashed", label="Cancel", label_pos=0.5, label_offset_y=-7)
    diag.add_edge("retry_auth", "login", source_port="bottom", target_port="bottom", source_offset=0, target_offset=-20,
                  waypoints=[(432, 625), (67, 625)], line_style="dashed", label="Use Password", label_pos=0.5, label_offset_y=-7)

    diag.add_edge("profile", "login", source_port="bottom", target_port="left", source_offset=-15, target_offset=12,
                  waypoints=[(592, 665), (12, 665), (12, 493)], line_style="dashed",
                  label="User Logout", label_pos=0.5, label_offset_y=-8)

    # ── Profile & Account Connections (Individual non-crossing ports) ──
    diag.add_edge("profile", "personal_info", source_port="top", target_port="bottom", source_offset=-35, target_offset=-10,
                  waypoints=[(572, 420), (597, 420)], label="Personal Info", label_pos=0.45, label_offset_x=-15)
    diag.add_edge("personal_info", "shop_prefs", source_port="right", target_port="left",
                  label="Preferences", label_pos=0.5, label_offset_y=-8)

    diag.add_edge("profile", "shop_prefs", source_port="top", target_port="bottom", source_offset=-10, target_offset=-30,
                  waypoints=[(597, 402), (800, 402)], label="Diet & Budget", label_pos=0.45, label_offset_y=-8)
    diag.add_edge("profile", "member_tier", source_port="top", target_port="left", source_offset=25,
                  waypoints=[(632, 432)], label="Member Tier", label_pos=0.5, label_offset_y=-8)
    diag.add_edge("profile", "order_history", source_port="right", target_port="left", source_offset=0,
                  label="Order History", label_pos=0.5, label_offset_y=-8)
    diag.add_edge("profile", "face_update", source_port="bottom", target_port="left", source_offset=25,
                  waypoints=[(632, 542)], label="Face Update", label_pos=0.5, label_offset_y=-8)
    diag.add_edge("profile", "auto_logout", source_port="bottom", target_port="left", source_offset=0,
                  waypoints=[(607, 596)], line_style="dashed",
                  label="Token Expired 401", label_pos=0.5, label_offset_y=-8)

    return diag

if __name__ == "__main__":
    diag = build_perfect_diagram()

    # 1. Output SVG
    out_svg = r"C:\Users\Admin\.gemini\antigravity-ide\brain\87b1a733-0a78-4a87-8b33-42d7ca05890d\perfect_hub_spoke_v1.svg"
    with open(out_svg, "w", encoding="utf-8") as f:
        f.write(diag.to_svg())
    print("Wrote SVG:", out_svg)

    # 2. Output PNG
    out_png = r"C:\Users\Admin\.gemini\antigravity-ide\brain\87b1a733-0a78-4a87-8b33-42d7ca05890d\perfect_hub_spoke_v1.png"
    res = diag.render_to_png(out_png, scale=3)
    print("Rendered PNG:", res)

    # 3. Export to JSON spec
    spec = diag.to_spec()
    spec["scale"] = 3
    json_path = os.path.join(ROOT_DIR, "specs", "flow_android_hub_spoke_spec.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=2, ensure_ascii=False)
    print("Updated JSON spec at:", json_path)
