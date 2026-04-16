import os
import shutil
import pymysql
import base64
from config import Config

def create_placeholder(path):
    # 1x1 transparent PNG base64
    b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    with open(path, "wb") as f:
        f.write(base64.b64decode(b64))

def update_db():
    print("Connecting to MySQL to update Phase 9 products...")
    
    # 1. Image preparation
    img_dir = "static/images"
    os.makedirs(img_dir, exist_ok=True)
    
    # Check if a placeholder exists or create a basic one from supermarket_product.png
    src_img = "static/images/products/supermarket_product.png"
    placeholder = "static/images/product_placeholder.png"
    if os.path.exists(src_img):
        shutil.copy(src_img, placeholder)
        print("Copied existing stock placeholder.")
    else:
        create_placeholder(placeholder)
        print("Generated fallback PNG placeholder.")

    # 2. Database Update
    conn = pymysql.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        db=Config.MYSQL_DB
    )
    cursor = conn.cursor()
    
    # Clean old products 
    cursor.execute("DELETE FROM order_items")
    cursor.execute("DELETE FROM orders") # To safely drop order_items
    cursor.execute("DELETE FROM products")
    
    products_data = [
        ('Rice (5kg)', 350, 50, 5000, 'rice.jpg', 'staples', '200001'),
        ('Wheat Flour (Atta 5kg)', 280, 50, 5000, 'wheat_flour.jpg', 'staples', '200002'),
        ('Toor Dal (1kg)', 160, 50, 1000, 'toor_dal.jpg', 'staples', '200003'),
        ('Sugar (1kg)', 45, 50, 1000, 'sugar.jpg', 'staples', '200004'),
        ('Milk Packet (500ml)', 30, 50, 500, 'milk.jpg', 'dairy', '200005'),
        ('Cooking Oil (1L)', 160, 50, 1000, 'cooking_oil.jpg', 'pantry', '200006'),
        ('Coca Cola (330ml)', 40, 50, 330, 'coke.jpg', 'beverages', '200007'),
        ('Chocolate (100g)', 50, 50, 100, 'chocolate.jpg', 'snacks', '200008'),
        ('Cherry Tomatoes (300g)', 60, 50, 300, 'tomatoes.jpg', 'produce', '200009'),
        ('Greek Yogurt (1kg)', 120, 50, 1000, 'yogurt.jpg', 'dairy', '200010')
    ]
    
    products_sql = """
        INSERT INTO products (name, price, stock, weight_g, image_url, category, barcode) 
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    cursor.executemany(products_sql, products_data)
    
    conn.commit()
    conn.close()
    print("Database updated with realistic weights and pricing successfully.")

if __name__ == "__main__":
    update_db()
