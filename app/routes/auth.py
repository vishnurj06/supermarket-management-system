from flask import Blueprint, render_template, request, session, redirect, url_for, flash, current_app
from werkzeug.security import check_password_hash, generate_password_hash
from app.models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    return redirect(url_for('auth.login'))

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
            
            # --- SMART REDIRECT LOGIC ---
            if user['role'] == 'admin' and 'admin' in current_app.blueprints:
                return redirect(url_for('admin.admin_dashboard'))
            elif user['role'] == 'staff' and 'staff' in current_app.blueprints:
                return redirect(url_for('staff.staff_panel'))
            elif user['role'] == 'customer':
                if 'customer' in current_app.blueprints:
                    return redirect(url_for('customer.customer_view'))
                else:
                    flash("Please use the Customer Portal (Port 5000) to log in.", "error")
                    session.clear()
                    return redirect(url_for('auth.login'))
            else:
                flash(f"Unauthorized: Your {user['role']} account cannot access this portal.", "error")
                session.clear()
                return redirect(url_for('auth.login'))
                
        return render_template('login.html', error="Invalid credentials")
            
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'customer' not in current_app.blueprints:
        flash("Registration is only available on the Customer Portal.", "error")
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        mobile = request.form.get('mobile')
        
        existing_user = User.get_by_username(username)
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'error')
            return redirect(url_for('auth.register'))
            
        success = User.create_customer(username, password)
        if success:
            # DIRECT DB UPDATE: Saves the extra fields instantly without breaking models.py
            try:
                from app.models import DB
                conn = DB.get_connection()
                with conn.cursor() as cursor:
                    cursor.execute("UPDATE users SET email=%s, mobile=%s WHERE username=%s", (email, mobile, username))
                conn.commit()
                conn.close()
            except Exception as e:
                pass # Fail silently if the columns don't exist yet
                
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('An error occurred. Please try again.', 'error')
            
    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

@auth_bp.route('/guest_start')
def guest_start():
    if 'customer' not in current_app.blueprints:
        flash("Guest checkout is only available on the Customer Portal.", "error")
        return redirect(url_for('auth.login'))
        
    import uuid
    session.clear()
    session['guest_id'] = str(uuid.uuid4())[:8]
    session['role'] = 'customer'
    session['username'] = 'Guest Shopper'
    return redirect(url_for('customer.customer_view'))