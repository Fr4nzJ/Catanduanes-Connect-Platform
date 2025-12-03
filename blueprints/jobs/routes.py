"""
Complete Job Management Routes for Catanduanes Connect Platform
- Job Listing with Map Integration
- Job Details
- Job Application
- Job Sorting & Filtering
- Email Notifications
"""

import uuid
import json
import logging
import os
from datetime import datetime, timedelta
from flask import render_template, request, redirect, url_for, flash, jsonify, current_app, g
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from . import jobs_bp
from database import get_neo4j_db, safe_run, _node_to_dict
from models import Job, JobApplication, Business, User
from forms import JobForm, JobApplicationForm, SearchForm
from decorators import role_required, login_required_optional, json_response, verified_required
from tasks import send_email_task, create_notification_task
from extensions import csrf

logger = logging.getLogger(__name__)

# ============================================================================
# JOB LISTING & FILTERING ROUTES
# ============================================================================

@jobs_bp.route('/')
@jobs_bp.route('/list')
@login_required_optional
def list_jobs():
    """
    List all jobs with advanced filtering, sorting, and map markers
    
    Query parameters:
    - q: search query
    - category: filter by category
    - type: filter by job type (full_time, part_time, etc.)
    - setup: filter by work setup (on_site, remote, hybrid)
    - salary_min: minimum salary
    - salary_max: maximum salary
    - location: filter by location
    - sort: sorting option (latest, salary_high, salary_low, alphabetical)
    - page: pagination page number
    """
    
    # Get form parameters
    search_query = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    job_type = request.args.get('type', '').strip()
    setup = request.args.get('setup', '').strip()
    salary_min = request.args.get('salary_min', type=int)
    salary_max = request.args.get('salary_max', type=int)
    location = request.args.get('location', '').strip()
    sort_by = request.args.get('sort', 'latest')
    page = request.args.get('page', 1, type=int)
    view = request.args.get('view', 'grid')  # grid or list or map
    
    per_page = 12
    skip = (page - 1) * per_page
    
    db = get_neo4j_db()
    with db.session() as session:
        # Build base query
        query = """
            MATCH (j:Job)-[:POSTED_BY]->(b:Business)
            WHERE j.is_active = true
        """
        params = {
            'skip': skip,
            'per_page': per_page
        }
        
        # Add search filters
        if search_query:
            query += " AND (j.title CONTAINS $search OR j.description CONTAINS $search OR b.name CONTAINS $search)"
            params['search'] = search_query
        
        if category:
            query += " AND j.category = $category"
            params['category'] = category
        
        if job_type:
            query += " AND j.type = $job_type"
            params['job_type'] = job_type
        
        if setup:
            query += " AND j.setup = $setup"
            params['setup'] = setup
        
        if salary_min:
            query += " AND (j.salary_min IS NULL OR j.salary_min >= $salary_min)"
            params['salary_min'] = salary_min
        
        if salary_max:
            query += " AND (j.salary_max IS NULL OR j.salary_max <= $salary_max)"
            params['salary_max'] = salary_max
        
        if location:
            query += " AND j.location CONTAINS $location"
            params['location'] = location
        
        # Add sorting
        sort_clause = ""
        if sort_by == 'salary_high':
            sort_clause = " ORDER BY j.salary_max DESC, j.salary_min DESC"
        elif sort_by == 'salary_low':
            sort_clause = " ORDER BY j.salary_min ASC"
        elif sort_by == 'alphabetical':
            sort_clause = " ORDER BY j.title ASC"
        else:  # latest
            sort_clause = " ORDER BY j.created_at DESC"
        
        # Execute query
        query += sort_clause + " SKIP $skip LIMIT $per_page"
        query += """
            RETURN j, b.id as business_id, b.name as business_name, b.latitude as business_lat, b.longitude as business_lng
        """
        
        jobs_result = safe_run(session, query, params)
        
        # Get total count
        count_query = """
            MATCH (j:Job)-[:POSTED_BY]->(b:Business)
            WHERE j.is_active = true
        """
        count_params = {}
        
        if search_query:
            count_query += " AND (j.title CONTAINS $search OR j.description CONTAINS $search OR b.name CONTAINS $search)"
            count_params['search'] = search_query
        
        if category:
            count_query += " AND j.category = $category"
            count_params['category'] = category
        
        if job_type:
            count_query += " AND j.type = $job_type"
            count_params['job_type'] = job_type
        
        if setup:
            count_query += " AND j.setup = $setup"
            count_params['setup'] = setup
        
        if location:
            count_query += " AND j.location CONTAINS $location"
            count_params['location'] = location
        
        count_query += " RETURN count(j) as total"
        
        count_result = safe_run(session, count_query, count_params)
        total = count_result[0]['total'] if count_result else 0
        
        # Get category counts
        categories_result = safe_run(session, """
            MATCH (j:Job)
            WHERE j.is_active = true
            RETURN j.category as category, count(j) as count
            ORDER BY count DESC
        """, {})
        
        category_counts = {}
        for record in categories_result:
            if record['category']:
                category_counts[record['category']] = record['count']
        
        # Convert results to Job objects
        jobs_list = []
        map_markers = []
        
        for record in jobs_result:
            job_data = _node_to_dict(record['j'])
            job_data['business_id'] = record['business_id']
            job_data['business_name'] = record['business_name']
            
            # Use business coordinates for job location on map
            if record['business_lat'] and record['business_lng']:
                job_data['latitude'] = record['business_lat']
                job_data['longitude'] = record['business_lng']
            
            job = Job(**job_data)
            jobs_list.append(job)
            
            # Add marker data for map
            if job.latitude and job.longitude:
                map_markers.append({
                    'id': job.id,
                    'title': job.title,
                    'business': job.business_name,
                    'lat': float(job.latitude),
                    'lng': float(job.longitude),
                    'salary': job.salary_range_display,
                    'type': job.type_display,
                    'url': url_for('jobs.job_detail', job_id=job.id)
                })
    
    pages = (total + per_page - 1) // per_page
    
    # Prepare jobs data for map (with display properties)
    jobs_data = []
    for job in jobs_list:
        job_dict = {
            'id': job.id,
            'title': job.title,
            'business_name': job.business_name,
            'type_display': job.type_display,
            'setup_display': job.setup_display,
            'salary_range_display': job.salary_range_display,
            'location': job.location,
            'latitude': job.latitude,
            'longitude': job.longitude
        }
        jobs_data.append(job_dict)
    
    return render_template('jobs/jobs_list.html',
        jobs=jobs_list,
        jobs_data=jobs_data,
        map_markers=json.dumps(map_markers),
        total_jobs=total,
        current_page=page,
        total_pages=pages,
        per_page=per_page,
        category_counts=category_counts,
        search_query=search_query,
        category=category,
        job_type=job_type,
        setup=setup,
        location=location,
        sort_by=sort_by,
        view=view,
        has_results=len(jobs_list) > 0
    )

