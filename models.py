from flask_login import UserMixin
from datetime import datetime
from typing import Optional, Dict, Any, List
import uuid

class User(UserMixin):
    def __init__(self, **kwargs):
        # 1. id MUST be supplied when we load from DB
        if 'id' not in kwargs or not kwargs['id']:
            raise ValueError("User must be created with an 'id'")
        self.id = str(kwargs['id'])

        # 2. everything else
        self.email           = kwargs.get('email')
        self.username        = kwargs.get('username')
        self.password_hash   = kwargs.get('password_hash')
        self.role            = kwargs.get('role', 'job_seeker')
        self.is_verified     = kwargs.get('is_verified', False)
        self._is_active      = kwargs.get('is_active', True)
        self.created_at      = kwargs.get('created_at', datetime.utcnow().isoformat())
        self.profile_picture = kwargs.get('profile_picture')
        self.phone           = kwargs.get('phone')
        self.location        = kwargs.get('location')
    
    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False
        
    @property
    def is_active(self):
        return self._is_active
        
    @is_active.setter
    def is_active(self, value):
        self._is_active = value
    
    def get_id(self):
        # Return the same ID stored in Neo4j
        return str(self.id)
    
    def has_role(self, role: str) -> bool:
        """Check if user has specified role"""
        if not self.role or not role:
            return False
        if isinstance(role, (list, tuple)):
            return self.role in role
        return self.role == role
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'role': self.role,
            'is_verified': self.is_verified,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'profile_picture': self.profile_picture,
            'phone': self.phone,
            'location': self.location
        }

    
    @classmethod
    def get_by_google_id(cls, google_id):
        """Get a user by their Google ID from Neo4j."""
        from database import get_neo4j_db, safe_run, _node_to_dict
        db = get_neo4j_db()
        with db.session() as session:
            result = safe_run(session, """
                MATCH (u:User {google_id: $google_id})
                RETURN u
            """, {'google_id': google_id})
            if result:
                user_data = _node_to_dict(result[0]['u'])
                return cls(**user_data)
        return None
    
    @classmethod
    def get_by_email(cls, email):
        """Get a user by their email from Neo4j."""
        from database import get_neo4j_db, safe_run, _node_to_dict
        db = get_neo4j_db()
        with db.session() as session:
            result = safe_run(session, """
                MATCH (u:User {email: $email})
                RETURN u
            """, {'email': email})
            if result:
                user_data = _node_to_dict(result[0]['u'])
                return cls(**user_data)
        return None

class Business:
    """Business model"""
    
    def __init__(self, **kwargs):
        # Ensure ID is always set and is a string
        raw_id = kwargs.get('id')
        if raw_id:
            self.id = str(raw_id)  # Convert to string if it's not already
        else:
            self.id = str(uuid.uuid4())
            
        self.name = kwargs.get('name')
        self.description = kwargs.get('description')
        self.category = kwargs.get('category')
        self.address = kwargs.get('address')
        self.latitude = kwargs.get('latitude')
        self.longitude = kwargs.get('longitude')
        self.phone = kwargs.get('phone')
        self.email = kwargs.get('email')
        self.website = kwargs.get('website')
        self.owner_id = kwargs.get('owner_id')
        self.permit_number = kwargs.get('permit_number')
        self.permit_file = kwargs.get('permit_file')
        self.is_verified = kwargs.get('is_verified', False)
        self.is_active = kwargs.get('is_active', True)
        self.created_at = kwargs.get('created_at', datetime.utcnow().isoformat())
        self.rating = kwargs.get('rating', 0.0)
        self.review_count = kwargs.get('review_count', 0)
        self.is_featured = kwargs.get('is_featured', False)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert business to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'address': self.address,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'phone': self.phone,
            'email': self.email,
            'website': self.website,
            'owner_id': self.owner_id,
            'permit_number': self.permit_number,
            'permit_file': self.permit_file,
            'is_verified': self.is_verified,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'rating': self.rating,
            'review_count': self.review_count,
            'is_featured': self.is_featured
        }

