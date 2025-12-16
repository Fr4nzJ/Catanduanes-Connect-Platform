import uuid
import logging
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from tasks import geocode_location_sync 
from . import businesses_bp
from database import get_neo4j_db, safe_run, _node_to_dict, _record_to_dict
from models import Business, Review
from forms import BusinessForm, ReviewForm, SearchForm
from decorators import role_required, login_required_optional, json_response, verified_required, business_owner_required
from tasks import send_email_task, create_notification_task
from app import cache  # Import the cache extension

logger = logging.getLogger(__name__)

@businesses_bp.route('/categories')
@login_required_optional
def categories_overview():
    """Display all categories with statistics"""
    db = get_neo4j_db()
    with db.session() as session:
        # Get all categories with stats
        query = """
            MATCH (b:Business)
            WHERE b.is_active = true
            WITH b.category as category, COUNT(b) as count, AVG(b.rating) as avg_rating, 
                 COUNT(CASE WHEN b.is_verified THEN 1 END) as verified_count
            RETURN category, count, avg_rating, verified_count
            ORDER BY count DESC
        """
        
        results = safe_run(session, query, {})
        
        categories = []
        for record in results:
            if record['category']:
                categories.append({
                    'name': record['category'],
                    'count': record['count'],
                    'avg_rating': record['avg_rating'] or 0.0,
                    'verified_count': record['verified_count'],
                    'verified_percentage': (record['verified_count'] / record['count'] * 100) if record['count'] > 0 else 0
                })
    
    return render_template('categories_overview.html', categories=categories)

@businesses_bp.route('/')
@login_required_optional
@cache.cached(timeout=300, query_string=True)   # ← add query_string=True
def list_businesses():
    """List all businesses with search and filtering"""
    form = SearchForm(request.args)
    
    # Get filter parameters
    query_text = form.query.data or ''
    category = form.category.data or ''
    location = form.location.data or ''
    min_rating = request.args.get('min_rating', '0', type=str)
    try:
        min_rating = float(min_rating) if min_rating != '0' else 0
    except (ValueError, TypeError):
        min_rating = 0
    
    verified_only = request.args.get('verified_only') == 'true'
    sort_by = form.sort_by.data or 'created_at'
    
    # Build query
    query = """
        MATCH (b:Business)
        WHERE b.is_active = true
    """
    params = {}
    
    # Add search filters
    if query_text:
        query += " AND (b.name CONTAINS $query OR b.description CONTAINS $query)"
        params['query'] = query_text
    
    if category:
        query += " AND b.category = $category"
        params['category'] = category
    
    if location:
        query += " AND b.address CONTAINS $location"
        params['location'] = location
    
    if min_rating > 0:
        query += " AND b.rating >= $min_rating"
        params['min_rating'] = min_rating
    
    if verified_only:
        query += " AND b.is_verified = true"
    
    # Add sorting
    if sort_by == 'rating':
        query += " ORDER BY b.rating DESC"
    elif sort_by == 'reviews':
        query += " ORDER BY b.review_count DESC"
    elif sort_by == 'name':
        query += " ORDER BY b.name ASC"
    else:  # created_at
        query += " ORDER BY b.created_at DESC"
    
    # Add pagination
    page = request.args.get('page', 1, type=int)
    per_page = 12
    skip = (page - 1) * per_page
    
    query += f" SKIP $skip LIMIT $limit"
    params['skip'] = skip
    params['limit'] = per_page
    
    query += """
        RETURN b
    """
    
    db = get_neo4j_db()
    with db.session() as session:
        businesses = safe_run(session, query, params)
        
        # Get total count for pagination
        count_query = """
            MATCH (b:Business)
            WHERE b.is_active = true
        """
        count_params = {}
        
        if query_text:
            count_query += " AND (b.name CONTAINS $query OR b.description CONTAINS $query)"
            count_params['query'] = query_text
        
        if category:
            count_query += " AND b.category = $category"
            count_params['category'] = category
        
        if location:
            count_query += " AND b.address CONTAINS $location"
            count_params['location'] = location
        
        if min_rating > 0:
            count_query += " AND b.rating >= $min_rating"
            count_params['min_rating'] = min_rating
        
        if verified_only:
            count_query += " AND b.is_verified = true"
        
        count_query += " RETURN count(b) as total"
        
        total_result = safe_run(session, count_query, count_params)
        total = total_result[0]['total'] if total_result else 0
    
    # Convert to Business objects and handle pagination
    business_list = []
    business_dicts = []  # Keep dictionaries for JSON serialization in map
    for record in businesses:
        business_data = _node_to_dict(record['b'])
        logger.info(f"Processing business: ID={business_data.get('id')}, Name={business_data.get('name')}")
        business = Business(**business_data)
        logger.info(f"Created Business object: ID={business.id}, Name={business.name}")
        business_list.append(business)
        # Also store as dict for map feature (JSON serializable)
        business_dicts.append(business_data)
        
    # Calculate pagination values
    total_pages = (total + per_page - 1) // per_page
    has_next = page < total_pages
    has_prev = page > 1
    
    # Create pagination object
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': total_pages,
        'has_next': has_next,
        'has_prev': has_prev,
        'next_num': page + 1 if has_next else None,
        'prev_num': page - 1 if has_prev else None
    }
    
    return render_template('businesses.html',
        businesses=business_list,
        businesses_data=business_dicts,  # Pass dicts for map JSON serialization
        form=form,
        pagination=pagination,
        total_pages=total_pages,
        current_page=page
    )

