#!/usr/bin/env python
"""
Quick test script to run Flask app with minimal setup
"""
import os
os.environ['FLASK_ENV'] = 'development'
os.environ['GEMINI_API_KEY'] = 'test-key-skip'  # Will still fail validation but chatbot will be None

import sys
sys.path.insert(0, '.')

# Suppress warnings
import warnings
warnings.filterwarnings('ignore')

# Redirect Gemini initialization errors
import logging
logging.getLogger('gemini_client').setLevel(logging.CRITICAL)
logging.getLogger('chatbot_core').setLevel(logging.CRITICAL)

# Now create and run app
from app import create_app

if __name__ == '__main__':
    try:
        app = create_app()
        print("[OK] Flask app created successfully")
        print("[OK] Starting development server on http://localhost:5000")
        print("[OK] Admin dashboard available at http://localhost:5000/admin/")
        app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)
    except Exception as e:
        print(f"Error starting app: {e}")
        import traceback
        traceback.print_exc()
