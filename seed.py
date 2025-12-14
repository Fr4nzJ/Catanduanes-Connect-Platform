#!/usr/bin/env python3
"""
Comprehensive Seed Script for Catanduanes Connect Platform
Creates 30 businesses with 30 jobs each for user 'ren'
Run with: python seed.py
"""

import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
import random
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load environment variables
load_dotenv()

# User details (ren - verified business owner)
OWNER_ID = "6d994a64-141a-462b-a880-03e0228b3ba7"
OWNER_EMAIL = "akagamiren9@gmail.com"
OWNER_USERNAME = "ren"

# Catanduanes businesses data
BUSINESS_NAMES = [
    "Virac Seafood Trading", "Pandan Island Fishing Co.", "Catanduanes Coconut Products",
    "Baras Agricultural Supply", "Viga Marine Resources", "Island Spice Exports",
    "Catanduanes Tourism Services", "Pandan Furniture Workshop", "Virac Hardware Store",
    "Caramoran Beach Resort", "Island Textile Industries", "Catanduanes Coffee Roastery",
    "Marine Tech Solutions", "Virac Food Processing", "Agricultural Equipment Rental",
    "Island Transport Services", "Pandan Craft Gallery", "Catanduanes Aquaculture",
    "Virac Printing Services", "Island Construction Materials", "Catanduanes Travel Agency",
    "Baras Organic Farm", "Pandan Hospitality Services", "Virac Logistics Hub",
    "Island Manufacturing Co.", "Catanduanes Retail Network", "Pandan Services Group",
    "Virac Trading Post", "Island Entertainment Center", "Catanduanes Tech Services",
    "Baras Import-Export Services"
]

CATEGORIES = [
    "seafood", "agriculture", "tourism", "manufacturing", "retail",
    "services", "logistics", "hospitality", "technology", "construction"
]

JOB_TITLES = [
    "Sales Representative", "Warehouse Manager", "Customer Service Officer",
    "Operations Supervisor", "Logistics Coordinator", "Quality Inspector",
    "Production Technician", "Administrative Assistant", "Delivery Driver",
    "Store Manager", "Junior Engineer", "Maintenance Technician",
    "Business Analyst", "Data Entry Specialist", "Inventory Manager",
    "Marketing Coordinator", "HR Officer", "Finance Clerk",
    "Event Coordinator", "Project Manager", "Account Executive",
    "Technical Support", "Safety Officer", "Supply Chain Officer",
    "Procurement Specialist", "Team Lead", "Assistant Manager",
    "Branch Manager", "Regional Manager", "Operations Manager"
]

LOCATIONS = [
    "Virac", "Baras", "Pandan", "Caramoran", "San Andres",
    "Gigante", "Viga", "Panganiban", "Sagapo", "Bula"
]

SKILLS = [
    "communication", "teamwork", "problem-solving", "time-management",
    "customer-service", "sales", "data-entry", "microsoft-office",
    "warehouse-management", "inventory", "driving", "physical-fitness",
    "attention-to-detail", "multitasking", "leadership", "negotiation",
    "report-writing", "phone-etiquette", "cash-handling", "stock-management"
]

def generate_businesses(owner_id):
    """Generate 30 businesses with complete credentials"""
    businesses = []
    
    for i, name in enumerate(BUSINESS_NAMES):
        business_id = str(uuid.uuid4())
        business = {
            "id": business_id,
            "name": name,
            "category": random.choice(CATEGORIES),
            "description": f"{name} is a leading business in Catanduanes, providing quality products and services since 2015. We specialize in delivering excellent service to our clients.",
            "address": f"{random.choice(LOCATIONS)}, Catanduanes, Philippines",
            "phone": f"+63{random.randint(900000000, 999999999)}",
            "email": f"contact@{name.lower().replace(' ', '')}.ph",
            "website": f"www.{name.lower().replace(' ', '')}.ph",
            "owner_id": owner_id,
            "is_active": True,
            "is_verified": True,
            "verification_status": "verified",
            "employee_count": random.randint(5, 100),
            "established_year": random.randint(2010, 2020),
            "rating": round(random.uniform(3.5, 5.0), 1),
            "reviews_count": random.randint(10, 500),
            "latitude": round(random.uniform(13.5, 14.0), 4),
            "longitude": round(random.uniform(123.5, 124.5), 4),
            "created_at": (datetime.now(timezone.utc) - timedelta(days=random.randint(1, 365))).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "business_hours": "8:00 AM - 5:00 PM",
            "permit_number": f"PERMIT-{i+1:03d}-2024",
            "is_hiring": True
        }
        businesses.append(business)
    
    return businesses