# ============================================================================
# JOB DETAIL ROUTE
# ============================================================================

@jobs_bp.route('/<job_id>')
@jobs_bp.route('/<job_id>/detail')
@login_required_optional
def job_detail(job_id):
    """Display detailed job information"""
    
    db = get_neo4j_db()
    with db.session() as session:
        # Get job and business details
        result = safe_run(session, """
            MATCH (j:Job {id: $job_id})-[:POSTED_BY]->(b:Business)
            OPTIONAL MATCH (b)<-[:REVIEWS]-(r:Review)
            WITH j, b, avg(r.rating) as avg_rating, count(r) as review_count
            RETURN j, b, avg_rating, review_count
        """, {'job_id': job_id})
        
        if not result:
            flash('Job not found.', 'error')
            return redirect(url_for('jobs.list_jobs'))
        
        record = result[0]
        job_data = _node_to_dict(record['j'])
        job_data['business_id'] = record['b']['id']
        job_data['business_name'] = record['b']['name']
        job_data['business_rating'] = record['avg_rating'] or 0.0
        job_data['business_review_count'] = record['review_count'] or 0
        
        job = Job(**job_data)
        
        business_data = _node_to_dict(record['b'])
        business_data['rating'] = record['avg_rating'] or 0.0
        business_data['review_count'] = record['review_count'] or 0
        business = Business(**business_data)
        
        # Check if user has applied
        has_applied = False
        if current_user.is_authenticated:
            has_applied_result = safe_run(session, """
                MATCH (u:User {id: $user_id})-[:APPLIED_TO]->(:JobApplication)-[:FOR_JOB]->(j:Job {id: $job_id})
                RETURN count(*) as count
            """, {'user_id': current_user.id, 'job_id': job_id})
            has_applied = has_applied_result[0]['count'] > 0 if has_applied_result else False
        
        # Get similar jobs (same category, same business)
        similar_jobs_result = safe_run(session, """
            MATCH (j:Job {id: $job_id})-[:POSTED_BY]->(b:Business)
            MATCH (other:Job)-[:POSTED_BY]->(b)
            WHERE other.id <> j.id AND other.is_active = true
            RETURN other
            LIMIT 3
        """, {'job_id': job_id})
        
        similar_jobs = []
        for rec in similar_jobs_result:
            job_data = _node_to_dict(rec['other'])
            job_data['business_name'] = business.name
            job_data['business_id'] = business.id
            similar_jobs.append(Job(**job_data))
    
    return render_template('jobs/job_detail.html',
        job=job,
        business=business,
        has_applied=has_applied,
        similar_jobs=similar_jobs
    )

# ============================================================================
# JOB APPLICATION ROUTES
# ============================================================================

