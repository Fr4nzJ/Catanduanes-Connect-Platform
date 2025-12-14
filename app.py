from neo4j.exceptions import ServiceUnavailable 
import os
import logging
from flask import Flask, render_template, request, jsonify, g, flash, redirect, url_for
from flask_login import LoginManager, login_required, current_user
from flask_babel import Babel
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
from datetime import datetime
from extensions import limiter, cache, csrf   # ← import from neutral module
from blueprints.chatbot.routes import chatbot_bp

from config import config
from database import init_neo4j, get_neo4j_db, safe_run, _node_to_dict
from models import User

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

# Initialize extensions
login_manager = LoginManager()
babel = Babel()
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://"  # Use in-memory storage
)
cache = Cache(config={
    "CACHE_TYPE": "SimpleCache",  # Simple in-memory cache
    "CACHE_DEFAULT_TIMEOUT": 300  # Default timeout of 5 minutes
})
csrf = CSRFProtect()

def init_csrf(app):
    """Initialize CSRF protection and exempt specific routes"""
    csrf.init_app(app)
    # List of routes to exempt from CSRF protection
    csrf_exempt_routes = [
        '/auth/resend-otp',  # Add more routes here if needed
    ]
    for route in csrf_exempt_routes:
        csrf.exempt(route)

@login_manager.user_loader
def load_user(user_id):
    """Load user from Neo4j for Flask-Login with enhanced role validation"""
    logger = logging.getLogger('user_loader')

    # ----  DEBUG  (temporary)  ----
    logger.info(f"load_user: looking for id={user_id!r}  type={type(user_id)}")

    if not user_id:
        logger.warning("Attempted to load user with empty ID")
        return None

    try:
        db = get_neo4j_db()
        with db.session() as session:
            result = safe_run(
                session,
                """
                MATCH (u:User)
                WHERE u.id = $user_id
                RETURN u
                """,
                {"user_id": user_id}
            )

            logger.info(f"load_user: safe_run returned {result}")   # <- DEBUG

            if not result:
                logger.warning(f"No user found with ID {user_id}")
                return None

            node = result[0]["u"]               # raw Neo4j node
            user_data = {k: v for k, v in node.items()}  # turn properties into dict
            user = User(**user_data)
            logger.info(f"User loaded: {user.email} (ID: {user.id}, Role: {user.role})")
            return user

    except Exception as e:
        logger.error(f"Error loading user {user_id}: {str(e)}", exc_info=True)
        return None


@login_manager.unauthorized_handler
def unauthorized():
    """Handle unauthorized access attempt"""
    flash('Please log in to access this page.', 'warning')
    return redirect(url_for('auth.login', next=request.url))

def create_app(config_name='default'):
    """Application factory function"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Ensure we have a secret key for sessions
    if not app.config.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = os.urandom(32)
    
    # Configure session settings
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours
    app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_NAME'] = 'catanduanes_session'
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    # Configure remember me
    app.config['REMEMBER_COOKIE_NAME'] = 'catanduanes_remember_token'
    app.config['REMEMBER_COOKIE_DURATION'] = 2592000  # 30 days
    app.config['REMEMBER_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
    app.config['REMEMBER_COOKIE_HTTPONLY'] = True
    app.config['REMEMBER_COOKIE_SAMESITE'] = 'Lax'
    
    # Initialize extensions
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.session_protection = 'strong'
    login_manager.refresh_view = 'auth.login'
    login_manager.needs_refresh_message = 'Please login again to confirm your identity'
    login_manager.needs_refresh_message_category = 'info'
    
    # Initialize CSRF protection with exemptions
    init_csrf(app)
    
    babel.init_app(app)
    limiter.init_app(app)
    cache.init_app(app)
    
    # Initialize database
    init_neo4j(app)
    
    # Import blueprints
    from blueprints.admin import admin_bp
    from blueprints.admin.management_routes import admin_mgmt
    from blueprints.auth import auth_bp
    from blueprints.businesses.routes import businesses_bp
    from blueprints.jobs.routes import jobs_bp
    # from blueprints.services.routes import services_bp
    from blueprints.dashboard.routes import dashboard_bp
    from blueprints.verification.routes import verification_bp
    from blueprints.chat.routes import chat_bp
    from blueprints.chatbot.routes import chatbot_bp
    from blueprints.api.routes import api_bp
    from blueprints.gemini.routes import gemini_bp
    
    # Register blueprints
    app.register_blueprint(admin_bp)  # URL prefix is already set in the blueprint
    app.register_blueprint(admin_mgmt)  # Admin management routes
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(businesses_bp, url_prefix="/businesses")
    app.register_blueprint(jobs_bp, url_prefix="/jobs")
    # app.register_blueprint(services_bp, url_prefix="/services")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
    app.register_blueprint(verification_bp, url_prefix="/verify")
    app.register_blueprint(chat_bp, url_prefix="/chat")
    app.register_blueprint(chatbot_bp, url_prefix="/chatbot")
    csrf.exempt(chatbot_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(gemini_bp, url_prefix="/gemini")
    
    @app.template_filter('datetime')
    def _datetime_filter(s):
        """ISO-string -> human-readable local time."""
        if not s:
            return ''
        dt = datetime.fromisoformat(s.replace('Z', '+00:00'))
        return dt.strftime('%d %b %Y, %H:%M')
    
    from flask import request

    @app.template_filter('url_replace')
    def url_replace(request_args, field, value):
        """Custom Jinja filter to replace or add a query parameter in the URL."""
        args = request_args.copy()
        args = args.to_dict()  # make sure it's a mutable dict
        args[field] = value
        return "&".join(f"{key}={val}" for key, val in args.items())



    
    # Register error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template("errors/500.html"), 500
    
    # Register main routes
    @app.route("/")
    def home():
        return render_template("home.html")

    @app.route("/about")
    def about():
        return render_template("about.html")
    
    @app.context_processor
    def inject_utils():
        return dict(min=min, max=max)

    # ------------------------------------------------------------------
    # Safe to create the driver now (real worker process)
    # ------------------------------------------------------------------
    init_neo4j(app)
    
    # Create admin account if not exists
    with app.app_context():
        from datetime import datetime
        import uuid
        import bcrypt
        
        db = get_neo4j_db()
        admin_email = "admin@catanduanes.com"
        admin_username = "admin"
        admin_password = "Admin123!"  # Change this after first login
        admin_role = "admin"
        
        with db.session() as session:
            result = safe_run(session, "MATCH (u:User {email: $email}) RETURN u", {"email": admin_email})
            if not result:
                password_hash = bcrypt.hashpw(admin_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
                safe_run(session, """
                    CREATE (u:User {
                        id: $id,
                        email: $email,
                        username: $username,
                        password_hash: $password_hash,
                        role: $role,
                        is_verified: true,
                        is_active: true,
                        created_at: $created_at
                    })
                """, {
                    "id": str(uuid.uuid4()),
                    "email": admin_email,
                    "username": admin_username,
                    "password_hash": password_hash,
                    "role": admin_role,
                    "created_at": datetime.utcnow().isoformat()
                })
                print(f"Created admin account: {admin_email} (change password after first login)")
    
    return app


# Create Flask app instance
app = create_app(os.getenv('FLASK_ENV') or ('production' if 'PORT' in os.environ else 'development'))

# Run the development server if this file is run directly
if __name__ == '__main__':
    app.run(debug=False, use_reloader=False, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
