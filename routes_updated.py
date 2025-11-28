import uuid
import logging
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os

from . import jobs_bp
from database import get_neo4j_db, safe_run, _node_to_dict, _record_to_dict
from models import Job, JobApplication, Business, Service, Review
from forms import JobForm, JobApplicationForm, SearchForm, BusinessForm, ServiceForm, ReviewForm
from decorators import role_required, login_required_optional, json_response, verified_required
from tasks import send_email_task, create_notification_task
from app import cache  # Import the cache extension

logger = logging.getLogger(__name__)

# Business Routes
@jobs_bp.route('/businesses/create', methods=['GET', 'POST'])
@login_required
@role_required('business_owner')
def create_business():
    """Create new business listing"""
    form = BusinessForm()
    
    if form.validate_on_submit():
        business_id = str(uuid.uuid4())
        
        # Handle file upload for business permit
        permit_file = None
        if form.permit_file.data:
            file = form.permit_file.data
            filename = secure_filename(file.filename)
            permit_file = f"businesses/{business_id}/{filename}"
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], permit_file))
        
        business_data = {
            'id': business_id,
            'name': form.name.data,
            'description': form.description.data,
            'category': form.category.data,
            'address': form.address.data,
            'phone': form.phone.data,
            'email': form.email.data,
            'website': form.website.data,
            'permit_number': form.permit_number.data,
            'permit_file': permit_file,
            'owner_id': current_user.id,
            'created_at': datetime.utcnow().isoformat(),
            'is_active': True,
            'is_verified': False
        }
        
        db = get_neo4j_db()
        with db.session() as session:
            safe_run(session, """
                CREATE (b:Business $business_data)
                WITH b
                MATCH (u:User {id: $owner_id})
                CREATE (u)-[:OWNS]->(b)
            """, {'business_data': business_data, 'owner_id': current_user.id})
        
        flash('Business registered successfully! It will be reviewed for verification.', 'success')
        return redirect(url_for('businesses.business_detail', business_id=business_id))
    
    return render_template('businesses_create.html', form=form)