@businesses_bp.route('/search/advanced')
@login_required_optional
def advanced_search():
    """Advanced search for businesses with multiple filters"""
    query_text = request.args.get('q', '').strip()
    category = request.args.get('category', '')
    location = request.args.get('location', '').strip()
    min_rating = request.args.get('min_rating', 0, type=float)
    verified_only = request.args.get('verified_only', False, type=bool)
    page = request.args.get('page', 1, type=int)
    per_page = 12
    skip = (page - 1) * per_page
    
    logger.info(f"Advanced search: query={query_text}, category={category}, location={location}, min_rating={min_rating}")
    
    db = get_neo4j_db()
    with db.session() as session:
        # Build dynamic query
        cypher_query = """
            MATCH (b:Business)
            WHERE b.is_active = true
        """
        params = {}
        
        # Search by text (name or description)
        if query_text:
            cypher_query += " AND (b.name CONTAINS $query OR b.description CONTAINS $query)"
            params['query'] = query_text
        
        # Filter by category
        if category:
            cypher_query += " AND b.category = $category"
            params['category'] = category
        
        # Filter by location
        if location:
            cypher_query += " AND b.address CONTAINS $location"
            params['location'] = location
        
        # Filter by minimum rating
        if min_rating > 0:
            cypher_query += " AND b.rating >= $min_rating"
            params['min_rating'] = min_rating
        
        # Filter verified businesses only
        if verified_only:
            cypher_query += " AND b.is_verified = true"
        
        # Add pagination and return
        cypher_query += f" SKIP $skip LIMIT $limit RETURN b ORDER BY b.created_at DESC"
        params['skip'] = skip
        params['limit'] = per_page
        
        businesses = safe_run(session, cypher_query, params)
        
        # Get total count
        count_query = """
            MATCH (b:Business)
            WHERE b.is_active = true
        """
        count_params = {}
        
        if query_text:
            count_query += " AND (b.name CONTAINS $query OR b.description CONTAINS $query)"
            count_params['query'] = query_text
        if category:
            count_query += " AND b.category = $category"
            count_params['category'] = category
        if location:
            count_query += " AND b.address CONTAINS $location"
            count_params['location'] = location
        if min_rating > 0:
            count_query += " AND b.rating >= $min_rating"
            count_params['min_rating'] = min_rating
        if verified_only:
            count_query += " AND b.is_verified = true"
        
        count_query += " RETURN count(b) as total"
        total_result = safe_run(session, count_query, count_params)
        total = total_result[0]['total'] if total_result else 0
    
    # Convert to Business objects
    business_list = []
    for record in businesses:
        business_data = _node_to_dict(record['b'])
        business = Business(**business_data)
        business_list.append(business)
    
    # Calculate pagination
    total_pages = (total + per_page - 1) // per_page
    has_next = page < total_pages
    has_prev = page > 1
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': total_pages,
        'has_next': has_next,
        'has_prev': has_prev,
        'next_num': page + 1 if has_next else None,
        'prev_num': page - 1 if has_prev else None
    }
    
    return render_template('businesses_search.html',
        businesses=business_list,
        pagination=pagination,
        search_query=query_text,
        selected_category=category,
        selected_location=location,
        min_rating=min_rating,
        verified_only=verified_only,
        total_results=total
    )

