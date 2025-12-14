#!/usr/bin/env python
from app import app
from database import Neo4jConnection

with app.app_context():
    conn = Neo4jConnection()
    session = conn.driver.session()
    try:
        # Count total jobs
        result = session.run('MATCH (j:Job) RETURN count(j) as total')
        record = result.single()
        total = record['total'] if record else 0
        print(f'Total jobs in database: {total}')

        # Check jobs with salary
        result2 = session.run('MATCH (j:Job) WHERE j.salary IS NOT NULL RETURN count(j) as total')
        record2 = result2.single()
        total_with_salary = record2['total'] if record2 else 0
        print(f'Jobs with salary info: {total_with_salary}')
        
        # Get sample jobs
        result3 = session.run('MATCH (j:Job) RETURN j.id, j.title, j.salary LIMIT 5')
        print('\nSample jobs:')
        for record in result3:
            print(f"  - {record['j.title']} (salary: {record['j.salary']})")
    finally:
        session.close()
