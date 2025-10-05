from flask import Flask, render_template, redirect, url_for, session, flash
import traceback
import os

app = Flask(__name__)

# Config settings - USE ENVIRONMENT VARIABLES FOR PRODUCTION
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'e3741741d2525b1db3f79a38893e7248b3c245b8d23c126b')
app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD', '')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB', 'rental_service')
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['DEBUG'] = os.environ.get('FLASK_ENV') != 'production'

# Import and register blueprints
try:
    from modules.auth import auth_bp
    from modules.admin_routes import admin_bp
    from modules.user_routes import user_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(user_bp)  # This will handle ALL routes including '/'
    print("✅ Blueprints registered successfully")
    
except Exception as e:
    print(f"❌ Error registering blueprints: {e}")
    traceback.print_exc()

# REMOVE the home route from app.py since it's now in user_routes.py
# The @user_bp.route('/') in user_routes.py will handle the home page

@app.errorhandler(500)
def internal_error(error):
    return f"<h1>500 Error</h1><pre>{traceback.format_exc()}</pre>", 500

@app.errorhandler(404)
def not_found(error):
    return "<h1>404 - Page not found</h1><p>The page you're looking for doesn't exist.</p>", 404

if __name__ == '__main__':
    app.run(debug=True)