@jobs_bp.route('/<job_id>/apply', methods=['GET', 'POST'])
@login_required
@role_required('job_seeker')
def apply_job(job_id):
    """Apply for a job"""
    
    if request.method == 'GET':
        # Check if job exists
        db = get_neo4j_db()
        with db.session() as session:
            job_result = safe_run(session, """
                MATCH (j:Job {id: $job_id})-[:POSTED_BY]->(b:Business)
                WHERE j.is_active = true
                RETURN j, b.name as business_name
            """, {'job_id': job_id})
            
            if not job_result:
                flash('Job not found.', 'error')
                return redirect(url_for('jobs.list_jobs'))
            
            job_data = _node_to_dict(job_result[0]['j'])
            job_data['business_name'] = job_result[0]['business_name']
            job = Job(**job_data)
        
        return render_template('jobs/job_apply.html', job=job)
    
    # POST request - handle application submission
    db = get_neo4j_db()
    with db.session() as session:
        # Check if job exists and is active
        job_result = safe_run(session, """
            MATCH (j:Job {id: $job_id})-[:POSTED_BY]->(b:Business)
            WHERE j.is_active = true
            RETURN j, b.id as business_id, b.email as business_email, u as owner
            MATCH (b)<-[:OWNS]-(u:User)
            RETURN j, b.id as business_id, b.name as business_name, b.email as business_email, u.email as owner_email, u.id as owner_id
        """, {'job_id': job_id})
        
        if not job_result:
            flash('Job not found or no longer active.', 'error')
            return redirect(url_for('jobs.list_jobs'))
        
        # Check if already applied
        existing_result = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:APPLIED_TO]->(:JobApplication)-[:FOR_JOB]->(j:Job {id: $job_id})
            RETURN count(*) as count
        """, {'user_id': current_user.id, 'job_id': job_id})
        
        if existing_result[0]['count'] > 0:
            flash('You have already applied for this job.', 'warning')
            return redirect(url_for('jobs.job_detail', job_id=job_id))
        
        cover_letter = request.form.get('cover_letter', '').strip()
        cv_file = request.files.get('cv')
        
        # Validate CV
        if not cv_file or cv_file.filename == '':
            return jsonify({'error': 'CV is required.'}), 400
        
        # Save CV file
        filename = secure_filename(cv_file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        if file_ext not in ['pdf', 'doc', 'docx', 'txt']:
            return jsonify({'error': 'Only PDF, DOC, DOCX, and TXT files are allowed.'}), 400
        
        # Create application
        application_id = str(uuid.uuid4())
        cv_filename = f"{application_id}.{file_ext}"
        cv_path = f"applications/{current_user.id}/{job_id}/{cv_filename}"
        
        full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], cv_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        try:
            cv_file.save(full_path)
        except Exception as e:
            logger.error(f"Failed to save CV: {str(e)}")
            return jsonify({'error': 'Failed to save CV. Please try again.'}), 500
        
        # Fetch user's resume from database
        user_resume = safe_run(session, """
            MATCH (u:User {id: $user_id})
            RETURN u.resume_data as resume_data
        """, {'user_id': current_user.id})
        
        user_resume_data = user_resume[0]['resume_data'] if user_resume and user_resume[0]['resume_data'] else None
        
        # Create application in database
        application_data = {
            'id': application_id,
            'uuid': str(uuid.uuid4()),
            'job_id': job_id,
            'job_title': job_result[0]['j']['title'],
            'business_id': job_result[0]['business_id'],
            'business_name': job_result[0]['business_name'],
            'applicant_id': current_user.id,
            'applicant_name': current_user.username,
            'applicant_email': current_user.email,
            'applicant_phone': current_user.phone or '',
            'cover_letter': cover_letter,
            'cv_file': cv_path,
            'resume_data': user_resume_data,
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        safe_run(session, """
            CREATE (a:JobApplication $app_data)
            WITH a
            MATCH (u:User {id: $user_id}), (j:Job {id: $job_id})
            CREATE (u)-[:APPLIED_TO]->(a)-[:FOR_JOB]->(j)
        """, {
            'app_data': application_data,
            'user_id': current_user.id,
            'job_id': job_id
        })
        
        # Update job applications count
        safe_run(session, """
            MATCH (j:Job {id: $job_id})
            SET j.applications_count = coalesce(j.applications_count, 0) + 1
        """, {'job_id': job_id})
        
        # Get owner info for email
        owner_result = safe_run(session, """
            MATCH (j:Job {id: $job_id})-[:POSTED_BY]->(b:Business)<-[:OWNS]-(owner:User)
            RETURN owner.email as owner_email, owner.id as owner_id, b.name as business_name
        """, {'job_id': job_id})
        
        owner_email = owner_result[0]['owner_email'] if owner_result else None
        
        # Send email to business owner
        if owner_email:
            try:
                email_context = {
                    'job_title': job_result[0]['j']['title'],
                    'business_name': job_result[0]['business_name'],
                    'applicant_name': current_user.username,
                    'applicant_email': current_user.email,
                    'applicant_phone': current_user.phone or 'N/A',
                    'cover_letter': cover_letter or 'No cover letter provided',
                    'application_date': datetime.utcnow().strftime('%B %d, %Y at %I:%M %p'),
                    'app_dashboard_url': url_for('dashboard.business_owner', _external=True),
                    'application_id': application_id,
                    'has_resume': bool(user_resume_data),
                    'has_cv': True,
                    'cv_filename': f"{application_id}.{file_ext}"
                }
                
                send_email_task(
                    to=owner_email,
                    subject=f'New Job Application: {job_result[0]["j"]["title"]} - {current_user.username}',
                    template='emails/job_application_notification.html',
                    context=email_context
                )
            except Exception as e:
                logger.error(f"Failed to send application notification email: {str(e)}")
        
        # Create notification for business owner - verify owner exists first
        if owner_result and owner_result[0]['owner_id']:
            owner_id = owner_result[0]['owner_id']
            
            # Verify owner user exists in database
            owner_check_result = safe_run(session, """
                MATCH (u:User {id: $user_id})
                RETURN u.id as id
            """, {'user_id': owner_id})
            
            if owner_check_result:
                create_notification_task.delay(
                    user_id=owner_id,
                    type='job_application',
                    title='New Job Application',
                    message=f'{current_user.username} applied for {job_result[0]["j"]["title"]}',
                    data={
                        'application_id': application_id,
                        'job_id': job_id,
                        'applicant_id': current_user.id,
                        'applicant_name': current_user.username
                    }
                )
            else:
                logger.warning(f"Owner user {owner_id} not found in database for notification")
        
        flash('Application submitted successfully!', 'success')
        return jsonify({'success': True, 'message': 'Application submitted successfully!', 'redirect_url': url_for('jobs.job_detail', job_id=job_id)})

@jobs_bp.route('/applications')
@login_required
@role_required('job_seeker')
def my_applications():
    """View user's job applications (as job seeker)"""
    
    db = get_neo4j_db()
    with db.session() as session:
        applications_result = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:APPLIED_TO]->(a:JobApplication)-[:FOR_JOB]->(j:Job)
            MATCH (j)-[:POSTED_BY]->(b:Business)
            RETURN a, j, b.name as business_name
            ORDER BY a.created_at DESC
        """, {'user_id': current_user.id})
        
        applications = []
        for record in applications_result:
            app_data = _node_to_dict(record['a'])
            job_data = _node_to_dict(record['j'])
            
            app_data['job_title'] = job_data['title']
            app_data['business_name'] = record['business_name']
            
            app = JobApplication(**app_data)
            applications.append(app)
    
    return render_template('jobs/my_applications.html', applications=applications)

# ============================================================================
# JOB MANAGEMENT (BUSINESS OWNER) ROUTES
# ============================================================================

@jobs_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required('business_owner')
def create_job():
    """Create a new job posting (business owner only)"""
    
    form = JobForm()
    
    db = get_neo4j_db()
    with db.session() as session:
        # Get user's businesses
        businesses_result = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:OWNS]->(b:Business)
            WHERE b.is_verified = true AND b.is_active = true
            RETURN b.id as id, b.name as name
            ORDER BY b.name ASC
        """, {'user_id': current_user.id})
        
        if not businesses_result:
            flash('You need to create and verify a business before posting jobs.', 'warning')
            return redirect(url_for('businesses.create_business'))
        
        # Populate business choices
        form.business_id.choices = [(b['id'], b['name']) for b in businesses_result]
    
    if form.validate_on_submit():
        job_id = str(uuid.uuid4())
        
        with db.session() as session:
            # Get business data for job location
            biz_result = safe_run(session, """
                MATCH (b:Business {id: $business_id})
                RETURN b.latitude as lat, b.longitude as lng, b.address as address
            """, {'business_id': form.business_id.data})
            
            job_data = {
                'id': job_id,
                'uuid': str(uuid.uuid4()),
                'title': form.title.data,
                'description': form.description.data,
                'category': form.category.data,
                'type': form.type.data,
                'setup': form.setup.data if hasattr(form, 'setup') else 'on_site',
                'salary_min': float(form.salary_min.data) if form.salary_min.data else None,
                'salary_max': float(form.salary_max.data) if form.salary_max.data else None,
                'currency': 'PHP',
                'location': biz_result[0]['address'] if biz_result else form.location.data,
                'latitude': float(biz_result[0]['lat']) if biz_result and biz_result[0]['lat'] else None,
                'longitude': float(biz_result[0]['lng']) if biz_result and biz_result[0]['lng'] else None,
                'requirements': form.requirements.data.split('\n') if form.requirements.data else [],
                'benefits': form.benefits.data.split('\n') if form.benefits.data else [],
                'is_active': True,
                'applications_count': 0,
                'views_count': 0,
                'created_at': datetime.utcnow().isoformat(),
                'expires_at': (datetime.utcnow() + timedelta(days=30)).isoformat()
            }
            
            # Create job and link to business
            safe_run(session, """
                CREATE (j:Job $job_data)
                WITH j
                MATCH (b:Business {id: $business_id})
                CREATE (j)-[:POSTED_BY]->(b)
                RETURN j.id as job_id
            """, {
                'job_data': job_data,
                'business_id': form.business_id.data
            })
        
        flash('Job posted successfully!', 'success')
        return redirect(url_for('jobs.job_detail', job_id=job_id))
    
    return render_template('jobs/create_job.html', form=form)

