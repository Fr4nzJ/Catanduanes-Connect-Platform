#!/usr/bin/env python3
"""
Seed script for Catanduanes Connect
Creates demo users, businesses, jobs, and services
"""

import os
import sys
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import Neo4jConnection, safe_run, _node_to_dict
from models import User, Business, Job, Review, Notification

# Load environment variables
load_dotenv()

def create_demo_users(db):
    """Create demo users for different roles"""
    print("Creating demo users...")
    
    users = [
        {
            'id': str(uuid.uuid4()),
            'email': 'admin@example.com',
            'username': 'admin',
            'password_hash': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewlyZjHVj65PJ.Pm',  # Password123!
            'role': 'admin',
            'is_verified': True,
            'is_active': True,
            'created_at': datetime.utcnow().isoformat(),
            'phone': '09123456789',
            'location': 'Virac, Catanduanes'
        },
        {
            'id': str(uuid.uuid4()),
            'email': 'job_seeker@example.com',
            'username': 'job_seeker',
            'password_hash': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewlyZjHVj65PJ.Pm',  # Password123!
            'role': 'job_seeker',
            'is_verified': True,
            'is_active': True,
            'created_at': datetime.utcnow().isoformat(),
            'phone': '09123456790',
            'location': 'Virac, Catanduanes'
        },
        {
            'id': str(uuid.uuid4()),
            'email': 'business_owner@example.com',
            'username': 'business_owner',
            'password_hash': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewlyZjHVj65PJ.Pm',  # Password123!
            'role': 'business_owner',
            'is_verified': True,
            'is_active': True,
            'created_at': datetime.utcnow().isoformat(),
            'phone': '09123456791',
            'location': 'Virac, Catanduanes'
        },
        {
            'id': str(uuid.uuid4()),
            'email': 'service_client@example.com',
            'username': 'service_provider',
            'password_hash': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewlyZjHVj65PJ.Pm',  # Password123!
            'role': 'service_client',
            'is_verified': True,
            'is_active': True,
            'created_at': datetime.utcnow().isoformat(),
            'phone': '09123456792',
            'location': 'Virac, Catanduanes'
        }
    ]
    
    with db.session() as session:
        for user_data in users:
            safe_run(session, """
                CREATE (u:User $user_data)
            """, {'user_data': user_data})
    
    print(f"Created {len(users)} demo users")
    return users

