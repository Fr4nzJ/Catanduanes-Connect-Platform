#!/usr/bin/env python
"""Test app module directly"""
import sys
import traceback

try:
    print("Attempting to import app module...")
    import app as app_module
    print("App module imported")
    print("Dir of app module:", [x for x in dir(app_module) if not x.startswith('_')][:20])
    
    # Try to get the Flask app
    if hasattr(app_module, 'app'):
        print("Found 'app' in module")
        flask_app = app_module.app
        print(f"Flask app type: {type(flask_app)}")
    else:
        print("'app' not found in module. Available: ", [x for x in dir(app_module) if not x.startswith('_')])
        
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
