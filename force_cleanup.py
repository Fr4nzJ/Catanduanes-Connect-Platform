#!/usr/bin/env python3
"""Force delete all jobs and businesses"""
from app import create_app
from database import get_neo4j_db, safe_run

app = create_app()

with app.app_context():
    db = get_neo4j_db()
    with db.session() as session:
        # Delete all jobs and relationships
        result = safe_run(session, "MATCH (n:Job) DETACH DELETE n RETURN count(n) as count")
        print(f"Deleted jobs: {result[0]['count'] if result else 0}")
        
        # Delete all businesses
        result = safe_run(session, "MATCH (n:Business) DETACH DELETE n RETURN count(n) as count")
        print(f"Deleted businesses: {result[0]['count'] if result else 0}")
        
        # Delete all job applications
        result = safe_run(session, "MATCH (n:JobApplication) DETACH DELETE n RETURN count(n) as count")
        print(f"Deleted job applications: {result[0]['count'] if result else 0}")
        
        print("\nCleanup complete!")
