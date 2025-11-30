"""
Seed script to create 10 businesses and 10 jobs for the Catanduanes Connect Platform
Business Owner: ren (ID: 70, UUID: aba99b14-2236-44a9-92ef-864446009e5e)
"""

import os
import sys
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Fix Unicode encoding for Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

load_dotenv()

# Neo4j connection details
NEO4J_URI = os.getenv('NEO4J_URI', 'neo4j://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'password')
NEO4J_DATABASE = os.getenv('NEO4J_DATABASE', 'neo4j')

# Business owner details
OWNER_ID = 'aba99b14-2236-44a9-92ef-864446009e5e'  # Use UUID instead of integer
OWNER_UUID = 'aba99b14-2236-44a9-92ef-864446009e5e'
OWNER_EMAIL = 'akagamiren9@gmail.com'

# Sample business data
BUSINESSES_DATA = [
    {
        'name': 'Catanduanes Fresh Seafood Exports',
        'category': 'Seafood & Fishing',
        'description': 'Premium seafood distribution and export services from Catanduanes',
        'address': 'Bauan, Catanduanes',
        'latitude': 13.8516,
        'longitude': 124.2158,
        'phone': '09171234567',
        'email': 'seafood@catanduanes.com',
        'website': 'https://catanduaneseafood.com',
    },
    {
        'name': 'Virac Coconut Processing Plant',
        'category': 'Agriculture & Processing',
        'description': 'Coconut oil, copra, and coconut-based products manufacturing',
        'address': 'Virac, Catanduanes',
        'latitude': 13.5914,
        'longitude': 124.2403,
        'phone': '09175234568',
        'email': 'coconut@virac.com',
        'website': 'https://viracoil.com',
    },
    {
        'name': 'Pandan Island Dive Resort & Tours',
        'category': 'Tourism & Hospitality',
        'description': 'Premier diving and island tourism experiences',
        'address': 'Pandan Island, Catanduanes',
        'latitude': 13.7211,
        'longitude': 124.4512,
        'phone': '09179234569',
        'email': 'bookings@pandandive.com',
        'website': 'https://pandandiveresort.com',
    },
    {
        'name': 'Catanduanes Textile Weavers Cooperative',
        'category': 'Handicrafts & Arts',
        'description': 'Traditional Filipino weaving and textile products',
        'address': 'San Andres, Catanduanes',
        'latitude': 13.6213,
        'longitude': 124.1891,
        'phone': '09182234560',
        'email': 'weaving@catweave.com',
        'website': 'https://catweave.com',
    },
    {
        'name': 'Caramoan Tech Solutions',
        'category': 'Information Technology',
        'description': 'Web development, mobile apps, and IT consulting services',
        'address': 'Caramoan, Catanduanes',
        'latitude': 13.9421,
        'longitude': 124.0945,
        'phone': '09185234561',
        'email': 'info@caramoantech.com',
        'website': 'https://caramoantech.com',
    },
    {
        'name': 'Purefoods Catanduanes Farm & Dairy',
        'category': 'Agriculture & Livestock',
        'description': 'Organic dairy products and livestock farming',
        'address': 'Bagamanoc, Catanduanes',
        'latitude': 13.8123,
        'longitude': 124.3045,
        'phone': '09188234562',
        'email': 'farm@purfoods.com',
        'website': 'https://purefarmsdairy.com',
    },
    {
        'name': 'Islet Beauty & Wellness Spa',
        'category': 'Health & Wellness',
        'description': 'Spa, massage therapy, and wellness services using local ingredients',
        'address': 'Viga, Catanduanes',
        'latitude': 13.5645,
        'longitude': 124.2891,
        'phone': '09191234563',
        'email': 'wellness@isletbeauty.com',
        'website': 'https://isletbeautywellness.com',
    },
    {
        'name': 'Catanduanes Construction & Development',
        'category': 'Construction & Real Estate',
        'description': 'General construction, real estate development, and renovation services',
        'address': 'Virac, Catanduanes',
        'latitude': 13.5934,
        'longitude': 124.2423,
        'phone': '09194234564',
        'email': 'construction@catdev.com',
        'website': 'https://catdevcon.com',
    },
    {
        'name': 'Island Breeze Renewable Energy',
        'category': 'Energy & Environment',
        'description': 'Solar panels, wind energy solutions, and sustainable energy consulting',
        'address': 'Panganiban, Catanduanes',
        'latitude': 13.6891,
        'longitude': 124.4123,
        'phone': '09197234565',
        'email': 'energy@islandbreeze.com',
        'website': 'https://islandbreeze-energy.com',
    },
    {
        'name': 'Catanduanes Online Marketing Hub',
        'category': 'Digital Marketing & E-commerce',
        'description': 'Digital marketing, social media management, and e-commerce solutions',
        'address': 'San Andres, Catanduanes',
        'latitude': 13.6223,
        'longitude': 124.1901,
        'phone': '09200234566',
        'email': 'marketing@cmarkethub.com',
        'website': 'https://catmarkethub.com',
    }
]

# Sample job data (one per business)
JOBS_DATA = [
    {
        'title': 'Seafood Processing Technician',
        'category': 'Seafood & Fishing',
        'type': 'full_time',
        'salary_min': 18000,
        'salary_max': 25000,
        'description': 'Looking for experienced seafood processing technician to handle quality control and product packaging in our export facility.',
        'requirements': ['2+ years seafood processing experience', 'Food handling certification', 'Attention to detail'],
        'benefits': ['13th month pay', 'Health insurance', 'Overtime pay'],
    },
    {
        'title': 'Coconut Oil Production Manager',
        'category': 'Agriculture & Processing',
        'type': 'full_time',
        'salary_min': 25000,
        'salary_max': 35000,
        'description': 'Manage coconut oil production operations, quality assurance, and team coordination.',
        'requirements': ['5+ years production management', 'Agricultural processing knowledge', 'Leadership skills'],
        'benefits': ['13th month pay', 'Health insurance', 'Housing assistance', 'Performance bonus'],
    },
    {
        'title': 'Dive Instructor & Tour Guide',
        'category': 'Tourism & Hospitality',
        'type': 'full_time',
        'salary_min': 20000,
        'salary_max': 30000,
        'description': 'Certified dive instructor needed for recreational and technical diving tours.',
        'requirements': ['PADI certification or equivalent', 'English proficiency', 'Customer service skills'],
        'benefits': ['Meals provided', 'Equipment provided', 'Commission on tours', 'Travel allowance'],
    },
    {
        'title': 'Textile Weaving Instructor',
        'category': 'Handicrafts & Arts',
        'type': 'full_time',
        'salary_min': 17000,
        'salary_max': 22000,
        'description': 'Train artisans in traditional Filipino weaving techniques and product design.',
        'requirements': ['Expert weaving skills', 'Teaching experience', 'Knowledge of traditional patterns'],
        'benefits': ['13th month pay', 'Free materials', 'Workshop access'],
    },
    {
        'title': 'Senior Web Developer',
        'category': 'Information Technology',
        'type': 'full_time',
        'salary_min': 35000,
        'salary_max': 50000,
        'description': 'Lead web development team for enterprise-level web applications and platforms.',
        'requirements': ['5+ years web development', 'Full-stack capabilities', 'Team leadership'],
        'benefits': ['13th month pay', 'Health insurance', 'Remote work', 'Professional development'],
    },
    {
        'title': 'Farm Manager & Veterinary Technician',
        'category': 'Agriculture & Livestock',
        'type': 'full_time',
        'salary_min': 22000,
        'salary_max': 32000,
        'description': 'Manage dairy farm operations and animal health care.',
        'requirements': ['Veterinary background', 'Farm management experience', 'Organic certification knowledge'],
        'benefits': ['13th month pay', 'Health insurance', 'Housing', 'Farm product allowance'],
    },
    {
        'title': 'Spa Therapist & Wellness Coordinator',
        'category': 'Health & Wellness',
        'type': 'full_time',
        'salary_min': 18000,
        'salary_max': 28000,
        'description': 'Licensed massage therapist and wellness coordinator for spa operations.',
        'requirements': ['Professional massage certification', 'Wellness training', 'Customer care excellence'],
        'benefits': ['13th month pay', 'Health benefits', 'Commission', 'Free spa services'],
    },
    {
        'title': 'Construction Project Manager',
        'category': 'Construction & Real Estate',
        'type': 'full_time',
        'salary_min': 28000,
        'salary_max': 40000,
        'description': 'Oversee multiple construction projects from planning to completion.',
        'requirements': ['5+ years construction PM experience', 'Engineering background', 'Budget management'],
        'benefits': ['13th month pay', 'Health insurance', 'Project bonus', 'Vehicle allowance'],
    },
    {
        'title': 'Solar Installation & Maintenance Technician',
        'category': 'Energy & Environment',
        'type': 'full_time',
        'salary_min': 24000,
        'salary_max': 34000,
        'description': 'Install, maintain, and troubleshoot renewable energy systems.',
        'requirements': ['Solar certification', 'Electrical knowledge', 'Safety compliance'],
        'benefits': ['13th month pay', 'Health insurance', 'Technical training', 'Overtime pay'],
    },
    {
        'title': 'Social Media Manager & Content Creator',
        'category': 'Digital Marketing & E-commerce',
        'type': 'full_time',
        'salary_min': 20000,
        'salary_max': 30000,
        'description': 'Create and manage social media content and digital marketing campaigns.',
        'requirements': ['2+ years social media experience', 'Content creation skills', 'Analytics knowledge'],
        'benefits': ['13th month pay', 'Health insurance', 'Remote work', 'Creative freedom'],
    }
]

def seed_data():
    """Seed businesses and jobs into Neo4j"""
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        with driver.session(database=NEO4J_DATABASE) as session:
            print("Starting data seeding process...")
            
            # Step 1: Create 10 Businesses
            print("\n" + "="*60)
            print("STEP 1: Creating 10 Businesses")
            print("="*60)
            
            business_ids = []
            for idx, biz_data in enumerate(BUSINESSES_DATA, 1):
                business_id = str(uuid.uuid4())
                business_ids.append(business_id)
                
                query = """
                    CREATE (b:Business {
                        id: $id,
                        uuid: $uuid,
                        name: $name,
                        category: $category,
                        description: $description,
                        address: $address,
                        latitude: $latitude,
                        longitude: $longitude,
                        phone: $phone,
                        email: $email,
                        website: $website,
                        is_verified: true,
                        is_active: true,
                        rating: 0.0,
                        review_count: 0,
                        is_featured: false,
                        created_at: $created_at
                    })
                    RETURN b.id as id
                """
                
                params = {
                    'id': business_id,
                    'uuid': str(uuid.uuid4()),
                    'name': biz_data['name'],
                    'category': biz_data['category'],
                    'description': biz_data['description'],
                    'address': biz_data['address'],
                    'latitude': biz_data['latitude'],
                    'longitude': biz_data['longitude'],
                    'phone': biz_data['phone'],
                    'email': biz_data['email'],
                    'website': biz_data['website'],
                    'created_at': datetime.utcnow().isoformat()
                }
                
                result = session.run(query, params).single()
                print(f"  [+] Business {idx}: {biz_data['name']}")
                print(f"      ID: {business_id}")
            
            # Step 2: Link all businesses to owner
            print("\n" + "="*60)
            print("STEP 2: Linking Businesses to Owner")
            print("="*60)
            
            for idx, biz_id in enumerate(business_ids, 1):
                query = """
                    MATCH (u:User {id: $owner_id})
                    MATCH (b:Business {id: $business_id})
                    MERGE (u)-[:OWNS]->(b)
                    RETURN b.name as name
                """
                
                params = {
                    'owner_id': OWNER_ID,
                    'business_id': biz_id
                }
                
                result = session.run(query, params).single()
                print(f"  [+] Linked business {idx} to owner")
            
            # Step 3: Create 10 Jobs (one per business)
            print("\n" + "="*60)
            print("STEP 3: Creating 10 Jobs")
            print("="*60)
            
            for idx, (job_data, biz_id, biz_data) in enumerate(zip(JOBS_DATA, business_ids, BUSINESSES_DATA), 1):
                job_id = str(uuid.uuid4())
                
                query = """
                    CREATE (j:Job {
                        id: $id,
                        uuid: $uuid,
                        title: $title,
                        description: $description,
                        category: $category,
                        type: $type,
                        salary_min: $salary_min,
                        salary_max: $salary_max,
                        currency: 'PHP',
                        location: $location,
                        latitude: $latitude,
                        longitude: $longitude,
                        requirements: $requirements,
                        benefits: $benefits,
                        is_active: true,
                        applications_count: 0,
                        created_at: $created_at,
                        expires_at: $expires_at
                    })
                    RETURN j.id as id
                """
                
                params = {
                    'id': job_id,
                    'uuid': str(uuid.uuid4()),
                    'title': job_data['title'],
                    'description': job_data['description'],
                    'category': job_data['category'],
                    'type': job_data['type'],
                    'salary_min': job_data['salary_min'],
                    'salary_max': job_data['salary_max'],
                    'location': biz_data['address'],
                    'latitude': biz_data['latitude'],
                    'longitude': biz_data['longitude'],
                    'requirements': job_data['requirements'],
                    'benefits': job_data['benefits'],
                    'created_at': datetime.utcnow().isoformat(),
                    'expires_at': (datetime.utcnow() + timedelta(days=30)).isoformat()
                }
                
                result = session.run(query, params).single()
                print(f"  [+] Job {idx}: {job_data['title']}")
                print(f"      ID: {job_id}")
                
                # Step 4: Link job to business
                link_query = """
                    MATCH (j:Job {id: $job_id})
                    MATCH (b:Business {id: $business_id})
                    MERGE (j)-[:POSTED_BY]->(b)
                    RETURN j.title as title, b.name as business
                """
                
                link_params = {
                    'job_id': job_id,
                    'business_id': biz_id
                }
                
                link_result = session.run(link_query, link_params).single()
                print(f"    Linked to: {link_result['business']}")
            
            print("\n" + "="*60)
            print("[SUCCESS] DATA SEEDING COMPLETED!")
            print("="*60)
            print(f"\nCreated:")
            print(f"  [+] 10 Businesses")
            print(f"  [+] 10 Jobs (1 per business)")
            print(f"  [+] All linked to owner: {OWNER_EMAIL}")
            print("\nBusiness Owner Details:")
            print(f"  ID: {OWNER_ID}")
            print(f"  Email: {OWNER_EMAIL}")
            print(f"  Username: ren")
            
            # Verification query
            print("\n" + "="*60)
            print("VERIFICATION:")
            print("="*60)
            
            verify_query = """
                MATCH (u:User {id: $owner_id})-[:OWNS]->(b:Business)
                RETURN count(b) as business_count
            """
            verify_result = session.run(verify_query, {'owner_id': OWNER_ID}).single()
            print(f"[+] Total businesses owned by user: {verify_result['business_count']}")
            
            jobs_query = """
                MATCH (j:Job)-[:POSTED_BY]->(:Business)<-[:OWNS]-(u:User {id: $owner_id})
                RETURN count(j) as job_count
            """
            jobs_result = session.run(jobs_query, {'owner_id': OWNER_ID}).single()
            print(f"[+] Total jobs posted by owner's businesses: {jobs_result['job_count']}")
            
    except Exception as e:
        print(f"\n[ERROR] Error during seeding: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        driver.close()

if __name__ == '__main__':
    seed_data()
