from flask import Blueprint, render_template, session, redirect, url_for

customer_bp = Blueprint('customer', __name__)

@customer_bp.route('/')
def index():
    return redirect(url_for('auth.login'))

@customer_bp.route('/customer')
def customer_view():
    if 'role' not in session or session.get('role') == 'customer':
        if 'guest_id' not in session and 'user_id' not in session:
            return redirect(url_for('auth.login'))
            
        username = session.get('username')
        return render_template('customer.html', username=username)
    else:
        # Redirect staff/admin away from customer panel inherently 
        return redirect(url_for('auth.login'))