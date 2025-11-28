import uuid
import logging
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from tasks import geocode_location_sync      # ✅  plain function
#  NOT  geocode_location_task_async
from . import services_bp
from database import get_neo4j_db, safe_run, _node_to_dict, _record_to_dict
from models import Service, Review
from forms import ServiceForm, ReviewForm, SearchForm
from decorators import role_required, login_required_optional, json_response, verified_required
from tasks import send_email_task, create_notification_task
from app import cache  # Import the cache extension

logger = logging.getLogger(__name__)


@services_bp.route('/')
@login_required_optional
@cache.cached(timeout=300)  # Cache for 5 minutes
def list_services():
    """List all services with search and filtering"""
    form = SearchForm(request.args)
    
    # Build query
    query = """
        MATCH (s:Service)
        WHERE s.is_active = true
    """
    params = {}
    
    # Add search filters
    if form.query.data:
        query += " AND (s.title CONTAINS $query OR s.description CONTAINS $query)"
        params['query'] = form.query.data
    
    if form.category.data:
        query += " AND s.category = $category"
        params['category'] = form.category.data
    
    if form.location.data:
        query += " AND s.location CONTAINS $location"
        params['location'] = form.location.data
    
    # Add sorting
    sort_by = form.sort_by.data or 'created_at'
    if sort_by == 'rating':
        query += """
            OPTIONAL MATCH (s)<-[:REVIEWS]-(r:Review)
            WITH s, avg(r.rating) as avg_rating
            ORDER BY avg_rating DESC
        """
    elif sort_by == 'name':
        query += """
            WITH s
            ORDER BY s.title ASC
        """
    else:  # created_at
        query += """
            WITH s
            ORDER BY s.created_at DESC
        """
    
    # Add pagination
    page = request.args.get('page', 1, type=int)
    per_page = 12
    skip = (page - 1) * per_page
    
    query += " SKIP $skip LIMIT $limit"
    params['skip'] = skip
    params['limit'] = per_page
    
    # Add final return
    query += " RETURN s"
    
    db = get_neo4j_db()
    with db.session() as session:
        services = safe_run(session, query, params)
        
        # Get total count for pagination
        count_query = """
            MATCH (s:Service)
            WHERE s.is_active = true
        """
        count_params = {}
        
        if form.query.data:
            count_query += " AND (s.title CONTAINS $query OR s.description CONTAINS $query)"
            count_params['query'] = form.query.data
        
        if form.category.data:
            count_query += " AND s.category = $category"
            count_params['category'] = form.category.data
        
        if form.location.data:
            count_query += " AND s.location CONTAINS $location"
            count_params['location'] = form.location.data
        
        count_query += " RETURN count(s) as total"
        
        total_result = safe_run(session, count_query, count_params)
        total = total_result[0]['total'] if total_result else 0
        
        # Get category counts
        category_counts = {}
        category_result = safe_run(session, """
            MATCH (s:Service)
            WHERE s.is_active = true
            RETURN s.category as category, count(*) as count
        """, {})
        
        for record in category_result:
            category = record['category'] or 'other'
            category_counts[category.lower()] = record['count']
        
        # Convert to Service objects with ratings
        service_list = []
        for record in services:
            service_data = _node_to_dict(record['s'])
            # Get rating if we haven't already from sorting
            if 'avg_rating' in record:
                service_data['rating'] = record['avg_rating'] or 0
            service_list.append(Service(**service_data))
    
    return render_template('services.html',
        services=service_list,
        form=form,
        category_counts=category_counts,
        pagination={
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page
        }
    )
