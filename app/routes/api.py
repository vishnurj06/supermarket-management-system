from flask import Blueprint, jsonify, request, session
from app.models import Product, Order

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/products')
def api_products():
    if session.get('role') != 'customer':
        return jsonify({"error": "Unauthorized"}), 403
        
    products = Product.get_all()
    return jsonify(products)

@api_bp.route('/checkout', methods=['POST'])
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

@api_bp.route('/orders/recent')
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

@api_bp.route('/order/<string:exit_code>')
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

@api_bp.route('/validate_exit', methods=['POST'])
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
    

@api_bp.route('/cart/scan', methods=['POST'])
def scan_to_cart():
    # 1. Security Check
    if 'user_id' not in session and 'guest_id' not in session:
        return jsonify({'error': 'Session expired. Please log in again.'}), 401

    data = request.get_json()
    identifier = data.get('identifier')

    if not identifier:
        return jsonify({'error': 'No barcode detected.'}), 400

    # 2. Find the product (Checks both Barcode and ID just in case)
    all_products = Product.get_all()
    product = next((p for p in all_products if str(p.get('barcode')) == str(identifier) or str(p['id']) == str(identifier)), None)

    if not product:
        return jsonify({'error': 'Product not found in store database.'}), 404

    # 3. Add to Cart Logic
    if 'cart' not in session:
        session['cart'] = {}

    p_id_str = str(product['id'])
    
    # If already in cart, increase quantity. Otherwise, add new item.
    if p_id_str in session['cart']:
        session['cart'][p_id_str]['quantity'] += 1
    else:
        session['cart'][p_id_str] = {
            'id': product['id'],
            'name': product['name'],
            'price': float(product['price']),
            'weight_g': product.get('weight_g', 0),
            'image_url': product.get('image_url', ''),
            'quantity': 1
        }
    
    session.modified = True

    return jsonify({
        'success': True,
        'name': product['name'],
        'price': product['price']
    })