@jobs_bp.route('/<job_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('business_owner')
def edit_job(job_id):
    """Edit an existing job posting"""
    
    db = get_neo4j_db()
    
    with db.session() as session:
        # Check ownership
        ownership_result = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:OWNS]->(b:Business)-[:POSTED_BY]->(:Job {id: $job_id})
            RETURN count(*) as count
        """, {'user_id': current_user.id, 'job_id': job_id})
        
        if not ownership_result or ownership_result[0]['count'] == 0:
            flash('You do not have permission to edit this job.', 'error')
            return redirect(url_for('jobs.list_jobs'))
        
        # Get job details
        job_result = safe_run(session, """
            MATCH (j:Job {id: $job_id})
            RETURN j
        """, {'job_id': job_id})
        
        if not job_result:
            flash('Job not found.', 'error')
            return redirect(url_for('jobs.list_jobs'))
    
    form = JobForm()
    
    if form.validate_on_submit():
        with db.session() as session:
            update_data = {
                'title': form.title.data,
                'description': form.description.data,
                'category': form.category.data,
                'type': form.type.data,
                'setup': form.setup.data if hasattr(form, 'setup') else 'on_site',
                'salary_min': float(form.salary_min.data) if form.salary_min.data else None,
                'salary_max': float(form.salary_max.data) if form.salary_max.data else None,
                'requirements': form.requirements.data.split('\n') if form.requirements.data else [],
                'benefits': form.benefits.data.split('\n') if form.benefits.data else [],
                'updated_at': datetime.utcnow().isoformat()
            }
            
            safe_run(session, """
                MATCH (j:Job {id: $job_id})
                SET j += $update_data
                RETURN j
            """, {
                'job_id': job_id,
                'update_data': update_data
            })
        
        flash('Job updated successfully!', 'success')
        return redirect(url_for('jobs.job_detail', job_id=job_id))
    
    # Populate form with existing data
    job_node = job_result[0]['j']
    if request.method == 'GET':
        form.title.data = job_node.get('title')
        form.description.data = job_node.get('description')
        form.category.data = job_node.get('category')
        form.type.data = job_node.get('type')
        form.salary_min.data = job_node.get('salary_min')
        form.salary_max.data = job_node.get('salary_max')
        
        reqs = job_node.get('requirements', [])
        form.requirements.data = '\n'.join(reqs) if reqs else ''
        
        bens = job_node.get('benefits', [])
        form.benefits.data = '\n'.join(bens) if bens else ''
    
    return render_template('jobs/edit_job.html', form=form, job_id=job_id)

@jobs_bp.route('/<job_id>/close', methods=['POST'])
@login_required
@role_required('business_owner')
def close_job(job_id):
    """Close a job posting"""
    
    db = get_neo4j_db()
    with db.session() as session:
        # Check ownership
        ownership_result = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:OWNS]->(b:Business)-[:POSTED_BY]->(:Job {id: $job_id})
            RETURN count(*) as count
        """, {'user_id': current_user.id, 'job_id': job_id})
        
        if not ownership_result or ownership_result[0]['count'] == 0:
            return jsonify({'error': 'You do not have permission to close this job.'}), 403
        
        # Close job
        safe_run(session, """
            MATCH (j:Job {id: $job_id})
            SET j.is_active = false
            RETURN j
        """, {'job_id': job_id})
    
    flash('Job closed successfully!', 'success')
    return redirect(url_for('jobs.my_postings'))

