from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.security import check_password_hash
from config import Config
from models import User, Product, Order

app = Flask(__name__)
app.config.from_object(Config)

# --- MIDDLEWARE & AUTH ---

@app.before_request
def require_login():
    allowed_routes = ['login', 'static', 'guest_start', 'api_products', 'api_checkout']
    if request.endpoint not in allowed_routes and 'user_id' not in session and 'guest_id' not in session:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.get_by_username(username)
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['username'] = user['username']
            
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user['role'] == 'staff':
                return redirect(url_for('staff_panel'))
            else:
                return redirect(url_for('customer_view'))
        return render_template('login.html', error="Invalid credentials")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- VIEWS ---

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/guest_start', methods=['GET', 'POST'])
def guest_start():
    import uuid
    session.clear()
    session['guest_id'] = str(uuid.uuid4())[:8]
    session['role'] = 'customer'
    session['username'] = 'Guest Shopper'
    return redirect(url_for('customer_view'))

@app.route('/customer')
def customer_view():
    if 'role' not in session or session.get('role') == 'customer':
        if 'guest_id' not in session and 'user_id' not in session:
            return redirect(url_for('login'))
            
        username = session.get('username')
        return render_template('customer.html', username=username)
    else:
        # Redirect staff/admin away from customer panel inherently 
        return redirect(url_for('login'))

@app.route('/exit')
def staff_panel():
    if session.get('role') not in ['admin', 'staff']:
        return redirect(url_for('login'))
    return render_template('staff.html')

@app.route('/admin')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    products = Product.get_all()
    orders = Order.get_recent(20)
    
    low_stock_items = [p for p in products if p['stock'] < 10]
        
    return render_template('admin.html', products=products, orders=orders, low_stock_items=low_stock_items, total_products=len(products))

@app.route('/admin/product/add', methods=['POST'])
def admin_product_add():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    
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
        
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/product/edit/<int:product_id>', methods=['POST'])
def admin_product_edit(product_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
        
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
        
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/product/delete/<int:product_id>', methods=['POST'])
def admin_product_delete(product_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
        
    try:
        Product.delete(product_id)
        flash('Product deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting product: {str(e)}', 'error')
        
    return redirect(url_for('admin_dashboard'))


# --- API ENDPOINTS ---

@app.route('/api/products')
def api_products():
    if session.get('role') != 'customer':
        return jsonify({"error": "Unauthorized"}), 403
        
    products = Product.get_all()
    return jsonify(products)

@app.route('/api/checkout', methods=['POST'])
def api_checkout():
    if session.get('role') != 'customer':
        return jsonify({"error": "Unauthorized"}), 403
        
    data = request.json
    cart = data.get('cart', [])
    tax_rate = 0.08
    
    if not cart:
        return jsonify({"error": "Cart is empty"}), 400
        
    try:
        subtotal = 0
        total_weight = 0
        order_items = []
        
        for item in cart:
            product = Product.get_by_id(item['id'])
            if not product:
                continue
                
            line_price = float(product['price']) * item['qty']
            line_weight = product['weight_g'] * item['qty']
            
            subtotal += line_price
            total_weight += line_weight
            order_items.append((product['id'], item['qty']))
            
        tax = subtotal * tax_rate
        total_amount = subtotal + tax
        
        order_id, exit_code = Order.create(
            user_id=session.get('user_id'), # Nullable in schema for guests
            total_amount=total_amount, 
            expected_weight=total_weight, 
            items=order_items
        )
        
        return jsonify({
            "success": True,
            "order_id": order_id,
            "exit_code": exit_code,
            "total_paid": total_amount,
            "expected_weight": total_weight
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/orders/recent')
def api_recent_orders():
    if session.get('role') not in ['admin', 'staff']:
        return jsonify({"error": "Unauthorized"}), 403
        
    try:
        orders = Order.get_recent(20)
        # Format dates
        for o in orders:
            if o['date']:
                o['date'] = o['date'].strftime('%b %d, %Y %H:%M')
        return jsonify(orders)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/order/<string:exit_code>')
def api_get_order(exit_code):
    if session.get('role') not in ['admin', 'staff']:
        return jsonify({"error": "Unauthorized"}), 403
        
    exit_code = exit_code.strip().upper()
    try:
        order = Order.get_by_exit_code(exit_code)
        if not order:
            return jsonify({"error": "No matching receipt found. Please verify the exit code."}), 404
            
        return jsonify(order)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/validate_exit', methods=['POST'])
def api_validate_exit():
    if session.get('role') not in ['admin', 'staff']:
        return jsonify({"error": "Unauthorized"}), 403
        
    data = request.json
    exit_code = data.get('exit_code', '').strip().upper()
    measured_weight = float(data.get('measured_weight', 0))
    
    try:
        order = Order.get_by_exit_code(exit_code)
        if not order:
            return jsonify({"error": "Invalid or already verified receipt."}), 404
            
        if order['exit_status'] in ['verified', 'EXITED']:
            return jsonify({"error": "Invalid or already verified receipt."}), 400
            
        expected = order['total_expected_weight']
        diff = abs(expected - measured_weight)
        
        if diff <= 50:
            new_status = 'EXITED'
            message = "Weight validation passed. Customer cleared for exit."
        else:
            if order['exit_status'] in ['recheck', 'inspection']:
                new_status = 'alert'
                message = "THEFT ALERT: Repeated weight mismatch detected."
            else:
                if measured_weight < expected:
                    new_status = 'recheck'
                    message = "Measurement mismatch detected. Please retry scan or recalibrate scale."
                else:
                    new_status = 'inspection'
                    message = "Measurement mismatch detected. Please retry scan or recalibrate scale."
            
        Order.update_exit_status(order['id'], new_status)
        
        return jsonify({
            "success": new_status == 'verified',
            "status": new_status,
            "message": message,
            "diff": diff
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
