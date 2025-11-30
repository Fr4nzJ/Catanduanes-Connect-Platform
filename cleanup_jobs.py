#!/usr/bin/env python3
"""Clean up and recreate jobs with correct relationships"""
from app import create_app
from database import get_neo4j_db, safe_run

app = create_app()

with app.app_context():
    db = get_neo4j_db()
    with db.session() as session:
        print("Cleaning up duplicate/incorrect jobs...")
        
        # Delete all jobs
        result = safe_run(session, """
            MATCH (j:Job)
            DETACH DELETE j
            RETURN count(j) as deleted
        """)
        print(f"Deleted jobs")
        
        # Delete all POSTED_BY relationships
        result = safe_run(session, """
            MATCH ()-[r:POSTED_BY]->()
            DELETE r
            RETURN count(r) as deleted
        """)
        print(f"Deleted POSTED_BY relationships")
        
        print("\nDatabase cleaned. Ready to re-seed with corrected script.")