@jobs_bp.route('/my-postings')
@login_required
@role_required('business_owner')
def my_postings():
    """View user's job postings (as business owner)"""
    
    db = get_neo4j_db()
    with db.session() as session:
        postings_result = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:OWNS]->(b:Business)-[:POSTED_BY]->(j:Job)
            RETURN j, b.name as business_name
            ORDER BY j.created_at DESC
        """, {'user_id': current_user.id})
        
        postings = []
        for record in postings_result:
            job_data = _node_to_dict(record['j'])
            job_data['business_name'] = record['business_name']
            job = Job(**job_data)
            postings.append(job)
    
    return render_template('jobs/my_postings.html', postings=postings)

# ============================================================================
# API ROUTES
# ============================================================================

@jobs_bp.route('/api/map-markers')
@login_required_optional
def get_map_markers():
    """Get job markers for map display"""
    
    bbox = request.args.get('bbox')  # bounding box for map view
    category = request.args.get('category', '').strip()
    
    db = get_neo4j_db()
    with db.session() as session:
        query = """
            MATCH (j:Job)-[:POSTED_BY]->(b:Business)
            WHERE j.is_active = true AND j.latitude IS NOT NULL AND j.longitude IS NOT NULL
        """
        params = {}
        
        if category:
            query += " AND j.category = $category"
            params['category'] = category
        
        query += """
            RETURN j, b.name as business_name
            LIMIT 100
        """
        
        results = safe_run(session, query, params)
        
        markers = []
        for record in results:
            job_data = _node_to_dict(record['j'])
            marker = {
                'id': job_data['id'],
                'title': job_data['title'],
                'business': record['business_name'],
                'lat': float(job_data['latitude']),
                'lng': float(job_data['longitude']),
                'salary': f"₱{job_data.get('salary_min', 'TBD')} - ₱{job_data.get('salary_max', 'TBD')}",
                'type': Job.JOB_TYPES.get(job_data['type'], job_data['type']),
                'url': url_for('jobs.job_detail', job_id=job_data['id'])
            }
            markers.append(marker)
    
    return jsonify(markers)

@jobs_bp.route('/api/search')
def api_search_jobs():
    """API endpoint for job search (autocomplete support)"""
    
    query = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    limit = request.args.get('limit', 10, type=int)
    
    db = get_neo4j_db()
    with db.session() as session:
        cypher_query = """
            MATCH (j:Job)-[:POSTED_BY]->(b:Business)
            WHERE j.is_active = true
        """
        params = {'limit': limit}
        
        if query:
            cypher_query += " AND (j.title CONTAINS $query OR j.description CONTAINS $query)"
            params['query'] = query
        
        if category:
            cypher_query += " AND j.category = $category"
            params['category'] = category
        
        cypher_query += """
            RETURN j, b.name as business_name
            ORDER BY j.created_at DESC
            LIMIT $limit
        """
        
        results = safe_run(session, cypher_query, params)
        
        jobs = []
        for record in results:
            job_data = _node_to_dict(record['j'])
            job_data['business_name'] = record['business_name']
            jobs.append(job_data)
    
    return jsonify(jobs)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def allowed_file(filename):
    """Check if file extension is allowed for resume uploads"""
    allowed = {'.pdf', '.doc', '.docx', '.txt', '.rtf'}
    return '.' in filename and \
           '.' + filename.rsplit('.', 1)[1].lower() in allowed
           
           
@jobs_bp.route('/resume/update', methods=['GET', 'POST'])
@login_required
@role_required('job_seeker')
def update_resume():
    """View and edit job seeker resume (fillable template)"""
    db = get_neo4j_db()
    
    if request.method == 'GET':
        # Show resume template form
        with db.session() as session:
            user_data = safe_run(session, """
                MATCH (u:User {id: $user_id})
                RETURN u.resume_data as resume_data, u.updated_at as updated_at
            """, {'user_id': current_user.id})
        
        resume_data = None
        if user_data and user_data[0].get('resume_data'):
            import json
            try:
                resume_data = json.loads(user_data[0].get('resume_data'))
            except:
                resume_data = None
        
        return render_template('jobs/update_resume.html', resume_data=resume_data)
    
    # POST request - handle resume data save
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No resume data provided'}), 400
        
        import json
        resume_json = json.dumps(data)
        
        # Update user resume in database
        with db.session() as session:
            safe_run(session, """
                MATCH (u:User {id: $user_id})
                SET u.resume_data = $resume_data, u.resume_updated_at = $updated_at
                RETURN u
            """, {
                'user_id': current_user.id,
                'resume_data': resume_json,
                'updated_at': datetime.utcnow().isoformat()
            })
        
        return jsonify({
            'message': 'Resume saved successfully',
            'status': 'success'
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Failed to save resume: {str(e)}")
        return jsonify({'error': 'Failed to save resume. Please try again.'}), 500

# AI Resume Assistant Routes
@jobs_bp.route('/analyze-resume', methods=['POST'])
@login_required
@role_required('job_seeker')
def analyze_resume():
    """Analyze resume using Gemini AI"""
    try:
        from gemini_client import get_gemini_response
        
        data = request.get_json()
        resume_text = data.get('resume', '')
        language = data.get('language', 'English')
        
        if not resume_text.strip():
            return jsonify({'status': 'error', 'error': 'Resume is empty'}), 400
        
        # Language instruction
        lang_instruction = {
            'English': 'Respond in English.',
            'Tagalog': 'Sumagot sa Tagalog. Gumamit ng natural at propesyonal na wika.',
            'Bicol': 'Tumugon sa Bicol (Catandunganon). Gumamit ng natural at propesyonal na wika.'
        }.get(language, 'Respond in English.')
        
        prompt = f"""You are a professional resume reviewer. Analyze this resume carefully and provide constructive feedback:

