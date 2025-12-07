#!/usr/bin/env python
"""Direct Flask app test"""
import sys
import traceback

try:
    print("Importing app...", file=sys.stderr)
    from app import app
    print("App imported successfully", file=sys.stderr)
    
    print("Creating test client...", file=sys.stderr)
    client = app.test_client()
    
    print("Testing /admin/users-management...", file=sys.stderr)
    response = client.get('/admin/users-management', follow_redirects=True)
    print(f"Response status: {response.status_code}", file=sys.stderr)
    
    if response.status_code != 200:
        print(f"Response data (first 500 chars):\n{response.get_data(as_text=True)[:500]}", file=sys.stderr)
    else:
        print("SUCCESS - Page loaded!", file=sys.stderr)
        
except Exception as e:
    print(f"Error: {str(e)}", file=sys.stderr)
    traceback.print_exc()
    sys.exit(1)
