from flask import Blueprint, render_template, session, redirect, url_for, flash
from app.models import Order

customer_bp = Blueprint('customer', __name__)

@customer_bp.route('/customer')
def customer_view():
    if 'role' not in session or session.get('role') == 'customer':
        if 'guest_id' not in session and 'user_id' not in session:
            return redirect(url_for('auth.login'))
            
        username = session.get('username')
        return render_template('customer.html', username=username)
    else:
        return redirect(url_for('auth.login'))

@customer_bp.route('/my_orders')
def my_orders():
    if 'user_id' not in session:
        flash("Please register or log in to view order history.", "error")
        return redirect(url_for('auth.login'))
        
    user_orders = Order.get_by_user_id(session['user_id'])
    
    for o in user_orders:
        if o['date']:
            o['date'] = o['date'].strftime('%b %d, %Y')

    return render_template('my_orders.html', orders=user_orders, username=session.get('username'))