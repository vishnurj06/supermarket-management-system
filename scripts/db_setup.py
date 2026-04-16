import pymysql
from werkzeug.security import generate_password_hash
from config import Config

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
        
        with open('schema.sql', 'r') as f:
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
        except pymysql.err.IntegrityError:
            print("Users already exist.")
        
        products_sql = """
            INSERT INTO products (name, price, stock, barcode, weight_g, image_url, category) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        products_data = [
            ('Artisan Sourdough', 5.99, 50, '100001', 500, '🥖', 'bakery'),
            ('Organic Avocados (2x)', 4.50, 40, '100002', 400, '🥑', 'produce'),
            ('Almond Milk (Unsweetened)', 3.99, 100, '100003', 1050, '🥛', 'dairy'),
            ('Free-Range Eggs (Dozen)', 6.49, 30, '100004', 650, '🥚', 'dairy'),
            ('Fairtrade Coffee Beans', 12.99, 60, '100005', 250, '☕', 'pantry'),
            ('Premium Sea Salt', 4.25, 20, '100006', 500, '🧂', 'pantry'),
            ('Grass-fed Beef Steak', 15.50, 15, '100007', 450, '🥩', 'meat'),
            ('Cherry Tomatoes', 3.49, 25, '100008', 300, '🍅', 'produce'),
            ('Greek Yogurt', 5.99, 45, '100009', 1000, '🥣', 'dairy'),
            ('Dark Chocolate (70%)', 3.50, 80, '100010', 100, '🍫', 'snacks')
        ]
        
        try:
            cursor.executemany(products_sql, products_data)
        except pymysql.err.IntegrityError:
            print("Products already exist.")
            
        conn.commit()
        print("Database initialized successfully!")
        
    except pymysql.err.OperationalError as e:
        print(f"Failed to connect to MySQL: {e}")
    finally:
        if 'conn' in locals() and conn.open:
            conn.close()

if __name__ == '__main__':
    init_db()
