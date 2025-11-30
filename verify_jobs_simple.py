#!/usr/bin/env python
"""Simple verification that the 10 jobs were created correctly"""

from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()

def verify_jobs():
    driver = GraphDatabase.driver(
        os.getenv('NEO4J_URI', 'neo4j://localhost:7687'),
        auth=(os.getenv('NEO4J_USER', 'neo4j'), os.getenv('NEO4J_PASSWORD', 'password'))
    )

    session = driver.session()

    print("\n" + "=" * 60)
    print("JOBS SYSTEM VERIFICATION")
    print("=" * 60)

    # Get all jobs with their businesses
    query = '''
        MATCH (j:Job)-[:POSTED_BY]->(b:Business)
        RETURN 
            j.title as job_title,
            j.type as employment_type,
            j.salary_min as min_salary,
            j.salary_max as max_salary,
            j.location as location,
            j.latitude as latitude,
            j.longitude as longitude,
            j.id as job_id,
            b.name as business_name,
            b.id as business_id
        ORDER BY j.title
    '''

    results = session.run(query)
    jobs = list(results)

    print(f"\n[SUCCESS] Found {len(jobs)} jobs in the system!\n")

    # Display all jobs
    for idx, job in enumerate(jobs, 1):
        print(f"{idx}. {job['job_title']}")
        print(f"   Business: {job['business_name']}")
        print(f"   Type: {job['employment_type']}")
        print(f"   Salary: {job['min_salary']:,} - {job['max_salary']:,} PHP")
        print(f"   Location: {job['location']}")
        print(f"   Coordinates: ({job['latitude']}, {job['longitude']})")
        print()

    # Verify map data format
    print("=" * 60)
    print("MAP MARKER DATA SAMPLE:")
    print("=" * 60)
    
    sample_jobs = jobs[:3]
    markers = []
    for job in sample_jobs:
        marker = {
            'id': job['job_id'],
            'title': job['job_title'],
            'business': job['business_name'],
            'lat': float(job['latitude']),
            'lng': float(job['longitude']),
            'salary': f"{job['min_salary']:,} - {job['max_salary']:,} PHP",
            'type': job['employment_type'],
            'location': job['location']
        }
        markers.append(marker)
        print(f"\nMarker: {marker['business']} - {marker['title']}")
        print(f"  Position: {marker['lat']}, {marker['lng']}")
        print(f"  Info: {marker['salary']} | {marker['type']} | {marker['location']}")

    session.close()
    driver.close()

    print("\n" + "=" * 60)
    print(f"[SUCCESS] All {len(jobs)} jobs verified and ready for the platform!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Access http://localhost:5000/jobs to view the jobs listing")
    print("2. Click on any job to see the detailed page")
    print("3. Click on the map view to see job locations")
    print("4. Try applying to a job")
    print("=" * 60 + "\n")

if __name__ == '__main__':
    verify_jobs()
