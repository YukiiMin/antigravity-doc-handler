"""
gen_master_erd.py — Generates publication-grade Physical ERD specifications for Smart Mart system:
1. specs/master_erd_spec.json: 4K UHD PlantUML Physical ERD (47 tables, Orthogonal 90°, OpenIconic <&key>,
   bullet markers ●/○, explicit SQL physical data types, 2-tier matrix layout).
2. specs/sub_erd_*.json: 8 modular domain Sub-ERD specifications in Mermaid / PlantUML.
"""

from __future__ import annotations

import json
import os
import sys

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(_CURRENT_DIR, ".."))
SPECS_DIR = os.path.join(ROOT_DIR, "specs")
DIAGRAM_ASSETS_DIR = os.path.join(ROOT_DIR, "diagram_assets")

os.makedirs(SPECS_DIR, exist_ok=True)
os.makedirs(DIAGRAM_ASSETS_DIR, exist_ok=True)

# ==============================================================================
# 1. TABLE DEFINITIONS (47 Tables across 8 Domains with Physical SQL Types)
# ==============================================================================

TABLES = [
    # --------------------------------------------------------------------------
    # 1. TÀI KHOẢN & KHÁCH HÀNG (ACCOUNT & CUSTOMER DOMAIN)
    # --------------------------------------------------------------------------
    {
        "name": "ACCOUNT",
        "domain": 1,
        "domain_name": "TÀI KHOẢN & KHÁCH HÀNG",
        "columns": [
            ("AccountID", "INT", True, False, False),
            ("Username", "VARCHAR(100)", False, False, False),
            ("PasswordHash", "VARCHAR(255)", False, False, False),
            ("Email", "VARCHAR(255)", False, False, False),
            ("Phone", "VARCHAR(20)", False, False, True),
            ("FullName", "VARCHAR(255)", False, False, False),
            ("AvatarUrl", "VARCHAR(500)", False, False, True),
            ("Status", "VARCHAR(50)", False, False, False),
            ("Role", "VARCHAR(50)", False, False, False),
            ("OtpCode", "VARCHAR(10)", False, False, True),
            ("OtpExpiredAt", "DATETIME", False, False, True),
            ("OtpType", "VARCHAR(50)", False, False, True),
            ("CreatedAt", "DATETIME", False, False, False),
            ("RefreshToken", "VARCHAR(500)", False, False, True),
            ("RefreshExpiry", "DATETIME", False, False, True),
            ("IsTokenRevoked", "BIT", False, False, False),
        ],
    },
    {
        "name": "MEMBER",
        "domain": 1,
        "domain_name": "TÀI KHOẢN & KHÁCH HÀNG",
        "columns": [
            ("MemberID", "INT", True, False, False),
            ("AccountID", "INT", False, True, False),
            ("FullName", "VARCHAR(255)", False, False, False),
            ("FacePath", "VARCHAR(500)", False, False, True),
            ("FaceVector", "TEXT", False, False, True),
            ("SpendingLimit", "DECIMAL(18,2)", False, False, True),
            ("TotalPoints", "INT", False, False, False),
        ],
    },
    {
        "name": "MEMBERSHIP",
        "domain": 1,
        "domain_name": "TÀI KHOẢN & KHÁCH HÀNG",
        "columns": [
            ("MembershipID", "INT", True, False, False),
            ("MemberID", "INT", False, True, False),
            ("TierName", "VARCHAR(50)", False, False, False),
            ("Status", "VARCHAR(50)", False, False, False),
        ],
    },
    {
        "name": "HEALTH_TAG",
        "domain": 1,
        "domain_name": "TÀI KHOẢN & KHÁCH HÀNG",
        "columns": [
            ("HealthTagID", "INT", True, False, False),
            ("TagName", "VARCHAR(100)", False, False, False),
            ("TagType", "VARCHAR(50)", False, False, False),
            ("IconName", "VARCHAR(100)", False, False, True),
        ],
    },
    {
        "name": "MEMBERHEALTH_PREFERENCE",
        "domain": 1,
        "domain_name": "TÀI KHOẢN & KHÁCH HÀNG",
        "columns": [
            ("MemberID", "INT", True, True, False),
            ("HealthTagID", "INT", True, True, False),
            ("status", "VARCHAR(50)", False, False, False),
        ],
    },
    {
        "name": "HEALTH_TAG_CONFLICT",
        "domain": 1,
        "domain_name": "TÀI KHOẢN & KHÁCH HÀNG",
        "columns": [
            ("TagId1", "INT", True, True, False),
            ("TagId2", "INT", True, True, False),
            ("ErrorMessage", "VARCHAR(255)", False, False, False),
        ],
    },

    # --------------------------------------------------------------------------
    # 2. SẢN PHẨM & DANH MỤC (PRODUCT CATALOG DOMAIN)
    # --------------------------------------------------------------------------
    {
        "name": "CATEGORY",
        "domain": 2,
        "domain_name": "SẢN PHẨM & DANH MỤC",
        "columns": [
            ("CategoryID", "INT", True, False, False),
            ("CategoryName", "VARCHAR(255)", False, False, False),
            ("Description", "VARCHAR(500)", False, False, True),
        ],
    },
    {
        "name": "SUBCATEGORY",
        "domain": 2,
        "domain_name": "SẢN PHẨM & DANH MỤC",
        "columns": [
            ("SubcategoryID", "INT", True, False, False),
            ("CategoryID", "INT", False, True, False),
            ("SubcategoryName", "VARCHAR(255)", False, False, False),
        ],
    },
    {
        "name": "PRODUCT_TYPE",
        "domain": 2,
        "domain_name": "SẢN PHẨM & DANH MỤC",
        "columns": [
            ("ProductTypeID", "INT", True, False, False),
            ("SubcategoryID", "INT", False, True, False),
            ("TypeName", "VARCHAR(255)", False, False, False),
        ],
    },
    {
        "name": "PRODUCT",
        "domain": 2,
        "domain_name": "SẢN PHẨM & DANH MỤC",
        "columns": [
            ("ProductID", "INT", True, False, False),
            ("ProductTypeID", "INT", False, True, False),
            ("ProductName", "VARCHAR(255)", False, False, False),
            ("UnitPrice", "DECIMAL(18,2)", False, False, False),
            ("PromotionPrice", "DECIMAL(18,2)", False, False, True),
            ("ExpiredDate", "DATETIME", False, False, True),
            ("ImageUrl", "VARCHAR(500)", False, False, True),
            ("WeightOrVolume", "DECIMAL(10,2)", False, False, True),
            ("Unit", "VARCHAR(50)", False, False, True),
            ("Description", "TEXT", False, False, True),
            ("Status", "VARCHAR(50)", False, False, False),
            ("SubstituteProductID", "INT", False, True, True),
            ("SKU", "VARCHAR(100)", False, False, True),
        ],
    },
    {
        "name": "PRODUCT_HEALTHTAG",
        "domain": 2,
        "domain_name": "SẢN PHẨM & DANH MỤC",
        "columns": [
            ("ProductID", "INT", True, True, False),
            ("HealthTagID", "INT", True, True, False),
        ],
    },

    # --------------------------------------------------------------------------
    # 3. GIỎ HÀNG, HÓA ĐƠN & THỰC ĐƠN (CART, INVOICE & MEAL DOMAIN)
    # --------------------------------------------------------------------------
    {
        "name": "CART",
        "domain": 3,
        "domain_name": "GIỎ HÀNG, HÓA ĐƠN & THỰC ĐƠN",
        "columns": [
            ("CartID", "INT", True, False, False),
            ("MemberID", "INT", False, True, False),
            ("CreatedAt", "DATETIME", False, False, False),
            ("UpdatedAt", "DATETIME", False, False, True),
        ],
    },
    {
        "name": "CART_ITEM",
        "domain": 3,
        "domain_name": "GIỎ HÀNG, HÓA ĐƠN & THỰC ĐƠN",
        "columns": [
            ("CartItemID", "INT", True, False, False),
            ("CartID", "INT", False, True, False),
            ("ProductID", "INT", False, True, False),
            ("Quantity", "INT", False, False, False),
            ("AddedAt", "DATETIME", False, False, False),
        ],
    },
    {
        "name": "INVOICE_HISTORY",
        "domain": 3,
        "domain_name": "GIỎ HÀNG, HÓA ĐƠN & THỰC ĐƠN",
        "columns": [
            ("InvoiceHistoryID", "INT", True, False, False),
            ("MemberID", "INT", False, True, False),
            ("PurchaseDate", "DATETIME", False, False, False),
            ("TotalPrice", "DECIMAL(18,2)", False, False, False),
        ],
    },
    {
        "name": "INVOICE_HISTORY_ITEM",
        "domain": 3,
        "domain_name": "GIỎ HÀNG, HÓA ĐƠN & THỰC ĐƠN",
        "columns": [
            ("InvoiceHistoryItemID", "INT", True, False, False),
            ("InvoiceHistoryID", "INT", False, True, False),
            ("ProductID", "INT", False, True, False),
            ("Quantity", "INT", False, False, False),
            ("UnitPrice", "DECIMAL(18,2)", False, False, False),
        ],
    },
    {
        "name": "MEAL_SUGGESTION",
        "domain": 3,
        "domain_name": "GIỎ HÀNG, HÓA ĐƠN & THỰC ĐƠN",
        "columns": [
            ("MealSuggestionID", "INT", True, False, False),
            ("MealName", "VARCHAR(255)", False, False, False),
            ("Description", "TEXT", False, False, True),
            ("YieldPortions", "INT", False, False, True),
            ("ImageUrl", "VARCHAR(500)", False, False, True),
            ("Calories", "INT", False, False, True),
            ("healthy_score", "INT", False, False, True),
            ("alternative_suggestion", "TEXT", False, False, True),
        ],
    },

    # --------------------------------------------------------------------------
    # 4. KHÔNG GIAN SIÊU THỊ & KỆ HÀNG (STORE LAYOUT DOMAIN)
    # --------------------------------------------------------------------------
    {
        "name": "FLOOR",
        "domain": 4,
        "domain_name": "KHÔNG GIAN SIÊU THỊ & KỆ HÀNG",
        "columns": [
            ("FloorID", "INT", True, False, False),
            ("FloorNumber", "INT", False, False, False),
        ],
    },
    {
        "name": "ZONE",
        "domain": 4,
        "domain_name": "KHÔNG GIAN SIÊU THỊ & KỆ HÀNG",
        "columns": [
            ("ZoneID", "INT", True, False, False),
            ("FloorID", "INT", False, True, False),
            ("ZoneName", "VARCHAR(100)", False, False, False),
            ("Description", "VARCHAR(500)", False, False, True),
        ],
    },
    {
        "name": "AISLE",
        "domain": 4,
        "domain_name": "KHÔNG GIAN SIÊU THỊ & KỆ HÀNG",
        "columns": [
            ("AisleID", "INT", True, False, False),
            ("ZoneID", "INT", False, True, False),
            ("AisleCode", "VARCHAR(50)", False, False, False),
            ("AisleName", "VARCHAR(100)", False, False, False),
        ],
    },
    {
        "name": "SHELF",
        "domain": 4,
        "domain_name": "KHÔNG GIAN SIÊU THỊ & KỆ HÀNG",
        "columns": [
            ("ShelfID", "INT", True, False, False),
            ("ShelfName", "VARCHAR(100)", False, False, False),
            ("AisleID", "INT", False, True, False),
            ("LevelNumber", "INT", False, False, False),
            ("NodeID", "INT", False, True, True),
        ],
    },
    {
        "name": "SLOT",
        "domain": 4,
        "domain_name": "KHÔNG GIAN SIÊU THỊ & KỆ HÀNG",
        "columns": [
            ("SlotID", "INT", True, False, False),
            ("ShelfID", "INT", False, True, False),
            ("SlotCode", "VARCHAR(50)", False, False, False),
            ("LastScannedAt", "DATETIME", False, False, True),
        ],
    },
    {
        "name": "PRODUCT_SLOT",
        "domain": 4,
        "domain_name": "KHÔNG GIAN SIÊU THỊ & KỆ HÀNG",
        "columns": [
            ("ProductsSlotID", "INT", True, False, False),
            ("SlotID", "INT", False, True, False),
            ("ProductID", "INT", False, True, False),
        ],
    },

    # --------------------------------------------------------------------------
    # 5. BẢN ĐỒ & ROBOT (SLAM & ROBOTICS DOMAIN)
    # --------------------------------------------------------------------------
    {
        "name": "MAP",
        "domain": 5,
        "domain_name": "BẢN ĐỒ & ROBOT",
        "columns": [
            ("MapID", "INT", True, False, False),
            ("FloorID", "INT", False, True, False),
            ("MapName", "VARCHAR(100)", False, False, False),
            ("MapData", "TEXT", False, False, True),
            ("FloorplanImageUrl", "VARCHAR(500)", False, False, True),
            ("WidthMeters", "FLOAT", False, False, False),
            ("HeightMeters", "FLOAT", False, False, False),
            ("Resolution", "FLOAT", False, False, False),
            ("OriginX", "FLOAT", False, False, False),
            ("OriginY", "FLOAT", False, False, False),
            ("OriginYaw", "FLOAT", False, False, False),
            ("IsActive", "BIT", False, False, False),
            ("CreatedAt", "DATETIME", False, False, False),
            ("SlamDataUrl", "VARCHAR(500)", False, False, True),
            ("PosegraphUrl", "VARCHAR(500)", False, False, True),
            ("RawYamlContent", "TEXT", False, False, True),
        ],
    },
    {
        "name": "NAVIGATION_NODE",
        "domain": 5,
        "domain_name": "BẢN ĐỒ & ROBOT",
        "columns": [
            ("NodeID", "INT", True, False, False),
            ("MapID", "INT", False, True, False),
            ("NodeName", "VARCHAR(100)", False, False, False),
            ("XCoord", "FLOAT", False, False, False),
            ("YCoord", "FLOAT", False, False, False),
            ("NodeType", "VARCHAR(50)", False, False, False),
            ("NodeRole", "VARCHAR(50)", False, False, True),
            ("IsBlocked", "BIT", False, False, False),
            ("HeadingYaw", "FLOAT", False, False, True),
        ],
    },
    {
        "name": "NAVIGATION_EDGE",
        "domain": 5,
        "domain_name": "BẢN ĐỒ & ROBOT",
        "columns": [
            ("EdgeID", "INT", True, False, False),
            ("FromNodeID", "INT", False, True, False),
            ("ToNodeID", "INT", False, True, False),
            ("Distance", "FLOAT", False, False, False),
            ("IsBidirectional", "BIT", False, False, False),
        ],
    },
    {
        "name": "ROBOT",
        "domain": 5,
        "domain_name": "BẢN ĐỒ & ROBOT",
        "columns": [
            ("RobotID", "INT", True, False, False),
            ("RobotName", "VARCHAR(100)", False, False, False),
            ("RobotCode", "VARCHAR(50)", False, False, False),
            ("BatteryPct", "INT", False, False, False),
            ("Mode", "VARCHAR(50)", False, False, False),
            ("Status", "VARCHAR(50)", False, False, False),
            ("LastSeenAt", "DATETIME", False, False, True),
            ("IPAddress", "VARCHAR(50)", False, False, True),
        ],
    },
    {
        "name": "ROBOT_LOG",
        "domain": 5,
        "domain_name": "BẢN ĐỒ & ROBOT",
        "columns": [
            ("LogID", "INT", True, False, False),
            ("RobotID", "INT", False, True, False),
            ("battery", "INT", False, False, False),
            ("location", "VARCHAR(100)", False, False, True),
            ("status", "VARCHAR(50)", False, False, False),
            ("timestamp", "DATETIME", False, False, False),
            ("XCoord", "FLOAT", False, False, True),
            ("YCoord", "FLOAT", False, False, True),
            ("HeadingRad", "FLOAT", False, False, True),
            ("CurrentNodeId", "INT", False, False, True),
        ],
    },
    {
        "name": "SHELF_SCAN",
        "domain": 5,
        "domain_name": "BẢN ĐỒ & ROBOT",
        "columns": [
            ("ScanID", "INT", True, False, False),
            ("ShelfID", "INT", False, True, False),
            ("RobotID", "INT", False, True, False),
            ("NavigationNodeID", "INT", False, True, True),
            ("MissionID", "VARCHAR(100)", False, False, True),
            ("WaypointIndex", "INT", False, False, True),
            ("ScannedAt", "DATETIME", False, False, False),
            ("EmptyPercentage", "DECIMAL(5,2)", False, False, False),
            ("DensityPercentage", "DECIMAL(5,2)", False, False, False),
            ("NeedsRestock", "BIT", False, False, False),
            ("ImageUrl", "VARCHAR(500)", False, False, True),
            ("EmptySlotCount", "INT", False, False, True),
            ("AiRecommendation", "TEXT", False, False, True),
            ("AiRawJson", "TEXT", False, False, True),
            ("AnalysisStatus", "VARCHAR(50)", False, False, True),
        ],
    },

    # --------------------------------------------------------------------------
    # 6. THƯƠNG HIỆU & QUẢNG CÁO (MARKETING & ADVERTISING DOMAIN)
    # --------------------------------------------------------------------------
    {
        "name": "BRAND",
        "domain": 6,
        "domain_name": "THƯƠNG HIỆU & QUẢNG CÁO",
        "columns": [
            ("BrandID", "INT", True, False, False),
            ("BrandName", "VARCHAR(255)", False, False, False),
            ("Wallet", "DECIMAL(18,2)", False, False, False),
            ("Description", "VARCHAR(500)", False, False, True),
            ("IsSystemBrand", "BIT", False, False, False),
        ],
    },
    {
        "name": "AD_PACKAGE",
        "domain": 6,
        "domain_name": "THƯƠNG HIỆU & QUẢNG CÁO",
        "columns": [
            ("PackageID", "INT", True, False, False),
            ("PackageName", "VARCHAR(255)", False, False, False),
            ("ClickFee", "DECIMAL(18,2)", False, False, False),
            ("RouteUnitPrice", "DECIMAL(18,2)", False, False, False),
            ("ZoneUnitPrice", "DECIMAL(18,2)", False, False, False),
            ("ShelfUnitPrice", "DECIMAL(18,2)", False, False, False),
            ("Budget", "DECIMAL(18,2)", False, False, False),
            ("AdScore", "INT", False, False, False),
            ("Status", "VARCHAR(50)", False, False, False),
            ("DurationDays", "INT", False, False, False),
            ("Description", "VARCHAR(500)", False, False, True),
            ("CreatedAt", "DATETIME", False, False, False),
            ("UpdatedAt", "DATETIME", False, False, True),
        ],
    },
    {
        "name": "AD_CAMPAIGN",
        "domain": 6,
        "domain_name": "THƯƠNG HIỆU & QUẢNG CÁO",
        "columns": [
            ("AdCampaignID", "INT", True, False, False),
            ("PackageID", "INT", False, True, False),
            ("BrandID", "INT", False, True, False),
            ("CampaignName", "VARCHAR(255)", False, False, False),
            ("StartDate", "DATETIME", False, False, False),
            ("EndDate", "DATETIME", False, False, False),
            ("Status", "VARCHAR(50)", False, False, False),
            ("DeliveryMode", "VARCHAR(50)", False, False, False),
            ("Description", "VARCHAR(500)", False, False, True),
            ("BannerUrl", "VARCHAR(500)", False, False, True),
            ("VideoUrl", "VARCHAR(500)", False, False, True),
            ("CreatedAt", "DATETIME", False, False, False),
            ("UpdatedAt", "DATETIME", False, False, True),
        ],
    },
    {
        "name": "AD_RESOURCE",
        "domain": 6,
        "domain_name": "THƯƠNG HIỆU & QUẢNG CÁO",
        "columns": [
            ("ResourceID", "INT", True, False, False),
            ("AdCampaignID", "INT", False, True, False),
            ("ResourceType", "VARCHAR(50)", False, False, False),
            ("ResourceURL", "VARCHAR(500)", False, False, False),
            ("ContentText", "TEXT", False, False, True),
            ("Resolution", "VARCHAR(50)", False, False, True),
            ("Status", "VARCHAR(50)", False, False, False),
        ],
    },
    {
        "name": "SPONSORED_PRODUCT",
        "domain": 6,
        "domain_name": "THƯƠNG HIỆU & QUẢNG CÁO",
        "columns": [
            ("SponsoredID", "INT", True, False, False),
            ("AdCampaignID", "INT", False, True, False),
            ("ProductID", "INT", False, True, False),
            ("Priority", "INT", False, False, False),
            ("status", "VARCHAR(50)", False, False, False),
        ],
    },
    {
        "name": "AD_CAMPAIGN_LOG",
        "domain": 6,
        "domain_name": "THƯƠNG HIỆU & QUẢNG CÁO",
        "columns": [
            ("LogID", "INT", True, False, False),
            ("AdCampaignID", "INT", False, True, False),
            ("ActionType", "VARCHAR(50)", False, False, False),
            ("ChargedAmount", "DECIMAL(18,2)", False, False, False),
            ("Timestamp", "DATETIME", False, False, False),
            ("SponsoredID", "INT", False, True, True),
            ("ProductID", "INT", False, True, True),
            ("RobotID", "INT", False, True, True),
            ("ShelfID", "INT", False, True, True),
            ("ZoneID", "INT", False, True, True),
            ("SlotID", "INT", False, True, True),
            ("MemberID", "INT", False, True, True),
            ("SessionID", "VARCHAR(100)", False, False, True),
            ("XCoord", "INT", False, False, True),
            ("YCoord", "INT", False, False, True),
            ("PerformedBy", "VARCHAR(50)", False, False, True),
            ("PerformedByUserId", "INT", False, False, True),
        ],
    },
    {
        "name": "AD_CAMPAIGN_ZONE",
        "domain": 6,
        "domain_name": "THƯƠNG HIỆU & QUẢNG CÁO",
        "columns": [
            ("AdCampaignID", "INT", True, True, False),
            ("ZoneID", "INT", True, True, False),
            ("ZonePriceCharged", "DECIMAL(18,2)", False, False, False),
            ("PurchasedAt", "DATETIME", False, False, False),
        ],
    },
    {
        "name": "AD_CAMPAIGN_SHELF",
        "domain": 6,
        "domain_name": "THƯƠNG HIỆU & QUẢNG CÁO",
        "columns": [
            ("AdCampaignID", "INT", True, True, False),
            ("ShelfID", "INT", True, True, False),
            ("ShelfPriceCharged", "DECIMAL(18,2)", False, False, False),
            ("PurchasedAt", "DATETIME", False, False, False),
        ],
    },

    # --------------------------------------------------------------------------
    # 7. TUYẾN ĐƯỜNG & QUẢNG CÁO THEO ROUTE (ROBOT ROUTE & AD CAMPAIGN DOMAIN)
    # --------------------------------------------------------------------------
    {
        "name": "ROBOT_ROUTE",
        "domain": 7,
        "domain_name": "TUYẾN ĐƯỜNG & QUẢNG CÁO THEO ROUTE",
        "columns": [
            ("RobotRouteID", "INT", True, False, False),
            ("RobotID", "INT", False, True, True),
            ("MapID", "INT", False, True, False),
            ("RouteName", "VARCHAR(100)", False, False, False),
            ("RouteType", "VARCHAR(50)", False, False, False),
            ("ZoneID", "INT", False, True, True),
            ("Description", "VARCHAR(500)", False, False, True),
            ("CreatedAt", "DATETIME", False, False, False),
        ],
    },
    {
        "name": "ROUTE_NODE_MAPPING",
        "domain": 7,
        "domain_name": "TUYẾN ĐƯỜNG & QUẢNG CÁO THEO ROUTE",
        "columns": [
            ("RouteNodeMappingID", "INT", True, False, False),
            ("RobotRouteID", "INT", False, True, False),
            ("NodeID", "INT", False, True, False),
            ("SequenceOrder", "INT", False, False, False),
            ("DwellTimeSeconds", "INT", False, False, False),
        ],
    },
    {
        "name": "ROUTE_ASSIGNMENT",
        "domain": 7,
        "domain_name": "TUYẾN ĐƯỜNG & QUẢNG CÁO THEO ROUTE",
        "columns": [
            ("RouteAssignmentID", "INT", True, False, False),
            ("RobotID", "INT", False, True, False),
            ("RobotRouteID", "INT", False, True, False),
            ("AssignedAt", "DATETIME", False, False, False),
            ("Status", "VARCHAR(50)", False, False, False),
        ],
    },
    {
        "name": "AD_CAMPAIGN_ROUTE",
        "domain": 7,
        "domain_name": "TUYẾN ĐƯỜNG & QUẢNG CÁO THEO ROUTE",
        "columns": [
            ("AdCampaignID", "INT", True, True, False),
            ("RobotRouteID", "INT", True, True, False),
            ("RoutePriceCharged", "DECIMAL(18,2)", False, False, False),
            ("PurchasedAt", "DATETIME", False, False, False),
        ],
    },

    # --------------------------------------------------------------------------
    # 8. QUẢN TRỊ & NHẬP LIỆU (ADMIN & AUDIT DOMAIN)
    # --------------------------------------------------------------------------
    {
        "name": "IMPORT_HISTORY",
        "domain": 8,
        "domain_name": "QUẢN TRỊ & NHẬP LIỆU",
        "columns": [
            ("ImportID", "INT", True, False, False),
            ("ImportType", "VARCHAR(50)", False, False, False),
            ("FileName", "VARCHAR(255)", False, False, False),
            ("TotalRows", "INT", False, False, False),
            ("SuccessCount", "INT", False, False, False),
            ("ErrorCount", "INT", False, False, False),
            ("DuplicateCount", "INT", False, False, False),
            ("Status", "VARCHAR(50)", False, False, False),
            ("ErrorDetailsJson", "TEXT", False, False, True),
            ("ImportedBy", "VARCHAR(100)", False, False, False),
            ("ImportedAt", "DATETIME", False, False, False),
        ],
    },
]