def create_demo_businesses(db, users):
    """Create demo businesses"""
    print("Creating demo businesses...")
    
    businesses = [
        {
            'id': str(uuid.uuid4()),
            'name': 'Virac IT Solutions',
            'description': 'Leading technology solutions provider offering software development, IT consulting, and digital transformation services for businesses in Catanduanes.',
            'category': 'technology',
            'address': 'Rizal Avenue, Virac, Catanduanes',
            'latitude': 13.5809,
            'longitude': 124.3842,
            'phone': '0528112345',
            'email': 'info@viracitsolutions.com',
            'website': 'https://viracitsolutions.com',
            'owner_id': users[2]['id'],  # business_owner
            'permit_number': 'BP-2024-001',
            'permit_file': 'businesses/virac-it-solutions/permit.pdf',
            'is_verified': True,
            'is_active': True,
            'created_at': datetime.utcnow().isoformat(),
            'rating': 4.8,
            'review_count': 12
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'Catanduanes Coastal Restaurant',
            'description': 'Authentic Filipino coastal cuisine featuring fresh seafood and traditional Bicolano dishes. Perfect for family dining and special occasions.',
            'category': 'restaurant',
            'address': 'San Pedro Street, Virac, Catanduanes',
            'latitude': 13.5820,
            'longitude': 124.3830,
            'phone': '0528112346',
            'email': 'info@coastalrestaurant.com',
            'website': 'https://coastalrestaurant.com',
            'owner_id': users[2]['id'],  # business_owner
            'permit_number': 'BP-2024-002',
            'permit_file': 'businesses/coastal-restaurant/permit.pdf',
            'is_verified': True,
            'is_active': True,
            'created_at': (datetime.utcnow() - timedelta(days=5)).isoformat(),
            'rating': 4.6,
            'review_count': 8
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'Island Healthcare Center',
            'description': 'Modern healthcare facility providing comprehensive medical services, emergency care, and specialized treatments for the community.',
            'category': 'healthcare',
            'address': 'Health Avenue, Virac, Catanduanes',
            'latitude': 13.5815,
            'longitude': 124.3850,
            'phone': '0528112347',
            'email': 'info@islandhealthcare.com',
            'website': 'https://islandhealthcare.com',
            'owner_id': users[2]['id'],  # business_owner
            'permit_number': 'BP-2024-003',
            'permit_file': 'businesses/island-healthcare/permit.pdf',
            'is_verified': True,
            'is_active': True,
            'created_at': (datetime.utcnow() - timedelta(days=10)).isoformat(),
            'rating': 4.9,
            'review_count': 15
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'Bicol Tech Academy',
            'description': 'Educational institution offering technology courses, vocational training, and professional development programs for students and professionals.',
            'category': 'education',
            'address': 'Education Boulevard, Virac, Catanduanes',
            'latitude': 13.5800,
            'longitude': 124.3860,
            'phone': '0528112348',
            'email': 'info@bicoltechacademy.com',
            'website': 'https://bicoltechacademy.com',
            'owner_id': users[2]['id'],  # business_owner
            'permit_number': 'BP-2024-004',
            'permit_file': 'businesses/bicol-tech-academy/permit.pdf',
            'is_verified': False,  # Pending verification
            'is_active': True,
            'created_at': (datetime.utcnow() - timedelta(days=2)).isoformat(),
            'rating': 0.0,
            'review_count': 0
        }
    ]
    
    with db.session() as session:
        for business_data in businesses:
            safe_run(session, """
                CREATE (b:Business $business_data)
            """, {'business_data': business_data})
            
            # Create ownership relationship
            safe_run(session, """
                MATCH (u:User {id: $owner_id}), (b:Business {id: $business_id})
                CREATE (u)-[:OWNS]->(b)
            """, {
                'owner_id': business_data['owner_id'],
                'business_id': business_data['id']
            })
    
    print(f"Created {len(businesses)} demo businesses")
    return businesses

