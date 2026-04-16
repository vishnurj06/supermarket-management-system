import pymysql
from config import Config

def migrate_indian_products():
    print("Connecting to MySQL server to migrate Indian Products...")
    try:
        conn = pymysql.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            db=Config.MYSQL_DB
        )
        cursor = conn.cursor()
        
        # 1. Clear out existing order references first
        cursor.execute("DELETE FROM order_items")
        cursor.execute("DELETE FROM orders")
        
        # 2. Clear out existing products
        cursor.execute("DELETE FROM products")
        
        # 3. Insert Indian Supermarket Products
        products_sql = """
            INSERT INTO products (name, price, stock, weight_g, image_url, category, barcode) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        indian_products = [
            ('Rice (5kg)', 350.00, 100, 5000, '🌾', 'staples', 'IN100001'),
            ('Wheat Flour (Atta 5kg)', 280.00, 100, 5000, '🍞', 'staples', 'IN100002'),
            ('Toor Dal (1kg)', 160.00, 80, 1000, '🥣', 'staples', 'IN100003'),
            ('Sugar (1kg)', 45.00, 150, 1000, '🧂', 'staples', 'IN100004'),
            ('Milk Packet (500ml)', 30.00, 200, 500, '🥛', 'dairy', 'IN100005'),
            ('Cooking Oil (1L)', 160.00, 90, 1000, '🛢️', 'pantry', 'IN100006'),
            ('Maggi Noodles', 14.00, 300, 70, '🍜', 'snacks', 'IN100007'),
            ('Biscuits (Parle-G/Britannia)', 20.00, 250, 150, '🍪', 'snacks', 'IN100008'),
            ('Tea Powder (Taj Mahal/Red Label 250g)', 150.00, 80, 250, '☕', 'beverages', 'IN100009'),
            ('Coffee (Bru/Nescafe 50g)', 95.00, 60, 50, '☕', 'beverages', 'IN100010'),
            ('Soap (Dettol/Dove)', 40.00, 150, 100, '🧼', 'personal_care', 'IN100011'),
            ('Shampoo (Clinic Plus/Sunsilk)', 120.00, 100, 340, '🧴', 'personal_care', 'IN100012'),
            ('Toothpaste (Colgate 100g)', 55.00, 120, 100, '🪥', 'personal_care', 'IN100013'),
            ('Eggs (Tray of 30)', 180.00, 40, 1500, '🥚', 'dairy', 'IN100014'),
            ('Onions (1kg)', 35.00, 200, 1000, '🧅', 'produce', 'IN100015'),
            ('Potatoes (1kg)', 25.00, 200, 1000, '🥔', 'produce', 'IN100016')
        ]
        
        cursor.executemany(products_sql, indian_products)
        conn.commit()
        
        print(f"Successfully migrated {len(indian_products)} Indian products to the database.")
        
    except Exception as e:
        print(f"Failed during migration: {e}")
        conn.rollback()
    finally:
        if 'conn' in locals() and conn.open:
            conn.close()

if __name__ == '__main__':
    migrate_indian_products()
