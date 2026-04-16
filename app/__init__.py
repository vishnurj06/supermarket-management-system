from flask import Flask, session, redirect, url_for, request
from app.config import Config

def create_app(role_filter=None):
    app = Flask(__name__)
    app.config.from_object(Config)

    # 1. Import all Blueprints
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.customer import customer_bp
    from app.routes.api import api_bp
    from app.routes.staff import staff_bp

    # Create a list to track which blueprints we register
    active_blueprints = ['auth']

    # 2. Logic to register ONLY what is needed for that "website"
    app.register_blueprint(auth_bp)

    if role_filter == 'customer':
        app.register_blueprint(customer_bp)
        app.register_blueprint(api_bp) 
        active_blueprints.extend(['customer', 'api'])
    
    elif role_filter == 'admin':
        app.register_blueprint(admin_bp)
        app.register_blueprint(staff_bp) 
        # --- FIX: API added to Admin port for live dashboard stats ---
        app.register_blueprint(api_bp) 
        active_blueprints.extend(['admin', 'staff', 'api'])
    
    elif role_filter == 'staff':
        app.register_blueprint(staff_bp)
        # --- FIX: API added to Staff port for exit validations ---
        app.register_blueprint(api_bp) 
        active_blueprints.extend(['staff', 'api'])
    
    else:
        # Fallback for old run.py
        app.register_blueprint(admin_bp)
        app.register_blueprint(customer_bp)
        app.register_blueprint(api_bp)
        app.register_blueprint(staff_bp)
        active_blueprints.extend(['admin', 'customer', 'api', 'staff'])

    # Store the active list in app config so templates can see it
    app.config['REGISTERED_BLUEPRINTS'] = active_blueprints

    # --- UPDATED MIDDLEWARE ---
    @app.before_request
    def require_login():
        allowed_routes = ['auth.login', 'auth.register', 'static', 'auth.guest_start']
        if request.endpoint not in allowed_routes and 'user_id' not in session and 'guest_id' not in session:
            return redirect(url_for('auth.login'))

    return app