@jobs_bp.route('/businesses/<business_id>/review', methods=['GET', 'POST'])
@login_required
@role_required(['job_seeker', 'service_client'])
def review_business(business_id):
    """Submit review for business"""
    form = ReviewForm()
    
    db = get_neo4j_db()
    with db.session() as session:
        # Get business details
        business_result = safe_run(session, """
            MATCH (b:Business {id: $business_id})
            RETURN b
        """, {'business_id': business_id})
        
        if not business_result:
            flash('Business not found.', 'error')
            return redirect(url_for('businesses.list_businesses'))
        
        business_data = _node_to_dict(business_result[0]['b'])
        business = Business(**business_data)
        
        # Check if user has already reviewed this business
        existing_review = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:REVIEWS]->(r:Review)-[:FOR_BUSINESS]->(b:Business {id: $business_id})
            RETURN count(*) as count
        """, {'user_id': current_user.id, 'business_id': business_id})
        
        if existing_review[0]['count'] > 0:
            flash('You have already reviewed this business.', 'warning')
            return redirect(url_for('businesses.business_detail', business_id=business_id))
    
    if form.validate_on_submit():
        review_id = str(uuid.uuid4())
        review_data = {
            'id': review_id,
            'rating': form.rating.data,
            'comment': form.comment.data,
            'user_id': current_user.id,
            'user_name': current_user.username,
            'business_id': business_id,
            'created_at': datetime.utcnow().isoformat()
        }
        
        with db.session() as session:
            safe_run(session, """
                CREATE (r:Review $review_data)
                WITH r
                MATCH (u:User {id: $user_id}), (b:Business {id: $business_id})
                CREATE (u)-[:REVIEWS]->(r)-[:FOR_BUSINESS]->(b)
            """, {
                'review_data': review_data,
                'user_id': current_user.id,
                'business_id': business_id
            })
        
        flash('Review submitted successfully!', 'success')
        return redirect(url_for('businesses.business_detail', business_id=business_id))
    
    return render_template('businesses_review.html', form=form, business=business)

@jobs_bp.route('/businesses/<business_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('business_owner')
def edit_business(business_id):
    """Edit existing business listing"""
    db = get_neo4j_db()
    
    with db.session() as session:
        # Check ownership
        ownership = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:OWNS]->(b:Business {id: $business_id})
            RETURN b
        """, {'user_id': current_user.id, 'business_id': business_id})
        
        if not ownership:
            flash('You do not have permission to edit this business.', 'error')
            return redirect(url_for('businesses.list_businesses'))
        
        business_data = _node_to_dict(ownership[0]['b'])
        business = Business(**business_data)
    
    
    if form.validate_on_submit():
        # Handle file upload if new permit is provided
        permit_file = business.permit_file  # Keep existing file
        if form.permit_file.data:
            file = form.permit_file.data
            filename = secure_filename(file.filename)
            permit_file = f"businesses/{business_id}/{filename}"
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], permit_file))
        
        update_data = {
            'name': form.name.data,
            'description': form.description.data,
            'category': form.category.data,
            'address': form.address.data,
            'phone': form.phone.data,
            'email': form.email.data,
            'website': form.website.data,
            'permit_number': form.permit_number.data,
            'permit_file': permit_file,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        with db.session() as session:
            safe_run(session, """
                MATCH (b:Business {id: $business_id})
                SET b += $update_data
            """, {'business_id': business_id, 'update_data': update_data})
        
        flash('Business updated successfully!', 'success')
        return redirect(url_for('businesses.business_detail', business_id=business_id))
    
    return render_template('businesses_edit.html', form=form, business=business)

@jobs_bp.route('/dashboard/business-owner')
@login_required
@role_required('business_owner')
def business_owner_dashboard():
    """Business owner dashboard"""
    db = get_neo4j_db()
    
    with db.session() as session:
        # Get user's businesses
        businesses = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:OWNS]->(b:Business)
            OPTIONAL MATCH (b)-[:POSTED_BY]->(j:Job)
            OPTIONAL MATCH (b)-[:OFFERS]->(s:Service)
            OPTIONAL MATCH (b)<-[:REVIEWS]-(r:Review)
            RETURN b, 
                   count(DISTINCT j) as jobs_count,
                   count(DISTINCT s) as services_count,
                   count(DISTINCT r) as reviews_count,
                   avg(r.rating) as average_rating
            ORDER BY b.created_at DESC
        """, {'user_id': current_user.id})
        
        # Get recent applications
        recent_applications = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:OWNS]->(b:Business)-[:POSTED_BY]->(j:Job)
            MATCH (a:JobApplication)-[:FOR_JOB]->(j)
            MATCH (a)<-[:APPLIED_TO]-(applicant:User)
            RETURN a, j.title as job_title, applicant.username as applicant_name
            ORDER BY a.created_at DESC
            LIMIT 5
        """, {'user_id': current_user.id})
        
        # Get statistics
        stats = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:OWNS]->(b:Business)
            OPTIONAL MATCH (b)-[:POSTED_BY]->(j:Job)
            OPTIONAL MATCH (b)-[:OFFERS]->(s:Service)
            OPTIONAL MATCH (a:JobApplication)-[:FOR_JOB]->(j)
            RETURN count(DISTINCT b) as total_businesses,
                   count(DISTINCT j) as active_jobs,
                   count(DISTINCT a) as total_applications,
                   count(DISTINCT s) as active_services
        """, {'user_id': current_user.id})
        
        stats_data = stats[0] if stats else {}
    
    return render_template('business_owner_dashboard.html',
                         businesses=businesses,
                         recent_applications=recent_applications,
                         stats=stats_data)

# Job Routes
            flash('Job not found.', 'error')
            return redirect(url_for('jobs.list_jobs'))
        
        record = result[0]
        job_data = _node_to_dict(record['j'])
        job_data['business_name'] = record['b']['name']
        job_data['business_id'] = record['b']['id']
        job_data['business_rating'] = record['avg_rating'] or 0
        job_data['business_review_count'] = record['review_count'] or 0
        
        job = Job(**job_data)
        
        # Get business info
        business_result = safe_run(session, """
            MATCH (b:Business {id: $business_id})
            OPTIONAL MATCH (b)<-[:REVIEWS]-(r:Review)
            WITH b, avg(r.rating) as avg_rating, count(r) as review_count
            RETURN b, avg_rating, review_count
        """, {'business_id': job.business_id})
        
        business = None
        if business_result:
            business_data = _node_to_dict(business_result[0]['b'])
            business_data['rating'] = business_result[0]['avg_rating'] or 0
            business_data['review_count'] = business_result[0]['review_count'] or 0
            business = Business(**business_data)
        
        # Check if user has already applied
        has_applied = False
        if current_user.is_authenticated:
            application = safe_run(session, """
                MATCH (u:User {id: $user_id})-[:APPLIED_TO]->(j:Job {id: $job_id})
                RETURN count(*) as count
            """, {'user_id': current_user.id, 'job_id': job_id})
            has_applied = application[0]['count'] > 0
    
    return render_template('job_detail.html', job=job, business=business, has_applied=has_applied)

@jobs_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required('business_owner')
def create_job():
    """Create new job posting"""
    form = JobForm()
    
    # Get user's businesses
    db = get_neo4j_db()
    with db.session() as session:
        businesses = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:OWNS]->(b:Business)
            WHERE b.is_verified = true AND b.is_active = true
            RETURN b
        """, {'user_id': current_user.id})
        
        if not businesses:
            flash('You need to create and verify a business before posting jobs.', 'warning')
            return redirect(url_for('businesses.create_business'))
        
        # Populate business choices
        form.business_id.choices = [(b['b']['id'], b['b']['name']) for b in businesses]
    
    if form.validate_on_submit():
        job_id = str(uuid.uuid4())
        
        # Handle file upload for requirements document
        requirements_file = None
        if form.requirements_file.data:
            file = form.requirements_file.data
            filename = secure_filename(file.filename)
            requirements_file = f"jobs/{job_id}/{filename}"
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], requirements_file))
        
        job_data = {
            'id': job_id,
            'title': form.title.data,
            'description': form.description.data,
            'category': form.category.data,
            'type': form.type.data,
            'salary_min': float(form.salary_min.data) if form.salary_min.data else None,
            'salary_max': float(form.salary_max.data) if form.salary_max.data else None,
            'currency': form.currency.data,
            'location': form.location.data,
            'business_id': form.business_id.data,
            'requirements': form.requirements.data,
            'benefits': form.benefits.data,
            'expires_at': form.expires_at.data.isoformat() if form.expires_at.data else None,
            'created_at': datetime.utcnow().isoformat(),
            'is_active': True
        }
        
        # Create job
        with db.session() as session:
            safe_run(session, """
                CREATE (j:Job $job_data)
                WITH j
                MATCH (b:Business {id: $business_id})
                CREATE (b)-[:POSTED_BY]->(j)
            """, {'job_data': job_data, 'business_id': form.business_id.data})
        
        flash('Job posted successfully!', 'success')
        return redirect(url_for('jobs.job_detail', job_id=job_id))
    
    return render_template('jobs_create.html', form=form)

