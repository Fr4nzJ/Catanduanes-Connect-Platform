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
            MATCH (u:User)-[:OWNS]->(b)
            RETURN j, b, u.id as business_owner_id
        """, {'job_id': job_id})
        
        if not result:
            flash('Job not found.', 'error')
            return redirect(url_for('jobs.list_jobs'))
        
        record = result[0]
        job_data = _node_to_dict(record['j'])
        job_data['business_id'] = record['b']['id']
        job_data['business_name'] = record['b']['name']
        job_data['business_owner_id'] = record['business_owner_id']
        
        job = Job(**job_data)
        
        business_data = _node_to_dict(record['b'])
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
            job_data['business_owner_id'] = record['business_owner_id']
            similar_jobs.append(Job(**job_data))
        
        # Check if current user is the job owner
        is_job_owner = False
        if current_user.is_authenticated and current_user.role == 'business_owner':
            is_job_owner = current_user.id == record['business_owner_id']
    
    return render_template('jobs/job_detail.html',
        job=job,
        business=business,
        has_applied=has_applied,
        similar_jobs=similar_jobs,
        is_job_owner=is_job_owner
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
            
            # Check if job is filled
            if job_data.get('status') == 'filled':
                flash('This job has already been filled.', 'warning')
                return redirect(url_for('jobs.job_detail', job_id=job_id))
            
            job_data['business_name'] = job_result[0]['business_name']
            job = Job(**job_data)
        
        return render_template('jobs/job_apply.html', job=job)
    
    # POST request - handle application submission
    db = get_neo4j_db()
    with db.session() as session:
        # Check if job exists and is active, and get business owner info
        job_result = safe_run(session, """
            MATCH (j:Job {id: $job_id})-[:POSTED_BY]->(b:Business)
            MATCH (u:User)-[:OWNS]->(b)
            WHERE j.is_active = true
            RETURN j, b.id as business_id, b.name as business_name, b.email as business_email, u.email as owner_email, u.id as owner_id
        """, {'job_id': job_id})
        
        if not job_result:
            flash('Job not found or no longer active.', 'error')
            return redirect(url_for('jobs.list_jobs'))
        
        # Check if job is filled
        job_data = _node_to_dict(job_result[0]['j'])
        if job_data.get('status') == 'filled':
            flash('This job has already been filled.', 'error')
            return redirect(url_for('jobs.job_detail', job_id=job_id))
        
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
            MATCH (j:Job {id: $job_id})-[:POSTED_BY]->(b:Business)
            MATCH (owner:User)-[:OWNS]->(b)
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
                
                from tasks import send_email_task_wrapper
                send_email_task_wrapper(
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
                create_notification_task(
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
                'salary_min': float(form.salary_min.data) if form.salary_min.data else None,
                'salary_max': float(form.salary_max.data) if form.salary_max.data else None,
                'currency': form.currency.data,
                'location': biz_result[0]['address'] if biz_result else form.location.data,
                'latitude': float(biz_result[0]['lat']) if biz_result and biz_result[0]['lat'] else None,
                'longitude': float(biz_result[0]['lng']) if biz_result and biz_result[0]['lng'] else None,
                'requirements': form.requirements.data.split('\n') if form.requirements.data else [],
                'benefits': form.benefits.data.split('\n') if form.benefits.data else [],
                'is_active': True,
                'status': 'pending',
                'is_approved': False,
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
    
    return render_template('jobs/jobs_create.html', form=form)

@jobs_bp.route('/<job_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('business_owner')
def edit_job(job_id):
    """Edit an existing job posting"""
    
    db = get_neo4j_db()
    
    with db.session() as session:
        # Check ownership
        ownership_result = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:OWNS]->(b:Business)
            MATCH (:Job {id: $job_id})-[:POSTED_BY]->(b)
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
    
    # Convert job node to Job object for template
    job = Job(**_node_to_dict(job_node))
    
    return render_template('jobs/jobs_edit.html', form=form, job=job, job_id=job_id)

@jobs_bp.route('/<job_id>/close', methods=['POST'])
@login_required
@role_required('business_owner')
def close_job(job_id):
    """Close a job posting"""
    
    db = get_neo4j_db()
    with db.session() as session:
        # Check ownership
        ownership_result = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:OWNS]->(b:Business)
            MATCH (:Job {id: $job_id})-[:POSTED_BY]->(b)
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
            MATCH (u:User {id: $user_id})-[:OWNS]->(b:Business)
            MATCH (j:Job)-[:POSTED_BY]->(b)
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
# APPLICANTS MANAGEMENT (BUSINESS OWNER) ROUTES
# ============================================================================

@jobs_bp.route('/my-applicants')
@login_required
@role_required('business_owner')
def my_applicants():
    """View all applicants to business owner's job postings"""
    
    db = get_neo4j_db()
    with db.session() as session:
        # Get all applications for jobs posted by user's businesses
        applicants_result = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:OWNS]->(b:Business)
            MATCH (j:Job)-[:POSTED_BY]->(b)
            MATCH (applicant:User)-[:APPLIED_TO]->(a:JobApplication)-[:FOR_JOB]->(j)
            RETURN a, applicant, j.id as job_id, j.title as job_title, b.name as business_name
            ORDER BY a.created_at DESC
        """, {'user_id': current_user.id})
        
        applicants = []
        for record in applicants_result:
            app_data = _node_to_dict(record['a'])
            applicant_data = _node_to_dict(record['applicant'])
            
            app_data['job_id'] = record['job_id']
            app_data['job_title'] = record['job_title']
            app_data['business_name'] = record['business_name']
            app_data['applicant_name'] = applicant_data.get('username', 'Unknown')
            app_data['applicant_id'] = applicant_data.get('id')
            app_data['applicant_email'] = applicant_data.get('email')
            
            applicants.append(app_data)
    
    return render_template('jobs/my_applicants.html', applicants=applicants)

@jobs_bp.route('/<job_id>/applicants')
@login_required
@role_required('business_owner')
def job_applicants(job_id):
    """View applicants for a specific job posting"""
    
    db = get_neo4j_db()
    with db.session() as session:
        # Verify user owns the job
        owner_check = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:OWNS]->(b:Business)
            MATCH (j:Job {id: $job_id})-[:POSTED_BY]->(b)
            RETURN j.id as id
        """, {'user_id': current_user.id, 'job_id': job_id})
        
        if not owner_check:
            flash('You do not have permission to view applicants for this job.', 'error')
            return redirect(url_for('jobs.my_postings'))
        
        # Get job details
        job_result = safe_run(session, """
            MATCH (j:Job {id: $job_id})
            RETURN j
        """, {'job_id': job_id})
        
        job = _node_to_dict(job_result[0]['j']) if job_result else None
        
        # Get all applicants for this job
        applicants_result = safe_run(session, """
            MATCH (applicant:User)-[:APPLIED_TO]->(a:JobApplication)-[:FOR_JOB]->(j:Job {id: $job_id})
            RETURN a, applicant
            ORDER BY a.created_at DESC
        """, {'job_id': job_id})
        
        applicants = []
        for record in applicants_result:
            app_data = _node_to_dict(record['a'])
            applicant_data = _node_to_dict(record['applicant'])
            
            app_data['applicant_id'] = applicant_data.get('id')
            app_data['applicant_name'] = applicant_data.get('username', 'Unknown')
            app_data['applicant_email'] = applicant_data.get('email')
            app_data['profile_picture'] = applicant_data.get('profile_picture')
            
            applicants.append(app_data)
    
    return render_template('jobs/job_applicants.html', job=job, applicants=applicants)

