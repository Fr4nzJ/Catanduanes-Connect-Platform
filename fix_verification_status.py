#!/usr/bin/env python3
"""
Fix existing Google-registered users who don't have verification_status set
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
    # Find all Google users who don't have verification_status set
    print("Finding Google users without verification_status...")
    
    result = safe_run(session, """
        MATCH (u:User)
        WHERE u.google_id IS NOT NULL
        AND (u.verification_status IS NULL OR u.verification_status = '')
        RETURN u.id, u.email, u.is_verified
        LIMIT 100
    """)
    
    if result:
        print(f"Found {len(result)} Google users to fix")
        
        for record in result:
            user_id = record['u.id']
            email = record['u.email']
            is_verified = record['u.is_verified']
            
            # Set verification_status based on is_verified
            # If they were marked as verified, set to 'approved'
            # Otherwise set to 'pending'
            new_status = 'approved' if is_verified else 'pending'
            
            safe_run(session, """
                MATCH (u:User {id: $user_id})
                SET u.verification_status = $status
            """, {
                'user_id': user_id,
                'status': new_status
            })
            
            print(f"  ✓ {email}: verification_status set to '{new_status}'")
        
        print(f"\n✅ Fixed {len(result)} users")
    else:
        print("✅ All Google users have verification_status set")
    
    # Also fix the is_verified field - should be true only if approved
    print("\nFixing is_verified field...")
    safe_run(session, """
        MATCH (u:User)
        WHERE u.verification_status = 'approved'
        SET u.is_verified = true
    """)
    
    safe_run(session, """
        MATCH (u:User)
        WHERE u.verification_status IN ['pending', 'rejected']
        SET u.is_verified = false
    """)
    
    print("✅ is_verified field synced with verification_status")
