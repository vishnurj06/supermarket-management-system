import pymysql.cursors
from config import Config

class DB:
    @staticmethod
    def get_connection():
        return pymysql.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            db=Config.MYSQL_DB,
            cursorclass=pymysql.cursors.DictCursor
        )

class User:
    @staticmethod
    def get_by_username(username):
        conn = DB.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
                return cursor.fetchone()
        finally:
            conn.close()

class Product:
    @staticmethod
    def get_all():
        conn = DB.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute('SELECT * FROM products')
                return cursor.fetchall()
        finally:
            conn.close()
            
    @staticmethod
    def get_by_id(product_id):
        conn = DB.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute('SELECT * FROM products WHERE id = %s', (product_id,))
                return cursor.fetchone()
        finally:
            conn.close()

    @staticmethod
    def create(name, price, stock, weight_g, image_url, category='', barcode=''):
        conn = DB.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO products (name, price, stock, weight_g, image_url, category, barcode)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                ''', (name, price, stock, weight_g, image_url, category, barcode))
                conn.commit()
                return cursor.lastrowid
        finally:
            conn.close()

    @staticmethod
    def update(product_id, name, price, stock, weight_g, image_url):
        conn = DB.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                    UPDATE products 
                    SET name=%s, price=%s, stock=%s, weight_g=%s, image_url=%s
                    WHERE id=%s
                ''', (name, price, stock, weight_g, image_url, product_id))
                conn.commit()
        finally:
            conn.close()

    @staticmethod
    def delete(product_id):
        conn = DB.get_connection()
        try:
            with conn.cursor() as cursor:
                # Need to handle order_items referencing this product.
                # In a real system, we'd maybe soft-delete, but for now we can either delete or delete from order_items
                # Usually we shouldn't delete products if they are in orders. But per requirement "Delete Product", let's just delete it directly.
                cursor.execute('DELETE FROM order_items WHERE product_id=%s', (product_id,))
                cursor.execute('DELETE FROM products WHERE id=%s', (product_id,))
                conn.commit()
        finally:
            conn.close()

class Order:
    @staticmethod
    def create(user_id, total_amount, expected_weight, items):
        import datetime
        
        conn = DB.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO orders (user_id, total_amount, total_expected_weight, payment_status, exit_status)
                    VALUES (%s, %s, %s, 'completed', 'pending')
                ''', (user_id, total_amount, expected_weight))
                order_id = cursor.lastrowid
                
                year = datetime.datetime.now().year
                exit_code = f"SM-{year}-{order_id:04d}"
                cursor.execute('UPDATE orders SET exit_code = %s WHERE id = %s', (exit_code, order_id))
                
                print("Saved Exit Code:", exit_code)
                
                for p_id, qty in items:
                    cursor.execute('INSERT INTO order_items (order_id, product_id, quantity) VALUES (%s, %s, %s)',
                                  (order_id, p_id, qty))
                    cursor.execute('UPDATE products SET stock = stock - %s WHERE id = %s AND stock >= %s', (qty, p_id, qty))
                    if cursor.rowcount == 0:
                        raise ValueError(f"Insufficient stock for product ID {p_id}")
                conn.commit()
                return order_id, exit_code
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_recent(limit=20):
        conn = DB.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                    SELECT o.id, COALESCE(u.username, 'Guest Shopper') as username, o.total_amount, o.total_expected_weight, o.exit_status, o.exit_code, o.date
                    FROM orders o
                    LEFT JOIN users u ON o.user_id = u.id
                    WHERE o.exit_code IS NOT NULL
                    ORDER BY 
                        CASE 
                            WHEN o.exit_status = 'pending' THEN 1
                            WHEN o.exit_status = 'completed' THEN 2
                            ELSE 3
                        END, 
                        o.date DESC
                    LIMIT %s
                ''', (limit,))
                return cursor.fetchall()
        finally:
            conn.close()

    @staticmethod
    def get_by_exit_code(exit_code):
        conn = DB.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                    SELECT o.id, COALESCE(u.username, 'Guest Shopper') as username, o.total_amount, o.total_expected_weight, o.exit_status, o.exit_code, o.date
                    FROM orders o
                    LEFT JOIN users u ON o.user_id = u.id
                    WHERE o.exit_code = %s
                ''', (exit_code,))
                return cursor.fetchone()
        finally:
            conn.close()

    @staticmethod
    def update_exit_status(order_id, new_status):
        print("DEBUG STATUS SENT TO DB:", new_status)

   
        new_status = new_status.lower()

        if new_status not in ["pending", "verified", "recheck", "inspection", "alert"]:
            new_status = "verified"

        conn = DB.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute('UPDATE orders SET exit_status = %s WHERE id = %s', (new_status, order_id))
                conn.commit()
        finally:
            conn.close()
