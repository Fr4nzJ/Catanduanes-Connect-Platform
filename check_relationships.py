#!/usr/bin/env python3
from app import create_app
from database import get_neo4j_db, safe_run

app = create_app()
with app.app_context():
    db = get_neo4j_db()
    with db.session() as session:
        # Check distinct businesses
        result = safe_run(session, '''
            MATCH (u:User {id: "aba99b14-2236-44a9-92ef-864446009e5e"})-[:OWNS]->(b:Business)
            RETURN DISTINCT b.id, b.name
            ORDER BY b.name
        ''')
        print(f'Distinct businesses owned: {len(result) if result else 0}')
        for rec in (result or []):
            print(f'  - {rec["b.name"]}')
        
        # Check jobs linked to any business
        result = safe_run(session, '''
            MATCH (b:Business)-[:POSTED_BY]->(j:Job)
            RETURN COUNT(DISTINCT j) as job_count
        ''')
        print(f'\nJobs with POSTED_BY relationships: {result[0]["job_count"] if result else 0}')
        
        # Check jobs linked through user
        result = safe_run(session, '''
            MATCH (u:User {id: "aba99b14-2236-44a9-92ef-864446009e5e"})-[:OWNS]->(b:Business)-[:POSTED_BY]->(j:Job)
            RETURN COUNT(j) as job_count
        ''')
        print(f'Jobs for user through OWNS->POSTED_BY: {result[0]["job_count"] if result else 0}')
        
        # Check any old J POSTED_BY B relationships
        result = safe_run(session, '''
            MATCH (j:Job)-[r:POSTED_BY]->(b:Business)
            RETURN COUNT(r) as rel_count
        ''')
        print(f'\nOld relationships (J)-[:POSTED_BY]->(B): {result[0]["rel_count"] if result else 0}')