@jobs_bp.route('/applicant/<application_id>')
@login_required
@role_required('business_owner')
def view_applicant_profile(application_id):
    """View detailed profile and application of an applicant"""
    
    db = get_neo4j_db()
    with db.session() as session:
        # Get application and applicant details
        app_result = safe_run(session, """
            MATCH (applicant:User)-[:APPLIED_TO]->(a:JobApplication {id: $app_id})-[:FOR_JOB]->(j:Job)
            MATCH (j)-[:POSTED_BY]->(b:Business), (owner:User {id: $owner_id})-[:OWNS]->(b)
            OPTIONAL MATCH (a)-[:HAS_INTERVIEW]->(i:Interview)
            RETURN a, applicant, j.id as job_id, j.title as job_title, b.name as business_name, i
        """, {'app_id': application_id, 'owner_id': current_user.id})
        
        if not app_result:
            flash('Application not found or you do not have permission to view it.', 'error')
            return redirect(url_for('jobs.my_applicants'))
        
        app_data = _node_to_dict(app_result[0]['a'])
        applicant_data = _node_to_dict(app_result[0]['applicant'])
        
        # Format application data
        app_data['job_id'] = app_result[0]['job_id']
        app_data['job_title'] = app_result[0]['job_title']
        app_data['business_name'] = app_result[0]['business_name']
        
        # Get interview data if exists
        interview_data = None
        if app_result[0]['i']:
            interview_data = _node_to_dict(app_result[0]['i'])
        
        # Parse resume_data if it's a string (JSON)
        resume_data = applicant_data.get('resume_data')
        if resume_data and isinstance(resume_data, str):
            try:
                import json
                from flask import current_app
                resume_data = json.loads(resume_data)
                current_app.logger.info(f"Successfully parsed resume_data for applicant {applicant_data.get('id')}: {bool(resume_data)}")
            except (json.JSONDecodeError, TypeError) as e:
                import logging
                logging.getLogger(__name__).error(f"Failed to parse resume_data: {str(e)}")
                resume_data = None
        else:
            if resume_data:
                import logging
                logging.getLogger(__name__).info(f"Resume data is already parsed or empty: {type(resume_data)}")
        
        # Format applicant profile
        applicant = {
            'id': applicant_data.get('id'),
            'username': applicant_data.get('username', 'Unknown'),
            'email': applicant_data.get('email'),
            'profile_picture': applicant_data.get('profile_picture'),
            'phone': applicant_data.get('phone'),
            'location': applicant_data.get('location'),
            'bio': applicant_data.get('bio'),
            'created_at': applicant_data.get('created_at'),
            'resume_data': resume_data,
            'full_name': applicant_data.get('full_name', applicant_data.get('username', 'Unknown'))
        }
    
    return render_template('jobs/applicant_profile.html', application=app_data, applicant=applicant, interview=interview_data)

