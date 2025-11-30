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
        resume_file = request.files.get('resume')
        
        # Validate resume
        if not resume_file or resume_file.filename == '':
            flash('Resume is required.', 'error')
            return redirect(url_for('jobs.apply_job', job_id=job_id))
        
        # Save resume file
        filename = secure_filename(resume_file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        if file_ext not in ['pdf', 'doc', 'docx', 'txt']:
            flash('Only PDF, DOC, DOCX, and TXT files are allowed.', 'error')
            return redirect(url_for('jobs.apply_job', job_id=job_id))
        
        # Create application
        application_id = str(uuid.uuid4())
        resume_filename = f"{application_id}.{file_ext}"
        resume_path = f"applications/{current_user.id}/{job_id}/{resume_filename}"
        
        full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], resume_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        try:
            resume_file.save(full_path)
        except Exception as e:
            logger.error(f"Failed to save resume: {str(e)}")
            flash('Failed to save resume. Please try again.', 'error')
            return redirect(url_for('jobs.apply_job', job_id=job_id))
        
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
            'resume_file': resume_path,
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
                    'app_dashboard_url': url_for('dashboard.business_applications', _external=True)
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
        return redirect(url_for('jobs.my_applications'))

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