@jobs_bp.route('/<job_id>/apply', methods=['POST'])
@login_required
@role_required('job_seeker')
def apply_job(job_id):
    """Apply for a job"""
    cover_letter = request.form.get('cover_letter', '')
    resume_file = request.files.get('resume')
    
    if not resume_file or resume_file.filename == '':
        return jsonify({'error': 'Resume is required'}), 400
    
    # Validate file
    if not allowed_file(resume_file.filename):
        return jsonify({'error': 'Invalid file type. Only PDF, DOC, DOCX files are allowed'}), 400
    
    db = get_neo4j_db()
    with db.session() as session:
        # Check if job exists and is active
        job_result = safe_run(session, """
            MATCH (j:Job {id: $job_id})
            WHERE j.is_active = true
            RETURN j
        """, {'job_id': job_id})
        
        if not job_result:
            return jsonify({'error': 'Job not found or no longer active'}), 404
        
        # Check if already applied
        existing = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:APPLIED_TO]->(j:Job {id: $job_id})
            RETURN count(*) as count
        """, {'user_id': current_user.id, 'job_id': job_id})
        
        if existing[0]['count'] > 0:
            return jsonify({'error': 'You have already applied for this job'}), 400
        
        # Save resume file
        filename = secure_filename(resume_file.filename)
        resume_path = f"applications/{current_user.id}/{job_id}/{filename}"
        full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], resume_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        resume_file.save(full_path)
        
        # Create application
        application_id = str(uuid.uuid4())
        application_data = {
            'id': application_id,
            'job_id': job_id,
            'applicant_id': current_user.id,
            'applicant_name': current_user.username,
            'cover_letter': cover_letter,
            'resume_file': resume_path,
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat()
        }
        
        safe_run(session, """
            CREATE (a:JobApplication $application_data)
            WITH a
            MATCH (u:User {id: $user_id}), (j:Job {id: $job_id})
            CREATE (u)-[:APPLIED_TO]->(a)-[:FOR_JOB]->(j)
        """, {
            'application_data': application_data,
            'user_id': current_user.id,
            'job_id': job_id
        })
        
        # Update job applications count
        safe_run(session, """
            MATCH (j:Job {id: $job_id})
            SET j.applications_count = coalesce(j.applications_count, 0) + 1
        """, {'job_id': job_id})
        
        # Get business owner for notification
        business_result = safe_run(session, """
            MATCH (b:Business)-[:POSTED_BY]->(j:Job {id: $job_id})
            MATCH (b)<-[:OWNS]-(owner:User)
            RETURN owner.id as owner_id, j.title as job_title
        """, {'job_id': job_id})
        
        if business_result:
            owner_id = business_result[0]['owner_id']
            job_title = business_result[0]['job_title']
            
            # Create notification for business owner
            create_notification_task.delay(
                user_id=owner_id,
                type='job_application',
                title='New Job Application',
                message=f'{current_user.username} has applied for {job_title}',
                data={
                    'application_id': application_id,
                    'job_id': job_id,
                    'applicant_id': current_user.id
                }
            )
    
    return jsonify({'message': 'Application submitted successfully'})

@jobs_bp.route('/applications')
@login_required
def my_applications():
    """View user's job applications"""
    db = get_neo4j_db()
    with db.session() as session:
        applications = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:APPLIED_TO]->(a:JobApplication)-[:FOR_JOB]->(j:Job)
            MATCH (j)-[:POSTED_BY]->(b:Business)
            RETURN a, j, b.name as business_name
            ORDER BY a.created_at DESC
        """, {'user_id': current_user.id})
        
        application_list = []
        for record in applications:
            app_data = _node_to_dict(record['a'])
            job_data = _node_to_dict(record['j'])
            app_data['job'] = job_data
            app_data['business_name'] = record['business_name']
            application_list.append(app_data)
    
    return render_template('jobs_applications.html', applications=application_list)

@jobs_bp.route('/<job_id>/close', methods=['POST'])
@login_required
def close_job(job_id):
    """Close job posting (business owner only)"""
    db = get_neo4j_db()
    with db.session() as session:
        # Check ownership
        ownership = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:OWNS]->(b:Business)-[:POSTED_BY]->(j:Job {id: $job_id})
            RETURN count(*) as count
        """, {'user_id': current_user.id, 'job_id': job_id})
        
        if ownership[0]['count'] == 0:
            return jsonify({'error': 'You do not have permission to close this job'}), 403
        
        # Close job
        safe_run(session, """
            MATCH (j:Job {id: $job_id})
            SET j.is_active = false
        """, {'job_id': job_id})
    
    return jsonify({'message': 'Job closed successfully'})