@jobs_bp.route('/applicant/<application_id>/download-cv')
@login_required
@role_required('business_owner')
def download_cv(application_id):
    """Download CV file from application"""
    
    db = get_neo4j_db()
    with db.session() as session:
        # Get application and verify ownership
        app_result = safe_run(session, """
            MATCH (applicant:User)-[:APPLIED_TO]->(a:JobApplication {id: $app_id})-[:FOR_JOB]->(j:Job)
            MATCH (j)-[:POSTED_BY]->(b:Business), (owner:User {id: $owner_id})-[:OWNS]->(b)
            RETURN a.cv_file as cv_file
        """, {'app_id': application_id, 'owner_id': current_user.id})
        
        if not app_result or not app_result[0]['cv_file']:
            flash('CV file not found.', 'error')
            return redirect(url_for('jobs.my_applicants'))
        
        cv_file_path = app_result[0]['cv_file']
        
        # Construct full file path
        full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], cv_file_path)
        
        # Check if file exists
        if not os.path.exists(full_path):
            flash('CV file not found on server.', 'error')
            return redirect(url_for('jobs.my_applicants'))
        
        # Get file extension for proper download
        _, file_extension = os.path.splitext(cv_file_path)
        filename = f"applicant_cv_{application_id}{file_extension}"
        
        # Use send_file to download
        from flask import send_file
        try:
            return send_file(full_path, as_attachment=True, download_name=filename)
        except Exception as e:
            logger.error(f"Error downloading CV: {e}")
            flash('Error downloading CV. Please try again.', 'error')
            return redirect(url_for('jobs.my_applicants'))

