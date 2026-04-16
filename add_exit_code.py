import pymysql
from config import Config

def update_schema():
    print("Connecting to MySQL server to add exit_code...")
    try:
        conn = pymysql.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            db=Config.MYSQL_DB
        )
        cursor = conn.cursor()
        
        # Check if exit_code exists to be safe
        cursor.execute("SHOW COLUMNS FROM orders LIKE 'exit_code'")
        result = cursor.fetchone()
        if not result:
            cursor.execute("ALTER TABLE orders ADD COLUMN exit_code VARCHAR(10) UNIQUE AFTER exit_status")
            print("Successfully added exit_code column.")
        else:
            print("exit_code column already exists.")
            
        # Update enum for exit_status
        cursor.execute("ALTER TABLE orders MODIFY COLUMN exit_status ENUM('pending', 'verified', 'recheck', 'inspection', 'alert') DEFAULT 'pending'")
        print("Successfully updated exit_status ENUM.")
        
        conn.commit()
        print("Database updated successfully!")
        
    except pymysql.err.OperationalError as e:
        print(f"Failed to connect to MySQL: {e}")
    finally:
        if 'conn' in locals() and conn.open:
            conn.close()

if __name__ == '__main__':
    update_schema()
