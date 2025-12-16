import os
import logging
import uuid
from datetime import datetime
from flask import render_template, redirect, url_for, current_app

from flask_login import login_required, current_user

from . import dashboard_bp
from database import get_neo4j_db, safe_run, _node_to_dict
from decorators import role_required

logger = logging.getLogger(__name__)

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
        'application_count': 0,
        'filled_jobs': 0,
        'pending_applicants': 0
    }
    applications = []
    businesses = []
    verification = {}
    
    with db.session() as session:
        # Step 1: Get business count (only businesses owned by user)
        business_count_result = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:OWNS]->(b:Business)
            RETURN count(b) as count
        """, {'user_id': current_user.id})
        
        if business_count_result and len(business_count_result) > 0:
            stats['business_count'] = business_count_result[0].get('count', 0)
        
        # Step 2: Get job counts and filled jobs
        job_results = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:OWNS]->(b:Business)
            MATCH (j:Job)-[:POSTED_BY]->(b)
            RETURN 
                sum(CASE WHEN j.is_active = true THEN 1 ELSE 0 END) as active_jobs,
                sum(CASE WHEN j.is_active = false THEN 1 ELSE 0 END) as filled_jobs
        """, {'user_id': current_user.id})
        
        if job_results and len(job_results) > 0:
            stats['job_count'] = job_results[0].get('active_jobs', 0)
            stats['filled_jobs'] = job_results[0].get('filled_jobs', 0)
        
        # Step 3: Get application counts with pending status
        app_results = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:OWNS]->(b:Business)
            MATCH (j:Job)-[:POSTED_BY]->(b)
            MATCH (j)<-[:FOR_JOB]-(a:JobApplication)
            RETURN 
                count(a) as total_applications,
                sum(CASE WHEN a.status = 'pending' THEN 1 ELSE 0 END) as pending_applicants
        """, {'user_id': current_user.id})
        
        if app_results and len(app_results) > 0:
            stats['application_count'] = app_results[0].get('total_applications', 0)
            stats['pending_applicants'] = app_results[0].get('pending_applicants', 0)
        
        # Step 4: Get recent applications with proper formatting
        applications_raw = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:OWNS]->(b:Business)
            MATCH (j:Job)-[:POSTED_BY]->(b)
            MATCH (j)<-[:FOR_JOB]-(a:JobApplication)<-[:APPLIED_TO]-(applicant:User)
            RETURN a, j.title as job_title, applicant.username as applicant_name
            ORDER BY a.created_at DESC 
            LIMIT 5
        """, {'user_id': current_user.id})
        
        if applications_raw:
            applications = applications_raw
        
        # Step 5: Get all businesses with job counts and reviews
        businesses_raw = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:OWNS]->(b:Business)
            OPTIONAL MATCH (j:Job)-[:POSTED_BY]->(b) WHERE j.is_active = true
            OPTIONAL MATCH (b)<-[:REVIEWS]-(r:Review)
            WITH b, count(DISTINCT j) as job_count, count(DISTINCT r) as reviews_count, avg(r.rating) as avg_rating
            RETURN b, job_count, reviews_count, avg_rating
            ORDER BY b.created_at DESC
        """, {'user_id': current_user.id})
        
        if businesses_raw:
            for record in businesses_raw:
                try:
                    business_node = record.get('b')
                    if business_node:
                        business_dict = _node_to_dict(business_node) if hasattr(business_node, '__dict__') else dict(business_node)
                        business_dict['jobs_count'] = record.get('job_count', 0)
                        business_dict['reviews_count'] = record.get('reviews_count', 0)
                        business_dict['rating'] = round(record.get('avg_rating', 0), 1) if record.get('avg_rating') else 0
                        businesses.append(business_dict)
                except Exception as e:
                    logger.error(f"Dashboard: Error processing business: {str(e)}")
        
        # Step 6: Get verification status
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
        
        # Get recent applications with complete job data
        applications_raw = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:APPLIED_TO]->(a:JobApplication)-[:FOR_JOB]->(j:Job)
            MATCH (j)-[:POSTED_BY]->(b:Business)
            RETURN a, j, b.name as business_name
            ORDER BY a.created_at DESC LIMIT 5
        """, {'user_id': current_user.id})
        
        # Format applications with nested job data for template
        applications = []
        for record in applications_raw:
            app_node = record.get('a')
            job_node = record.get('j')
            if app_node and job_node:
                app_dict = _node_to_dict(app_node) if hasattr(app_node, '__dict__') else dict(app_node)
                job_dict = _node_to_dict(job_node) if hasattr(job_node, '__dict__') else dict(job_node)
                app_dict['job'] = job_dict
                app_dict['business_name'] = record.get('business_name', '')
                applications.append(app_dict)
        
        # Get verification status
        verification = safe_run(session, """
            MATCH (u:User {id: $user_id})
            RETURN u.verification_status as status,
                   u.is_verified as is_verified
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
    
    # FIX: Handle empty stats safely
    stats_data = stats[0] if stats and len(stats) > 0 else {
        'total_applications': 0,
        'pending_applications': 0,
        'accepted_applications': 0,
        'rejected_applications': 0
    }
    
    return render_template('dashboard/job_seeker_dashboard.html',
        stats=stats_data,
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

@dashboard_bp.route('/notifications')
@login_required
def notifications():
    """Display notifications page for current user"""
    db = get_neo4j_db()
    notifications_list = []
    unread_count = 0
    
    try:
        with db.session() as session:
            # Get all notifications for current user
            result = safe_run(session, """
                MATCH (n:Notification)
                WHERE n.user_id = $user_id
                RETURN n
                ORDER BY n.created_at DESC
            """, {'user_id': current_user.id})
            
            if result:
                for record in result:
                    node_data = _node_to_dict(record['n'])
                    notifications_list.append(node_data)
                    if not node_data.get('is_read'):
                        unread_count += 1
    except Exception as e:
        logger.error(f"Error loading notifications: {str(e)}")
    
    return render_template('dashboard/notifications.html',
        notifications=notifications_list,
        unread_count=unread_count,
        total_count=len(notifications_list)
    )