@jobs_bp.route('/applicant/<application_id>/accept', methods=['POST'])
@login_required
@role_required('business_owner')
def accept_applicant(application_id):
    """Accept a job application"""
    
    db = get_neo4j_db()
    with db.session() as session:
        # Verify ownership and update status
        result = safe_run(session, """
            MATCH (applicant:User)-[:APPLIED_TO]->(a:JobApplication {id: $app_id})-[:FOR_JOB]->(j:Job)
            MATCH (j)-[:POSTED_BY]->(b:Business), (owner:User {id: $owner_id})-[:OWNS]->(b)
            SET a.status = 'accepted', a.reviewed_at = datetime()
            SET j.status = 'filled', j.filled_at = datetime()
            RETURN applicant.email as applicant_email, applicant.username as applicant_name, 
                   j.title as job_title, j.id as job_id, a.id as application_id
        """, {'app_id': application_id, 'owner_id': current_user.id})
        
        if not result:
            return jsonify({'success': False, 'error': 'Application not found or unauthorized'}), 403
        
        applicant_email = result[0]['applicant_email']
        applicant_name = result[0]['applicant_name']
        job_title = result[0]['job_title']
        job_id = result[0]['job_id']
        
        # Send email notification
        try:
            from tasks import send_email_task_wrapper
            send_email_task_wrapper(
                to=applicant_email,
                subject=f'Your Application for {job_title} - Accepted',
                template='email/application_accepted.html',
                context={
                    'applicant_name': applicant_name,
                    'job_title': job_title,
                    'company_name': current_user.username
                }
            )
        except Exception as e:
            logger.error(f"Failed to send acceptance email: {e}")
        
        flash('Application accepted! Applicant has been notified.', 'success')
        return redirect(url_for('jobs.view_applicant_profile', application_id=application_id))

@jobs_bp.route('/applicant/<application_id>/reject', methods=['POST'])
@login_required
@role_required('business_owner')
def reject_applicant(application_id):
    """Reject a job application"""
    
    reason = request.form.get('reason', 'No reason provided')
    
    db = get_neo4j_db()
    with db.session() as session:
        # Verify ownership and update status
        result = safe_run(session, """
            MATCH (applicant:User)-[:APPLIED_TO]->(a:JobApplication {id: $app_id})-[:FOR_JOB]->(j:Job)
            MATCH (j)-[:POSTED_BY]->(b:Business), (owner:User {id: $owner_id})-[:OWNS]->(b)
            SET a.status = 'rejected', a.rejection_reason = $reason, a.reviewed_at = datetime()
            RETURN applicant.email as applicant_email, applicant.username as applicant_name, 
                   j.title as job_title
        """, {'app_id': application_id, 'owner_id': current_user.id, 'reason': reason})
        
        if not result:
            return jsonify({'success': False, 'error': 'Application not found or unauthorized'}), 403
        
        applicant_email = result[0]['applicant_email']
        applicant_name = result[0]['applicant_name']
        job_title = result[0]['job_title']
        
        # Send email notification
        try:
            from tasks import send_email_task_wrapper
            send_email_task_wrapper(
                to=applicant_email,
                subject=f'Your Application for {job_title} - Not Selected',
                template='email/application_rejected.html',
                context={
                    'applicant_name': applicant_name,
                    'job_title': job_title,
                    'reason': reason
                }
            )
        except Exception as e:
            logger.error(f"Failed to send rejection email: {e}")
        
        flash('Application rejected! Applicant has been notified.', 'success')
        return redirect(url_for('jobs.view_applicant_profile', application_id=application_id))

# ============================================================================
# INTERVIEW SCHEDULING ROUTES
# ============================================================================