def create_demo_jobs(db, businesses):
    """Create demo jobs"""
    print("Creating demo jobs...")
    
    jobs = [
        {
            'id': str(uuid.uuid4()),
            'title': 'Senior Software Developer',
            'description': 'We are looking for an experienced software developer to join our team. You will be responsible for designing, developing, and maintaining web applications using modern technologies.',
            'category': 'technology',
            'type': 'full_time',
            'salary_min': 50000,
            'salary_max': 80000,
            'currency': 'PHP',
            'location': 'Virac, Catanduanes',
            'latitude': 13.5809,
            'longitude': 124.3842,
            'business_id': businesses[0]['id'],  # Virac IT Solutions
            'business_name': 'Virac IT Solutions',
            'requirements': 'Bachelor\'s degree in Computer Science, 3+ years experience in web development, proficiency in Python/JavaScript',
            'benefits': 'Health insurance, flexible working hours, professional development opportunities',
            'is_active': True,
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(days=30)).isoformat(),
            'applications_count': 0
        },
        {
            'id': str(uuid.uuid4()),
            'title': 'Restaurant Manager',
            'description': 'Seeking an experienced restaurant manager to oversee daily operations, manage staff, and ensure excellent customer service at our coastal restaurant.',
            'category': 'hospitality',
            'type': 'full_time',
            'salary_min': 35000,
            'salary_max': 50000,
            'currency': 'PHP',
            'location': 'Virac, Catanduanes',
            'latitude': 13.5820,
            'longitude': 124.3830,
            'business_id': businesses[1]['id'],  # Coastal Restaurant
            'business_name': 'Catanduanes Coastal Restaurant',
            'requirements': 'Experience in restaurant management, leadership skills, customer service orientation',
            'benefits': 'Meal allowance, performance bonuses, career advancement opportunities',
            'is_active': True,
            'created_at': (datetime.utcnow() - timedelta(days=3)).isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(days=27)).isoformat(),
            'applications_count': 2
        },
        {
            'id': str(uuid.uuid4()),
            'title': 'Registered Nurse',
            'description': 'Join our healthcare team as a registered nurse. Provide compassionate care to patients and support our medical staff in delivering quality healthcare services.',
            'category': 'healthcare',
            'type': 'full_time',
            'salary_min': 40000,
            'salary_max': 60000,
            'currency': 'PHP',
            'location': 'Virac, Catanduanes',
            'latitude': 13.5815,
            'longitude': 124.3850,
            'business_id': businesses[2]['id'],  # Island Healthcare
            'business_name': 'Island Healthcare Center',
            'requirements': 'Bachelor of Science in Nursing, valid PRC license, experience in clinical setting preferred',
            'benefits': 'Competitive salary, health insurance, continuing education support',
            'is_active': True,
            'created_at': (datetime.utcnow() - timedelta(days=7)).isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(days=23)).isoformat(),
            'applications_count': 5
        },
        {
            'id': str(uuid.uuid4()),
            'title': 'Part-time Web Developer',
            'description': 'Looking for a part-time web developer to assist with ongoing projects. Flexible hours, perfect for students or those seeking additional income.',
            'category': 'technology',
            'type': 'part_time',
            'salary_min': 25000,
            'salary_max': 35000,
            'currency': 'PHP',
            'location': 'Virac, Catanduanes',
            'latitude': 13.5809,
            'longitude': 124.3842,
            'business_id': businesses[0]['id'],  # Virac IT Solutions
            'business_name': 'Virac IT Solutions',
            'requirements': 'Basic knowledge of HTML, CSS, and JavaScript, willingness to learn',
            'benefits': 'Flexible schedule, remote work option, mentorship opportunities',
            'is_active': True,
            'created_at': (datetime.utcnow() - timedelta(days=1)).isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(days=29)).isoformat(),
            'applications_count': 1
        }
    ]
    
    with db.session() as session:
        for job_data in jobs:
            safe_run(session, """
                CREATE (j:Job $job_data)
            """, {'job_data': job_data})
            
            # Create relationship with business
            safe_run(session, """
                MATCH (b:Business {id: $business_id}), (j:Job {id: $job_id})
                CREATE (b)-[:POSTED_BY]->(j)
            """, {
                'business_id': job_data['business_id'],
                'job_id': job_data['id']
            })
    
    print(f"Created {len(jobs)} demo jobs")
    return jobs

