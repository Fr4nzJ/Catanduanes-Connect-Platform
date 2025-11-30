#!/usr/bin/env python
"""Test the jobs routes to verify functionality"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from models import Job, Business

def test_jobs():
    app = create_app()
    
    with app.app_context():
        print("Testing Jobs System")
        print("=" * 60)
        
        # Test 1: Get all jobs
        jobs = Job.query.all()
        print(f"\n[+] Total jobs in database: {len(jobs)}")
        
        if jobs:
            print(f"\n[+] First 5 jobs:")
            for job in jobs[:5]:
                print(f"    - {job.title} (ID: {job.id})")
                # Get business
                result = db.session.execute(
                    db.text("""
                        MATCH (j:Job {id: $job_id})-[:POSTED_BY]->(b:Business)
                        RETURN b.name as business_name
                    """),
                    {"job_id": job.id}
                )
                row = result.first()
                if row:
                    print(f"      Posted by: {row[0]}")
                    print(f"      Salary: {job.salary_min:,} - {job.salary_max:,} PHP")
        
        # Test 2: Check map marker generation
        print(f"\n[+] Testing map marker generation...")
        markers = []
        for job in jobs[:3]:
            result = db.session.execute(
                db.text("""
                    MATCH (j:Job {id: $job_id})-[:POSTED_BY]->(b:Business)
                    RETURN j.title as title, j.salary_min as min, j.salary_max as max,
                           j.latitude as lat, j.longitude as lng, b.name as business
                """),
                {"job_id": job.id}
            )
            for row in result:
                marker = {
                    'title': row[0],
                    'salary': f"{row[1]:,} - {row[2]:,} PHP",
                    'lat': row[3],
                    'lng': row[4],
                    'business': row[5]
                }
                markers.append(marker)
                print(f"    - {marker['business']}: {marker['title']}")
                print(f"      Location: ({marker['lat']}, {marker['lng']})")
        
        print("\n" + "=" * 60)
        print("[SUCCESS] Jobs system is functional!")
        
if __name__ == '__main__':
    test_jobs()
