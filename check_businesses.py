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
    result = session.run('MATCH (b:Business) RETURN COUNT(b) as count')
    count = result.single()['count']
    print(f'Total businesses: {count}')
    
    result = session.run('''
        MATCH (b:Business) 
        RETURN b.name, b.latitude, b.longitude, b.created_at
        ORDER BY b.created_at DESC
        LIMIT 5
    ''')
    print('\nMost recent 5 businesses:')
    for record in result:
        print(f'  - {record["b.name"]} ({record["b.latitude"]}, {record["b.longitude"]})')