@businesses_bp.route('/featured')
@login_required_optional
def featured_businesses():
    """Display featured businesses"""
    db = get_neo4j_db()
    with db.session() as session:
        # Get featured businesses with highest ratings first
        query = """
            MATCH (b:Business)
            WHERE b.is_active = true AND b.is_featured = true
            ORDER BY b.rating DESC
            LIMIT 8
            RETURN b
        """
        
        results = safe_run(session, query, {})
        
        business_list = []
        for record in results:
            business_data = _node_to_dict(record['b'])
            logger.info(f"Processing featured business: ID={business_data.get('id')}, Name={business_data.get('name')}")
            business = Business(**business_data)
            business_list.append(business)
    
    return render_template('featured_businesses.html',
        businesses=business_list,
        total_featured=len(business_list)
    )

@businesses_bp.route('/category/<category>')
@login_required_optional
def category_detail(category):
    """Display businesses by category"""
    logger.info(f"Viewing category: {category}")
    
    db = get_neo4j_db()
    with db.session() as session:
        # Get category statistics
        stats_query = """
            MATCH (b:Business)
            WHERE b.is_active = true AND b.category = $category
            RETURN 
                COUNT(b) as total_count,
                AVG(b.rating) as avg_rating,
                COUNT(CASE WHEN b.is_verified THEN 1 END) as verified_count,
                COUNT(CASE WHEN b.review_count > 0 THEN 1 END) as reviewed_count
        """
        
        stats_result = safe_run(session, stats_query, {'category': category})
        
        if not stats_result or stats_result[0]['total_count'] == 0:
            logger.warning(f"Category not found: {category}")
            flash(f'Category "{category}" not found.', 'error')
            return redirect(url_for('businesses.list_businesses'))
        
        stats = stats_result[0]
        
        # Get businesses in this category with pagination
        page = request.args.get('page', 1, type=int)
        per_page = 12
        skip = (page - 1) * per_page
        
        query = """
            MATCH (b:Business)
            WHERE b.is_active = true AND b.category = $category
            ORDER BY b.rating DESC, b.review_count DESC
            SKIP $skip LIMIT $limit
            RETURN b
        """
        
        results = safe_run(session, query, {
            'category': category,
            'skip': skip,
            'limit': per_page
        })
        
        # Get total for pagination
        total = stats['total_count']
        total_pages = (total + per_page - 1) // per_page
        
        business_list = []
        for record in results:
            business_data = _node_to_dict(record['b'])
            business = Business(**business_data)
            business_list.append(business)
        
        # Create pagination object
        pagination = {
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1,
            'next_num': page + 1 if page < total_pages else None,
            'prev_num': page - 1 if page > 1 else None
        }
    
    return render_template('category_detail.html',
        category=category,
        businesses=business_list,
        stats=stats,
        pagination=pagination,
        current_page=page
    )

