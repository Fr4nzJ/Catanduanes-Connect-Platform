#!/usr/bin/env python3
"""
Check the verification status of all users
"""

import os
from dotenv import load_dotenv
from database import Neo4jConnection, safe_run

load_dotenv()

db = Neo4jConnection(
    uri=os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
    user=os.getenv('NEO4J_USER', 'neo4j'),
    password=os.getenv('NEO4J_PASSWORD', 'password')
)

with db.session() as session:
    result = safe_run(session, """
        MATCH (u:User)
        RETURN u.id, u.email, u.username, u.role, u.google_id, 
               u.verification_status, u.is_verified
        ORDER BY u.created_at DESC
    """)
    
    print("=" * 120)
    print(f"{'Email':<35} {'Username':<20} {'Role':<15} {'Verification Status':<20} {'Is Verified':<12} {'Google':<8}")
    print("=" * 120)
    
    for record in result:
        email = record['u.email'] or 'N/A'
        username = record['u.username'] or 'N/A'
        role = record['u.role'] or 'N/A'
        status = record['u.verification_status'] or 'None'
        is_verified = record['u.is_verified']
        has_google = '✓' if record['u.google_id'] else ''
        
        print(f"{email:<35} {username:<20} {role:<15} {status:<20} {str(is_verified):<12} {has_google:<8}")
    
    print("=" * 120)
