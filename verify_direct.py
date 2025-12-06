#!/usr/bin/env python
"""Direct Neo4j verification script"""

from neo4j import GraphDatabase
import os

# Connect directly to Neo4j
uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
user = os.getenv("NEO4J_USERNAME", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "00000000")

driver = GraphDatabase.driver(uri, auth=(user, password))

def verify_user(session):
    result = session.run('''
        MATCH (u:User {id: $user_id})
        SET u.is_verified = true,
            u.verification_status = 'approved',
            u.verified_at = datetime()
        RETURN u.username, u.email, u.is_verified, u.verification_status
    ''', user_id='aba99b14-2236-44a9-92ef-864446009e5e')
    
    record = result.single()
    if record:
        print('✅ User verification completed:')
        print(f'   Username: {record["u.username"]}')
        print(f'   Email: {record["u.email"]}')
        print(f'   Verified: {record["u.is_verified"]}')
        print(f'   Status: {record["u.verification_status"]}')
    else:
        print('❌ User not found')

try:
    with driver.session() as session:
        verify_user(session)
except Exception as e:
    print(f'Error: {e}')
finally:
    driver.close()