@jobs_bp.route('/applicant/<application_id>/schedule-interview', methods=['POST'])
@login_required
@role_required('business_owner')
def schedule_interview(application_id):
    """Schedule an interview for accepted applicant"""
    
    interview_type = request.form.get('interview_type')  # 'online' or 'onsite'
    
    if interview_type == 'online':
        interview_date = request.form.get('interview_date')
        interview_time = request.form.get('interview_time')
        google_meet_link = request.form.get('google_meet_link', '')
        instructions = request.form.get('instructions', '')
    else:  # onsite
        interview_date = request.form.get('interview_date')
        interview_time = request.form.get('interview_time')
        location = request.form.get('location')
        contact_person = request.form.get('contact_person')
        contact_phone = request.form.get('contact_phone')
        instructions = request.form.get('instructions', '')
    
    db = get_neo4j_db()
    with db.session() as session:
        # Verify application exists and is accepted
        verify = safe_run(session, """
            MATCH (applicant:User)-[:APPLIED_TO]->(a:JobApplication {id: $app_id})-[:FOR_JOB]->(j:Job)
            MATCH (j)-[:POSTED_BY]->(b:Business), (owner:User {id: $owner_id})-[:OWNS]->(b)
            WHERE a.status = 'accepted'
            RETURN applicant.id as applicant_id, applicant.email as applicant_email, 
                   applicant.username as applicant_name, j.title as job_title
        """, {'app_id': application_id, 'owner_id': current_user.id})
        
        if not verify:
            return jsonify({'success': False, 'error': 'Application not found, unauthorized, or not accepted'}), 403
        
        applicant_id = verify[0]['applicant_id']
        applicant_email = verify[0]['applicant_email']
        applicant_name = verify[0]['applicant_name']
        job_title = verify[0]['job_title']
        
        interview_id = str(uuid.uuid4())
        interview_datetime = f"{interview_date}T{interview_time}"
        
        try:
            # Create Interview node and connect to application
            if interview_type == 'online':
                create = safe_run(session, """
                    MATCH (a:JobApplication {id: $app_id})
                    MATCH (applicant:User {id: $applicant_id})
                    CREATE (i:Interview {
                        id: $interview_id,
                        type: 'online',
                        interview_datetime: $interview_datetime,
                        google_meet_link: $google_meet_link,
                        instructions: $instructions,
                        status: 'scheduled',
                        created_at: datetime(),
                        updated_at: datetime()
                    })
                    CREATE (a)-[:HAS_INTERVIEW]->(i)
                    CREATE (applicant)-[:INVITED_TO]->(i)
                    RETURN i.id as interview_id
                """, {
                    'app_id': application_id,
                    'applicant_id': applicant_id,
                    'interview_id': interview_id,
                    'interview_datetime': interview_datetime,
                    'google_meet_link': google_meet_link,
                    'instructions': instructions
                })
            else:  # onsite
                create = safe_run(session, """
                    MATCH (a:JobApplication {id: $app_id})
                    MATCH (applicant:User {id: $applicant_id})
                    CREATE (i:Interview {
                        id: $interview_id,
                        type: 'onsite',
                        interview_datetime: $interview_datetime,
                        location: $location,
                        contact_person: $contact_person,
                        contact_phone: $contact_phone,
                        instructions: $instructions,
                        status: 'scheduled',
                        created_at: datetime(),
                        updated_at: datetime()
                    })
                    CREATE (a)-[:HAS_INTERVIEW]->(i)
                    CREATE (applicant)-[:INVITED_TO]->(i)
                    RETURN i.id as interview_id
                """, {
                    'app_id': application_id,
                    'applicant_id': applicant_id,
                    'interview_id': interview_id,
                    'interview_datetime': interview_datetime,
                    'location': location,
                    'contact_person': contact_person,
                    'contact_phone': contact_phone,
                    'instructions': instructions
                })
            
            # Send email notification
            try:
                from tasks import send_email_task_wrapper
                
                if interview_type == 'online':
                    email_template = 'email/interview_scheduled_online.html'
                    context = {
                        'applicant_name': applicant_name,
                        'job_title': job_title,
                        'interview_date': interview_date,
                        'interview_time': interview_time,
                        'google_meet_link': google_meet_link,
                        'instructions': instructions
                    }
                else:
                    email_template = 'email/interview_scheduled_onsite.html'
                    context = {
                        'applicant_name': applicant_name,
                        'job_title': job_title,
                        'interview_date': interview_date,
                        'interview_time': interview_time,
                        'location': location,
                        'contact_person': contact_person,
                        'contact_phone': contact_phone,
                        'instructions': instructions
                    }
                
                send_email_task_wrapper(
                    to=applicant_email,
                    subject=f'Interview Scheduled for {job_title}',
                    template=email_template,
                    context=context
                )
            except Exception as e:
                logger.error(f"Failed to send interview email: {e}")
            
            return jsonify({
                'success': True,
                'message': f'Interview scheduled successfully! Applicant notified via email.',
                'interview_id': interview_id
            })
        
        except Exception as e:
            logger.error(f"Error scheduling interview: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

@jobs_bp.route('/my-interviews')
@login_required
def my_interviews():
    """View all interviews for job seeker"""
    
    db = get_neo4j_db()
    with db.session() as session:
        # Get all interviews for the current user
        interviews = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:INVITED_TO]->(i:Interview)
            MATCH (i)-[:HAS_INTERVIEW]-(a:JobApplication)-[:FOR_JOB]->(j:Job)
            MATCH (j)-[:POSTED_BY]->(b:Business)
            MATCH (b)<-[:OWNS]-(owner:User)
            RETURN i, a, j, b, owner
            ORDER BY i.interview_datetime DESC
        """, {'user_id': current_user.id})
        
        interview_list = []
        for rec in interviews:
            interview_data = _node_to_dict(rec['i'])
            interview_data['job_title'] = rec['j']['title']
            interview_data['business_name'] = rec['b']['name']
            interview_data['owner_name'] = rec['owner']['username']
            interview_data['application_status'] = rec['a']['status']
            interview_list.append(interview_data)
        
        return render_template('interviews/my_interviews.html', interviews=interview_list)

@jobs_bp.route('/interview/<interview_id>/accept', methods=['POST'])
@login_required
def accept_interview(interview_id):
    """Accept interview invitation"""
    
    db = get_neo4j_db()
    with db.session() as session:
        result = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:INVITED_TO]->(i:Interview {id: $interview_id})
            SET i.status = 'accepted', i.applicant_response = 'accepted', i.response_date = datetime()
            RETURN i.id as interview_id
        """, {'user_id': current_user.id, 'interview_id': interview_id})
        
        if not result:
            return jsonify({'success': False, 'error': 'Interview not found'}), 403
        
        return jsonify({
            'success': True,
            'message': 'Interview acceptance confirmed!'
        })

