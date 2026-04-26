from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify
from app.models import Order, User, DB
from werkzeug.security import check_password_hash

customer_bp = Blueprint('customer', __name__)

@customer_bp.route('/customer')
def customer_view():
    if 'role' not in session or session.get('role') == 'customer':
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
            
        # NEW: Fetch the user's profile and support tickets from the database
        user_data = {}
        tickets = []
        
        if 'user_id' in session:
            conn = DB.get_connection()
            try:
                with conn.cursor() as cursor:
                    # Fetch Profile
                    cursor.execute("SELECT * FROM users WHERE id=%s", (session['user_id'],))
                    user_data = cursor.fetchone() or {}
                    
                    # Fetch Tickets
                    cursor.execute("SELECT * FROM support_tickets WHERE username=%s ORDER BY created_at DESC", (session['username'],))
                    tickets = cursor.fetchall()
            except Exception as e:
                print(f"Error fetching customer data: {e}")
            finally:
                conn.close()
                
        return render_template('customer.html', 
                               username=session.get('username'),
                               user=user_data,     # Pass profile data to HTML
                               tickets=tickets)    # Pass tickets to HTML
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


@customer_bp.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    data = request.json
    user_id = session['user_id']
    password = data.get('password') 
    
    conn = DB.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT password_hash FROM users WHERE id=%s', (user_id,))
            user_record = cursor.fetchone()
            
            # --- THE FIX IS HERE ---
            # Use check_password_hash to safely compare the typed password with the encrypted hash
            if not user_record or not check_password_hash(user_record.get('password_hash'), password): 
                return jsonify({'success': False, 'message': 'Incorrect password'}), 403

            # Update the Database
            cursor.execute('''
                UPDATE users 
                SET full_name=%s, email=%s, mobile=%s, gender=%s, dob=%s, wants_offers=%s 
                WHERE id=%s
            ''', (
                data.get('full_name'), data.get('email'), data.get('mobile'), 
                data.get('gender'), data.get('dob'), data.get('wants_offers'), 
                user_id
            ))
            conn.commit()
            
        return jsonify({'success': True, 'message': 'Profile updated successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

@customer_bp.route('/submit_support', methods=['POST'])
def submit_support():
    if 'username' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    data = request.json
    conn = DB.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('''
                INSERT INTO support_tickets (username, issue_type, message) 
                VALUES (%s, %s, %s)
            ''', (session['username'], data.get('type'), data.get('message')))
            conn.commit()
        return jsonify({'success': True, 'message': 'Support ticket sent to Admin!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()