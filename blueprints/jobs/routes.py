import uuid
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import logging

from . import jobs_bp
from database import get_neo4j_db, safe_run, _node_to_dict
from models import Job, JobApplication, Business
from forms import JobForm, ReviewForm
from decorators import role_required, login_required_optional

logger = logging.getLogger(__name__)

@jobs_bp.route('/<job_id>')
@login_required_optional
def job_detail(job_id):
    db = get_neo4j_db()
    with db.session() as session:
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
        job_data['business_name'] = record['b']['name']
        job_data['business_id'] = record['b']['id']
        job_data['business_rating'] = record['avg_rating'] or 0
        job_data['business_review_count'] = record['review_count'] or 0
        job = Job(**job_data)
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
        has_applied = False
        if current_user.is_authenticated:
            application = safe_run(session, """
                MATCH (u:User {id: $user_id})-[:APPLIED_TO]->(j:Job {id: $job_id})
                RETURN count(*) as count
            """, {'user_id': current_user.id, 'job_id': job_id})
            has_applied = application[0]['count'] > 0
    return render_template('jobs/job_detail.html', job=job, business=business, has_applied=has_applied)




import uuid
import logging
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os

from . import jobs_bp
from database import get_neo4j_db, safe_run, _node_to_dict, _record_to_dict
from models import Job, JobApplication
from forms import JobForm, JobApplicationForm, SearchForm
from decorators import role_required, login_required_optional, json_response, verified_required
from tasks import send_email_task, create_notification_task
from app import cache  # Import the cache extension

logger = logging.getLogger(__name__)

@jobs_bp.route('/')
@login_required_optional
@cache.cached(timeout=300)  # Cache for 5 minutes
def list_jobs():
    """List all jobs with search and filtering"""
    form = SearchForm(request.args)
    
    # Build query
    query = """
        MATCH (j:Job)-[:POSTED_BY]->(b:Business)
        WHERE j.is_active = true
    """
    params = {}
    
    # Add search filters
    if form.query.data:
        query += " AND (j.title CONTAINS $query OR j.description CONTAINS $query)"
        params['query'] = form.query.data
    
    if form.category.data:
        query += " AND j.category = $category"
        params['category'] = form.category.data
    
    if form.location.data:
        query += " AND j.location CONTAINS $location"
        params['location'] = form.location.data
    
    # Add sorting
    sort_by = form.sort_by.data or 'created_at'
    if sort_by == 'rating':
        query += """
            OPTIONAL MATCH (b)<-[:REVIEWS]-(r:Review)
            WITH j, b, avg(r.rating) as avg_rating
        """
        query += " ORDER BY avg_rating DESC"
    elif sort_by == 'name':
        query += " ORDER BY j.title ASC"
    else:  # created_at
        query += " ORDER BY j.created_at DESC"
    
    # Add pagination
    page = request.args.get('page', 1, type=int)
    per_page = 12
    skip = (page - 1) * per_page
    
    query += f" SKIP $skip LIMIT $limit"
    params['skip'] = skip
    params['limit'] = per_page
    
    query += """
        RETURN j, b.name as business_name, b.id as business_id
    """
    
    db = get_neo4j_db()
    with db.session() as session:
        jobs = safe_run(session, query, params)
        
        # Get total count for pagination
        count_query = """
            MATCH (j:Job)
            WHERE j.is_active = true
        """
        count_params = {}
        
        if form.query.data:
            count_query += " AND (j.title CONTAINS $query OR j.description CONTAINS $query)"
            count_params['query'] = form.query.data
        
        if form.category.data:
            count_query += " AND j.category = $category"
            count_params['category'] = form.category.data
        
        if form.location.data:
            count_query += " AND j.location CONTAINS $location"
            count_params['location'] = form.location.data
        
        count_query += " RETURN count(j) as total"
        
        total_result = safe_run(session, count_query, count_params)
        total = total_result[0]['total'] if total_result else 0

        # Compute category counts for sidebar (defaults to 0 if not present)
        category_count_results = safe_run(session, """
            MATCH (j:Job)
            WHERE j.is_active = true
            RETURN j.category as category, count(j) as count
        """, {})
        category_counts = {}
        for r in category_count_results:
            key = r.get('category') or 'other'
            # normalize to lowercase keys used in template
            category_counts[key.lower()] = r.get('count', 0)
    
    # Convert to Job objects
    job_list = []
    for record in jobs:
        job_data = _node_to_dict(record['j'])
        job_data['business_name'] = record['business_name']
        job_data['business_id'] = record['business_id']
        job_list.append(Job(**job_data))
    
    return render_template('jobs.html',
        jobs=job_list,
        form=form,
        category_counts=category_counts,
        pagination={
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page
        }
    )

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
        
        # Geocode location if needed
        if form.location.data:
            from tasks import geocode_location_task
            geocode_result = geocode_location_task.delay(form.location.data)
            if geocode_result:
                job_data['latitude'] = geocode_result.get('latitude')
                job_data['longitude'] = geocode_result.get('longitude')
        
        # Create job
        with db.session() as session:
            safe_run(session, """
                CREATE (j:Job $job_data)
                WITH j
                MATCH (b:Business {id: $business_id})
                CREATE (b)-[:POSTED_BY]->(j)
            """, {'job_data': job_data, 'business_id': form.business_id.data})
            
            # Get business name for the job object
            business_result = safe_run(session, """
                MATCH (b:Business {id: $business_id})
                RETURN b.name as name
            """, {'business_id': form.business_id.data})
            
            if business_result:
                job_data['business_name'] = business_result[0]['name']
        
        # Create notification for followers
        create_notification_task.delay(
            type='new_job',
            title='New Job Posted',
            message=f'A new job "{form.title.data}" has been posted',
            data={'job_id': job_id, 'business_id': form.business_id.data}
        )
        
        flash('Job posted successfully!', 'success')
        return redirect(url_for('jobs.job_detail', job_id=job_id))
    
    return render_template('jobs/jobs_create.html', form=form)

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
@role_required('job_seeker')
def my_applications():
    """View user's job applications as a job seeker"""
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
    
    return render_template('jobs/jobs_applications.html', applications=application_list)

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

@jobs_bp.route('/api/search')
@json_response
def api_search_jobs():
    """API endpoint for job search"""
    query = request.args.get('q', '')
    category = request.args.get('category', '')
    location = request.args.get('location', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    db = get_neo4j_db()
    with db.session() as session:
        # Build query
        cypher_query = """
            MATCH (j:Job)-[:POSTED_BY]->(b:Business)
            WHERE j.is_active = true
        """
        params = {}
        
        if query:
            cypher_query += " AND (j.title CONTAINS $query OR j.description CONTAINS $query)"
            params['query'] = query
        
        if category:
            cypher_query += " AND j.category = $category"
            params['category'] = category
        
        if location:
            cypher_query += " AND j.location CONTAINS $location"
            params['location'] = location
        
        # Add pagination
        skip = (page - 1) * per_page
        cypher_query += f" SKIP $skip LIMIT $limit"
        params['skip'] = skip
        params['limit'] = per_page
        
        cypher_query += """
            RETURN j, b.name as business_name
            ORDER BY j.created_at DESC
        """
        
        results = safe_run(session, cypher_query, params)
        
        jobs = []
        for record in results:
            job_data = _node_to_dict(record['j'])
            job_data['business_name'] = record['business_name']
            jobs.append(job_data)
    
    return {
        'jobs': jobs,
        'page': page,
        'per_page': per_page,
        'total': len(jobs)
    }

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


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