@jobs_bp.route('/interview/<interview_id>/reject', methods=['POST'])
@login_required
def reject_interview(interview_id):
    """Reject interview invitation"""
    
    reason = request.form.get('reason', '')
    
    db = get_neo4j_db()
    with db.session() as session:
        result = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:INVITED_TO]->(i:Interview {id: $interview_id})
            SET i.status = 'rejected', i.applicant_response = 'rejected', 
                i.rejection_reason = $reason, i.response_date = datetime()
            RETURN i.id as interview_id
        """, {'user_id': current_user.id, 'interview_id': interview_id, 'reason': reason})
        
        if not result:
            return jsonify({'success': False, 'error': 'Interview not found'}), 403
        
        return jsonify({
            'success': True,
            'message': 'Interview invitation declined.'
        })

@jobs_bp.route('/applicant/<application_id>/message', methods=['POST'])
@login_required
@role_required('business_owner')
def message_applicant(application_id):
    """Send message to applicant"""
    
    message = request.form.get('message', '').strip()
    
    if not message:
        return jsonify({'success': False, 'error': 'Message cannot be empty'}), 400
    
    db = get_neo4j_db()
    with db.session() as session:
        # Verify ownership and get applicant info
        result = safe_run(session, """
            MATCH (applicant:User)-[:APPLIED_TO]->(a:JobApplication {id: $app_id})-[:FOR_JOB]->(j:Job)
            MATCH (j)-[:POSTED_BY]->(b:Business), (owner:User {id: $owner_id})-[:OWNS]->(b)
            RETURN applicant.email as applicant_email, applicant.username as applicant_name,
                   owner.username as owner_name, j.title as job_title, a.id as application_id
        """, {'app_id': application_id, 'owner_id': current_user.id})
        
        if not result:
            return jsonify({'success': False, 'error': 'Application not found or unauthorized'}), 403
        
        applicant_email = result[0]['applicant_email']
        applicant_name = result[0]['applicant_name']
        owner_name = result[0]['owner_name']
        job_title = result[0]['job_title']
        
        # Send email notification
        try:
            send_email_task.delay(
                to=applicant_email,
                subject=f'Message from {owner_name} regarding {job_title}',
                template='email/applicant_message.html',
                context={
                    'applicant_name': applicant_name,
                    'owner_name': owner_name,
                    'job_title': job_title,
                    'message': message
                }
            )
        except Exception as e:
            logger.error(f"Failed to send message email: {e}")
        
        flash('Message sent to applicant!', 'success')
        return jsonify({'success': True}), 200

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
    use_ai = request.args.get('ai', 'false').lower() == 'true'
    
    db = get_neo4j_db()
    with db.session() as session:
        cypher_query = """
            MATCH (j:Job)-[:POSTED_BY]->(b:Business)
            WHERE j.is_active = true
        """
        params = {'limit': limit}
        
        if query:
            # Use semantic AI search if enabled and query is provided
            if use_ai and query:
                try:
                    from gemini_client import get_gemini_response
                    
                    # Use AI to understand search intent and expand keywords
                    expansion_prompt = f"""The user is searching for jobs with this query: "{query}"
                    
