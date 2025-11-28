import os
import uuid
from datetime import datetime
from flask import render_template, redirect, url_for, current_app
from flask_login import login_required, current_user

from . import dashboard_bp
from database import get_neo4j_db, safe_run
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
    """Business owner dashboard"""
    db = get_neo4j_db()
    with db.session() as session:
        # Get business statistics
        stats = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:OWNS]->(b:Business)
            OPTIONAL MATCH (b)<-[:REVIEWS]-(r:Review)
            OPTIONAL MATCH (b)-[:POSTED_BY]->(j:Job)
            OPTIONAL MATCH (j)<-[:APPLIED_TO]-(a:JobApplication)
            RETURN count(DISTINCT b) as business_count,
                   count(DISTINCT j) as job_count,
                   count(DISTINCT a) as application_count,
                   avg(r.rating) as avg_rating,
                   count(DISTINCT r) as review_count
        """, {'user_id': current_user.id})
        
        # Get recent job applications
        applications = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:OWNS]->(b:Business)-[:POSTED_BY]->(j:Job)
            MATCH (j)<-[:FOR_JOB]-(a:JobApplication)<-[:APPLIED_TO]-(applicant:User)
            RETURN a, j.title as job_title, applicant.username as applicant_name
            ORDER BY a.created_at DESC LIMIT 5
        """, {'user_id': current_user.id})
        
        # Get verification status
        verification = safe_run(session, """
            MATCH (u:User {id: $user_id})
            OPTIONAL MATCH (u)-[:SUBMITTED]->(v:Verification)
            RETURN u.verification_status as status,
                   v.submitted_at as submitted_at,
                   v.reviewed_at as reviewed_at,
                   v.reviewer_notes as notes
            ORDER BY v.submitted_at DESC LIMIT 1
        """, {'user_id': current_user.id})
    
    return render_template('dashboard/business_owner_dashboard.html',
        stats=stats[0] if stats else {},
        applications=applications,
        verification=verification[0] if verification else {}
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
            RETURN u.verification_status as status,
                   v.submitted_at as submitted_at,
                   v.reviewed_at as reviewed_at,
                   v.reviewer_notes as notes
            ORDER BY v.submitted_at DESC LIMIT 1
        """, {'user_id': current_user.id})
        
        # Get recommended jobs
        recommended_jobs = safe_run(session, """
            MATCH (u:User {id: $user_id})
            OPTIONAL MATCH (u)-[:APPLIED_TO]->(:JobApplication)-[:FOR_JOB]->(appliedJob:Job)
            WITH u, collect(DISTINCT appliedJob.id) AS appliedIds

            MATCH (newJob:Job)-[:POSTED_BY]->(b:Business)
            WHERE newJob.is_active = true
            AND NOT newJob.id IN appliedIds
            RETURN newJob, b.name AS business_name
            ORDER BY newJob.created_at DESC
            LIMIT 5
        """, {'user_id': current_user.id})
    
    return render_template('dashboard/job_seeker_dashboard.html',
        stats=stats[0] if stats else {},
        applications=applications,
        verification=verification[0] if verification else {},
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
            RETURN u.verification_status as status,
                   v.submitted_at as submitted_at,
                   v.reviewed_at as reviewed_at,
                   v.reviewer_notes as notes
            ORDER BY v.submitted_at DESC LIMIT 1
        """, {'user_id': current_user.id})
    
    return render_template('dashboard/service_provider_dashboard.html',
        stats=stats[0] if stats else {},
        bookings=bookings,
        verification=verification[0] if verification else {}
    )