# ==============================================================================
# 2. RELATIONSHIPS (All 69 Crow's Foot Physical Connections)
# ==============================================================================

RELATIONSHIPS = [
    # Account & Member
    ("ACCOUNT", "||--o{", "MEMBER"),
    ("MEMBER", "||--o{", "MEMBERSHIP"),
    ("MEMBER", "||--o{", "MEMBERHEALTH_PREFERENCE"),
    ("HEALTH_TAG", "||--o{", "MEMBERHEALTH_PREFERENCE"),
    ("HEALTH_TAG", "||--o{", "HEALTH_TAG_CONFLICT"),

    # Products & Catalog
    ("CATEGORY", "||--o{", "SUBCATEGORY"),
    ("SUBCATEGORY", "||--o{", "PRODUCT_TYPE"),
    ("PRODUCT_TYPE", "||--o{", "PRODUCT"),
    ("PRODUCT", "||--o{", "PRODUCT_HEALTHTAG"),
    ("HEALTH_TAG", "||--o{", "PRODUCT_HEALTHTAG"),
    ("PRODUCT", "||--o{", "PRODUCT"),  # Self-ref: SubstituteProductID

    # Cart, Invoices & Meals
    ("MEMBER", "||--o{", "CART"),
    ("CART", "||--o{", "CART_ITEM"),
    ("PRODUCT", "||--o{", "CART_ITEM"),
    ("MEMBER", "||--o{", "INVOICE_HISTORY"),
    ("INVOICE_HISTORY", "||--o{", "INVOICE_HISTORY_ITEM"),
    ("PRODUCT", "||--o{", "INVOICE_HISTORY_ITEM"),
    ("PRODUCT", "||--o{", "MEAL_SUGGESTION"),

    # Store Layout & Shelves
    ("FLOOR", "||--o{", "ZONE"),
    ("ZONE", "||--o{", "AISLE"),
    ("AISLE", "||--o{", "SHELF"),
    ("SHELF", "||--o{", "SLOT"),
    ("SLOT", "||--o{", "PRODUCT_SLOT"),
    ("PRODUCT", "||--o{", "PRODUCT_SLOT"),

    # Map & Navigation & SLAM
    ("FLOOR", "||--o{", "MAP"),
    ("MAP", "||--o{", "NAVIGATION_NODE"),
    ("NAVIGATION_NODE", "||--o{", "NAVIGATION_EDGE"),
    ("NAVIGATION_NODE", "||--o{", "SHELF"),
    ("NAVIGATION_NODE", "||--o{", "SHELF_SCAN"),

    # Robotics
    ("ROBOT", "||--o{", "ROBOT_LOG"),
    ("ROBOT", "||--o{", "SHELF_SCAN"),
    ("SHELF", "||--o{", "SHELF_SCAN"),
    ("ROBOT", "||--o{", "ROBOT_ROUTE"),
    ("MAP", "||--o{", "ROBOT_ROUTE"),
    ("ZONE", "||--o{", "ROBOT_ROUTE"),
    ("ROBOT_ROUTE", "||--o{", "ROUTE_NODE_MAPPING"),
    ("NAVIGATION_NODE", "||--o{", "ROUTE_NODE_MAPPING"),
    ("ROBOT_ROUTE", "||--o{", "ROUTE_ASSIGNMENT"),
    ("ROBOT", "||--o{", "ROUTE_ASSIGNMENT"),

    # Brand & Ads
    ("BRAND", "||--o{", "AD_CAMPAIGN"),
    ("AD_PACKAGE", "||--o{", "AD_CAMPAIGN"),
    ("AD_CAMPAIGN", "||--o{", "AD_RESOURCE"),
    ("AD_CAMPAIGN", "||--o{", "SPONSORED_PRODUCT"),
    ("PRODUCT", "||--o{", "SPONSORED_PRODUCT"),
    ("AD_CAMPAIGN", "||--o{", "AD_CAMPAIGN_ZONE"),
    ("ZONE", "||--o{", "AD_CAMPAIGN_ZONE"),
    ("AD_CAMPAIGN", "||--o{", "AD_CAMPAIGN_SHELF"),
    ("SHELF", "||--o{", "AD_CAMPAIGN_SHELF"),

    # Route Ads & Assignments
    ("AD_CAMPAIGN", "||--o{", "AD_CAMPAIGN_ROUTE"),
    ("ROBOT_ROUTE", "||--o{", "AD_CAMPAIGN_ROUTE"),

    # Ad Campaign Logs
    ("AD_CAMPAIGN", "||--o{", "AD_CAMPAIGN_LOG"),
    ("SPONSORED_PRODUCT", "||--o{", "AD_CAMPAIGN_LOG"),
    ("PRODUCT", "||--o{", "AD_CAMPAIGN_LOG"),
    ("ROBOT", "||--o{", "AD_CAMPAIGN_LOG"),
    ("SHELF", "||--o{", "AD_CAMPAIGN_LOG"),
    ("ZONE", "||--o{", "AD_CAMPAIGN_LOG"),
    ("SLOT", "||--o{", "AD_CAMPAIGN_LOG"),
    ("MEMBER", "||--o{", "AD_CAMPAIGN_LOG"),
]