# Service Routes
@jobs_bp.route('/services/create', methods=['GET', 'POST'])
@login_required
@role_required(['business_owner', 'service_provider'])
def create_service():
    """Create new service offering"""
    form = ServiceForm()
    
    if form.validate_on_submit():
        service_id = str(uuid.uuid4())
        
        service_data = {
            'id': service_id,
            'title': form.title.data,
            'description': form.description.data,
            'category': form.category.data,
            'price': float(form.price.data),
            'price_type': form.price_type.data,
            'location': form.location.data,
            'duration': form.duration.data,
            'requirements': form.requirements.data,
            'provider_id': current_user.id,
            'created_at': datetime.utcnow().isoformat(),
            'is_active': True,
            'is_verified': False
        }
        
        db = get_neo4j_db()
        with db.session() as session:
            safe_run(session, """
                CREATE (s:Service $service_data)
                WITH s
                MATCH (u:User {id: $provider_id})
                CREATE (u)-[:PROVIDES]->(s)
            """, {'service_data': service_data, 'provider_id': current_user.id})
        
        flash('Service created successfully!', 'success')
        return redirect(url_for('services.service_detail', service_id=service_id))
    
    return render_template('services_create.html', form=form)

@jobs_bp.route('/services/<service_id>/review', methods=['GET', 'POST'])
@login_required
@role_required(['job_seeker', 'service_client'])
def review_service(service_id):
    """Submit review for service"""
    form = ReviewForm()
    
    db = get_neo4j_db()
    with db.session() as session:
        # Get service details
        service_result = safe_run(session, """
            MATCH (s:Service {id: $service_id})
            RETURN s
        """, {'service_id': service_id})
        
        if not service_result:
            flash('Service not found.', 'error')
            return redirect(url_for('services.list_services'))
        
        service_data = _node_to_dict(service_result[0]['s'])
        service = Service(**service_data)
        
        # Check if user has already reviewed this service
        existing_review = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:REVIEWS]->(r:Review)-[:FOR_SERVICE]->(s:Service {id: $service_id})
            RETURN count(*) as count
        """, {'user_id': current_user.id, 'service_id': service_id})
        
        if existing_review[0]['count'] > 0:
            flash('You have already reviewed this service.', 'warning')
            return redirect(url_for('services.service_detail', service_id=service_id))
    
    if form.validate_on_submit():
        review_id = str(uuid.uuid4())
        review_data = {
            'id': review_id,
            'rating': form.rating.data,
            'comment': form.comment.data,
            'user_id': current_user.id,
            'user_name': current_user.username,
            'service_id': service_id,
            'created_at': datetime.utcnow().isoformat()
        }
        
        with db.session() as session:
            safe_run(session, """
                CREATE (r:Review $review_data)
                WITH r
                MATCH (u:User {id: $user_id}), (s:Service {id: $service_id})
                CREATE (u)-[:REVIEWS]->(r)-[:FOR_SERVICE]->(s)
            """, {
                'review_data': review_data,
                'user_id': current_user.id,
                'service_id': service_id
            })
        
        flash('Review submitted successfully!', 'success')
        return redirect(url_for('services.service_detail', service_id=service_id))
    
    return render_template('services_review.html', form=form, service=service)

@jobs_bp.route('/services/my-services')
@login_required
@role_required(['business_owner', 'service_provider'])
def my_services():
    """View user's created services"""
    db = get_neo4j_db()
    with db.session() as session:
        services = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:PROVIDES]->(s:Service)
            OPTIONAL MATCH (s)<-[:REVIEWS]-(r:Review)
            OPTIONAL MATCH (s)<-[:BOOKED]-(b:Booking)
            RETURN s, 
                   avg(r.rating) as average_rating,
                   count(DISTINCT r) as reviews_count,
                   count(DISTINCT b) as bookings_count,
                   max(b.created_at) as last_booking
            ORDER BY s.created_at DESC
        """, {'user_id': current_user.id})
        
        # Get statistics
        stats = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:PROVIDES]->(s:Service)
            OPTIONAL MATCH (s)<-[:REVIEWS]-(r:Review)
            RETURN count(DISTINCT s) as total_services,
                   sum(CASE WHEN s.is_active = true THEN 1 ELSE 0 END) as active_services,
                   count(DISTINCT r) as total_reviews,
                   avg(r.rating) as average_rating
        """, {'user_id': current_user.id})
        
        stats_data = stats[0] if stats else {}
        
        service_list = []
        for record in services:
            service_data = _node_to_dict(record['s'])
            service_data['average_rating'] = record['average_rating'] or 0
            service_data['reviews_count'] = record['reviews_count'] or 0
            service_data['bookings_count'] = record['bookings_count'] or 0
            service_data['last_booking'] = record['last_booking']
            service_list.append(Service(**service_data))
    
    return render_template('services_my_services.html',
                         services=service_list,
                         stats=stats_data)

