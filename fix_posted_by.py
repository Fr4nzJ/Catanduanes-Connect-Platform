#!/usr/bin/env python3
"""Fix the POSTED_BY relationship direction for all jobs"""
from app import create_app
from database import get_neo4j_db, safe_run

app = create_app()

with app.app_context():
    db = get_neo4j_db()
    with db.session() as session:
        print("Fixing POSTED_BY relationships...")
        
        # First, delete all incorrectly oriented relationships
        print("Removing incorrect relationships (Job)-[:POSTED_BY]->(Business)...")
        result = safe_run(session, """
            MATCH (j:Job)-[r:POSTED_BY]->(b:Business)
            DELETE r
            RETURN count(r) as deleted
        """)
        print(f"Deleted {result[0]['deleted'] if result else 0} incorrect relationships")
        
        # Now create the correct relationships
        print("Creating correct relationships (Business)-[:POSTED_BY]->(Job)...")
        result = safe_run(session, """
            MATCH (b:Business)
            MATCH (j:Job {location: b.address})
            MERGE (b)-[:POSTED_BY]->(j)
            RETURN count(*) as created
        """)
        print(f"Created relationships")
        
        # Verify the fix
        print("\nVerifying fix...")
        result = safe_run(session, """
            MATCH (u:User {id: "aba99b14-2236-44a9-92ef-864446009e5e"})-[:OWNS]->(b:Business)-[:POSTED_BY]->(j:Job)
            RETURN count(j) as job_count
        """)
        print(f"Jobs now visible: {result[0]['job_count'] if result else 0}")
        
        # Show some details
        result = safe_run(session, """
            MATCH (b:Business)-[:POSTED_BY]->(j:Job)
            RETURN b.name as business, j.title as job_title, j.id as job_id
            LIMIT 5
        """)
        print("\nSample linked jobs:")
        for record in result:
            print(f"  - {record['business']}: {record['job_title']}")