@businesses_bp.route('/<business_id>')
@login_required_optional
def business_detail(business_id):
    """Business detail page"""
    logger.info(f"Accessing business detail for ID: {business_id}")
    
    # Debug logging for ID format
    logger.debug(f"Business ID type: {type(business_id)}, value: {business_id}")
    
    db = get_neo4j_db()
    with db.session() as session:
        # First, try to find the business with more detailed query
        logger.debug("Executing business search query...")
        basic_result = safe_run(session, """
            MATCH (b:Business)
            WHERE b.id = $business_id OR toString(b.id) = $business_id
            RETURN b
        """, {'business_id': business_id})
        
        # Log the query result
        logger.debug(f"Query result: {basic_result if basic_result else 'No results'}")
        
        if not basic_result:
            logger.error(f"Business not found with ID: {business_id}")
            flash('Business not found.', 'error')
            return redirect(url_for('businesses.list_businesses'))
            
        # Now get the full details
        result = safe_run(session, """
            MATCH (b:Business {id: $business_id})
            OPTIONAL MATCH (u:User)-[:REVIEWS]->(review:Review)-[:FOR_BUSINESS]->(b)
            OPTIONAL MATCH (j:Job)-[:POSTED_BY]->(b)
            WHERE j.is_active = true
            WITH b, avg(review.rating) as avg_rating, count(DISTINCT review) as review_count,
                 count(DISTINCT j) as job_count
            RETURN b, avg_rating, review_count, job_count
        """, {'business_id': business_id})
        
        if not result:
            logger.error(f"Failed to get business details for ID: {business_id}")
            flash('Error loading business details.', 'error')
            return redirect(url_for('businesses.list_businesses'))
        
        record = result[0]
        business_data = _node_to_dict(record['b'])
        business_data['rating'] = record['avg_rating'] or 0
        business_data['review_count'] = record['review_count'] or 0
        business_data['job_count'] = record['job_count'] or 0
        
        business = Business(**business_data)
        
        # Get reviews
        reviews = safe_run(session, """
            MATCH (u:User)-[:REVIEWS]->(r:Review)-[:FOR_BUSINESS]->(b:Business {id: $business_id})
            RETURN r           AS review_node,
                   u.username  AS reviewer_name
            ORDER BY r.created_at DESC
            LIMIT 10
        """, {'business_id': business_id})
        
        logger.info(f"Found {len(reviews) if reviews else 0} reviews for business {business_id}")
        
        review_list = []
        for rec in reviews:
            review_data = _node_to_dict(rec['review_node'])
            review_data['reviewer_name'] = rec['reviewer_name']
            review_list.append(Review(**review_data))
        
        # Get jobs
        jobs = safe_run(session, """
            MATCH (b:Business {id: $business_id})-[:POSTED_BY]->(j:Job)
            WHERE j.is_active = true
            RETURN j
            ORDER BY j.created_at DESC
            LIMIT 5
        """, {'business_id': business_id})
        
        job_list = []
        for job_record in jobs:
            job_data = _node_to_dict(job_record['j'])
            job_list.append(job_data)
    
    return render_template('business_detail.html',
        business=business,
        reviews=review_list,
        jobs=job_list
    )

@businesses_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required('business_owner')
def create_business():
    """Create new business"""
    form = BusinessForm()
    
    if form.validate_on_submit():
        business_id = str(uuid.uuid4())
        
        # Handle permit file upload
        permit_file = form.permit_file.data
        filename = secure_filename(permit_file.filename)
        permit_path = f"businesses/{business_id}/{filename}"
        full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], permit_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        permit_file.save(full_path)
        
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
            'permit_file': permit_path,
            'owner_id': current_user.id,
            'is_verified': False,
            'is_active': True,
            'created_at': datetime.utcnow().isoformat(),
            'rating': 0.0,
            'review_count': 0
        }
        
        # Geocode address

        manual_lat = request.form.get('latitude')
        manual_lng = request.form.get('longitude')
        if manual_lat and manual_lng:
            business_data['latitude']  = float(manual_lat)
            business_data['longitude'] = float(manual_lng)
        else:
            # your existing geocode fallback
            from tasks import geocode_location_sync   # the plain function
            result = geocode_location_sync(form.address.data)
            if result:
                lat, lon = result.get('latitude'), result.get('longitude')
                if lat and lon:
                    business_data['latitude']  = lat
                    business_data['longitude'] = lon
        # --------------------------------------------
        # --------------------------------------------
        
        db = get_neo4j_db()
        with db.session() as session:
            # Create business
            safe_run(session, """
                CREATE (b:Business $business_data)
                WITH b
                MATCH (u:User {id: $user_id})
                CREATE (u)-[:OWNS]->(b)
            """, {'business_data': business_data, 'user_id': current_user.id})
        
        # Send verification request to admin
        create_notification_task(
            type='business_verification',
            title='New Business Registration',
            message=f'New business "{form.name.data}" requires verification',
            data={'business_id': business_id, 'owner_id': current_user.id}
        )
        
        flash('Business registration submitted successfully! It will be reviewed by our team.', 'success')
        return redirect(url_for('businesses.business_detail', business_id=business_id))
    
    return render_template('business/businesses_create.html', form=form)