def generate_jobs(business_id, business_name):
    """Generate 30 jobs for a business"""
    jobs = []
    
    for i in range(30):
        job_id = str(uuid.uuid4())
        job_title = JOB_TITLES[i % len(JOB_TITLES)]
        
        # Salary range based on job type
        base_salary = random.randint(15000, 35000)
        
        job = {
            "id": job_id,
            "title": f"{job_title} - {business_name}",
            "description": f"We are hiring a {job_title} for {business_name}. You will be responsible for various tasks including customer service, operations, and business development. This is an excellent opportunity to grow your career with a reputable company in Catanduanes.",
            "business_id": business_id,
            "business_name": business_name,
            "category": random.choice(CATEGORIES),
            "location": random.choice(LOCATIONS) + ", Catanduanes",
            "employment_type": random.choice(["Full-time", "Part-time", "Contract", "Temporary"]),
            "salary_min": base_salary,
            "salary_max": base_salary + random.randint(5000, 15000),
            "salary_currency": "PHP",
            "required_skills": random.sample(SKILLS, random.randint(3, 7)),
            "experience_required": f"{random.randint(0, 5)} years",
            "education_level": random.choice(["High School", "Associate", "Bachelor", "Master"]),
            "posted_date": (datetime.now(timezone.utc) - timedelta(days=random.randint(1, 60))).isoformat(),
            "deadline": (datetime.now(timezone.utc) + timedelta(days=random.randint(10, 60))).isoformat(),
            "applications_count": random.randint(0, 50),
            "views_count": random.randint(50, 500),
            "is_active": random.choice([True, True, True, False]),  # 75% active
            "is_filled": random.choice([False, False, False, False, False, True]),  # 17% filled
            "status": "open" if random.random() > 0.17 else "filled",
            "created_at": (datetime.now(timezone.utc) - timedelta(days=random.randint(1, 60))).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "benefits": [
                "Health Insurance",
                "13th Month Pay",
                "Performance Bonus",
                "Paid Leave",
                "Training & Development"
            ],
            "job_description": f"Position: {job_title}\n\nResponsibilities:\n- Perform core duties related to {job_title.lower()}\n- Collaborate with team members\n- Maintain quality standards\n- Report to management\n- Contribute to team goals\n\nRequirements:\n- {random.randint(0, 5)} years of experience\n- Excellent communication skills\n- Problem-solving ability\n- Team player mentality\n- Willingness to learn\n\nLocation: {random.choice(LOCATIONS)}, Catanduanes"
        }
        jobs.append(job)
    
    return jobs

def safe_run(session, query, params=None):
    """Execute a Cypher query safely"""
    try:
        result = session.run(query, params or {})
        return result.data()
    except Exception as e:
        print(f"Error executing query: {e}")
        return None

