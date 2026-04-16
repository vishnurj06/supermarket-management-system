from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from werkzeug.security import check_password_hash  # <-- Added this import!
from app.models import User

auth_bp = Blueprint('auth', __name__)

# login route
@auth_bp.route('/login', methods=['GET', 'POST'])
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
                return redirect(url_for('admin.admin_dashboard')) # <-- Updated namespace
            elif user['role'] == 'staff':
                return redirect(url_for('staff.staff_panel')) # (We will set this up later)
            else:
                return redirect(url_for('customer.customer_view')) # <-- Updated namespace
        return render_template('login.html', error="Invalid credentials")
            
    return render_template('login.html')

# logout route
@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login')) # <-- Updated namespace

# guest start route
@auth_bp.route('/guest_start')
def guest_start():
    import uuid
    session.clear()
    session['guest_id'] = str(uuid.uuid4())[:8]
    session['role'] = 'customer'
    session['username'] = 'Guest Shopper'
    return redirect(url_for('customer.customer_view')) # <-- Updated namespace