import os
import urllib.request
import pymysql
from config import Config

# Mapping barcode to unsplash/image URLs
images_to_download = {
    'IN100001': 'https://images.unsplash.com/photo-1586201375761-83865001e31c?w=400&h=400&fit=crop', # rice
    'IN100002': 'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=400&h=400&fit=crop', # flour
    'IN100003': 'https://images.unsplash.com/photo-1585994803975-dcf45ba252b4?w=400&h=400&fit=crop', # dal
    'IN100004': 'https://images.unsplash.com/photo-1581428982868-e410dd4fc73c?w=400&h=400&fit=crop', # sugar
    'IN100005': 'https://images.unsplash.com/photo-1563636619-e9143da7973b?w=400&h=400&fit=crop', # milk
    'IN100006': 'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=400&h=400&fit=crop', # oil
    'IN100007': 'https://images.unsplash.com/photo-1612929633738-8fe44f7ec841?w=400&h=400&fit=crop', # noodles
    'IN100008': 'https://images.unsplash.com/photo-1558961363-fa8fdf82db35?w=400&h=400&fit=crop', # biscuits
    'IN100009': 'https://images.unsplash.com/photo-1597481499750-3e6b22637e12?w=400&h=400&fit=crop', # tea
    'IN100010': 'https://images.unsplash.com/photo-1559525839-b184a4d698c7?w=400&h=400&fit=crop', # coffee
    'IN100011': 'https://images.unsplash.com/photo-1600857544200-b2f666a9a2ec?w=400&h=400&fit=crop', # soap
    'IN100012': 'https://images.unsplash.com/photo-1535585209827-a15fcdbc4c2d?w=400&h=400&fit=crop', # shampoo
    'IN100013': 'https://images.unsplash.com/photo-1559598467-f8b76c8155d0?w=400&h=400&fit=crop', # toothpaste
    'IN100014': 'https://images.unsplash.com/photo-1587486913049-53fc88980bcf?w=400&h=400&fit=crop', # eggs
    'IN100015': 'https://images.unsplash.com/photo-1618512496248-a07ce83aa8cb?w=400&h=400&fit=crop', # onions
    'IN100016': 'https://images.unsplash.com/photo-1518977676601-b53f82aba655?w=400&h=400&fit=crop'  # potatoes
}

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    img_dir = os.path.join(base_dir, 'static', 'images', 'products')
    
    conn = pymysql.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        db=Config.MYSQL_DB
    )
    cursor = conn.cursor()
    
    for barcode, url in images_to_download.items():
        filename = f"{barcode}.jpg"
        filepath = os.path.join(img_dir, filename)
        
        print(f"Downloading {filename}...")
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response, open(filepath, 'wb') as out_file:
                out_file.write(response.read())
                
            local_url = f"/static/images/products/{filename}"
            # Update DB with new local URL
            cursor.execute("UPDATE products SET image_url=%s WHERE barcode=%s", (local_url, barcode))
        except Exception as e:
            print(f"Failed to download or update {barcode}: {e}")
            
    conn.commit()
    conn.close()
    print("Downloaded images and updated DB successfully!")

if __name__ == '__main__':
    main()
