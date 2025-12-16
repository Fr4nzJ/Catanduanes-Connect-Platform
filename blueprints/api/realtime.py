"""
Real-time API endpoints for live data updates
"""

from flask import jsonify, current_app
from database import get_neo4j_db, safe_run
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def get_platform_stats():
    """Get real-time platform statistics"""
    db = get_neo4j_db()
    
    try:
        with db.session() as session:
            # Get active jobs
            jobs_result = safe_run(session, """
                MATCH (j:Job)
                WHERE j.status IS NULL OR j.status <> 'filled'
                RETURN count(j) as active_jobs
            """)
            active_jobs = jobs_result[0]['active_jobs'] if jobs_result else 0
            
            # Get total businesses
            businesses_result = safe_run(session, """
                MATCH (b:Business)
                WHERE b.is_active = true AND b.is_verified = true
                RETURN count(b) as total_businesses
            """)
            total_businesses = businesses_result[0]['total_businesses'] if businesses_result else 0
            
            # Get total services (Service nodes may not exist in this system)
            try:
                services_result = safe_run(session, """
                    MATCH (s:Service)
                    WHERE s.is_active = true
                    RETURN count(s) as total_services
                """)
                total_services = services_result[0]['total_services'] if services_result else 0
            except Exception:
                total_services = 0
            
            # Get total users
            users_result = safe_run(session, """
                MATCH (u:User)
                WHERE u.is_active = true
                RETURN count(u) as total_users
            """)
            total_users = users_result[0]['total_users'] if users_result else 0
            
            # Get recent activity count (last 24 hours)
            recent_result = safe_run(session, """
                MATCH (a:JobApplication)
                WHERE a.created_at > datetime() - duration('P1D')
                RETURN count(a) as recent_applications
            """)
            recent_applications = recent_result[0]['recent_applications'] if recent_result else 0
            
            return {
                'active_jobs': active_jobs,
                'total_businesses': total_businesses,
                'total_services': total_services,
                'total_users': total_users,
                'recent_applications': recent_applications,
                'timestamp': datetime.utcnow().isoformat()
            }
    except Exception as e:
        logger.error(f"Error fetching platform stats: {e}")
        return {
            'active_jobs': 0,
            'total_businesses': 0,
            'total_services': 0,
            'total_users': 0,
            'recent_applications': 0,
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }


def get_business_owner_stats(user_id):
    """Get real-time stats for a business owner"""
    db = get_neo4j_db()
    
    try:
        with db.session() as session:
            # Get jobs posted
            jobs_result = safe_run(session, """
                MATCH (u:User {id: $user_id})-[:OWNS]->(b:Business)<-[:POSTED_BY]-(j:Job)
                RETURN count(j) as total_jobs
            """, {'user_id': user_id})
            total_jobs = jobs_result[0]['total_jobs'] if jobs_result else 0
            
            # Get active jobs
            active_result = safe_run(session, """
                MATCH (u:User {id: $user_id})-[:OWNS]->(b:Business)<-[:POSTED_BY]-(j:Job)
                WHERE j.status IS NULL OR j.status <> 'filled'
                RETURN count(j) as active_jobs
            """, {'user_id': user_id})
            active_jobs = active_result[0]['active_jobs'] if active_result else 0
            
            # Get filled jobs
            filled_result = safe_run(session, """
                MATCH (u:User {id: $user_id})-[:OWNS]->(b:Business)<-[:POSTED_BY]-(j:Job)
                WHERE j.status = 'filled'
                RETURN count(j) as filled_jobs
            """, {'user_id': user_id})
            filled_jobs = filled_result[0]['filled_jobs'] if filled_result else 0
            
            # Get total applicants
            applicants_result = safe_run(session, """
                MATCH (u:User {id: $user_id})-[:OWNS]->(b:Business)<-[:POSTED_BY]-(j:Job)<-[:APPLIED_FOR]-(a:JobApplication)
                RETURN count(a) as total_applicants
            """, {'user_id': user_id})
            total_applicants = applicants_result[0]['total_applicants'] if applicants_result else 0
            
            # Get pending applicants (not reviewed)
            pending_result = safe_run(session, """
                MATCH (u:User {id: $user_id})-[:OWNS]->(b:Business)<-[:POSTED_BY]-(j:Job)<-[:APPLIED_FOR]-(a:JobApplication)
                WHERE a.status IS NULL OR a.status = 'pending'
                RETURN count(a) as pending_applicants
            """, {'user_id': user_id})
            pending_applicants = pending_result[0]['pending_applicants'] if pending_result else 0
            
            return {
                'total_jobs': total_jobs,
                'active_jobs': active_jobs,
                'filled_jobs': filled_jobs,
                'total_applicants': total_applicants,
                'pending_applicants': pending_applicants,
                'timestamp': datetime.utcnow().isoformat()
            }
    except Exception as e:
        logger.error(f"Error fetching business owner stats: {e}")
        return {
            'total_jobs': 0,
            'active_jobs': 0,
            'filled_jobs': 0,
            'total_applicants': 0,
            'pending_applicants': 0,
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }


def get_job_seeker_stats(user_id):
    """Get real-time stats for a job seeker"""
    db = get_neo4j_db()
    
    try:
        with db.session() as session:
            # Get applications submitted
            applications_result = safe_run(session, """
                MATCH (u:User {id: $user_id})-[:APPLIED_FOR]->(a:JobApplication)
                RETURN count(a) as total_applications
            """, {'user_id': user_id})
            total_applications = applications_result[0]['total_applications'] if applications_result else 0
            
            # Get accepted applications
            accepted_result = safe_run(session, """
                MATCH (u:User {id: $user_id})-[:APPLIED_FOR]->(a:JobApplication)
                WHERE a.status = 'accepted'
                RETURN count(a) as accepted
            """, {'user_id': user_id})
            accepted = accepted_result[0]['accepted'] if accepted_result else 0
            
            # Get pending applications
            pending_result = safe_run(session, """
                MATCH (u:User {id: $user_id})-[:APPLIED_FOR]->(a:JobApplication)
                WHERE a.status IS NULL OR a.status = 'pending'
                RETURN count(a) as pending
            """, {'user_id': user_id})
            pending = pending_result[0]['pending'] if pending_result else 0
            
            # Get rejected applications
            rejected_result = safe_run(session, """
                MATCH (u:User {id: $user_id})-[:APPLIED_FOR]->(a:JobApplication)
                WHERE a.status = 'rejected'
                RETURN count(a) as rejected
            """, {'user_id': user_id})
            rejected = rejected_result[0]['rejected'] if rejected_result else 0
            
            return {
                'total_applications': total_applications,
                'accepted': accepted,
                'pending': pending,
                'rejected': rejected,
                'timestamp': datetime.utcnow().isoformat()
            }
    except Exception as e:
        logger.error(f"Error fetching job seeker stats: {e}")
        return {
            'total_applications': 0,
            'accepted': 0,
            'pending': 0,
            'rejected': 0,
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }
