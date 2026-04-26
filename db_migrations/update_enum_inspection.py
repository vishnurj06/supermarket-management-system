import pymysql
from config import Config

def main():
    try:
        conn = pymysql.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            db=Config.MYSQL_DB
        )
        cursor = conn.cursor()
        
        # Alter the ENUM in orders to include 'inspection'
        cursor.execute("ALTER TABLE orders MODIFY COLUMN exit_status ENUM('pending', 'verified', 'recheck', 'alert', 'inspection') DEFAULT 'pending'")
        conn.commit()
        print("Successfully updated exit_status enum in orders table to include inspection.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals() and conn.open:
            conn.close()

if __name__ == '__main__':
    main()
