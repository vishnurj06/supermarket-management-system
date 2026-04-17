import sys
import os
import pymysql
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

# 1. Point Python to the root folder so it can find 'app' and 'schema.sql'
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, ROOT_DIR)

from app.config import Config

def init_db():
    print("Connecting to MySQL server...")
    try:
        conn = pymysql.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            port=3306
        )
        cursor = conn.cursor()
        
        # 2. FIX: Find schema.sql in the ROOT directory
        schema_path = os.path.join(ROOT_DIR, 'schema.sql')
        
        print(f"Reading schema from: {schema_path}")
        with open(schema_path, 'r') as f:
            sql_script = f.read()
            
        statements = [stmt.strip() for stmt in sql_script.split(';') if stmt.strip()]
        for statement in statements:
            cursor.execute(statement)
        
        conn.commit()
        cursor.execute(f"USE {Config.MYSQL_DB}")
        
        admin_pw = generate_password_hash('admin123')
        staff_pw = generate_password_hash('staff123')
        cust_pw = generate_password_hash('customer123')
        
        users_sql = "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)"
        users_data = [
            ('admin', admin_pw, 'admin'),
            ('staff', staff_pw, 'staff'),
            ('customer', cust_pw, 'customer')
        ]
        
        try:
            cursor.executemany(users_sql, users_data)
            print("Added default users.")
        except pymysql.err.IntegrityError:
            print("Users already exist.")
        
        products_sql = """
            INSERT INTO products (name, price, stock, barcode, weight_g, image_url, category) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        products_data = [
            ('Artisan Sourdough', 5.99, 50, '100001', 500, '🥖', 'bakery'),
            ('Organic Avocados (2x)', 4.50, 40, '100002', 400, '🥑', 'produce'),
            ('Almond Milk', 3.99, 100, '100003', 1050, '🥛', 'dairy'),
            ('Hide And Seek Biscuit', 42.00, 3, '100004', 120, '🍪', 'snacks'),
            ('Coca-Cola, 750ml', 32.00, 18, '100005', 750, '🥤', 'beverages')
        ]
        
        try:
            cursor.executemany(products_sql, products_data)
            print("Added default products.")
        except pymysql.err.IntegrityError:
            print("Products already exist.")
            
        # 3. FIX: Raw PyMySQL inserts for Dummy Orders
        print("Inserting dummy sales data...")
        try:
            now = datetime.now()
            orders_sql = """
                INSERT INTO orders (exit_code, username, total_amount, exit_status, total_expected_weight, date) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            orders_data = [
                ('SM-2026-0001', 'customer', 1250.50, 'verified', 2000, now - timedelta(days=1)),
                ('SM-2026-0002', 'customer', 450.00, 'pending', 800, now),
                ('SM-2026-0003', 'customer', 890.25, 'verified', 1500, now - timedelta(days=2))
            ]
            cursor.executemany(orders_sql, orders_data)
            print("Added dummy orders.")
        except Exception as e:
            print(f"Skipped dummy orders: {e}")

        conn.commit()
        print("✅ Database initialized successfully with test data!")
        
    except pymysql.err.OperationalError as e:
        print(f"❌ Failed to connect to MySQL: {e}")
    except FileNotFoundError:
        print(f"❌ Could not find schema.sql at {schema_path}. Please make sure it is in the main folder!")
    finally:
        if 'conn' in locals() and conn.open:
            conn.close()

if __name__ == '__main__':
    init_db()