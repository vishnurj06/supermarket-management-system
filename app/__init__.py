from flask import Flask, session, redirect, url_for, request
from app.config import Config

def create_app():
    app = Flask(__name__)
    
    # Load configuration settings (like your secret key) from app/config.py
    app.config.from_object(Config)

    # --- GLOBAL MIDDLEWARE ---
    @app.before_request
    def require_login():
        # Notice we updated the endpoints to include their blueprint names
        allowed_routes = ['auth.login', 'static', 'auth.guest_start', 'api.api_products', 'api.api_checkout']
        if request.endpoint not in allowed_routes and 'user_id' not in session and 'guest_id' not in session:
            return redirect(url_for('auth.login'))

    # --- IMPORT & REGISTER BLUEPRINTS ---
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.customer import customer_bp
    from app.routes.api import api_bp
    from app.routes.staff import staff_bp  

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(staff_bp)

    return app