{resume_text}

Please provide a detailed analysis including:
1. **Overall Assessment**: Rate the resume quality (0-100) and provide a brief summary
2. **Strengths**: List 3-4 strong points about the resume
3. **Areas for Improvement**: Identify specific sections that need enhancement
4. **Recommendations**: Provide 3-5 specific, actionable recommendations to strengthen the resume

Format your response clearly with section headers.

{lang_instruction}"""
        
        logger.info(f"Calling Gemini API for resume analysis in {language}")
        analysis = get_gemini_response(prompt)
        logger.info("Resume analysis completed successfully")
        
        return jsonify({
            'status': 'success',
            'analysis': analysis
        })
    except Exception as e:
        logger.error(f"Error analyzing resume: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@jobs_bp.route('/get-resume-suggestions', methods=['POST'])
@login_required
@role_required('job_seeker')
def get_resume_suggestions():
    """Get improvement suggestions for resume using Gemini AI"""
    try:
        from gemini_client import get_gemini_response
        
        data = request.get_json()
        resume_text = data.get('resume', '')
        language = data.get('language', 'English')
        
        if not resume_text.strip():
            return jsonify({'status': 'error', 'error': 'Resume is empty'}), 400
        
        # Language instruction
        lang_instruction = {
            'English': 'Respond in English.',
            'Tagalog': 'Sumagot sa Tagalog. Gumamit ng natural at propesyonal na wika.',
            'Bicol': 'Tumugon sa Bicol (Catandunganon). Gumamit ng natural at propesyonal na wika.'
        }.get(language, 'Respond in English.')
        
        prompt = f"""Review this resume and provide specific, actionable improvement suggestions:

{resume_text}

Analyze each section (Personal Info, Skills, Education, Experience, Interests, Activities) and provide:
- 1-2 specific suggestions per section that has content
- Focus on clarity, impact, and completeness
- Suggestions should be immediately actionable

Format as a numbered list. Example:
1. Expand your technical skills section with proficiency levels
2. Add measurable achievements to your experience descriptions
3. etc.

Provide 5-8 total suggestions.

{lang_instruction}"""
        
        logger.info(f"Calling Gemini API for resume suggestions in {language}")
        suggestions = get_gemini_response(prompt)
        logger.info("Resume suggestions completed successfully")
        
        # Parse into list if it's a string
        if isinstance(suggestions, str):
            # Split by newlines and filter for numbered items
            lines = suggestions.split('\n')
            suggestion_list = []
            for line in lines:
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                    # Clean up the suggestion
                    suggestion = line.lstrip('0123456789.-•) ').strip()
                    if suggestion:
                        suggestion_list.append(suggestion)
        else:
            suggestion_list = suggestions
        
        return jsonify({
            'status': 'success',
            'suggestions': suggestion_list
        })
    except Exception as e:
        logger.error(f"Error getting resume suggestions: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@jobs_bp.route('/check-resume-completion', methods=['POST'])
@login_required
@role_required('job_seeker')
def check_resume_completion():
    """Check resume completion and completeness percentage using Gemini AI"""
    try:
        from gemini_client import get_gemini_response
        
        data = request.get_json()
        resume_text = data.get('resume', '')
        language = data.get('language', 'English')
        
        if not resume_text.strip():
            return jsonify({'status': 'error', 'error': 'Resume is empty'}), 400
        
        # Language instruction
        lang_instruction = {
            'English': 'Respond in English.',
            'Tagalog': 'Sumagot sa Tagalog. Gumamit ng natural at propesyonal na wika.',
            'Bicol': 'Tumugon sa Bicol (Catandunganon). Gumamit ng natural at propesyonal na wika.'
        }.get(language, 'Respond in English.')
        
        prompt = f"""Evaluate the completeness of this resume. Rate it on a scale of 0-100 based on:
- Personal information completeness
- Skills section quality and detail
- Education history
- Work experience details
- Overall content quality and formatting

{resume_text}

Provide a JSON response with this exact format:
{{
    "score": <number 0-100>,
    "issues": [
        "issue 1",
        "issue 2"
    ]
}}

In the issues array, list what's missing or needs improvement. Be specific about which sections need work.

{lang_instruction}"""
        
        logger.info(f"Calling Gemini API for resume completion check in {language}")
        response = get_gemini_response(prompt)
        logger.info("Resume completion check completed successfully")
        
        # Try to parse JSON response
        try:
            import json
            # Clean response if it contains markdown code blocks
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0]
            elif '```' in response:
                response = response.split('```')[1].split('```')[0]
            
            completion_data = json.loads(response.strip())
        except Exception as parse_error:
            logger.warning(f"Failed to parse JSON response: {parse_error}")
            # Fallback response if JSON parsing fails
            completion_data = {
                'score': 65,
                'issues': [
                    'Consider adding more detail to your work experience',
                    'Expand your skills section with specific technologies or tools',
                    'Include quantifiable achievements in your experience'
                ]
            }
        
        return jsonify({
            'status': 'success',
            'completion': completion_data
        })
    except Exception as e:
        logger.error(f"Error checking resume completion: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


# ============================================================================
# AI-POWERED JOB APPLICATION ASSISTANCE ENDPOINTS
# ============================================================================

@jobs_bp.route('/improve-application', methods=['POST'])
@login_required
@role_required('job_seeker')
def improve_application():
    """Improve job application cover letter using Gemini AI"""
    try:
        from gemini_client import get_gemini_response
        
        data = request.get_json()
        cover_letter = data.get('cover_letter', '')
        job_title = data.get('job_title', 'this position')
        language = data.get('language', 'English')
        
        if not cover_letter.strip():
            return jsonify({'status': 'error', 'error': 'Cover letter is empty'}), 400
        
        # Language instruction
        lang_instruction = {
            'English': 'Respond in English.',
            'Tagalog': 'Sumagot sa Tagalog. Gumamit ng natural at propesyonal na wika.',
            'Bicol': 'Tumugon sa Bicol (Catandunganon). Gumamit ng natural at propesyonal na wika.'
        }.get(language, 'Respond in English.')
        
        job_title_safe = job_title[:50] if job_title else 'this position'  # Limit length to avoid filter issues
        prompt = f"""You are a career advisor. Help improve this job application letter for a {job_title_safe} role.

