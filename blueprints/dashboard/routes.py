import os
import uuid
from datetime import datetime
from flask import render_template, redirect, url_for, current_app
from flask_login import login_required, current_user

from . import dashboard_bp
from database import get_neo4j_db, safe_run, _node_to_dict
from decorators import role_required

@dashboard_bp.route('/')
@login_required
def index():
    """Main dashboard that redirects to role-specific dashboard"""
    if current_user.has_role('business_owner'):
        return redirect(url_for('dashboard.business_owner'))
    elif current_user.has_role('job_seeker'):
        return redirect(url_for('dashboard.job_seeker'))
    elif current_user.has_role('service_provider'):
        return redirect(url_for('dashboard.service_provider'))
    return redirect(url_for('home'))

@dashboard_bp.route('/business-owner')
@login_required
@role_required('business_owner')
def business_owner():
    """Business owner dashboard - fetch all data explicitly from database"""
    db = get_neo4j_db()
    
    # Initialize data
    stats = {
        'business_count': 0,
        'job_count': 0,
        'application_count': 0
    }
    applications = []
    businesses = []
    verification = {}
    
    with db.session() as session:
        # Step 1: Ensure OWNS relationships exist
        logger.info(f"Dashboard: Creating OWNS relationships for user {current_user.id}")
        create_owns = safe_run(session, """
            MATCH (u:User {id: $user_id})
            MATCH (b:Business)
            MERGE (u)-[:OWNS]->(b)
            RETURN count(*) as created
        """, {'user_id': current_user.id})
        
        if create_owns:
            logger.info(f"Dashboard: Created/verified {create_owns[0].get('created', 0)} OWNS relationships")
        
        # Step 2: Get business count
        logger.info("Dashboard: Fetching business count")
        business_count_result = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:OWNS]->(b:Business)
            RETURN count(b) as count
        """, {'user_id': current_user.id})
        
        if business_count_result and len(business_count_result) > 0:
            stats['business_count'] = business_count_result[0].get('count', 0)
            logger.info(f"Dashboard: Found {stats['business_count']} businesses")
        
        # Step 3: Get job count
        logger.info("Dashboard: Fetching job count")
        job_count_result = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:OWNS]->(b:Business)
            MATCH (j:Job)-[:POSTED_BY]->(b)
            WHERE j.is_active = true
            RETURN count(j) as count
        """, {'user_id': current_user.id})
        
        if job_count_result and len(job_count_result) > 0:
            stats['job_count'] = job_count_result[0].get('count', 0)
            logger.info(f"Dashboard: Found {stats['job_count']} jobs")
        
        # Step 4: Get application count
        logger.info("Dashboard: Fetching application count")
        app_count_result = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:OWNS]->(b:Business)
            MATCH (j:Job)-[:POSTED_BY]->(b)
            MATCH (j)<-[:FOR_JOB]-(a:JobApplication)
            RETURN count(a) as count
        """, {'user_id': current_user.id})
        
        if app_count_result and len(app_count_result) > 0:
            stats['application_count'] = app_count_result[0].get('count', 0)
            logger.info(f"Dashboard: Found {stats['application_count']} applications")
        
        # Step 5: Get recent applications with details
        logger.info("Dashboard: Fetching recent applications")
        applications_raw = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:OWNS]->(b:Business)
            MATCH (j:Job)-[:POSTED_BY]->(b)
            MATCH (j)<-[:FOR_JOB]-(a:JobApplication)<-[:APPLIED_TO]-(applicant:User)
            RETURN a as application, 
                   j.title as job_title, 
                   applicant.username as applicant_name,
                   applicant.email as applicant_email
            ORDER BY a.created_at DESC 
            LIMIT 5
        """, {'user_id': current_user.id})
        
        if applications_raw:
            logger.info(f"Dashboard: Processing {len(applications_raw)} applications")
            applications = applications_raw
        
        # Step 6: Get all businesses with their job counts
        logger.info("Dashboard: Fetching businesses")
        businesses_raw = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:OWNS]->(b:Business)
            OPTIONAL MATCH (j:Job)-[:POSTED_BY]->(b) WHERE j.is_active = true
            WITH b, count(j) as job_count
            RETURN b, job_count
            ORDER BY b.created_at DESC
        """, {'user_id': current_user.id})
        
        if businesses_raw:
            logger.info(f"Dashboard: Processing {len(businesses_raw)} businesses")
            for record in businesses_raw:
                try:
                    business_node = record.get('b')
                    if business_node:
                        business_dict = _node_to_dict(business_node) if hasattr(business_node, '__dict__') else dict(business_node)
                        business_dict['jobs_count'] = record.get('job_count', 0)
                        businesses.append(business_dict)
                except Exception as e:
                    logger.error(f"Dashboard: Error processing business: {str(e)}")
        
        # Step 7: Get verification status
        logger.info("Dashboard: Fetching verification status")
        verification_result = safe_run(session, """
            MATCH (u:User {id: $user_id})
            RETURN u.verification_status as status,
                   u.is_verified as is_verified
        """, {'user_id': current_user.id})
        
        if verification_result and len(verification_result) > 0:
            verification = {
                'status': verification_result[0].get('status', 'unverified'),
                'is_verified': verification_result[0].get('is_verified', False)
            }
            logger.info(f"Dashboard: Verification status: {verification['status']}")
    
    logger.info(f"Dashboard: Rendering with stats - businesses: {stats['business_count']}, jobs: {stats['job_count']}, applications: {stats['application_count']}")
    
    return render_template('business/business_owner_dashboard.html',
        stats=stats,
        applications=applications,
        businesses=businesses,
        verification=verification
    )

@dashboard_bp.route('/job-seeker')
@login_required
@role_required('job_seeker')
def job_seeker():
    """Job seeker dashboard"""
    db = get_neo4j_db()
    with db.session() as session:
        # Get application statistics
        stats = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:APPLIED_TO]->(a:JobApplication)
            RETURN count(a) as total_applications,
                   sum(CASE WHEN a.status = 'pending' THEN 1 ELSE 0 END) as pending_applications,
                   sum(CASE WHEN a.status = 'accepted' THEN 1 ELSE 0 END) as accepted_applications,
                   sum(CASE WHEN a.status = 'rejected' THEN 1 ELSE 0 END) as rejected_applications
        """, {'user_id': current_user.id})
        
        # Get recent applications
        applications = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:APPLIED_TO]->(a:JobApplication)-[:FOR_JOB]->(j:Job)
            MATCH (j)-[:POSTED_BY]->(b:Business)
            RETURN a, j.title as job_title, b.name as business_name
            ORDER BY a.created_at DESC LIMIT 5
        """, {'user_id': current_user.id})
        
        # Get verification status
        verification = safe_run(session, """
            MATCH (u:User {id: $user_id})
            OPTIONAL MATCH (u)-[:SUBMITTED]->(v:Verification)
            WITH u, v ORDER BY v.created_at DESC LIMIT 1
            RETURN u.verification_status as status,
                   v.submitted_at as submitted_at,
                   v.reviewed_at as reviewed_at,
                   v.reviewer_notes as notes
        """, {'user_id': current_user.id})
        
        # Get recommended jobs
        recommended_jobs_raw = safe_run(session, """
            MATCH (u:User {id: $user_id})
            OPTIONAL MATCH (u)-[:APPLIED_TO]->(:JobApplication)-[:FOR_JOB]->(appliedJob:Job)
            WITH u, collect(DISTINCT appliedJob.id) AS appliedIds

            MATCH (newJob:Job)-[:POSTED_BY]->(b:Business)
            WHERE newJob.is_active = true
            AND NOT newJob.id IN appliedIds
            RETURN newJob, b.name AS business_name, b.rating AS business_rating
            ORDER BY newJob.created_at DESC
            LIMIT 5
        """, {'user_id': current_user.id})
        
        # Format recommended jobs for template
        recommended_jobs = []
        for record in recommended_jobs_raw:
            job_data = record.get('newJob')
            if job_data:
                recommended_jobs.append({
                    'id': job_data.get('id'),
                    'title': job_data.get('title'),
                    'description': job_data.get('description', ''),
                    'location': job_data.get('location', ''),
                    'created_at': job_data.get('created_at', ''),
                    'business_name': record.get('business_name', ''),
                    'business_rating': record.get('business_rating', 0) or 0
                })
        
        verification_info = verification[0] if verification else {}
        verification_status = verification_info.get('status', 'pending')
    
    return render_template('dashboard/job_seeker_dashboard.html',
        stats=stats[0] if stats else {},
        applications=applications,
        verification=verification_info,
        verification_status=verification_status,
        recommended_jobs=recommended_jobs
    )

@dashboard_bp.route('/service-provider')
@login_required
@role_required('service_provider')
def service_provider():
    """Service provider dashboard"""
    db = get_neo4j_db()
    with db.session() as session:
        # Get service statistics
        stats = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:PROVIDES]->(s:Service)
            OPTIONAL MATCH (s)<-[:REVIEWS]-(r:Review)
            OPTIONAL MATCH (s)<-[:BOOKED]-(b:Booking)
            RETURN count(DISTINCT s) as service_count,
                   count(DISTINCT b) as booking_count,
                   avg(r.rating) as avg_rating,
                   count(DISTINCT r) as review_count
        """, {'user_id': current_user.id})
        
        # Get recent bookings
        bookings = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:PROVIDES]->(s:Service)
            MATCH (s)<-[:FOR_SERVICE]-(b:Booking)<-[:BOOKED]-(client:User)
            RETURN b, s.title as service_title, client.username as client_name
            ORDER BY b.created_at DESC LIMIT 5
        """, {'user_id': current_user.id})
        
        # Get verification status
        verification = safe_run(session, """
            MATCH (u:User {id: $user_id})
            OPTIONAL MATCH (u)-[:SUBMITTED]->(v:Verification)
            WITH u, v ORDER BY v.created_at DESC LIMIT 1
            RETURN u.verification_status as status,
                   v.submitted_at as submitted_at,
                   v.reviewed_at as reviewed_at,
                   v.reviewer_notes as notes
        """, {'user_id': current_user.id})
        
        verification_info = verification[0] if verification else {}
        verification_status = verification_info.get('status', 'pending')
    
    return render_template('dashboard/service_provider_dashboard.html',
        stats=stats[0] if stats else {},
        bookings=bookings,
        verification=verification_info,
        verification_status=verification_status
    )