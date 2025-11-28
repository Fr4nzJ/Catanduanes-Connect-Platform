import os
from dotenv import load_dotenv
from database import Neo4jConnection

load_dotenv()

db = Neo4jConnection(
    uri=os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
    user=os.getenv('NEO4J_USER', 'neo4j'),
    password=os.getenv('NEO4J_PASSWORD', 'password')
)

with db.session() as session:
    result = session.run('''
        MATCH (b:Business) 
        RETURN COUNT(b) as total_count
    ''')
    print("=" * 60)
    print(f"TOTAL BUSINESSES: {result.single()['total_count']}")
    print("=" * 60)
    
    result = session.run('''
        MATCH (b:Business) 
        WHERE b.created_at < '2025-11-29'
        RETURN COUNT(b) as old_count
    ''')
    old = result.single()['old_count']
    print(f"\nOld businesses (before today): {old}")
    
    result = session.run('''
        MATCH (b:Business) 
        WHERE b.created_at >= '2025-11-29'
        RETURN COUNT(b) as new_count
    ''')
    new = result.single()['new_count']
    print(f"New businesses (today): {new}")
    
    print("\nAll businesses:")
    result = session.run('''
        MATCH (b:Business) 
        RETURN b.name, b.created_at
        ORDER BY b.created_at ASC
    ''')
    for record in result:
        print(f"  - {record['b.name']} ({record['b.created_at']})")