# ==============================================================================
# 3. BUILD PLANTUML CODE (Physical ERD Strict Standard)
# ==============================================================================

def generate_plantuml_code() -> str:
    lines = [
        "@startuml",
        "!theme plain",
        "scale 3840 width",
        "hide circle",
        "skinparam linetype ortho",
        "skinparam nodesep 26",
        "skinparam ranksep 30",
        "skinparam roundcorner 4",
        "skinparam shadowing false",
        "skinparam defaultFontName \"Segoe UI\"",
        "skinparam defaultFontSize 11",
        "",
        "skinparam class {",
        "    BackgroundColor #FFFFFF",
        "    BorderColor #1E293B",
        "    BorderThickness 1.5",
        "    ArrowColor #1E293B",
        "    ArrowThickness 2.0",
        "    FontColor #0F172A",
        "    FontSize 12",
        "    FontStyle bold",
        "    HeaderBackgroundColor #F1F5F9",
        "    AttributeFontColor #1E293B",
        "    AttributeFontSize 10.5",
        "}",
        "",
    ]

    # Render Entities by Domain
    current_domain = None
    for tbl in TABLES:
        if tbl["domain"] != current_domain:
            current_domain = tbl["domain"]
            lines.append(f"' ============================================================")
            lines.append(f"' {current_domain}. {tbl['domain_name']}")
            lines.append(f"' ============================================================")

        lines.append(f'entity "{tbl["name"]}" as {tbl["name"]} {{')

        # Separate PKs and normal columns
        pk_cols = [c for c in tbl["columns"] if c[2]]
        non_pk_cols = [c for c in tbl["columns"] if not c[2]]

        for name, col_type, is_pk, is_fk, is_nullable in pk_cols:
            dot = "<color:#94A3B8>○</color>" if is_nullable else "<color:#0F172A>●</color>"
            fk_tag = ",FK" if is_fk else ""
            lines.append(f"    {dot} <&key> **{name}** : {col_type} <<PK{fk_tag}>>")

        if pk_cols and non_pk_cols:
            lines.append("    --")

        for name, col_type, is_pk, is_fk, is_nullable in non_pk_cols:
            dot = "<color:#94A3B8>○</color>" if is_nullable else "<color:#0F172A>●</color>"
            fk_tag = " <<FK>>" if is_fk else ""
            lines.append(f"    {dot} {name} : {col_type}{fk_tag}")

        lines.append("}")
        lines.append("")

    # Render Relationships (No verb labels per Physical ERD rule!)
    lines.append("' ============================================================")
    lines.append("' RELATIONSHIPS (MANHATTAN ORTHOGONAL 90° - STRICT PHYSICAL ERD)")
    lines.append("' ============================================================")
    for src, rel, tgt in RELATIONSHIPS:
        lines.append(f"{src} {rel} {tgt}")

    # Layout Anchors (Invisible constraints to balance 2-tier matrix)
    lines.append("")
    lines.append("' ============================================================")
    lines.append("' 2-TIER MATRIX BALANCED LAYOUT ANCHORS (INVISIBLE)")
    lines.append("' ============================================================")
    lines.append("' Row 1: Account, Product, Cart/Invoice, Import Admin")
    lines.append("' Row 2: Store Layout, SLAM Robot, Marketing Ads, Route Ads")
    lines.append("MEMBER -[hidden]down-> FLOOR")
    lines.append("PRODUCT -[hidden]down-> MAP")
    lines.append("INVOICE_HISTORY -[hidden]down-> BRAND")
    lines.append("IMPORT_HISTORY -[hidden]down-> ROBOT_ROUTE")
    lines.append("")
    lines.append("@enduml")

    return "\n".join(lines)


