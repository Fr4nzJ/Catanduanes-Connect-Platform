"""Test configuration for Catanduanes Connect"""

import pytest
import re
from bs4 import BeautifulSoup
from app import create_app
from config import TestingConfig
from database import Neo4jConnection, safe_run, _node_to_dict
from models import User
import uuid
from datetime import datetime


def get_csrf_token(response_data):
    """Extract CSRF token from response HTML or return None if not found"""
    soup = BeautifulSoup(response_data, 'html.parser')
    csrf_input = soup.find('input', {'name': 'csrf_token'})
    if csrf_input and csrf_input.get('value'):
        return csrf_input['value']
        
    # As a fallback for XHR requests, check for a meta tag
    csrf_meta = soup.find('meta', {'name': 'csrf-token'})
    if csrf_meta and csrf_meta.get('content'):
        return csrf_meta['content']
        
    # If no CSRF token is found, check the response for other issues
    error_title = soup.find('title')
    if error_title and '405 Method Not Allowed' in error_title.text:
        raise ValueError(f"Endpoint does not support GET method: {error_title.text}")
    elif 'The CSRF token is missing' in response_data.decode():
        raise ValueError("Response indicates missing CSRF token")
    
    raise ValueError(f"Could not find CSRF token in response: {response_data[:200]}")


