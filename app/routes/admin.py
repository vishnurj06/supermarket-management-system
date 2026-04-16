import os
import qrcode
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, current_app
from app.models import Product, Order, User

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# admin dashboard route
@admin_bp.route('/')
def admin_dashboard(): # <-- Renamed to match the redirect in auth.py
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login')) # <-- Updated namespace
    
    products = Product.get_all()
    orders = Order.get_recent(20)
    
    low_stock_items = [p for p in products if p['stock'] < 10]
        
    return render_template('admin.html', products=products, orders=orders, low_stock_items=low_stock_items, total_products=len(products))

# admin add product route
@admin_bp.route('/add_product', methods=['POST'])
def add_product():
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login')) # <-- Updated namespace
    
    try:
        Product.create(
            name=request.form['name'],
            price=float(request.form['price']),
            stock=int(request.form['stock']),
            weight_g=int(request.form['weight_g']),
            image_url=request.form['image_url'],
            category=request.form.get('category', ''),
            barcode=request.form.get('barcode', '')
        )
        flash('Product added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding product: {str(e)}', 'error')
        
    return redirect(url_for('admin.admin_dashboard')) # <-- Updated namespace

# admin edit product route
@admin_bp.route('/product/edit/<int:product_id>', methods=['POST']) # <-- Removed the extra /admin
def edit_product(product_id):
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))
        
    try:
        Product.update(
            product_id=product_id,
            name=request.form['name'],
            price=float(request.form['price']),
            stock=int(request.form['stock']),
            weight_g=int(request.form['weight_g']),
            image_url=request.form['image_url']
        )
        flash('Product updated successfully!', 'success')
    except Exception as e:
        flash(f'Error updating product: {str(e)}', 'error')
        
    return redirect(url_for('admin.admin_dashboard'))

# admin delete product route
@admin_bp.route('/product/delete/<int:product_id>', methods=['POST']) # <-- Removed the extra /admin
def delete_product(product_id):
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))
        
    try:
        Product.delete(product_id)
        flash('Product deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting product: {str(e)}', 'error')
        
    return redirect(url_for('admin.admin_dashboard'))


#qr generator route
def generate_product_qr(product_id, barcode):
    """Generates a QR code image for a product and saves it to the static folder"""
    # The data embedded in the QR code. We use the barcode if it exists, otherwise the ID.
    qr_data = f"SMARTMART:{barcode if barcode else product_id}"
    
    # Generate the QR Code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save it to the static/qrcodes directory
    filename = f"qr_{product_id}.png"
    filepath = os.path.join(current_app.root_path, 'static', 'qrcodes', filename)
    img.save(filepath)
    
    return filename

@admin_bp.route('/product/qr/<int:product_id>')
def view_qr(product_id):
    # Fetch the product from your database using your existing model
    # Note: Adjust 'Product.get_by_id' if your method is named differently!
    from app.models import Product 
    product = Product.get_by_id(product_id)
    
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for('admin.admin_dashboard'))
        
    filename = f"qr_{product_id}.png"
    filepath = os.path.join(current_app.root_path, 'static', 'qrcodes', filename)
    
    # If the QR code doesn't exist yet, generate it on the fly!
    if not os.path.exists(filepath):
        generate_product_qr(product['id'], product.get('barcode'))
        
    qr_url = url_for('static', filename=f'qrcodes/{filename}')
    
    # We will render a very simple, clean page just for displaying the QR code
    return f"""
    <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100vh; font-family:sans-serif; background:#f8fafc;">
        <div style="background:white; padding:3rem; border-radius:1rem; box-shadow:0 4px 6px -1px rgba(0,0,0,0.1); text-align:center;">
            <h2>{product['name']}</h2>
            <p style="color:#64748b; margin-bottom:2rem;">SKU/Barcode: {product.get('barcode', product['id'])}</p>
            <img src="{qr_url}" alt="QR Code" style="width:250px; height:250px; border:1px solid #e2e8f0; border-radius:0.5rem;">
            <br><br>
            <button onclick="window.print()" style="background:#2563eb; color:white; border:none; padding:0.75rem 1.5rem; border-radius:0.5rem; cursor:pointer; font-size:1rem; margin-right:1rem;">🖨️ Print Tag</button>
            <a href="/admin" style="color:#2563eb; text-decoration:none; font-weight:600;">Back to Dashboard</a>
        </div>
    </div>
    """