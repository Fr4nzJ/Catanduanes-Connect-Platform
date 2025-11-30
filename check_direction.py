#!/usr/bin/env python3
from app import create_app
from database import get_neo4j_db, safe_run

app = create_app()
with app.app_context():
    db = get_neo4j_db()
    with db.session() as session:
        # Check the actual direction in the data
        result = safe_run(session, '''
            MATCH (j:Job)-[:POSTED_BY]->(b:Business)
            RETURN COUNT(j) as count1
        ''')
        print(f'Jobs with (J)-[:POSTED_BY]->(B): {result[0]["count1"] if result else 0}')
        
        result = safe_run(session, '''
            MATCH (b:Business)-[:POSTED_BY]->(j:Job)
            RETURN COUNT(j) as count2
        ''')
        print(f'Jobs with (B)-[:POSTED_BY]->(J): {result[0]["count2"] if result else 0}')
