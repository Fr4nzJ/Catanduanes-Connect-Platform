#!/usr/bin/env python3
"""Complete cleanup of all seed data"""
from app import create_app
from database import get_neo4j_db, safe_run

app = create_app()

with app.app_context():
    db = get_neo4j_db()
    with db.session() as session:
        print("Performing complete cleanup...")
        
        # Delete all relationships and nodes
        result = safe_run(session, """
            MATCH (n)
            WHERE labels(n) IN [['Job'], ['Business'], ['JobApplication']]
            DETACH DELETE n
            RETURN count(n) as deleted
        """)
        print(f"Deleted nodes: {result[0]['deleted'] if result else 0}")
        
        print("\nCleanup complete. Ready for fresh seeding.")