Generate 3-5 alternative job titles, skills, or keywords that are semantically similar to what they might be looking for.
Return only the keywords/titles, one per line, without numbering or extra formatting.

Example:
If query is "code" - return variations like: programmer, developer, software engineer, coding, backend
If query is "sales" - return variations like: business development, sales representative, account executive, selling"""
                    
                    keywords_response = get_gemini_response(expansion_prompt)
                    expanded_keywords = [k.strip() for k in keywords_response.split('\n') if k.strip()]
                    
                    # Build search with both original and expanded keywords
                    search_conditions = [query] + expanded_keywords
                    or_conditions = " OR ".join([f"(j.title CONTAINS '{kw}' OR j.description CONTAINS '{kw}')" for kw in search_conditions[:5]])
                    cypher_query += f" AND ({or_conditions})"
                    
                    logger.info(f"AI-enhanced search for: {query}, expanded keywords: {expanded_keywords}")
                except Exception as e:
                    logger.warning(f"AI search expansion failed, falling back to basic search: {e}")
                    cypher_query += " AND (j.title CONTAINS $query OR j.description CONTAINS $query)"
                    params['query'] = query
            else:
                # Regular text search
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


@jobs_bp.route('/api/ai-search')
@login_required_optional
def ai_search_jobs():
    """AI-powered semantic job search that understands intent and synonyms"""
    
    query = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    limit = request.args.get('limit', 12, type=int)
    
    if not query or len(query) < 2:
        return jsonify({'error': 'Search query too short'}), 400
    
    try:
        from gemini_client import get_gemini_response
        
        logger.info(f"Starting AI semantic search for: {query}")
        
        # Step 1: Use Gemini to understand user intent and generate search variations
        intent_prompt = f"""The user is searching for jobs with this query: "{query}"

Analyze what they're looking for and return a JSON object with:
1. "primary_keywords": list of main keywords they're searching for
2. "related_keywords": list of related/synonymous terms (e.g., if they search "design", include "UI/UX", "graphic design", "web design")
3. "job_titles": list of job titles that match this search intent
4. "skills": list of skills that typically go with these jobs
5. "categories": list of likely job categories

Return ONLY valid JSON, no markdown or extra text.

