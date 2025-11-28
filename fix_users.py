import os
import uuid
from neo4j import GraphDatabase, basic_auth

# Neo4j connection settings
NEO4J_URI = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.environ.get('NEO4J_USERNAME', os.environ.get('NEO4J_USER', 'neo4j'))
NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD', 'password')
NEO4J_DATABASE = os.environ.get('NEO4J_DATABASE', 'neo4j')

print(f"Connecting to Neo4j at {NEO4J_URI} as {NEO4J_USER}")

try:
    driver = GraphDatabase.driver(NEO4J_URI, auth=basic_auth(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session(database=NEO4J_DATABASE) as session:
        # Check users missing required fields
        result = session.run("""
            MATCH (u:User)
            WHERE u.id IS NULL 
               OR u.username IS NULL 
               OR u.role IS NULL 
               OR u.is_verified IS NULL 
               OR u.is_active IS NULL
            RETURN u
        """)
        
        incomplete_users = list(result)
        if incomplete_users:
            print(f"\nFound {len(incomplete_users)} users with missing required fields:")
            for record in incomplete_users:
                user = record['u']
                print(f"Email: {user.get('email')}")
                print(f"  Missing fields: " + 
                    ", ".join(f for f in ['id', 'username', 'role', 'is_verified', 'is_active'] 
                             if user.get(f) is None))
                
                # Generate missing fields
                updates = {
                    'id': user.get('id') or str(uuid.uuid4()),
                    'username': user.get('username') or user['email'].split('@')[0],
                    'role': user.get('role') or 'job_seeker',
                    'is_verified': user.get('is_verified', True),  # Assume verified for existing
                    'is_active': user.get('is_active', True)      # Assume active for existing
                }
                
                # Update the user
                session.run("""
                    MATCH (u:User {email: $email})
                    SET u += $updates
                    RETURN u
                """, {'email': user['email'], 'updates': updates})
                
                print("  Updated with:", updates)
                print()
        else:
            print("\nAll users have required fields.")
            
        # List all users after updates
        print("\nCurrent users:")
        result = session.run("""
            MATCH (u:User)
            RETURN u.id, u.email, u.username, u.role, u.is_verified, u.is_active
            ORDER BY u.email
        """)
        
        for record in result:
            print(
                f"Email: {record['u.email']}\n"
                f"  id={record['u.id']}\n"
                f"  username={record['u.username']}\n"
                f"  role={record['u.role']}\n"
                f"  verified={record['u.is_verified']}\n"
                f"  active={record['u.is_active']}\n"
            )
            
    driver.close()
except Exception as e:
    print(f"Error: {e}")