Application letter:
{cover_letter}

Provide:
1. Suggestions to strengthen the letter
2. What works well currently
3. Tips to make it stand out

{lang_instruction}"""
        
        logger.info(f"Calling Gemini API to improve application for {job_title} in {language}")
        improvements = get_gemini_response(prompt)
        logger.info("Application improvement completed successfully")
        
        return jsonify({
            'status': 'success',
            'improvements': improvements
        })
    except Exception as e:
        logger.error(f"Error improving application: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@jobs_bp.route('/application-tips', methods=['POST'])
@login_required
@role_required('job_seeker')
def application_tips():
    """Get job-specific application tips using Gemini AI"""
    try:
        from gemini_client import get_gemini_response
        
        data = request.get_json()
        job_title = data.get('job_title', 'this position')
        language = data.get('language', 'English')
        
        # Language instruction
        lang_instruction = {
            'English': 'Respond in English.',
            'Tagalog': 'Sumagot sa Tagalog. Gumamit ng natural at propesyonal na wika.',
            'Bicol': 'Tumugon sa Bicol (Catandunganon). Gumamit ng natural at propesyonal na wika.'
        }.get(language, 'Respond in English.')
        
        job_title_safe = job_title[:50] if job_title else 'this position'  # Limit length to avoid filter issues
        prompt = f"""You are a career advisor. Provide tips for applying to a {job_title_safe} position.

Include advice about:
1. Important skills to highlight
2. Key points to emphasize in the application
3. Tips to stand out from other applicants

{lang_instruction}"""
        
        logger.info(f"Calling Gemini API for application tips for {job_title} in {language}")
        tips = get_gemini_response(prompt)
        logger.info("Application tips generated successfully")
        
        return jsonify({
            'status': 'success',
            'tips': tips
        })
    except Exception as e:
        logger.error(f"Error generating application tips: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@jobs_bp.route('/review-application', methods=['POST'])
@login_required
@role_required('job_seeker')
def review_application():
    """Complete application review using Gemini AI"""
    try:
        from gemini_client import get_gemini_response
        
        data = request.get_json()
        cover_letter = data.get('cover_letter', '')
        job_title = data.get('job_title', 'this position')
        language = data.get('language', 'English')
        
        if not cover_letter.strip():
            return jsonify({'status': 'error', 'error': 'Cover letter is empty'}), 400
        
        # Language instruction
        lang_instruction = {
            'English': 'Respond in English.',
            'Tagalog': 'Sumagot sa Tagalog. Gumamit ng natural at propesyonal na wika.',
            'Bicol': 'Tumugon sa Bicol (Catandunganon). Gumamit ng natural at propesyonal na wika.'
        }.get(language, 'Respond in English.')
        
        prompt = f"""Review this application letter for a {job_title[:50]} position.

Letter:
{cover_letter}

Respond with a JSON object containing: score (0-100), strengths (list), improvements (list), ready (bool if score >= 70), and notes (string).

{lang_instruction}"""
        
        logger.info(f"Calling Gemini API to review application for {job_title} in {language}")
        response = get_gemini_response(prompt)
        logger.info("Application review completed successfully")
        
        # Try to parse JSON response
        try:
            import json
            # Clean response if it contains markdown code blocks
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0]
            elif '```' in response:
                response = response.split('```')[1].split('```')[0]
            
            review_data = json.loads(response.strip())
            # Normalize field names if needed
            if 'overallScore' not in review_data and 'score' in review_data:
                review_data['overallScore'] = review_data.pop('score')
            if 'readyToSubmit' not in review_data and 'ready' in review_data:
                review_data['readyToSubmit'] = review_data.pop('ready')
            if 'recommendations' not in review_data and 'notes' in review_data:
                review_data['recommendations'] = review_data.pop('notes')
        except Exception as parse_error:
            logger.warning(f"Failed to parse JSON response: {parse_error}")
            # Fallback response if JSON parsing fails
            review_data = {
                'overallScore': 70,
                'strengths': [
                    'Clear expression of interest',
                    'Relevant experience mentioned'
                ],
                'improvements': [
                    'Add specific examples',
                    'Include measurable achievements'
                ],
                'readyToSubmit': True,
                'recommendations': 'Application shows promise. Consider strengthening with specific examples.'
            }
        
        return jsonify({
            'status': 'success',
            'review': review_data
        })
    except Exception as e:
        logger.error(f"Error reviewing application: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500