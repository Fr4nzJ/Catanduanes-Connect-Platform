import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY') or 'dev-secret-key-change-in-production'
    NEO4J_URI = os.environ.get('NEO4J_URI') or 'bolt://localhost:7687'
    NEO4J_USER = os.environ.get('NEO4J_USERNAME') or 'neo4j'  # Note: Using NEO4J_USERNAME from env
    NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD') or 'password'  # Default Neo4j Desktop password
    NEO4J_DATABASE = os.environ.get('NEO4J_DATABASE') or 'neo4j'
    
    # Simple cache instead of Redis
    CACHE_TYPE = 'SimpleCache'
    
    # Email Configuration
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('GMAIL_USER')
    MAIL_PASSWORD = os.environ.get('GMAIL_PASSWORD')
    ADMIN_EMAILS = os.environ.get('ADMIN_EMAILS', '').split(',')
    
    # Google OAuth
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI')

    # API Keys
    MEMO_API_TOKEN = os.environ.get('MEMO_API_TOKEN')
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    SEMAPHORE_API_KEY = os.environ.get('SEMAPHORE_API_KEY', '5dc45caa4475c0e877cdfda343b04ed0')
    
    # File Upload
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'static/uploads'
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH') or 16777216)
    ALLOWED_EXTENSIONS = set(os.environ.get('ALLOWED_EXTENSIONS', 'pdf,doc,docx,jpg,jpeg,png').split(','))
    
    # Security
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() in ['true', '1', 'yes']
    SESSION_COOKIE_HTTPONLY = os.environ.get('SESSION_COOKIE_HTTPONLY', 'True').lower() in ['true', '1', 'yes']
    REMEMBER_COOKIE_HTTPONLY = os.environ.get('REMEMBER_COOKIE_HTTPONLY', 'True').lower() in ['true', '1', 'yes']
    WTF_CSRF_TIME_LIMIT = int(os.environ.get('WTF_CSRF_TIME_LIMIT') or 3600)
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = "memory://"
    
    # External Services
    SENTRY_DSN = os.environ.get('SENTRY_DSN')
    GEOCODING_API_KEY = os.environ.get('GEOCODING_API_KEY')
    
    # Application Settings
    SITE_NAME = os.environ.get('SITE_NAME') or 'Catanduanes Connect'
    SITE_URL = os.environ.get('SITE_URL') or 'http://localhost:5000'
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'admin@catanduanesconnect.com'
    
    # Cache
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300
    
    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Log to syslog in production
        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    WTF_CSRF_ENABLED = False
    CACHE_TYPE = 'SimpleCache'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}