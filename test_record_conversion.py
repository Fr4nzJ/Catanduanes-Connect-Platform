#!/usr/bin/env python
"""Test record conversion to understand the issue"""
import sys
from app import app
from database import get_neo4j_db, safe_run, _record_to_dict, _node_to_dict

with app.app_context():
    db = get_neo4j_db()
    
    with db.session() as session:
        # Test a simple query
        result = safe_run(session, "MATCH (u:User) RETURN u LIMIT 1")
        
        print("=" * 80)
        print("Result type:", type(result))
        print("Result:", result)
        print()
        
        if result:
            record = result[0]
            print("Record type:", type(record))
            print("Record:", record)
            print("Record keys:", record.keys() if hasattr(record, 'keys') else 'No keys method')
            print()
            
            if 'u' in record:
                user = record['u']
                print("User type:", type(user))
                print("User:", user)
                print("User is dict:", isinstance(user, dict))
                if isinstance(user, dict):
                    print("User keys:", user.keys())
                    print("Has username:", 'username' in user)
                    if 'username' in user:
                        print("Username value:", user['username'])