def seed_database():
    """Main seed function"""
    print("="*70)
    print("CATANDUANES CONNECT PLATFORM - DATABASE SEEDING")
    print("="*70)
    print(f"\nOwner: {OWNER_USERNAME}")
    print(f"Email: {OWNER_EMAIL}")
    print(f"ID: {OWNER_ID}\n")
    
    # Create direct Neo4j connection
    uri = os.getenv('NEO4J_URI', 'neo4j+s://37bf8852.databases.neo4j.io')
    username = os.getenv('NEO4J_USERNAME', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD', '')
    
    driver = GraphDatabase.driver(uri, auth=(username, password))
    
    try:
        with driver.session() as session:
            
            # Generate businesses
            print("Generating 30 businesses with complete credentials...")
            businesses = generate_businesses(OWNER_ID)
            
            total_jobs = 0
            total_created_businesses = 0
            total_created_jobs = 0
            
            # Create businesses and jobs
            for i, business in enumerate(businesses, 1):
                try:
                    # Create business node
                    create_business_query = """
                        CREATE (b:Business {
                            id: $id,
                            name: $name,
                            category: $category,
                            description: $description,
                            address: $address,
                            phone: $phone,
                            email: $email,
                            website: $website,
                            owner_id: $owner_id,
                            is_active: $is_active,
                            is_verified: $is_verified,
                            verification_status: $verification_status,
                            employee_count: $employee_count,
                            established_year: $established_year,
                            rating: $rating,
                            reviews_count: $reviews_count,
                            latitude: $latitude,
                            longitude: $longitude,
                            created_at: $created_at,
                            updated_at: $updated_at,
                            business_hours: $business_hours,
                            permit_number: $permit_number,
                            is_hiring: $is_hiring
                        })
                        RETURN b.id as id
                    """
                    
                    result = safe_run(session, create_business_query, business)
                    if result:
                        total_created_businesses += 1
                    
                    # Create relationship to owner
                    owner_rel_query = """
                        MATCH (b:Business {id: $business_id})
                        MATCH (u:User {id: $owner_id})
                        CREATE (u)-[:OWNS]->(b)
                    """
                    safe_run(session, owner_rel_query, {
                        "business_id": business["id"],
                        "owner_id": OWNER_ID
                    })
                    
                    # Generate and create jobs for this business
                    print(f"  OK Business {i}/30: {business['name']}")
                    print(f"     Creating 30 jobs for this business...")
                    
                    jobs = generate_jobs(business["id"], business["name"])
                    
                    created_jobs = 0
                    for job in jobs:
                        create_job_query = """
                            CREATE (j:Job {
                                id: $id,
                                title: $title,
                                description: $description,
                                business_id: $business_id,
                                business_name: $business_name,
                                category: $category,
                                location: $location,
                                employment_type: $employment_type,
                                salary_min: $salary_min,
                                salary_max: $salary_max,
                                salary_currency: $salary_currency,
                                required_skills: $required_skills,
                                experience_required: $experience_required,
                                education_level: $education_level,
                                posted_date: $posted_date,
                                deadline: $deadline,
                                applications_count: $applications_count,
                                views_count: $views_count,
                                is_active: $is_active,
                                is_filled: $is_filled,
                                status: $status,
                                created_at: $created_at,
                                updated_at: $updated_at,
                                benefits: $benefits,
                                job_description: $job_description
                            })
                            RETURN j.id as id
                        """
                        
                        job_result = safe_run(session, create_job_query, job)
                        if job_result:
                            created_jobs += 1
                        
                        # Create relationship from business to job
                        job_rel_query = """
                            MATCH (b:Business {id: $business_id})
                            MATCH (j:Job {id: $job_id})
                            CREATE (b)-[:POSTS]->(j)
                        """
                        safe_run(session, job_rel_query, {
                            "business_id": business["id"],
                            "job_id": job["id"]
                        })
                    
                    total_created_jobs += created_jobs
                    print(f"     {created_jobs} jobs created successfully\n")
                    
                except Exception as e:
                    print(f"  ERROR processing business {i}: {e}\n")
                    continue
            
            # Print summary
            print("\n" + "="*70)
            print("SUCCESS: SEEDING COMPLETED!")
            print("="*70)
            print(f"\nDatabase Statistics:")
            print(f"   - Businesses Created: {total_created_businesses}/30")
            print(f"   - Total Jobs Created: {total_created_jobs}")
            print(f"   - Average Jobs per Business: {total_created_jobs // max(total_created_businesses, 1)}")
            print(f"   - Owner: {OWNER_USERNAME} ({OWNER_EMAIL})")
            print(f"   - Owner ID: {OWNER_ID}")
            print("\n" + "="*70)
            print("\nYour database is now populated with realistic Catanduanes business data!")
            print("You can now test the application with real businesses and job listings.")
            print("All businesses and jobs are linked to user 'ren'.\n")
            
    except Exception as e:
        print(f"\nERROR during seeding: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        driver.close()

if __name__ == "__main__":
    seed_database()
