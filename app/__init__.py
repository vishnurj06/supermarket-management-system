from flask import Flask

def create_app():
    # 1. Create the Flask app instance
    app = Flask(__name__)
    
    # Optional: If you have a secret key or settings in config.py, we load them here later.
    app.secret_key = "super_secret_key_for_now" 

    # 2. Import your blueprints
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.customer import customer_bp
    from app.routes.api import api_bp

    # 3. Register the blueprints with the main app
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(api_bp)

    return app