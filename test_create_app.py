#!/usr/bin/env python
"""Test create_app function"""
import traceback

try:
    print("Importing create_app...")
    from app import create_app
    print("create_app imported successfully")
    
    print("Calling create_app()...")
    test_app = create_app('development')
    print(f"App created: {type(test_app)}")
    
    print("SUCCESS!")
    
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
