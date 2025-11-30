#!/usr/bin/env python3
from app import create_app
from database import get_neo4j_db, safe_run

app = create_app()

with app.app_context():
    db = get_neo4j_db()
    with db.session() as session:
        # Check the user ID
        result = safe_run(session, """
            MATCH (u:User {id: "aba99b14-2236-44a9-92ef-864446009e5e"})
            RETURN u.id as user_id, u.username as username
        """)
        print('User found:', result)
        
        # Check businesses owned by this user
        result = safe_run(session, """
            MATCH (u:User {id: "aba99b14-2236-44a9-92ef-864446009e5e"})-[:OWNS]->(b:Business)
            RETURN count(b) as business_count
        """)
        print('Businesses owned:', result)
        
        # Check jobs
        result = safe_run(session, """
            MATCH (u:User {id: "aba99b14-2236-44a9-92ef-864446009e5e"})-[:OWNS]->(b:Business)-[:POSTED_BY]->(j:Job)
            RETURN count(j) as job_count
        """)
        print('Jobs posted:', result)
        
        # Check how businesses are linked to jobs
        result = safe_run(session, """
            MATCH (b:Business)<-[:POSTED_BY]-(j:Job)
            RETURN b.id as business_id, count(j) as job_count
            LIMIT 5
        """)
        print('\nBusiness-Job relationships:', result)
        
        # Check all jobs and their business links
        result = safe_run(session, """
            MATCH (j:Job)
            OPTIONAL MATCH (b:Business)-[:POSTED_BY]->(j)
            RETURN j.id as job_id, j.title as title, b.id as business_id
            LIMIT 10
        """)
        print('\nAll jobs:', result)