class Job:
    """Job listing model"""
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('id') or str(uuid.uuid4())
        self.title = kwargs.get('title')
        self.description = kwargs.get('description')
        self.category = kwargs.get('category')
        self.type = kwargs.get('type', 'full_time')  # full_time, part_time, contract, internship
        self.salary_min = kwargs.get('salary_min')
        self.salary_max = kwargs.get('salary_max')
        self.currency = kwargs.get('currency', 'PHP')
        self.location = kwargs.get('location')
        self.latitude = kwargs.get('latitude')
        self.longitude = kwargs.get('longitude')
        self.business_id = kwargs.get('business_id')
        self.business_name = kwargs.get('business_name')
        self.requirements = kwargs.get('requirements', [])
        self.benefits = kwargs.get('benefits', [])
        self.is_active = kwargs.get('is_active', True)
        self.created_at = kwargs.get('created_at', datetime.utcnow().isoformat())
        self.expires_at = kwargs.get('expires_at')
        self.applications_count = kwargs.get('applications_count', 0)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'type': self.type,
            'salary_min': self.salary_min,
            'salary_max': self.salary_max,
            'currency': self.currency,
            'location': self.location,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'business_id': self.business_id,
            'business_name': self.business_name,
            'requirements': self.requirements,
            'benefits': self.benefits,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'expires_at': self.expires_at,
            'applications_count': self.applications_count
        }

class Service:
    """Service listing model"""
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('id') or str(uuid.uuid4())
        self.title = kwargs.get('title')
        self.description = kwargs.get('description')
        self.category = kwargs.get('category')
        self.price = kwargs.get('price')
        self.currency = kwargs.get('currency', 'PHP')
        self.price_type = kwargs.get('price_type', 'fixed')  # fixed, hourly, daily
        self.location = kwargs.get('location')
        self.latitude = kwargs.get('latitude')
        self.longitude = kwargs.get('longitude')
        self.provider_id = kwargs.get('provider_id')
        self.provider_name = kwargs.get('provider_name')
        self.duration = kwargs.get('duration')
        self.requirements = kwargs.get('requirements', [])
        self.is_active = kwargs.get('is_active', True)
        self.created_at = kwargs.get('created_at', datetime.utcnow().isoformat())
        self.rating = kwargs.get('rating', 0.0)
        self.review_count = kwargs.get('review_count', 0)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert service to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'price': self.price,
            'currency': self.currency,
            'price_type': self.price_type,
            'location': self.location,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'provider_id': self.provider_id,
            'provider_name': self.provider_name,
            'duration': self.duration,
            'requirements': self.requirements,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'rating': self.rating,
            'review_count': self.review_count
        }

class Review:
    """Review model"""
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('id') or str(uuid.uuid4())
        self.rating = kwargs.get('rating')
        self.comment = kwargs.get('comment')
        self.user_id = kwargs.get('user_id')
        self.user_name = kwargs.get('user_name')
        self.target_id = kwargs.get('target_id')
        self.target_type = kwargs.get('target_type')  # business, service
        self.created_at = kwargs.get('created_at', datetime.utcnow().isoformat())
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert review to dictionary"""
        return {
            'id': self.id,
            'rating': self.rating,
            'comment': self.comment,
            'user_id': self.user_id,
            'user_name': self.user_name,
            'target_id': self.target_id,
            'target_type': self.target_type,
            'created_at': self.created_at
        }

class Notification:
    """Notification model"""
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('id') or str(uuid.uuid4())
        self.user_id = kwargs.get('user_id')
        self.type = kwargs.get('type')  # job_application, review, business_verified, etc.
        self.title = kwargs.get('title')
        self.message = kwargs.get('message')
        self.data = kwargs.get('data', {})
        self.is_read = kwargs.get('is_read', False)
        self.created_at = kwargs.get('created_at', datetime.utcnow().isoformat())
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert notification to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'title': self.title,
            'message': self.message,
            'data': self.data,
            'is_read': self.is_read,
            'created_at': self.created_at
        }

class JobApplication:
    """Job application model"""
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('id') or str(uuid.uuid4())
        self.job_id = kwargs.get('job_id')
        self.applicant_id = kwargs.get('applicant_id')
        self.applicant_name = kwargs.get('applicant_name')
        self.cover_letter = kwargs.get('cover_letter')
        self.resume_file = kwargs.get('resume_file')
        self.status = kwargs.get('status', 'pending')  # pending, accepted, rejected
        self.created_at = kwargs.get('created_at', datetime.utcnow().isoformat())
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert job application to dictionary"""
        return {
            'id': self.id,
            'job_id': self.job_id,
            'applicant_id': self.applicant_id,
            'applicant_name': self.applicant_name,
            'cover_letter': self.cover_letter,
            'resume_file': self.resume_file,
            'status': self.status,
            'created_at': self.created_at
        }