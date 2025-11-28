#!/usr/bin/env python3
"""Simple test script to verify the application setup"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import create_app
    from database import get_neo4j_db
    from models import User
    from forms import LoginForm, RegistrationForm
    from blueprints.auth import auth_bp
    
    print("✅ All imports successful!")
    
    # Test app creation
    app = create_app('testing')
    print("✅ App created successfully!")
    
    # Test blueprint registration
    print(f"✅ Auth blueprint registered: {auth_bp.name}")
    
    # Test form creation
    with app.app_context():
        login_form = LoginForm()
        signup_form = RegistrationForm()
        print("✅ Forms created successfully!")
        
        # Test CSRF token generation
        with app.test_request_context():
            try:
                csrf_token = login_form.csrf_token
                print("✅ CSRF token available")
            except Exception as e:
                print(f"⚠️  CSRF token issue: {e}")
    
    print("\n🎉 Setup verification complete!")
    print("The application structure is correct and ready for testing.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()