@businesses_bp.route('/<business_id>/review', methods=['POST'])
def add_review(business_id):
    """Add review to business (AJAX/JSON only, always returns JSON)"""
    # Check authentication, always return JSON for AJAX
    if not current_user.is_authenticated:
        return jsonify({'error': 'Authentication required. Please log in.'}), 401
    try:
        # Get JSON data from request
        data = request.get_json() or {}
        
        # Validate required fields
        rating = data.get('rating')
        comment = data.get('comment', '').strip()
        
        if not rating or not comment:
            return jsonify({'error': 'Rating and comment are required'}), 400
        
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                return jsonify({'error': 'Rating must be between 1 and 5'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid rating value'}), 400
        
        if len(comment) < 10:
            return jsonify({'error': 'Comment must be at least 10 characters long'}), 400
        
        if len(comment) > 500:
            return jsonify({'error': 'Comment must not exceed 500 characters'}), 400
        
        db = get_neo4j_db()
        with db.session() as session:
            # Check if business exists
            business_result = safe_run(session, """
                MATCH (b:Business {id: $business_id})
                RETURN b.id as business_id
            """, {'business_id': business_id})
            
            if not business_result:
                return jsonify({'error': 'Business not found'}), 404
            
            # Check if user has already reviewed this business
            existing_review = safe_run(session, """
                MATCH (u:User {id: $user_id})-[:REVIEWS]->(r:Review)-[:FOR_BUSINESS]->(b:Business {id: $business_id})
                RETURN r.id as review_id
            """, {'user_id': current_user.id, 'business_id': business_id})
            
            if existing_review:
                return jsonify({'error': 'You have already reviewed this business'}), 409
            
            # Create review
            review_id = str(uuid.uuid4())
            created_at = datetime.utcnow().isoformat()
            
            # Create the review node and relationships
            create_result = safe_run(session, """
                CREATE (r:Review {
                    id: $review_id,
                    rating: $rating,
                    comment: $comment,
                    reviewer_name: $reviewer_name,
                    created_at: $created_at,
                    updated_at: $created_at
                })
                WITH r
                MATCH (u:User {id: $user_id}), (b:Business {id: $business_id})
                CREATE (u)-[:REVIEWS]->(r)-[:FOR_BUSINESS]->(b)
                RETURN r.id as review_id
            """, {
                'review_id': review_id,
                'rating': rating,
                'comment': comment,
                'reviewer_name': current_user.username,
                'created_at': created_at,
                'user_id': current_user.id,
                'business_id': business_id
            })
            
            if not create_result:
                logger.error(f"Failed to create review for business {business_id}")
                return jsonify({'error': 'Failed to create review'}), 500
            
            logger.info(f"Review created successfully: {review_id} for business {business_id} by user {current_user.id}")
            
            # Update business rating
            update_result = safe_run(session, """
                MATCH (b:Business {id: $business_id})<-[:REVIEWS]-(r:Review)
                WITH b, avg(r.rating) as avg_rating, count(r) as review_count
                SET b.rating = ROUND(avg_rating * 10) / 10,
                    b.review_count = review_count
                RETURN b.rating as new_rating, b.review_count as new_count
            """, {'business_id': business_id})
            
            logger.info(f"Updated business rating for {business_id}")
            
            # Create notification for business owner
            owner_result = safe_run(session, """
                MATCH (owner:User)-[:OWNS]->(b:Business {id: $business_id})
                RETURN owner.id as owner_id
            """, {'business_id': business_id})
            
            if owner_result and owner_result[0]['owner_id']:
                try:
                    create_notification_task(
                        user_id=owner_result[0]['owner_id'],
                        type='new_review',
                        title='New Review',
                        message=f'{current_user.username} left a {rating}/5 review for your business',
                        data={
                            'review_id': review_id,
                            'business_id': business_id,
                            'rating': rating
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to create notification: {str(e)}")
        
        return jsonify({
            'success': True,
            'message': 'Review submitted successfully!',
            'review_id': review_id
        }), 201
    except Exception as e:
        logger.error(f"Error adding review: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to submit review. Please try again.'}), 500

@businesses_bp.route('/dashboard')
@login_required
@role_required('business_owner')
def dashboard():
    """Business-owner dashboard with live counters."""
    db = get_neo4j_db()

    # ---------- 1.  OWNER-SPECIFIC STATS ----------
    with db.session() as session:
        stats = safe_run(session, """
            MATCH (u:User {id: $uid})
            
            // total businesses owned
            OPTIONAL MATCH (u)-[:OWNS]->(b:Business)
            WITH u, count(DISTINCT b) AS business_count
            
            // total jobs posted (active jobs from owned businesses)
            OPTIONAL MATCH (u)-[:OWNS]->(b2:Business)<-[:POSTED_BY]-(j:Job)
            WHERE j.is_active = true
            WITH u, business_count, count(DISTINCT j) AS job_count
            
            // filled jobs (jobs with filled status)
            OPTIONAL MATCH (u)-[:OWNS]->(b3:Business)<-[:POSTED_BY]-(j2:Job)
            WHERE j2.status = 'filled'
            WITH u, business_count, job_count, count(DISTINCT j2) AS filled_jobs
            
            // total applicants (applications to user's jobs)
            OPTIONAL MATCH (u)-[:OWNS]->(b4:Business)<-[:POSTED_BY]-(j3:Job)<-[:FOR_JOB]-(a:JobApplication)
            WITH u, business_count, job_count, filled_jobs, count(DISTINCT a) AS application_count
            
            // pending applicants (applications with pending status)
            OPTIONAL MATCH (u)-[:OWNS]->(b5:Business)<-[:POSTED_BY]-(j4:Job)<-[:FOR_JOB]-(a2:JobApplication)
            WHERE a2.status = 'pending'
            
            RETURN business_count,
                   job_count,
                   filled_jobs,
                   application_count,
                   count(DISTINCT a2) AS pending_applicants
        """, {"uid": current_user.id})[0]

    # ---------- 2.  BUSINESS & APPLICATION LISTS (your original queries) ----------
    with db.session() as session:
        businesses = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:OWNS]->(b:Business)
            OPTIONAL MATCH (b)<-[:FOR_BUSINESS]-(r:Review)
            OPTIONAL MATCH (b)<-[:POSTED_BY]-(j:Job) WHERE j.is_active = true
            WITH b, 
                 avg(CASE WHEN r IS NOT NULL THEN r.rating ELSE null END) as avg_rating,
                 count(DISTINCT r) as review_count,
                 count(DISTINCT j) as jobs_count
            RETURN b, avg_rating, review_count, jobs_count
            ORDER BY b.created_at DESC
        """, {"user_id": current_user.id})

        business_list = []
        for rec in businesses:
            b = Business(**_node_to_dict(rec["b"]))
            b.rating = rec["avg_rating"] or 0
            b.reviews_count = rec["review_count"] or 0
            b.jobs_count = rec["jobs_count"] or 0
            business_list.append(b)

        applications = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:OWNS]->(b:Business)-[:POSTED_BY]->(j:Job)
            MATCH (applicant:User)-[:APPLIED_TO]->(a:JobApplication)-[:FOR_JOB]->(j)
            RETURN a, j, applicant.username as applicant_name
            ORDER BY a.created_at DESC
            LIMIT 10
        """, {"user_id": current_user.id})

        application_list = [
            {
                **_node_to_dict(rec["a"]),
                "job_title": rec["j"]["title"],
                "applicant_name": rec["applicant_name"],
            }
            for rec in applications
        ]

    # ---------- 3.  RENDER ----------
    return render_template(
        "business/business_owner_dashboard.html",
        stats=stats,
        businesses=business_list,
        applications=application_list
    )

@businesses_bp.route('/<business_id>/edit', methods=['GET', 'POST'])
@login_required
@business_owner_required
def edit_business(business_id):
    """Edit business information"""
    db = get_neo4j_db()
    with db.session() as session:
        # Get business
        business_result = safe_run(session, """
            MATCH (b:Business {id: $business_id})
            RETURN b
        """, {'business_id': business_id})
        
        if not business_result:
            flash('Business not found.', 'error')
            return redirect(url_for('businesses.dashboard'))
        
        business_data = _node_to_dict(business_result[0]['b'])
    
    form = BusinessForm(obj=business_data)
    
    if form.validate_on_submit():
        update_data = {
            'name': form.name.data,
            'description': form.description.data,
            'category': form.category.data,
            'address': form.address.data,
            'phone': form.phone.data,
            'email': form.email.data,
            'website': form.website.data,
            'permit_number': form.permit_number.data
        }
        
        # Handle new permit file
        if form.permit_file.data:
            permit_file = form.permit_file.data
            filename = secure_filename(permit_file.filename)
            permit_path = f"businesses/{business_id}/{filename}"
            full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], permit_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            permit_file.save(full_path)
            update_data['permit_file'] = permit_path
        
        # Geocode address if changed
        if form.address.data != business_data.get('address'):
            from tasks import geocode_location_task
            geocode_result = geocode_location_task.delay(form.address.data)
            if geocode_result:
                lat, lon = geocode_result.get('latitude'), geocode_result.get('longitude')
                if lat and lon:
                    update_data['latitude'] = lat
                    update_data['longitude'] = lon
        
        db = get_neo4j_db()
        with db.session() as session:
            # Update business
            safe_run(session, """
                MATCH (b:Business {id: $business_id})
                SET b += $update_data
            """, {'business_id': business_id, 'update_data': update_data})
        
        flash('Business updated successfully!', 'success')
        return redirect(url_for('businesses.business_detail', business_id=business_id))
    
    return render_template('business/businesses_edit.html', form=form, business=business_data)

@businesses_bp.route('/api/search')
@json_response
def api_search_businesses():
    """API endpoint for business search"""
    query = request.args.get('q', '')
    category = request.args.get('category', '')
    location = request.args.get('location', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    db = get_neo4j_db()
    with db.session() as session:
        # Build query
        cypher_query = """
            MATCH (b:Business)
            WHERE b.is_active = true
        """
        params = {}
        
        if query:
            cypher_query += " AND (b.name CONTAINS $query OR b.description CONTAINS $query)"
            params['query'] = query
        
        if category:
            cypher_query += " AND b.category = $category"
            params['category'] = category
        
        if location:
            cypher_query += " AND b.address CONTAINS $location"
            params['location'] = location
        
        # Add pagination
        skip = (page - 1) * per_page
        cypher_query += f" SKIP $skip LIMIT $limit"
        params['skip'] = skip
        params['limit'] = per_page
        
        cypher_query += """
            RETURN b
            ORDER BY b.created_at DESC
        """
        
        results = safe_run(session, cypher_query, params)
        
        businesses = []
        for record in results:
            business_data = _node_to_dict(record['b'])
            businesses.append(business_data)
    
    return {
        'businesses': businesses,
        'page': page,
        'per_page': per_page,
        'total': len(businesses)
    }

@businesses_bp.route('/api/ai-search')
@login_required_optional
def ai_search_businesses():
    """AI-powered semantic business search that understands intent and synonyms"""
    
    query = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    limit = request.args.get('limit', 12, type=int)
    
    if not query or len(query) < 2:
        return jsonify({'error': 'Search query too short'}), 400
    
    try:
        from gemini_client import get_gemini_response
        
        logger.info(f"Starting AI semantic search for businesses: {query}")
        
        # Step 1: Use Gemini to understand user intent and generate search variations
        intent_prompt = f"""The user is searching for businesses with this query: "{query}"

Analyze what they're looking for and return a JSON object with:
1. "primary_keywords": list of main keywords they're searching for
2. "related_keywords": list of related/synonymous terms (e.g., if they search "restaurant", include "food", "dining", "cafe")
3. "business_types": list of business types/categories that match this search intent
4. "services": list of services typically offered by such businesses
5. "categories": list of likely business categories in Catanduanes context

Return ONLY valid JSON, no markdown or extra text.

Example for "restaurant":
{{"primary_keywords": ["restaurant", "food"], "related_keywords": ["dining", "cafe", "eatery"], "business_types": ["Restaurant", "Cafe", "Food Service"], "services": ["dine-in", "takeout", "catering"], "categories": ["restaurant", "services"]}}"""
        
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
            logger.info(f"Parsed business intent data: {intent_data}")
        except Exception as parse_error:
            logger.warning(f"Failed to parse intent response: {parse_error}, using fallback")
            intent_data = {
                'primary_keywords': [query],
                'related_keywords': [],
                'business_types': [query],
                'services': [],
                'categories': []
            }
        
        # Step 2: Query database with expanded search terms
        db = get_neo4j_db()
        with db.session() as session:
            # Build search with all keywords
            all_keywords = intent_data.get('primary_keywords', []) + intent_data.get('related_keywords', []) + intent_data.get('business_types', [])
            all_keywords = list(set([k.lower().strip() for k in all_keywords if k]))[:10]  # Limit to 10 unique keywords
            
            search_conditions = []
            for kw in all_keywords:
                search_conditions.append(f"(b.name ICONTAINS '{kw}' OR b.description ICONTAINS '{kw}')")
            
            where_clause = " OR ".join(search_conditions) if search_conditions else "1=1"
            
            cypher_query = f"""
                MATCH (b:Business)
                WHERE b.is_active = true AND ({where_clause})
            """
            
            if category:
                cypher_query += " AND b.category = $category"
            
            cypher_query += f"""
                RETURN b, 
                    (CASE 
                        WHEN b.name ICONTAINS '{query}' THEN 3
                        ELSE 1
                    END) as relevance_score
                ORDER BY relevance_score DESC, b.rating DESC, b.created_at DESC
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
                    MATCH (b:Business)
                    WHERE b.is_active = true AND (b.name ICONTAINS $query OR b.description ICONTAINS $query)
                """
                if category:
                    cypher_query += " AND b.category = $category"
                
                cypher_query += f"""
                    RETURN b
                    ORDER BY b.rating DESC, b.created_at DESC
                    LIMIT {limit}
                """
                
                params = {'query': query}
                if category:
                    params['category'] = category
                
                results = safe_run(session, cypher_query, params)
            
            businesses = []
            for record in results:
                business_data = _node_to_dict(record['b'])
                businesses.append(business_data)
        
        logger.info(f"AI search found {len(businesses)} results for: {query}")
        
        return jsonify({
            'success': True,
            'query': query,
            'count': len(businesses),
            'search_intent': intent_data,
            'businesses': businesses
        })
    
    except Exception as e:
        logger.error(f"Error in AI business search: {str(e)}", exc_info=True)
        # Fallback to regular search
        try:
            db = get_neo4j_db()
            with db.session() as session:
                cypher_query = """
                    MATCH (b:Business)
                    WHERE b.is_active = true AND (b.name CONTAINS $query OR b.description CONTAINS $query)
                """
                if category:
                    cypher_query += " AND b.category = $category"
                
                cypher_query += f"""
                    RETURN b
                    ORDER BY b.rating DESC, b.created_at DESC
                    LIMIT {limit}
                """
                
                params = {'query': query}
                if category:
                    params['category'] = category
                
                results = safe_run(session, cypher_query, params)
                
                businesses = []
                for record in results:
                    business_data = _node_to_dict(record['b'])
                    businesses.append(business_data)
            
            return jsonify({
                'success': True,
                'query': query,
                'count': len(businesses),
                'businesses': businesses,
                'note': 'Search fell back to basic mode'
            })
        except Exception as fallback_error:
            logger.error(f"Fallback business search also failed: {fallback_error}")
            return jsonify({
                'success': False,
                'error': 'Search temporarily unavailable. Please try again.'
            }), 500

@businesses_bp.route('/api/map/points')
@json_response
def api_map_points():
    """API endpoint for map points"""
    bounds = request.args.get('bounds', '')
    category = request.args.get('category', '')
    
    db = get_neo4j_db()
    with db.session() as session:
        query = """
            MATCH (b:Business)
            WHERE b.is_active = true 
            AND b.is_verified = true
            AND b.latitude IS NOT NULL 
            AND b.longitude IS NOT NULL
        """
        params = {}
        
        if category:
            query += " AND b.category = $category"
            params['category'] = category
        
        query += """
            RETURN b.id as id, b.name as name, b.latitude as lat, b.longitude as lon,
                   b.category as category, b.rating as rating
        """
        
        results = safe_run(session, query, params)
        
        features = []
        for record in results:
            features.append({
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [record['lon'], record['lat']]
                },
                'properties': {
                    'id': record['id'],
                    'name': record['name'],
                    'category': record['category'],
                    'rating': record['rating']
                }
            })
    
    return {
        'type': 'FeatureCollection',
        'features': features
    }

@businesses_bp.route('/notifications')
@login_required
def notifications():
    """Display notifications page for business owner"""
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