@pytest.fixture
def app():
    app = create_app('testing')
    app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'WTF_CSRF_CHECK_DEFAULT': False,
        'WTF_CSRF_TIME_LIMIT': None
    })
    
    from app import csrf
    csrf.init_app(app)  # Rebind CSRF with updated config
    
    with app.app_context():
        yield app

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test runner"""
    return app.test_cli_runner()


@pytest.fixture(autouse=True)
def neo4j_db():
    """Create Neo4j test database connection"""
    try:
        db = Neo4jConnection(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="00000000"
        )
        
        # Clean up before each test
        with db.session() as session:
            safe_run(session, "MATCH (n) DETACH DELETE n")
        
        yield db
        
    except Exception as e:
        pytest.fail(f"Failed to connect to Neo4j database: {str(e)}")
        
    finally:
        try:
            # Clean up after each test
            with db.session() as session:
                safe_run(session, "MATCH (n) DETACH DELETE n")
            db.close()
        except:
            pass  # If cleanup fails, don't raise error


import bcrypt

@pytest.fixture
def test_user(neo4j_db):
    """Create a test user"""
    password = 'Password123!'
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    user_data = {
        'id': str(uuid.uuid4()),
        'email': 'test@example.com',
        'username': 'testuser',
        'password_hash': password_hash,
        'role': 'job_seeker',
        'is_verified': True,
        'is_active': True,
        'created_at': datetime.utcnow().isoformat()
    }
    
    with neo4j_db.session() as session:
        safe_run(session, """
            CREATE (u:User $user_data)
        """, {'user_data': user_data})
    
    user = User(**user_data)
    yield user
    
    # Cleanup
    with neo4j_db.session() as session:
        safe_run(session, """
            MATCH (u:User {id: $user_id})
            DELETE u
        """, {'user_id': user.id})


@pytest.fixture
def test_business_owner(neo4j_db):
    """Create a test business owner"""
    password = 'Password123!'
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    user_data = {
        'id': str(uuid.uuid4()),
        'email': 'business@example.com',
        'username': 'businessowner',
        'password_hash': password_hash,
        'role': 'business_owner',
        'is_verified': True,
        'is_active': True,
        'created_at': datetime.utcnow().isoformat()
    }
    
    with neo4j_db.session() as session:
        safe_run(session, """
            CREATE (u:User $user_data)
        """, {'user_data': user_data})
    
    user = User(**user_data)
    yield user
    
    # Cleanup
    with neo4j_db.session() as session:
        safe_run(session, """
            MATCH (u:User {id: $user_id})
            DELETE u
        """, {'user_id': user.id})


@pytest.fixture
def test_business(neo4j_db, test_business_owner):
    """Create a test business"""
    business_data = {
        'id': str(uuid.uuid4()),
        'name': 'Test Business',
        'description': 'Test business description',
        'category': 'technology',
        'address': 'Test Address',
        'phone': '1234567890',
        'email': 'business@test.com',
        'owner_id': test_business_owner.id,
        'permit_number': 'BP-2024-001',
        'is_verified': True,
        'is_active': True,
        'created_at': datetime.utcnow().isoformat(),
        'rating': 4.5,
        'review_count': 10
    }
    
    with neo4j_db.session() as session:
        safe_run(session, """
            CREATE (b:Business $business_data)
        """, {'business_data': business_data})
        
        safe_run(session, """
            MATCH (u:User {id: $owner_id}), (b:Business {id: $business_id})
            CREATE (u)-[:OWNS]->(b)
        """, {
            'owner_id': test_business_owner.id,
            'business_id': business_data['id']
        })
    
    yield business_data
    
    # Cleanup
    with neo4j_db.session() as session:
        safe_run(session, """
            MATCH (b:Business {id: $business_id})
            DELETE b
        """, {'business_id': business_data['id']})


@pytest.fixture
def test_job(neo4j_db, test_business, test_business_owner):
    """Create a test job"""
    job_data = {
        'id': str(uuid.uuid4()),
        'title': 'Test Job',
        'description': 'Test job description',
        'category': 'technology',
        'type': 'full_time',
        'salary_min': 50000,
        'salary_max': 80000,
        'currency': 'PHP',
        'location': 'Test Location',
        'business_id': test_business['id'],
        'business_name': test_business['name'],
        'requirements': 'Test requirements',
        'benefits': 'Test benefits',
        'is_active': True,
        'created_at': datetime.utcnow().isoformat(),
        'applications_count': 0
    }
    
    with neo4j_db.session() as session:
        safe_run(session, """
            CREATE (j:Job $job_data)
        """, {'job_data': job_data})
        
        safe_run(session, """
            MATCH (b:Business {id: $business_id}), (j:Job {id: $job_id})
            CREATE (b)-[:POSTED_BY]->(j)
        """, {
            'business_id': test_business['id'],
            'job_id': job_data['id']
        })
    
    yield job_data
    
    # Cleanup
    with neo4j_db.session() as session:
        safe_run(session, """
            MATCH (j:Job {id: $job_id})
            DELETE j
        """, {'job_id': job_data['id']})


@pytest.fixture
def auth_client(client, test_user):
    """Create authenticated test client"""
    with client:
        from flask_login import login_user
        with client.session_transaction() as sess:
            login_user(test_user)
            sess['user_id'] = test_user.id
            sess['_fresh'] = True
        return client


@pytest.fixture
def business_owner_client(client, test_business_owner):
    """Create authenticated business owner test client"""
    with client.session_transaction() as sess:
        sess['user_id'] = test_business_owner.id
    return client


@pytest.fixture
def admin_client(client):
    """Create authenticated admin test client"""
    # Create admin user
    from database import Neo4jConnection, safe_run
    from models import User
    import uuid
    from datetime import datetime
    
    db = Neo4jConnection("bolt://localhost:7687", "neo4j", "password")
    
    admin_data = {
        'id': str(uuid.uuid4()),
        'email': 'admin@test.com',
        'username': 'testadmin',
        'password_hash': 'hashed_password',
        'role': 'admin',
        'is_verified': True,
        'is_active': True,
        'created_at': datetime.utcnow().isoformat()
    }
    
    with db.session() as session:
        safe_run(session, """
            CREATE (u:User $admin_data)
        """, {'admin_data': admin_data})
    
    admin_user = User(**admin_data)
    
    with client.session_transaction() as sess:
        sess['user_id'] = admin_user.id
    
    yield client
    
    # Cleanup
    with db.session() as session:
        safe_run(session, """
            MATCH (u:User {id: $user_id})
            DELETE u
        """, {'user_id': admin_user.id})
    
    db.close()