@jobs_bp.route('/services/<service_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required(['business_owner', 'service_provider'])
def edit_service(service_id):
    """Edit existing service offering"""
    db = get_neo4j_db()
    
    with db.session() as session:
        # Check ownership
        ownership = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:PROVIDES]->(s:Service {id: $service_id})
            RETURN s
        """, {'user_id': current_user.id, 'service_id': service_id})
        
        if not ownership:
            flash('You do not have permission to edit this service.', 'error')
            return redirect(url_for('services.list_services'))
        
        service_data = _node_to_dict(ownership[0]['s'])
        service = Service(**service_data)
    
    form = ServiceForm(obj=service)
    
    if form.validate_on_submit():
        update_data = {
            'title': form.title.data,
            'description': form.description.data,
            'category': form.category.data,
            'price': float(form.price.data),
            'price_type': form.price_type.data,
            'location': form.location.data,
            'duration': form.duration.data,
            'requirements': form.requirements.data,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        with db.session() as session:
            safe_run(session, """
                MATCH (s:Service {id: $service_id})
                SET s += $update_data
            """, {'service_id': service_id, 'update_data': update_data})
        
        flash('Service updated successfully!', 'success')
        return redirect(url_for('services.service_detail', service_id=service_id))
    
    return render_template('services_edit.html', form=form, service=service)
@jobs_bp.route('/services/<service_id>/toggle-status', methods=['POST'])
@login_required
@role_required(['business_owner', 'service_provider'])
def toggle_service_status(service_id):
    """Toggle service active status"""
    db = get_neo4j_db()
    with db.session() as session:
        # Check ownership
        ownership = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:PROVIDES]->(s:Service {id: $service_id})
            RETURN s.is_active as is_active
        """, {'user_id': current_user.id, 'service_id': service_id})
        
        if not ownership:
            return jsonify({'error': 'You do not have permission to modify this service'}), 403
        
        current_status = ownership[0]['is_active']
        new_status = not current_status
        
        # Update status
        safe_run(session, """
            MATCH (s:Service {id: $service_id})
            SET s.is_active = $new_status
        """, {'service_id': service_id, 'new_status': new_status})
    
    action = 'activated' if new_status else 'paused'
    return jsonify({'message': f'Service {action} successfully'})

