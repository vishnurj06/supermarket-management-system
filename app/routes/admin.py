import os
import time
import qrcode
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, current_app
from app.models import Product, Order, User, DB

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@admin_bp.route('')
def admin_dashboard():
    try: products = Product.get_all()
    except Exception: products = []
    
    orders = []
    try:
        if hasattr(Order, 'get_all'): orders = Order.get_all()
    except Exception: pass
        
    # Safely fetch users and filter out admins/staff
    users = []
    try:
        if hasattr(User, 'get_all'):
            all_users = User.get_all()
            # FIX: Only keep the user if their role is exactly 'customer'
            users = [u for u in all_users if u.get('role', '').lower() == 'customer']
    except Exception:
        pass
    
    # --- NEW: Time-based Analytics Calculation ---
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday()) # Monday
    month_start = today_start.replace(day=1)

    stats = {
        'daily_rev': 0, 'weekly_rev': 0, 'monthly_rev': 0, 'total_rev': 0,
        'daily_ord': 0, 'weekly_ord': 0, 'monthly_ord': 0, 'total_ord': 0
    }

    for o in orders:
        amt = float(o.get('total_amount', 0))
        o_date = o.get('date')
        
        stats['total_rev'] += amt
        stats['total_ord'] += 1
        
        if o_date:
            # PyMySQL returns datetime objects. We compare them securely.
            if isinstance(o_date, datetime):
                if o_date >= today_start:
                    stats['daily_rev'] += amt
                    stats['daily_ord'] += 1
                if o_date >= week_start:
                    stats['weekly_rev'] += amt
                    stats['weekly_ord'] += 1
                if o_date >= month_start:
                    stats['monthly_rev'] += amt
                    stats['monthly_ord'] += 1

    low_stock_items = [p for p in products if p.get('stock', 0) < 10]
    total_products = len(products)

    # ... (your existing stats and low_stock code) ...

    # NEW: Fetch Support Tickets
    tickets = []
    conn = DB.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM support_tickets ORDER BY created_at DESC')
            tickets = cursor.fetchall()
    except Exception as e:
        print(f"Error fetching tickets: {e}")
    finally:
        conn.close()
        
    return render_template('admin.html', 
                           products=products, 
                           orders=orders, 
                           users=users, 
                           total_products=total_products, 
                           low_stock_items=low_stock_items,
                           stats=stats,
                           tickets=tickets) # <-- Add tickets here!
    
    return render_template('admin.html', 
                           products=products, 
                           orders=orders, 
                           users=users, 
                           total_products=total_products, 
                           low_stock_items=low_stock_items,
                           stats=stats) # Pass new stats to the HTML

@admin_bp.route('/add_product', methods=['POST'])
def add_product():
    if session.get('role') != 'admin': return redirect(url_for('auth.login'))
    try:
        barcode_input = request.form.get('barcode', '').strip()
        if not barcode_input: barcode_input = f"AUTO-{int(time.time())}"

        Product.create(
            name=request.form['name'], price=float(request.form['price']),
            stock=int(request.form['stock']), weight_g=int(request.form.get('weight_g', 0)),
            image_url=request.form['image_url'], category=request.form.get('category', ''),
            barcode=barcode_input
        )
        flash('Product added successfully!', 'success')
    except Exception as e: flash(f'Error adding product: {str(e)}', 'error')
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/product/edit/<int:product_id>', methods=['POST'])
def edit_product(product_id):
    if session.get('role') != 'admin': return redirect(url_for('auth.login'))
    try:
        Product.update(
            product_id=product_id, name=request.form['name'], price=float(request.form['price']),
            stock=int(request.form['stock']), weight_g=int(request.form.get('weight_g', 0)),
            image_url=request.form['image_url']
        )
        flash('Product updated successfully!', 'success')
    except Exception as e: flash(f'Error updating product: {str(e)}', 'error')
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/product/delete/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    if session.get('role') != 'admin': return redirect(url_for('auth.login'))
    try:
        Product.delete(product_id)
        flash('Product deleted successfully!', 'success')
    except Exception as e: flash(f'Error deleting product: {str(e)}', 'error')
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/product/qr/<int:product_id>')
def view_qr(product_id):
    product = Product.get_by_id(product_id)
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for('admin.admin_dashboard'))
        
    filename = f"qr_{product_id}.png"
    filepath = os.path.join(current_app.root_path, 'static', 'qrcodes', filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    if not os.path.exists(filepath):
        qr_data = f"SMARTMART:{product.get('barcode', product_id)}"
        qr = qrcode.make(qr_data)
        qr.save(filepath)
        
    qr_url = url_for('static', filename=f'qrcodes/{filename}')
    
    return f"""
    <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100vh; font-family:sans-serif; background:#f8fafc;">
        <div style="background:white; padding:3rem; border-radius:1rem; box-shadow:0 4px 6px -1px rgba(0,0,0,0.1); text-align:center;">
            <h2>{product['name']}</h2>
            <p style="color:#64748b; margin-bottom:2rem;">SKU/Barcode: {product.get('barcode', product['id'])}</p>
            <img src="{qr_url}" alt="QR Code" style="width:250px; height:250px; border:1px solid #e2e8f0; border-radius:0.5rem;">
            <br><br>
            <button onclick="window.print()" style="background:#2563eb; color:white; border:none; padding:0.75rem 1.5rem; border-radius:0.5rem; cursor:pointer; font-size:1rem; margin-right:1rem;">🖨️ Print Tag</button>
            <a href="{url_for('admin.admin_dashboard')}" style="color:#2563eb; text-decoration:none; font-weight:600;">Back to Dashboard</a>
        </div>
    </div>
    """

@admin_bp.route('/resolve_ticket/<int:ticket_id>', methods=['POST'])
def resolve_ticket(ticket_id):
    if session.get('role') != 'admin': 
        return redirect(url_for('auth.login'))
        
    conn = DB.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE support_tickets SET status='Resolved' WHERE id=%s", (ticket_id,))
            conn.commit()
        flash('Ticket marked as resolved.', 'success')
    except Exception as e: 
        flash(f'Error resolving ticket: {str(e)}', 'error')
    finally:
        conn.close()
        
    return redirect(url_for('admin.admin_dashboard'))