def create_demo_services(db, users):
    """Create demo services"""
    print("Creating demo services...")
    
    services = [
        {
            'id': str(uuid.uuid4()),
            'title': 'Professional Web Development',
            'description': 'Custom website development using modern technologies. From simple landing pages to complex web applications.',
            'category': 'professional_services',
            'price': 15000,
            'currency': 'PHP',
            'price_type': 'fixed',
            'location': 'Virac, Catanduanes',
            'latitude': 13.5809,
            'longitude': 124.3842,
            'provider_id': users[3]['id'],  # service_client
            'provider_name': 'service_provider',
            'duration': '1-2 weeks',
            'requirements': 'Project requirements discussion, content preparation',
            'is_active': True,
            'created_at': datetime.utcnow().isoformat(),
            'rating': 4.7,
            'review_count': 6
        },
        {
            'id': str(uuid.uuid4()),
            'title': 'Home Cleaning Services',
            'description': 'Professional home cleaning services for houses and apartments. Deep cleaning, regular maintenance, and move-in/move-out cleaning.',
            'category': 'home_services',
            'price': 500,
            'currency': 'PHP',
            'price_type': 'hourly',
            'location': 'Virac, Catanduanes',
            'latitude': 13.5820,
            'longitude': 124.3830,
            'provider_id': users[3]['id'],  # service_client
            'provider_name': 'service_provider',
            'duration': '2-4 hours',
            'requirements': 'Access to property, cleaning supplies provided',
            'is_active': True,
            'created_at': (datetime.utcnow() - timedelta(days=2)).isoformat(),
            'rating': 4.5,
            'review_count': 4
        },
        {
            'id': str(uuid.uuid4()),
            'title': 'Tutoring Services',
            'description': 'Personalized tutoring in mathematics, science, and English for elementary and high school students.',
            'category': 'education_training',
            'price': 300,
            'currency': 'PHP',
            'price_type': 'hourly',
            'location': 'Virac, Catanduanes',
            'latitude': 13.5810,
            'longitude': 124.3840,
            'provider_id': users[3]['id'],  # service_client
            'provider_name': 'service_provider',
            'duration': '1-2 hours per session',
            'requirements': 'Study materials, quiet learning environment',
            'is_active': True,
            'created_at': (datetime.utcnow() - timedelta(days=5)).isoformat(),
            'rating': 4.9,
            'review_count': 8
        }
    ]
    
    with db.session() as session:
        for service_data in services:
            safe_run(session, """
                CREATE (s:Service $service_data)
            """, {'service_data': service_data})
            
            # Create relationship with provider
            safe_run(session, """
                MATCH (u:User {id: $provider_id}), (s:Service {id: $service_id})
                CREATE (u)-[:PROVIDES]->(s)
            """, {
                'provider_id': service_data['provider_id'],
                'service_id': service_data['id']
            })
    
    print(f"Created {len(services)} demo services")
    return services

def create_demo_reviews(db, users, businesses, services):
    """Create demo reviews"""
    print("Creating demo reviews...")
    
    reviews = [
        # Business reviews
        {
            'id': str(uuid.uuid4()),
            'rating': 5,
            'comment': 'Excellent service! The team at Virac IT Solutions delivered our website on time and exceeded our expectations.',
            'user_id': users[1]['id'],  # job_seeker
            'user_name': 'job_seeker',
            'target_id': businesses[0]['id'],
            'target_type': 'business',
            'created_at': (datetime.utcnow() - timedelta(days=10)).isoformat()
        },
        {
            'id': str(uuid.uuid4()),
            'rating': 4,
            'comment': 'Great food and atmosphere. The seafood is always fresh and the staff are very accommodating.',
            'user_id': users[1]['id'],  # job_seeker
            'user_name': 'job_seeker',
            'target_id': businesses[1]['id'],
            'target_type': 'business',
            'created_at': (datetime.utcnow() - timedelta(days=8)).isoformat()
        },
        {
            'id': str(uuid.uuid4()),
            'rating': 5,
            'comment': 'Professional and caring healthcare providers. The facility is clean and well-equipped.',
            'user_id': users[3]['id'],  # service_client
            'user_name': 'service_provider',
            'target_id': businesses[2]['id'],
            'target_type': 'business',
            'created_at': (datetime.utcnow() - timedelta(days=6)).isoformat()
        },
        # Service reviews
        {
            'id': str(uuid.uuid4()),
            'rating': 5,
            'comment': 'Outstanding web development work. Very professional and responsive to our needs.',
            'user_id': users[2]['id'],  # business_owner
            'user_name': 'business_owner',
            'target_id': services[0]['id'],
            'target_type': 'service',
            'created_at': (datetime.utcnow() - timedelta(days=12)).isoformat()
        },
        {
            'id': str(uuid.uuid4()),
            'rating': 4,
            'comment': 'Thorough cleaning service. The house was spotless after they finished.',
            'user_id': users[1]['id'],  # job_seeker
            'user_name': 'job_seeker',
            'target_id': services[1]['id'],
            'target_type': 'service',
            'created_at': (datetime.utcnow() - timedelta(days=7)).isoformat()
        }
    ]
    
    with db.session() as session:
        for review_data in reviews:
            safe_run(session, """
                CREATE (r:Review $review_data)
            """, {'review_data': review_data})
            
            # Create relationships
            if review_data['target_type'] == 'business':
                safe_run(session, """
                    MATCH (u:User {id: $user_id}), (r:Review {id: $review_id}), (b:Business {id: $target_id})
                    CREATE (u)-[:REVIEWS]->(r)-[:FOR_BUSINESS]->(b)
                """, {
                    'user_id': review_data['user_id'],
                    'review_id': review_data['id'],
                    'target_id': review_data['target_id']
                })
            else:  # service
                safe_run(session, """
                    MATCH (u:User {id: $user_id}), (r:Review {id: $review_id}), (s:Service {id: $target_id})
                    CREATE (u)-[:REVIEWS]->(r)-[:FOR_SERVICE]->(s)
                """, {
                    'user_id': review_data['user_id'],
                    'review_id': review_data['id'],
                    'target_id': review_data['target_id']
                })
    
    print(f"Created {len(reviews)} demo reviews")
    return reviews

