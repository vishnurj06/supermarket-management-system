from flask import Blueprint, render_template, session, redirect, url_for

staff_bp = Blueprint('staff', __name__)

@staff_bp.route('/exit')
def staff_panel():
    if session.get('role') not in ['admin', 'staff']:
        return redirect(url_for('auth.login'))
    return render_template('staff.html')