@services_bp.route('/provider-dashboard')
@login_required
@role_required('service_client')
def service_provider_dashboard():
    """Main dashboard for service-provider role."""
    # ----  basic stats  ----
    db = get_neo4j_db()
    with db.session() as session:
        stats = safe_run(session, """
            MATCH (u:User {id: $uid})-[:PROVIDES]->(s:Service)
            OPTIONAL MATCH (s)<-[:BOOKED]-(b:Booking)
            OPTIONAL MATCH (s)<-[:REVIEWS]-(r:Review)
            RETURN count(DISTINCT s)  AS total_services,
                   count(DISTINCT b)  AS total_bookings,
                   avg(r.rating)      AS average_rating
        """, {"uid": current_user.id})[0]

        services = safe_run(session, """
            MATCH (u:User {id: $uid})-[:PROVIDES]->(s:Service)
            OPTIONAL MATCH (s)<-[:REVIEWS]-(rev:Review)
            RETURN s, avg(rev.rating) AS rating, count(rev) AS reviews_count
            ORDER BY s.created_at DESC
        """, {"uid": current_user.id})

        recent_bookings = safe_run(session, """
            MATCH (u:User {id: $uid})-[:PROVIDES]->(s:Service)<-[:FOR_SERVICE]-(b:Booking)
            MATCH (client:User)-[:BOOKED]->(b)
            RETURN b, s.title AS service_title, client.username AS client_name
            ORDER BY b.created_at DESC
            LIMIT 5
        """, {"uid": current_user.id})

    verification_status = (
        "verified" if current_user.is_verified else
        "pending"  if safe_run(session, """
            MATCH (u:User {id: $uid})-[:SUBMITTED]->(v:Verification {status:'pending'})
            RETURN 1 LIMIT 1
        """, {"uid": current_user.id}) else "not_submitted")

    return render_template(
        'service_provider_dashboard.html',
        stats=stats,
        services=[dict(_node_to_dict(rec["s"]),
                       rating=rec["rating"] or 0,
                       reviews_count=rec["reviews_count"] or 0) for rec in services],
        recent_bookings=[dict(_node_to_dict(rec["b"]),
                              service_title=rec["service_title"],
                              client_name=rec["client_name"]) for rec in recent_bookings],
        verification_status=verification_status
    )

# Correct my_services route/function (single definition)
@services_bp.route('/my-services')
@login_required
@role_required(['business_owner', 'service_client'])
def my_services():
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
    return render_template('services/services_my_services.html',
                         services=service_list,
                         stats=stats_data)


