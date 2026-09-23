import os

img_dir = r"e:\Do_an_SU26\SuperMarketBot-Android-Robot\screenShot"
imgs = [
    "01_Welcome_Kiosk_Idle.jpg",
    "02_Daily_Promotions.jpg",
    "03_Role_Selection.jpg",
    "04_Guest_Home_Dashboard.jpg",
    "05_Voice_Search_Listening.jpg",
    "06_Category_Catalog.jpg",
    "07_Product_Search_Result.jpg",
    "08_Face_Scan_Success.jpg",
    "09_Member_Home_Dashboard.jpg",
    "10_Member_Special_Offers.jpg",
    "11_Product_Detail_View.jpg",
    "12_Product_Detail_Added_Cart.jpg",
    "13_Recipe_Detail_Cook_Guide.jpg",
    "14_Member_Cart_List.jpg",
    "15_Cart_Guide_Dispatching.jpg",
    "16_Cart_Guide_Timeout.png",
]

for img in imgs:
    path = os.path.join(img_dir, img)
    print(f"{img}: exists={os.path.exists(path)}, size={os.path.getsize(path) if os.path.exists(path) else 0}")
