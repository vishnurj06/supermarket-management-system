from flask import Blueprint, render_template, request, session, redirect, url_for, flash
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