# Correct edit_service route/function (single definition, only edit logic)
@services_bp.route('/<service_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required(['business_owner', 'service_client'])
def edit_service(service_id):
    db = get_neo4j_db()
    with db.session() as session:
        ownership = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:PROVIDES]->(s:Service {id: $service_id})
            RETURN s
        """, {'user_id': current_user.id, 'service_id': service_id})
        if not ownership:
            flash('You do not have permission to edit this service.', 'error')
            return redirect(url_for('services.my_services'))
        service_data = _node_to_dict(ownership[0]['s'])
    form = ServiceForm(obj=service_data)
    if form.validate_on_submit():
        update_data = {
            'title': form.title.data,
            'description': form.description.data,
            'category': form.category.data,
            'price': float(form.price.data),
            'currency': form.currency.data,
            'price_type': form.price_type.data,
            'location': form.location.data,
            'duration': form.duration.data,
            'requirements': form.requirements.data
        }
        # Geocode location if changed
        if form.location.data != service_data.get('location'):
            from tasks import geocode_location_task
            geocode_result = geocode_location_task.delay(form.location.data)
            if geocode_result:
                lat, lon = geocode_result.get('latitude'), geocode_result.get('longitude')
                if lat and lon:
                    update_data['latitude'] = lat
                    update_data['longitude'] = lon
        db = get_neo4j_db()
        with db.session() as session:
            safe_run(session, """
                MATCH (s:Service {id: $service_id})
                SET s += $update_data
            """, {'service_id': service_id, 'update_data': update_data})
        flash('Service updated successfully!', 'success')
        return redirect(url_for('services.service_detail', service_id=service_id))
    return render_template('services/services_edit.html', form=form, service=service_data)

@services_bp.route('/<service_id>')
@login_required_optional
def service_detail(service_id):
    """Service detail page"""
    db = get_neo4j_db()
    with db.session() as session:
        result = safe_run(session, """
            MATCH (s:Service {id: $service_id})
            OPTIONAL MATCH (s)<-[:REVIEWS]-(r:Review)
            WITH s, avg(r.rating) as avg_rating, count(r) as review_count
            RETURN s, avg_rating, review_count
        """, {'service_id': service_id})
        
        if not result:
            flash('Service not found.', 'error')
            return redirect(url_for('services.list_services'))
        
        record = result[0]
        service_data = _node_to_dict(record['s'])
        service_data['rating'] = record['avg_rating'] or 0
        service_data['review_count'] = record['review_count'] or 0
        
        service = Service(**service_data)
        
        # Get reviews
        reviews = safe_run(session, """
            MATCH (s:Service {id: $service_id})<-[r:REVIEWS]-(u:User)
            RETURN r, u.username as reviewer_name
            ORDER BY r.created_at DESC
            LIMIT 10
        """, {'service_id': service_id})
        
        review_list = []
        for review_record in reviews:
            review_data = _node_to_dict(review_record['r'])
            review_data['reviewer_name'] = review_record['reviewer_name']
            review_list.append(Review(**review_data))
    
    return render_template('service_detail.html', service=service, reviews=review_list)

@services_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required('service_client')
def create_service():
    """Create new service listing"""
    form = ServiceForm()
    
    if form.validate_on_submit():
        service_id = str(uuid.uuid4())

        # 1.  build the dictionary first
        service_data = {
            'id': service_id,
            'title': form.title.data,
            'description': form.description.data,
            'category': form.category.data,
            'price': float(form.price.data),
            'currency': form.currency.data,
            'price_type': form.price_type.data,
            'location': form.location.data,
            'duration': form.duration.data,
            'provider_id': current_user.id,
            'provider_name': current_user.username,
            'requirements': form.requirements.data,
            'created_at': datetime.utcnow().isoformat(),
            'is_active': True,
            'rating': 0.0,
            'review_count': 0
        }

        # 2.  add coordinates (pinned or geocoded)
        manual_lat = request.form.get('latitude')
        manual_lng = request.form.get('longitude')
        if manual_lat and manual_lng:
            service_data['latitude']  = float(manual_lat)
            service_data['longitude'] = float(manual_lng)
        else:
            from tasks import geocode_location_sync
            result = geocode_location_sync(form.location.data)
            if result:
                service_data['latitude']  = result['latitude']
                service_data['longitude'] = result['longitude']

        # 3.  create node
        db = get_neo4j_db()
        with db.session() as session:
            safe_run(session, """
                CREATE (s:Service $service_data)
                WITH s
                MATCH (u:User {id: $user_id})
                CREATE (u)-[:PROVIDES]->(s)
            """, {'service_data': service_data, 'user_id': current_user.id})

        
        flash('Service created successfully!', 'success')
        return redirect(url_for('services.service_detail', service_id=service_id))
    
    return render_template('services/services_create.html', form=form)

@services_bp.route('/<service_id>/review', methods=['POST'])
@login_required
@verified_required
def add_review(service_id):
    """Add review to service"""
    form = ReviewForm()
    
    if form.validate_on_submit():
        db = get_neo4j_db()
        with db.session() as session:
            # Check if service exists
            service = safe_run(session, """
                MATCH (s:Service {id: $service_id})
                RETURN s
            """, {'service_id': service_id})
            
            if not service:
                flash('Service not found.', 'error')
                return redirect(url_for('services.list_services'))
            
            # Check if user has already reviewed
            existing = safe_run(session, """
                MATCH (u:User {id: $user_id})-[r:REVIEWS]->(s:Service {id: $service_id})
                RETURN r
            """, {'user_id': current_user.id, 'service_id': service_id})
            
            if existing:
                flash('You have already reviewed this service.', 'error')
                return redirect(url_for('services.service_detail', service_id=service_id))
            
            # Create review
            review_id = str(uuid.uuid4())
            review_data = {
                'id': review_id,
                'rating': form.rating.data,
                'comment': form.comment.data,
                'user_id': current_user.id,
                'user_name': current_user.username,
                'target_id': service_id,
                'target_type': 'service',
                'created_at': datetime.utcnow().isoformat()
            }
            
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
            
            # Update service rating
            safe_run(session, """
                MATCH (s:Service {id: $service_id})<-[:REVIEWS]-(r:Review)
                WITH s, avg(r.rating) as avg_rating, count(r) as review_count
                SET s.rating = avg_rating,
                    s.review_count = review_count
            """, {'service_id': service_id})
            
            # Create notification for service provider
            provider_result = safe_run(session, """
                MATCH (provider:User)-[:PROVIDES]->(s:Service {id: $service_id})
                RETURN provider.id as provider_id
            """, {'service_id': service_id})
            
            if provider_result:
                create_notification_task.delay(
                    user_id=provider_result[0]['provider_id'],
                    type='new_review',
                    title='New Review',
                    message=f'{current_user.username} left a review for your service',
                    data={
                        'review_id': review_id,
                        'service_id': service_id,
                        'rating': form.rating.data
                    }
                )
        
        flash('Review added successfully!', 'success')
        return redirect(url_for('services.service_detail', service_id=service_id))
    
    return render_template('services/services_review.html', form=form, service_id=service_id)

@services_bp.route('/<service_id>/contact', methods=['POST'])
@login_required
def contact_provider(service_id):
    """Contact service provider"""
    message = request.form.get('message', '')
    
    if not message.strip():
        return jsonify({'error': 'Message is required'}), 400
    
    db = get_neo4j_db()
    with db.session() as session:
        # Get service and provider
        result = safe_run(session, """
            MATCH (s:Service {id: $service_id})<-[:PROVIDES]-(u:User)
            RETURN s, u
        """, {'service_id': service_id})
        
        if not result:
            return jsonify({'error': 'Service not found'}), 404
        
        service = _node_to_dict(result[0]['s'])
        provider = _node_to_dict(result[0]['u'])
        
        # Create notification for provider
        create_notification_task.delay(
            user_id=provider['id'],
            type='service_inquiry',
            title='New Service Inquiry',
            message=f'{current_user.username} is interested in your service "{service["title"]}"',
            data={
                'service_id': service_id,
                'inquirer_id': current_user.id,
                'message': message
            }
        )
    
    return jsonify({'message': 'Message sent successfully'})



@services_bp.route('/<service_id>/toggle', methods=['POST'])
@login_required
def toggle_service(service_id):
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
        
        new_status = not ownership[0]['is_active']
        
        safe_run(session, """
            MATCH (s:Service {id: $service_id})
            SET s.is_active = $is_active
        """, {'service_id': service_id, 'is_active': new_status})
    
    return jsonify({'message': 'Service status updated successfully', 'is_active': new_status})

@services_bp.route('/api/search')
@json_response
def api_search_services():
    """API endpoint for service search"""
    query = request.args.get('q', '')
    category = request.args.get('category', '')
    location = request.args.get('location', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    db = get_neo4j_db()
    with db.session() as session:
        # Build query
        cypher_query = """
            MATCH (s:Service)
            WHERE s.is_active = true
        """
        params = {}
        
        if query:
            cypher_query += " AND (s.title CONTAINS $query OR s.description CONTAINS $query)"
            params['query'] = query
        
        if category:
            cypher_query += " AND s.category = $category"
            params['category'] = category
        
        if location:
            cypher_query += " AND s.location CONTAINS $location"
            params['location'] = location
        
        # Add pagination
        skip = (page - 1) * per_page
        cypher_query += f" SKIP $skip LIMIT $limit"
        params['skip'] = skip
        params['limit'] = per_page
        
        cypher_query += """
            RETURN s
            ORDER BY s.created_at DESC
        """
        
        results = safe_run(session, cypher_query, params)
        
        services = []
        for record in results:
            service_data = _node_to_dict(record['s'])
            services.append(service_data)
    
    return {
        'services': services,
        'page': page,
        'per_page': per_page,
        'count': len(services)
    }