Example for "coding":
{{"primary_keywords": ["coding", "code"], "related_keywords": ["programming", "developer", "software"], "job_titles": ["Software Developer", "Programmer", "Backend Developer"], "skills": ["Python", "JavaScript", "Java"], "categories": ["IT", "Software Development"]}}"""
        
        intent_response = get_gemini_response(intent_prompt)
        
        # Parse the intent response
        try:
            import json
            # Clean response if it has markdown
            if '```json' in intent_response:
                intent_response = intent_response.split('```json')[1].split('```')[0]
            elif '```' in intent_response:
                intent_response = intent_response.split('```')[1].split('```')[0]
            
            intent_data = json.loads(intent_response.strip())
            logger.info(f"Parsed intent data: {intent_data}")
        except Exception as parse_error:
            logger.warning(f"Failed to parse intent response: {parse_error}, using fallback")
            intent_data = {
                'primary_keywords': [query],
                'related_keywords': [],
                'job_titles': [query],
                'skills': [],
                'categories': []
            }
        
        # Step 2: Query database with expanded search terms
        db = get_neo4j_db()
        with db.session() as session:
            # Build search with all keywords
            all_keywords = intent_data.get('primary_keywords', []) + intent_data.get('related_keywords', []) + intent_data.get('job_titles', [])
            all_keywords = list(set([k.lower().strip() for k in all_keywords if k]))[:10]  # Limit to 10 unique keywords
            
            search_conditions = []
            for kw in all_keywords:
                search_conditions.append(f"(j.title ICONTAINS '{kw}' OR j.description ICONTAINS '{kw}')")
            
            where_clause = " OR ".join(search_conditions) if search_conditions else "1=1"
            
            cypher_query = f"""
                MATCH (j:Job)-[:POSTED_BY]->(b:Business)
                WHERE j.is_active = true AND ({where_clause})
            """
            
            if category:
                cypher_query += " AND j.category = $category"
            
            cypher_query += f"""
                RETURN j, b.name as business_name, 
                    (CASE 
                        WHEN j.title ICONTAINS '{query}' THEN 3
                        ELSE 1
                    END) as relevance_score
                ORDER BY relevance_score DESC, j.created_at DESC
                LIMIT {limit}
            """
            
            params = {}
            if category:
                params['category'] = category
            
            try:
                results = safe_run(session, cypher_query, params)
            except Exception as query_error:
                # Fallback to simpler query if complex one fails
                logger.warning(f"Complex query failed, using simple search: {query_error}")
                cypher_query = """
                    MATCH (j:Job)-[:POSTED_BY]->(b:Business)
                    WHERE j.is_active = true AND (j.title ICONTAINS $query OR j.description ICONTAINS $query)
                """
                if category:
                    cypher_query += " AND j.category = $category"
                
                cypher_query += f"""
                    RETURN j, b.name as business_name
                    ORDER BY j.created_at DESC
                    LIMIT {limit}
                """
                
                params = {'query': query}
                if category:
                    params['category'] = category
                
                results = safe_run(session, cypher_query, params)
            
            jobs = []
            for record in results:
                job_data = _node_to_dict(record['j'])
                job_data['business_name'] = record['business_name']
                jobs.append(job_data)
        
        logger.info(f"AI search found {len(jobs)} results for: {query}")
        
        return jsonify({
            'success': True,
            'query': query,
            'count': len(jobs),
            'search_intent': intent_data,
            'jobs': jobs
        })
    
    except Exception as e:
        logger.error(f"Error in AI search: {str(e)}", exc_info=True)
        # Fallback to regular search
        try:
            db = get_neo4j_db()
            with db.session() as session:
                cypher_query = """
                    MATCH (j:Job)-[:POSTED_BY]->(b:Business)
                    WHERE j.is_active = true AND (j.title CONTAINS $query OR j.description CONTAINS $query)
                """
                if category:
                    cypher_query += " AND j.category = $category"
                
                cypher_query += f"""
                    RETURN j, b.name as business_name
                    ORDER BY j.created_at DESC
                    LIMIT {limit}
                """
                
                params = {'query': query}
                if category:
                    params['category'] = category
                
                results = safe_run(session, cypher_query, params)
                
                jobs = []
                for record in results:
                    job_data = _node_to_dict(record['j'])
                    job_data['business_name'] = record['business_name']
                    jobs.append(job_data)
            
            return jsonify({
                'success': True,
                'query': query,
                'count': len(jobs),
                'jobs': jobs,
                'note': 'Search fell back to basic mode'
            })
        except Exception as fallback_error:
            logger.error(f"Fallback search also failed: {fallback_error}")
            return jsonify({
                'success': False,
                'error': 'Search temporarily unavailable. Please try again.'
            }), 500

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