def create_demo_notifications(db, users):
    """Create demo notifications"""
    print("Creating demo notifications...")
    
    notifications = [
        {
            'id': str(uuid.uuid4()),
            'user_id': users[2]['id'],  # business_owner
            'type': 'business_verified',
            'title': 'Business Verified',
            'message': 'Your business Virac IT Solutions has been verified and is now live on the platform.',
            'data': {'business_id': 'virac-it-solutions-id'},
            'is_read': False,
            'created_at': (datetime.utcnow() - timedelta(days=1)).isoformat()
        },
        {
            'id': str(uuid.uuid4()),
            'user_id': users[2]['id'],  # business_owner
            'type': 'new_job_application',
            'title': 'New Job Application',
            'message': 'You have received a new application for Senior Software Developer position.',
            'data': {'job_id': 'senior-dev-job-id', 'applicant_id': 'applicant-id'},
            'is_read': False,
            'created_at': (datetime.utcnow() - timedelta(hours=2)).isoformat()
        },
        {
            'id': str(uuid.uuid4()),
            'user_id': users[1]['id'],  # job_seeker
            'type': 'job_application_received',
            'title': 'Application Received',
            'message': 'Your application for the Restaurant Manager position has been received.',
            'data': {'job_id': 'restaurant-manager-job-id', 'business_id': 'coastal-restaurant-id'},
            'is_read': True,
            'created_at': (datetime.utcnow() - timedelta(days=3)).isoformat()
        }
    ]
    
    with db.session() as session:
        for notification_data in notifications:
            safe_run(session, """
                CREATE (n:Notification $notification_data)
            """, {'notification_data': notification_data})
    
    print(f"Created {len(notifications)} demo notifications")
    return notifications

def main():
    """Main seeding function"""
    print("Starting Catanduanes Connect seeding...")
    
    # Initialize database connection
    db = Neo4jConnection(
        uri=os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
        user=os.getenv('NEO4J_USER', 'neo4j'),
        password=os.getenv('NEO4J_PASSWORD', 'password')
    )
    
    try:
        # Create demo data
        users = create_demo_users(db)
        businesses = create_demo_businesses(db, users)
        jobs = create_demo_jobs(db, businesses)
        services = create_demo_services(db, users)
        reviews = create_demo_reviews(db, users, businesses, services)
        notifications = create_demo_notifications(db, users)
        
        print("\nSeeding completed successfully!")
        print("\nDemo Accounts:")
        print("- Admin: admin@example.com / Password123!")
        print("- Job Seeker: job_seeker@example.com / Password123!")
        print("- Business Owner: business_owner@example.com / Password123!")
        print("- Service Client: service_client@example.com / Password123!")
        
        print(f"\nCreated:")
        print(f"- {len(users)} users")
        print(f"- {len(businesses)} businesses")
        print(f"- {len(jobs)} jobs")
        print(f"- {len(services)} services")
        print(f"- {len(reviews)} reviews")
        print(f"- {len(notifications)} notifications")
        
    except Exception as e:
        print(f"Error during seeding: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()