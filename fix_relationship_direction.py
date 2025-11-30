#!/usr/bin/env python3
"""Fix the relationship direction from (B)-[:POSTED_BY]->(J) to (J)-[:POSTED_BY]->(B)"""
from app import create_app
from database import get_neo4j_db, safe_run

app = create_app()
with app.app_context():
    db = get_neo4j_db()
    with db.session() as session:
        print("Converting relationship direction...")
        
        # Delete all current POSTED_BY relationships
        result = safe_run(session, '''
            MATCH ()-[r:POSTED_BY]->()
            DELETE r
            RETURN COUNT(r) as deleted
        ''')
        print(f"Deleted old relationships: {result[0]['deleted'] if result else 0}")
        
        # Create new relationships in the correct direction
        result = safe_run(session, '''
            MATCH (b:Business), (j:Job)
            WHERE j.location = b.address
            MERGE (j)-[:POSTED_BY]->(b)
            RETURN COUNT(*) as created
        ''')
        print(f"Created relationships")
        
        # Verify
        result = safe_run(session, '''
            MATCH (j:Job)-[:POSTED_BY]->(b:Business)
            RETURN COUNT(j) as count
        ''')
        print(f"\nVerification - Jobs with (J)-[:POSTED_BY]->(B): {result[0]['count'] if result else 0}")
