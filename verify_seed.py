#!/usr/bin/env python
"""Verify that seed data was successfully created in Neo4j"""

from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()

def verify():
    driver = GraphDatabase.driver(
        os.getenv('NEO4J_URI', 'neo4j://localhost:7687'),
        auth=(os.getenv('NEO4J_USER', 'neo4j'), os.getenv('NEO4J_PASSWORD', 'password'))
    )

    session = driver.session()

    print("Verifying seed data...")
    print("=" * 60)

    # Test 1: Count all businesses
    count_query = 'MATCH (b:Business) RETURN count(b) as count'
    result = session.run(count_query).single()
    total_businesses = result['count']
    print(f"Total businesses in database: {total_businesses}")

    # Test 2: Count all jobs
    count_jobs = 'MATCH (j:Job) RETURN count(j) as count'
    result = session.run(count_jobs).single()
    total_jobs = result['count']
    print(f"Total jobs in database: {total_jobs}")

    # Test 3: Check owner exists
    owner_query = 'MATCH (u:User {id: "aba99b14-2236-44a9-92ef-864446009e5e"}) RETURN u.username, u.email'
    result = session.run(owner_query).single()
    if result:
        print(f"Owner found: {result['u.username']} ({result['u.email']})")
    else:
        print("Owner not found")

    # Test 4: Check relationships
    rel_query = 'MATCH (u:User {id: "aba99b14-2236-44a9-92ef-864446009e5e"})-[:OWNS]->(b:Business) RETURN count(b) as count'
    result = session.run(rel_query).single()
    owned_businesses = result['count']
    print(f"Businesses owned by user 70: {owned_businesses}")

    # Test 5: List some job postings
    print("\n" + "=" * 60)
    print("Sample Jobs Created:")
    print("=" * 60)
    job_list_query = '''
        MATCH (j:Job)-[:POSTED_BY]->(b:Business)
        RETURN j.title as title, b.name as business, j.salary_min as min, j.salary_max as max
        LIMIT 5
    '''
    results = session.run(job_list_query)
    for record in results:
        print(f"[+] {record['title']}")
        print(f"    Business: {record['business']}")
        print(f"    Salary: {record['min']:,} - {record['max']:,} PHP")

    session.close()
    driver.close()

    print("\n" + "=" * 60)
    if total_businesses == 10 and total_jobs == 10:
        print("[SUCCESS] All seed data created successfully!")
    else:
        print(f"[WARNING] Expected 10 businesses and 10 jobs, but found {total_businesses} and {total_jobs}")

if __name__ == '__main__':
    verify()