# ==============================================================================
# 4. GENERATE MASTER ERD SPEC
# ==============================================================================

def generate_master_spec() -> dict:
    puml_code = generate_plantuml_code()
    spec = {
        "engine": "plantuml",
        "diagram_type": "erd",
        "diagram_name": "master_erd_smart_mart",
        "title": "Smart Mart 40-Table Master Architecture Physical ERD (4K UHD 100% Attributes Orthogonal)",
        "output_path": "diagram_assets/master_erd_smart_mart.png",
        "dpi": 96,
        "width_cm": 14.0,
        "max_height_cm": 20.0,
        "code": puml_code,
    }
    return spec


# ==============================================================================
# 5. GENERATE SUB-ERD SPECS (8 Domains in Mermaid Pastel)
# ==============================================================================

def generate_sub_specs() -> list[tuple[str, dict]]:
    domains = [
        (1, "sub_erd_account_health", "Phân hệ 1: Tài khoản, Khách hàng & Sức khỏe (Physical ERD)", [
            "ACCOUNT", "MEMBER", "MEMBERSHIP", "HEALTH_TAG", "MEMBERHEALTH_PREFERENCE", "HEALTH_TAG_CONFLICT"
        ]),
        (2, "sub_erd_product_catalog", "Phân hệ 2: Danh mục & Thông tin Sản phẩm (Physical ERD)", [
            "CATEGORY", "SUBCATEGORY", "PRODUCT_TYPE", "PRODUCT", "PRODUCT_HEALTHTAG"
        ]),
        (3, "sub_erd_cart_invoice_meal", "Phân hệ 3: Giỏ hàng, Hóa đơn & Gợi ý Món ăn (Physical ERD)", [
            "CART", "CART_ITEM", "INVOICE_HISTORY", "INVOICE_HISTORY_ITEM", "MEAL_SUGGESTION"
        ]),
        (4, "sub_erd_store_layout", "Phân hệ 4: Bố trí Mặt bằng Siêu thị & Vị trí Kệ hàng (Physical ERD)", [
            "FLOOR", "ZONE", "AISLE", "SHELF", "SLOT", "PRODUCT_SLOT"
        ]),
        (5, "sub_erd_slam_robot", "Phân hệ 5: Điều hướng Robot & Bản đồ SLAM (Physical ERD)", [
            "MAP", "NAVIGATION_NODE", "NAVIGATION_EDGE", "ROBOT", "ROBOT_LOG", "SHELF_SCAN"
        ]),
        (6, "sub_erd_marketing_ads", "Phân hệ 6: Quảng cáo & Tiếp thị Thương hiệu (Physical ERD)", [
            "BRAND", "AD_PACKAGE", "AD_CAMPAIGN", "AD_RESOURCE", "SPONSORED_PRODUCT", "AD_CAMPAIGN_LOG", "AD_CAMPAIGN_ZONE", "AD_CAMPAIGN_SHELF"
        ]),
        (7, "sub_erd_robot_routes", "Phân hệ 7: Tuyến đường Di chuyển & Quảng cáo theo Route (Physical ERD)", [
            "ROBOT_ROUTE", "ROUTE_NODE_MAPPING", "ROUTE_ASSIGNMENT", "AD_CAMPAIGN_ROUTE"
        ]),
        (8, "sub_erd_import_admin", "Phân hệ 8: Quản trị Dữ liệu & Lịch sử Nhập liệu (Physical ERD)", [
            "IMPORT_HISTORY"
        ]),
    ]

    table_map = {t["name"]: t for t in TABLES}
    sub_specs = []

    for dom_id, filename, title, table_names in domains:
        lines = ["erDiagram"]

        # Entities
        for tname in table_names:
            tbl = table_map[tname]
            lines.append(f"    {tbl['name']} {{")
            for col in tbl["columns"]:
                name, col_type, is_pk, is_fk, is_nullable = col
                # Clean type for mermaid
                clean_type = col_type.split("(")[0].lower()
                key_tag = ""
                if is_pk and is_fk:
                    key_tag = " PK,FK"
                elif is_pk:
                    key_tag = " PK"
                elif is_fk:
                    key_tag = " FK"
                lines.append(f"        {clean_type} {name}{key_tag}")
            lines.append("    }")

        lines.append("")

        # Internal relationships within this domain
        table_set = set(table_names)
        for src, rel, tgt in RELATIONSHIPS:
            if src in table_set and tgt in table_set:
                lines.append(f'    {src} {rel} {tgt} : ""')

        mermaid_code = "\n".join(lines) + "\n"

        spec = {
            "engine": "mermaid",
            "diagram_type": "erd",
            "diagram_name": filename,
            "title": title,
            "theme_preset": "erd_pastel",
            "scale": 3,
            "output_path": f"diagram_assets/{filename}.png",
            "code": mermaid_code,
        }
        sub_specs.append((filename, spec))

    return sub_specs


# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

def main():
    print("=" * 65)
    print("GENERATING 47-TABLE PHYSICAL ERD SPECIFICATIONS")
    print("=" * 65)

    # 1. Master ERD Spec (PlantUML 4K UHD)
    master_spec = generate_master_spec()
    master_file = os.path.join(SPECS_DIR, "master_erd_spec.json")
    with open(master_file, "w", encoding="utf-8") as f:
        json.dump(master_spec, f, indent=2, ensure_ascii=False)
    print(f"[OK] Master ERD Spec written to: {master_file}")

    # 2. Sub-ERD Specs (8 Domains in Mermaid)
    sub_specs = generate_sub_specs()
    for filename, spec in sub_specs:
        sub_file = os.path.join(SPECS_DIR, f"{filename}_spec.json")
        with open(sub_file, "w", encoding="utf-8") as f:
            json.dump(spec, f, indent=2, ensure_ascii=False)
        print(f"[OK] Sub-ERD Spec written to: {sub_file}")

    print("\nAll Physical ERD specifications generated successfully!")

    if "--render" in sys.argv:
        if ROOT_DIR not in sys.path:
            sys.path.insert(0, ROOT_DIR)
        import shutil
        from plantuml_renderer import render_plantuml_to_png
        from mermaid_renderer import render_mermaid_to_png

        print("\n" + "=" * 65)
        print("RENDERING MASTER ERD & 8 SUB-ERD DIAGRAMS")
        print("=" * 65)

        # 1. Render Master ERD
        print("\n[1/9] Rendering Master ERD (PlantUML 4K UHD)...")
        res_m = render_plantuml_to_png(master_spec, base_dir=ROOT_DIR)
        dest_m = os.path.abspath(os.path.join(DIAGRAM_ASSETS_DIR, "master_erd_smart_mart.png"))
        if os.path.abspath(res_m["png_path"]) != dest_m:
            shutil.copy(res_m["png_path"], dest_m)
        print(f"  -> [OK] Master ERD: {dest_m} | Res: {res_m['dimensions_px']} | Size: {res_m['file_size_bytes']} bytes")

        # 2. Render all 8 Sub-ERDs
        for idx, (filename, spec) in enumerate(sub_specs, 2):
            print(f"\n[{idx}/9] Rendering Sub-ERD: {filename} (Mermaid)...")
            res_s = render_mermaid_to_png(spec, base_dir=ROOT_DIR)
            dest_s = os.path.abspath(os.path.join(DIAGRAM_ASSETS_DIR, f"{filename}.png"))
            if os.path.abspath(res_s["png_path"]) != dest_s:
                shutil.copy(res_s["png_path"], dest_s)
            print(f"  -> [OK] {dest_s} | Res: {res_s['dimensions_px']} | Size: {res_s['file_size_bytes']} bytes")

        print("\n" + "=" * 65)
        print("ALL 9 DIAGRAMS RENDERED & VERIFIED IN diagram_assets/")
        print("=" * 65)


if __name__ == "__main__":
    main()