# Verification Routes
@jobs_bp.route('/verification/upload', methods=['GET', 'POST'])
@login_required
def upload_verification_documents():
    """Upload verification documents"""
    from forms import VerificationForm
    
    form = VerificationForm()
    
    if form.validate_on_submit():
        db = get_neo4j_db()
        
        with db.session() as session:
            # Create verification record
            verification_id = str(uuid.uuid4())
            verification_data = {
                'id': verification_id,
                'user_id': current_user.id,
                'status': 'pending',
                'created_at': datetime.utcnow().isoformat()
            }
            
            # Handle file uploads based on user role
            files_uploaded = []
            
            # Always require ID document
            if form.id_document.data:
                file = form.id_document.data
                filename = secure_filename(file.filename)
                file_path = f"verification/{current_user.id}/{verification_id}/{filename}"
                full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                file.save(full_path)
                files_uploaded.append({'type': 'id', 'path': file_path})
            
            # Role-specific documents
            if current_user.role == 'business_owner':
                if form.business_permit.data:
                    file = form.business_permit.data
                    filename = secure_filename(file.filename)
                    file_path = f"verification/{current_user.id}/{verification_id}/{filename}"
                    full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file_path)
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    file.save(full_path)
                    files_uploaded.append({'type': 'business_permit', 'path': file_path})
                
                verification_data['business_address'] = form.business_address.data
                verification_data['permit_number'] = form.permit_number.data
                
            elif current_user.role == 'job_seeker':
                if form.resume.data:
                    file = form.resume.data
                    filename = secure_filename(file.filename)
                    file_path = f"verification/{current_user.id}/{verification_id}/{filename}"
                    full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file_path)
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    file.save(full_path)
                    files_uploaded.append({'type': 'resume', 'path': file_path})
            
            verification_data['documents'] = files_uploaded
            
            # Create verification record
            safe_run(session, """
                CREATE (v:Verification $verification_data)
                WITH v
                MATCH (u:User {id: $user_id})
                CREATE (u)-[:SUBMITTED]->(v)
            """, {'verification_data': verification_data, 'user_id': current_user.id})
        
        flash('Verification documents submitted successfully! You will be notified once reviewed.', 'success')
        return jsonify({'message': 'Documents submitted successfully', 'redirect_url': url_for('dashboard')})
    
    return render_template('verification_upload.html', form=form)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']