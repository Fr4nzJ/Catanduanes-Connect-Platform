
import logging
from datetime import datetime, timedelta
from flask import render_template, request, redirect, url_for, flash, jsonify, current_app, Blueprint, g
from flask_login import login_required, current_user
from functools import wraps
from database import get_neo4j_db, safe_run, _node_to_dict
from models import User, Business, Job, Review, Notification
from decorators import role_required, json_response
from tasks import send_email_task, create_notification_task
from forms import BusinessForm, JobForm
import bcrypt
from . import admin_bp

_TIME_TABLE = {
    '1d': 'P1D',
    '7d': 'P7D',
    '30d': 'P30D',
    '90d': 'P90D',
    '1y': 'P1Y'
}

# Admin role decorator
def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        logger.info(f"Checking admin access - User: {current_user}, Authenticated: {current_user.is_authenticated}")
        
        if not current_user.is_authenticated:
            logger.warning("User not authenticated")
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        logger.info(f"User authenticated - ID: {current_user.id}, Role: {current_user.role}")
        
        if not current_user.has_role('admin'):
            logger.warning(f"Access denied - User {current_user.id} has role {current_user.role}")
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('home'))
        
        # Add role to g for template access
        g.role = current_user.role
        logger.info(f"Admin access granted to user {current_user.id}")
            
        return f(*args, **kwargs)
    return decorated_function

def _paginate(session, query, count_query, params, per_page=20):
    """Return (items, pagination_dict)."""
    from flask import request
    page = request.args.get('page', 1, type=int)

    total = safe_run(session, count_query, params)[0]['total']
    params.update(skip=(page-1)*per_page, limit=per_page)
    items = safe_run(session, query, params) or []

    total_pages = (total + per_page - 1) // per_page
    pagination = {
        'page': page,
        'pages': total_pages,
        'total': total,
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'prev_num': page - 1,
        'next_num': page + 1,
    }
    return items, pagination
from flask_login import login_required, current_user
from functools import wraps
from database import get_neo4j_db, safe_run, _node_to_dict
from models import User, Business, Job, Review, Notification
from decorators import role_required, json_response
from tasks import send_email_task, create_notification_task
from forms import BusinessForm, JobForm
import bcrypt

logger = logging.getLogger(__name__)

from . import admin_bp


def admin_required(f):
    """Decorator to require admin role"""
    return role_required('admin')(f)

@admin_bp.route('/')
@login_required
def index():
    """Admin dashboard"""
    # Log request details
    logger.info(f"Admin index access - User: {current_user.email}, ID: {current_user.id}, Role: {current_user.role}")
    
    # Force re-check admin status from database
    db = get_neo4j_db()
    with db.session() as session:
        result = safe_run(session, """
            MATCH (u:User {id: $user_id}) 
            RETURN u.role as role
        """, {"user_id": current_user.id})
        
        if not result or result[0]['role'] != 'admin':
            logger.warning(f"Non-admin access attempt - User {current_user.id} ({current_user.email})")
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('home'))
    
    logger.info(f"Admin access granted to {current_user.email}")
    
    # Get platform statistics
    with db.session() as session:
        stats = safe_run(session, """
            MATCH (u:User) WITH count(u) as total_users
            MATCH (b:Business) WITH total_users, count(b) as total_businesses
            MATCH (j:Job) WITH total_users, total_businesses, count(j) as total_jobs
            MATCH (s:Service) WITH total_users, total_businesses, total_jobs, count(s) as total_services
            MATCH (r:Review) WITH total_users, total_businesses, total_jobs, total_services, count(r) as total_reviews
            MATCH (v:Verification {status: 'pending'}) 
            RETURN total_users, total_businesses, total_jobs, total_services, total_reviews, count(v) as pending_verifications
        """)

        # Get recent activity
        activity = safe_run(session, """
            MATCH (u:User)
            WHERE u.created_at IS NOT NULL
            WITH u ORDER BY u.created_at DESC LIMIT 5
            RETURN u.username as username, u.role as role, 'registered' as action, u.created_at as timestamp
            UNION
            MATCH (u:User)-[:SUBMITTED]->(v:Verification)
            WITH u, v ORDER BY v.created_at DESC LIMIT 5
            RETURN u.username as username, u.role as role, 'submitted_verification' as action, v.created_at as timestamp
            ORDER BY timestamp DESC LIMIT 10
        """)

        # Get user growth data for chart
        user_growth = safe_run(session, """
            MATCH (u:User)
            WHERE u.created_at IS NOT NULL
            WITH datetime(u.created_at) as join_date, count(u) as new_users
            RETURN join_date, new_users
            ORDER BY join_date ASC
            LIMIT 30
        """)

        # Get content distribution data for chart
        content_stats = safe_run(session, """
            MATCH (b:Business) WITH count(b) as businesses
            MATCH (j:Job) WITH businesses, count(j) as jobs
            MATCH (s:Service) WITH businesses, jobs, count(s) as services
            MATCH (r:Review) WITH businesses, jobs, services, count(r) as reviews
            RETURN businesses, jobs, services, reviews
        """)

        # Get system health metrics
        health_metrics = safe_run(session, """
            MATCH (u:User) WITH count(u) as total_users
            MATCH (u:User {is_verified: true}) WITH total_users, count(u) as verified_users
            MATCH (b:Business) WITH total_users, verified_users, count(b) as total_businesses
            MATCH (b:Business)-[:POSTED_BY]->(j:Job) WITH total_users, verified_users, total_businesses, count(j) as total_jobs
            MATCH (s:Service) WITH total_users, verified_users, total_businesses, total_jobs, count(s) as total_services
            RETURN total_users, verified_users, total_businesses, total_jobs, total_services
        """)

        return render_template('admin/admin_dashboard.html',
                                stats=stats[0] if stats else None,
                                activity=activity,
                                user_growth=user_growth,
                                content_stats=content_stats[0] if content_stats else None,
                                health_metrics=health_metrics[0] if health_metrics else None,
                                system_status={
                                    'last_check': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                                    'status': 'operational'
                                },
                                storage_usage={               # <-- add this
                                    'percentage': 0,
                                    'used': 0,
                                    'total': 0
                                })

@admin_bp.route('/content')
@login_required
@admin_required
def content():
    """Admin content moderation interface"""
    content_type = request.args.get('type', 'businesses')
    status = request.args.get('status', 'all')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    db = get_neo4j_db()
    with db.session() as session:
        # Build query based on content type
        if content_type == 'businesses':
            query = "MATCH (b:Business)"
            count_query = query + " RETURN count(b) as total"
            if status != 'all':
                query += " WHERE b.status = $status"
                count_query = query + " WHERE b.status = $status"
            query += " RETURN b ORDER BY b.created_at DESC SKIP $skip LIMIT $limit"
            
        elif content_type == 'jobs':
            query = "MATCH (j:Job)"
            count_query = query + " RETURN count(j) as total"
            if status != 'all':
                query += " WHERE j.status = $status"
                count_query = query + " WHERE j.status = $status"
            query += " RETURN j ORDER BY j.created_at DESC SKIP $skip LIMIT $limit"
            
        elif content_type == 'services':
            query = "MATCH (s:Service)"
            count_query = query + " RETURN count(s) as total"
            if status != 'all':
                query += " WHERE s.status = $status"
                count_query = query + " WHERE s.status = $status"
            query += " RETURN s ORDER BY s.created_at DESC SKIP $skip LIMIT $limit"
            
        elif content_type == 'reviews':
            query = "MATCH (r:Review)"
            count_query = query + " RETURN count(r) as total"
            if status != 'all':
                query += " WHERE r.status = $status"
                count_query = query + " WHERE r.status = $status"
            query += " RETURN r ORDER BY r.created_at DESC SKIP $skip LIMIT $limit"
            
        # Get total count
        params = {'status': status} if status != 'all' else {}
        count_result = safe_run(session, count_query, params)
        total = count_result[0]['total'] if count_result else 0
        
        # Get paginated content
        skip = (page - 1) * per_page
        params.update({'skip': skip, 'limit': per_page})
        results = safe_run(session, query, params)
        
        content_items = [_node_to_dict(result[list(result.keys())[0]]) for result in results]
        
    total_pages = (total + per_page - 1) // per_page
    
    return render_template('admin/admin_content.html',
                       content_items=content_items,
                       content_type=content_type,
                       status=status,
                       current_page=page,
                       total_pages=total_pages,
                       total=total)


# @admin_bp.route('/settings', methods=['GET', 'POST'])
# @login_required
# @admin_required
# def settings():
#     """Admin system settings interface"""
#     if request.method == 'POST':
#         category = request.form.get('category')
#         settings_data = {}
        
#         if category == 'general':
#             settings_data = {
#                 'site_name': request.form.get('site_name'),
#                 'site_description': request.form.get('site_description'),
#                 'maintenance_mode': request.form.get('maintenance_mode') == 'on',
#                 'user_registration': request.form.get('user_registration') == 'on'
#             }
#         elif category == 'email':
#             settings_data = {
#                 'smtp_host': request.form.get('smtp_host'),
#                 'smtp_port': request.form.get('smtp_port'),
#                 'smtp_user': request.form.get('smtp_user'),
#                 'smtp_password': request.form.get('smtp_password'),
#                 'email_from': request.form.get('email_from')
#             }
#         elif category == 'security':
#             settings_data = {
#                 'min_password_length': request.form.get('min_password_length'),
#                 'password_expiry_days': request.form.get('password_expiry_days'),
#                 'max_login_attempts': request.form.get('max_login_attempts'),
#                 'session_timeout': request.form.get('session_timeout')
#             }
#         elif category == 'integrations':
#             settings_data = {
#                 'google_maps_api_key': request.form.get('google_maps_api_key'),
#                 'google_oauth_client_id': request.form.get('google_oauth_client_id'),
#                 'google_oauth_client_secret': request.form.get('google_oauth_client_secret')
#             }
            
#         db = get_neo4j_db()
#         with db.session() as session:
#             # Update settings in database
#             query = """
#                 MERGE (s:Settings {category: $category})
#                 SET s += $settings
#             """
#             safe_run(session, query, {
#                 'category': category,
#                 'settings': settings_data
#             })
            
#         flash(f'{category.title()} settings updated successfully.', 'success')
#         return redirect(url_for('admin.settings', category=category))
        
#     # GET request handling
#     category = request.args.get('category', 'general')
#     db = get_neo4j_db()
#     with db.session() as session:
#         # Get current settings
#         query = "MATCH (s:Settings {category: $category}) RETURN s"
#         result = safe_run(session, query, {'category': category})
#         settings = _node_to_dict(result[0]['s']) if result else {}
        
#         return render_template('admin/admin_settings.html',
#                            category=category,
#                            settings=settings)

@admin_bp.route('/verifications')
@login_required
@admin_required
def verification_review():
    """Admin interface for reviewing verifications"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    status = request.args.get('status', 'pending')
    
    db = get_neo4j_db()
    with db.session() as session:
        # Build query based on status filter
        query = """
            MATCH (v:Verification)
            MATCH (u:User)-[:SUBMITTED]->(v)
            WHERE v.status = $status
        """
        
        # Get total count
        count_query = query + " RETURN count(v) as total"
        count_result = safe_run(session, count_query, {'status': status})
        total = count_result[0]['total'] if count_result else 0
        
        # Get pending count for badge
        pending_count = None
        if status != 'pending':
            pending_result = safe_run(session, """
                MATCH (v:Verification {status: 'pending'})
                RETURN count(v) as count
            """)
            pending_count = pending_result[0]['count'] if pending_result else 0
        
        # Get verifications for current page with user info and documents
        query += """
            RETURN v, u,
                [(v)-[:HAS_DOCUMENT]->(d:Document) | d] as documents
            ORDER BY v.created_at DESC
            SKIP $skip
            LIMIT $limit
        """
        params = {
            'status': status,
            'skip': (page - 1) * per_page,
            'limit': per_page
        }
        
        verifications_result = safe_run(session, query, params)
        verifications = []
        
        if verifications_result:
            for record in verifications_result:
                verification_data = {
                    'v': _node_to_dict(record['v']),
                    'u': _node_to_dict(record['u']),
                    'user_type': record['v'].get('user_type', 'user'),
                    'documents': [_node_to_dict(doc) for doc in record['documents']]
                }
                verifications.append(verification_data)
        
        # Calculate pagination
        total_pages = (total + per_page - 1) // per_page
        pagination = {
            'page': page,
            'pages': total_pages,
            'total': total,
            'has_prev': page > 1,
            'has_next': page < total_pages,
            'start': (page - 1) * per_page + 1,
            'end': min(page * per_page, total),
            'prev_num': page - 1,
            'next_num': page + 1
        }
        
    return render_template('admin/verification_review.html',
                         verifications=verifications,
                         status=status,
                         pagination=pagination,
                         pending_count=pending_count)

# Dashboard route moved to admin.index above
# @admin_bp.route('/')
# @login_required
# @admin_required
# def dashboard():
#     """Admin dashboard with overview and quick stats"""
#     db = get_neo4j_db()
#     with db.session() as session:
#         # Get quick stats
#         stats = safe_run(session, """
#             MATCH (u:User) WITH count(u) as total_users
#             MATCH (b:Business) WITH total_users, count(b) as total_businesses
#             MATCH (j:Job) WITH total_users, total_businesses, count(j) as total_jobs
#             MATCH (s:Service) WITH total_users, total_businesses, total_jobs, count(s) as total_services
#             MATCH (r:Review) WITH total_users, total_businesses, total_jobs, total_services, count(r) as total_reviews
#             MATCH (v:Verification {status: 'pending'}) 
#             RETURN total_users, total_businesses, total_jobs, total_services, total_reviews, count(v) as pending_verifications
#         """)
        
#         # Total users
#         users_result = safe_run(session, "MATCH (u:User) RETURN count(u) as total")
#         stats['total_users'] = users_result[0]['total'] if users_result else 0
        
#         # Active users (last 30 days)
#         active_users_result = safe_run(session, """
#             MATCH (u:User) 
#             WHERE u.last_login >= datetime() - duration('P30D')
#             RETURN count(u) as active
#         """)
#         stats['active_users'] = active_users_result[0]['active'] if active_users_result else 0
        
#         # Total businesses
#         businesses_result = safe_run(session, "MATCH (b:Business) RETURN count(b) as total")
#         stats['total_businesses'] = businesses_result[0]['total'] if businesses_result else 0
        
#         # Pending business verifications
#         pending_businesses_result = safe_run(session, """
#             MATCH (b:Business) 
#             WHERE b.is_verified = false 
#             RETURN count(b) as pending
#         """)
#         stats['pending_businesses'] = pending_businesses_result[0]['pending'] if pending_businesses_result else 0
        
#         # Total jobs
#         jobs_result = safe_run(session, "MATCH (j:Job) RETURN count(j) as total")
#         stats['total_jobs'] = jobs_result[0]['total'] if jobs_result else 0
        
#         # Active jobs
#         active_jobs_result = safe_run(session, """
#             MATCH (j:Job) 
#             WHERE j.is_active = true 
#             RETURN count(j) as active
#         """)
#         stats['active_jobs'] = active_jobs_result[0]['active'] if active_jobs_result else 0
        
#         # Total services
#         services_result = safe_run(session, "MATCH (s:Service) RETURN count(s) as total")
#         stats['total_services'] = services_result[0]['total'] if services_result else 0
        
#         # Recent activity (last 24 hours)
#         recent_activity = safe_run(session, """
#             MATCH (u:User)
#             WHERE u.created_at >= datetime() - duration('P1D')
#             RETURN 'new_user' as type, u.username as name, u.created_at as timestamp
#             ORDER BY u.created_at DESC LIMIT 5
#         """)
        
#         recent_businesses = safe_run(session, """
#             MATCH (b:Business)
#             WHERE b.created_at >= datetime() - duration('P1D')
#             RETURN 'new_business' as type, b.name as name, b.created_at as timestamp
#             ORDER BY b.created_at DESC LIMIT 5
#         """)
        
#         recent_jobs = safe_run(session, """
#             MATCH (j:Job)
#             WHERE j.created_at >= datetime() - duration('P1D')
#             RETURN 'new_job' as type, j.title as name, j.created_at as timestamp
#             ORDER BY j.created_at DESC LIMIT 5
#         """)
        
#         recent_activity = (recent_activity or []) + (recent_businesses or []) + (recent_jobs or [])
#         recent_activity.sort(key=lambda x: x['timestamp'], reverse=True)
#         recent_activity = recent_activity[:10]
        
#         # Verification stats
#         verification_stats = safe_run(session, """
#             MATCH (v:Verification)
#             RETURN v.status as status, count(v) as count
#         """)
#         verification_counts = {}
#         if verification_stats:
#             for record in verification_stats:
#                 verification_counts[record['status']] = record['count']
            
#         stats['pending_verifications'] = verification_counts.get('pending', 0)
#         stats['verified_users'] = verification_counts.get('verified', 0)
#         stats['rejected_verifications'] = verification_counts.get('rejected', 0)
        
#         # Recent verification activity
#         recent_verifications = safe_run(session, """
#             MATCH (u:User)-[:SUBMITTED]->(v:Verification)
#             WHERE v.created_at >= datetime() - duration('P1D')
#             OR v.reviewed_at >= datetime() - duration('P1D')
#             RETURN 'verification' as type, 
#                    v.status as status,
#                    u.username as name,
#                    CASE 
#                      WHEN v.reviewed_at IS NOT NULL THEN v.reviewed_at 
#                      ELSE v.created_at 
#                    END as timestamp
#             ORDER BY timestamp DESC LIMIT 5
#         """)
        
#         if recent_verifications:
#             recent_activity = recent_activity + recent_verifications
#             recent_activity.sort(key=lambda x: x['timestamp'], reverse=True)
#             recent_activity = recent_activity[:10]
        
#         # System health indicators
#         health = {
#             'database_status': 'healthy',
#             'email_status': 'healthy',
#             'ai_service_status': 'healthy',
#             'last_backup': datetime.utcnow().isoformat(),
#             'uptime': '99.9%'
#         }
    
#     return render_template('admin/dashboard.html', 
#                          stats=stats, 
#                          recent_activity=recent_activity,
#                          verification_counts=verification_counts,
#                          health=health)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """User management interface"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    role_filter = request.args.get('role', '')
    status_filter = request.args.get('status', '')
    search = request.args.get('search', '')
    role_filter = request.args.get('role', '')
    status_filter = request.args.get('status', '')
    
    db = get_neo4j_db()
    
    with db.session() as session:
        # Build query based on filters
        query = """
            MATCH (u:User)
            WHERE 1=1
        """
        params = {}
        
        if search:
            query += " AND (u.username CONTAINS $search OR u.email CONTAINS $search)"
            params['search'] = search
            
        if role_filter:
            query += " AND u.role = $role"
            params['role'] = role_filter
            
        if status_filter:
            if status_filter == 'active':
                query += " AND u.is_active = true"
            elif status_filter == 'inactive':
                query += " AND u.is_active = false"
            elif status_filter == 'verified':
                query += " AND u.is_verified = true"
            elif status_filter == 'unverified':
                query += " AND u.is_verified = false"
        
        # Get total count
        count_query = query + " RETURN count(u) as total"
        count_result = safe_run(session, count_query, params)
        total_users = count_result[0]['total'] if count_result else 0
        
        # Get users for current page
        query += """
            RETURN u
            ORDER BY u.created_at DESC
            SKIP $skip
            LIMIT $limit
        """
        params['skip'] = (page - 1) * per_page
        params['limit'] = per_page
        
        users_result = safe_run(session, query, params)
        users = [_node_to_dict(rec['u']) | {'id': str(_node_to_dict(rec['u'])['id'])}
         for rec in (users_result or [])]


        
        # Get role distribution
        roles_result = safe_run(session, """
            MATCH (u:User)
            RETURN u.role as role, count(u) as count
            ORDER BY count DESC
        """)
        role_distribution = {role['role']: role['count'] for role in roles_result} if roles_result else {}
    
    total_pages = (total_users + per_page - 1) // per_page
    
    return render_template('admin/users.html',
                         users=users,
                         total_users=total_users,
                         page=page,
                         total_pages=total_pages,
                         search=search,
                         role_filter=role_filter,
                         status_filter=status_filter,
                         role_distribution=role_distribution)

@admin_bp.route('/users/<user_id>')
@login_required
@admin_required
def user_detail(user_id):
    """User detail and management page"""
    db = get_neo4j_db()
    
    with db.session() as session:
        # Get user details
        user_result = safe_run(session, """
            MATCH (u:User {id: $user_id})
            RETURN u
        """, {'user_id': user_id})
        
        if not user_result:
            flash('User not found.', 'error')
            return redirect(url_for('admin.users'))
        
        user = _node_to_dict(user_result[0]['u'])
        
        # Get user's businesses
        businesses_result = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:OWNS]->(b:Business)
            RETURN b
            ORDER BY b.created_at DESC
        """, {'user_id': user_id})
        businesses = [_node_to_dict(b['b']) for b in businesses_result] if businesses_result else []
        
        # Get user's job applications
        applications_result = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:APPLIED_FOR]->(a:JobApplication)-[:FOR_JOB]->(j:Job)
            RETURN a, j
            ORDER BY a.created_at DESC
        """, {'user_id': user_id})
        applications = []
        for app in applications_result or []:
            applications.append({
                'application': _node_to_dict(app['a']),
                'job': _node_to_dict(app['j'])
            })
        
        # Get user's reviews
        reviews_result = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:WROTE]->(r:Review)
            RETURN r
            ORDER BY r.created_at DESC
        """, {'user_id': user_id})
        reviews = [_node_to_dict(r['r']) for r in reviews_result] if reviews_result else []
    
    return render_template('admin/user_detail.html',
                         user=user,
                         businesses=businesses,
                         applications=applications,
                         reviews=reviews)

@admin_bp.route('/users/<user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
@json_response
def toggle_user_status(user_id):
    """Toggle user active status"""
    db = get_neo4j_db()
    
    with db.session() as session:
        # Get current status
        result = safe_run(session, """
            MATCH (u:User {id: $user_id})
            RETURN u.is_active as is_active
        """, {'user_id': user_id})
        
        if not result:
            return {'error': 'User not found'}, 404
        
        current_status = result[0]['is_active']
        new_status = not current_status
        
        # Update status
        safe_run(session, """
            MATCH (u:User {id: $user_id})
            SET u.is_active = $is_active
        """, {'user_id': user_id, 'is_active': new_status})
        
        # Create notification for user
        action = 'activated' if new_status else 'deactivated'
        create_notification_task.delay(
            user_id=user_id,
            type='account_status',
            title=f'Account {action.title()}',
            message=f'Your account has been {action} by an administrator.',
            data={'action': action, 'admin_id': current_user.id}
        )
    
    return {'success': True, 'new_status': new_status}

@admin_bp.route('/businesses')
@login_required
@admin_required
def businesses():
    """Business management interface"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    category_filter = request.args.get('category', '')
    
    db = get_neo4j_db()
    
    with db.session() as session:
        # Build query based on filters
        query = """
            MATCH (b:Business)
            WHERE 1=1
        """
        params = {}
        
        if search:
            query += " AND (b.name CONTAINS $search OR b.description CONTAINS $search)"
            params['search'] = search
            
        if status_filter:
            if status_filter == 'verified':
                query += " AND b.is_verified = true"
            elif status_filter == 'unverified':
                query += " AND b.is_verified = false"
            elif status_filter == 'active':
                query += " AND b.is_active = true"
            elif status_filter == 'inactive':
                query += " AND b.is_active = false"
        
        if category_filter:
            query += " AND b.category = $category"
            params['category'] = category_filter
        
        # Get total count
        count_query = query + " RETURN count(b) as total"
        count_result = safe_run(session, count_query, params)
        total_businesses = count_result[0]['total'] if count_result else 0
        
        # Get businesses for current page
        query += """
            OPTIONAL MATCH (owner:User)-[:OWNS]->(b)
            RETURN b, owner.username as owner_name
            ORDER BY b.created_at DESC
            SKIP $skip
            LIMIT $limit
        """
        params['skip'] = (page - 1) * per_page
        params['limit'] = per_page
        
        businesses_result = safe_run(session, query, params)
        businesses = []
        for business in businesses_result or []:
            biz_data = _node_to_dict(business['b'])
            biz_data['owner_name'] = business.get('owner_name', 'Unknown')
            businesses.append(biz_data)
        
        # Get category distribution
        categories_result = safe_run(session, """
            MATCH (b:Business)
            RETURN b.category as category, count(b) as count
            ORDER BY count DESC
        """)
        category_distribution = {cat['category']: cat['count'] for cat in categories_result} if categories_result else {}
    
    total_pages = (total_businesses + per_page - 1) // per_page
    
    return render_template('admin/businesses.html',
                         businesses=businesses,
                         total_businesses=total_businesses,
                         page=page,
                         total_pages=total_pages,
                         search=search,
                         status_filter=status_filter,
                         category_filter=category_filter,
                         category_distribution=category_distribution)

@admin_bp.route('/businesses/<business_id>/verify', methods=['POST'])
@login_required
@admin_required
@json_response
def verify_business(business_id):
    """Verify a business"""
    db = get_neo4j_db()
    
    with db.session() as session:
        # Get business details
        business_result = safe_run(session, """
            MATCH (b:Business {id: $business_id})<-[:OWNS]-(owner:User)
            RETURN b, owner
        """, {'business_id': business_id})
        
        if not business_result:
            return {'error': 'Business not found'}, 404
        
        business_data = _node_to_dict(business_result[0]['b'])
        owner = _node_to_dict(business_result[0]['owner'])
        
        # Verify business
        safe_run(session, """
            MATCH (b:Business {id: $business_id})
            SET b.is_verified = true,
                b.verified_at = $verified_at,
                b.verified_by = $verified_by
        """, {
            'business_id': business_id,
            'verified_at': datetime.utcnow().isoformat(),
            'verified_by': current_user.id
        })
        
        # Create notification for business owner
        create_notification_task.delay(
            user_id=owner['id'],
            type='business_verified',
            title='Business Verified',
            message=f'Your business "{business_data["name"]}" has been verified by an administrator.',
            data={'business_id': business_id, 'business_name': business_data['name']}
        )
        
        # Send verification email
        send_email_task.delay(
            to=owner['email'],
            subject='Business Verified - Catanduanes Connect',
            template='email/business_verified.html',
            context={
                'business_name': business_data['name'],
                'owner_name': owner['username'],
                'site_name': current_app.config['SITE_NAME']
            }
        )
    
    return {'success': True}

@admin_bp.route('/jobs')
@login_required
@admin_required
def jobs():
    """Job management interface"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    category_filter = request.args.get('category', '')
    
    db = get_neo4j_db()
    
    with db.session() as session:
        # Build query based on filters
        query = """
            MATCH (j:Job)
            WHERE 1=1
        """
        params = {}
        
        if search:
            query += " AND (j.title CONTAINS $search OR j.description CONTAINS $search)"
            params['search'] = search
            
        if status_filter:
            if status_filter == 'active':
                query += " AND j.is_active = true"
            elif status_filter == 'inactive':
                query += " AND j.is_active = false"
            elif status_filter == 'expired':
                query += " AND j.expires_at < datetime()"
        
        if category_filter:
            query += " AND j.category = $category"
            params['category'] = category_filter
        
        # Get total count
        count_query = query + " RETURN count(j) as total"
        count_result = safe_run(session, count_query, params)
        total_jobs = count_result[0]['total'] if count_result else 0
        
        # Get jobs for current page
        query += """
            OPTIONAL MATCH (b:Business)-[:POSTED]->(j)
            RETURN j, b.name as business_name, b.id as business_id
            ORDER BY j.created_at DESC
            SKIP $skip
            LIMIT $limit
        """
        params['skip'] = (page - 1) * per_page
        params['limit'] = per_page
        
        jobs_result = safe_run(session, query, params)
        jobs = []
        for job in jobs_result or []:
            job_data = _node_to_dict(job['j'])
            job_data['business_name'] = job.get('business_name', 'Unknown')
            job_data['business_id'] = job.get('business_id')
            jobs.append(job_data)
        
        # Get category distribution
        categories_result = safe_run(session, """
            MATCH (j:Job)
            RETURN j.category as category, count(j) as count
            ORDER BY count DESC
        """)
        category_distribution = {cat['category']: cat['count'] for cat in categories_result} if categories_result else {}
    
    total_pages = (total_jobs + per_page - 1) // per_page
    
    return render_template('admin/jobs.html',
                         jobs=jobs,
                         total_jobs=total_jobs,
                         page=page,
                         total_pages=total_pages,
                         search=search,
                         status_filter=status_filter,
                         category_filter=category_filter,
                         category_distribution=category_distribution)

@admin_bp.route('/services')
@login_required
@admin_required
def services():
    """Service management interface"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    category_filter = request.args.get('category', '')
    
    db = get_neo4j_db()
    
    with db.session() as session:
        # Build query based on filters
        query = """
            MATCH (s:Service)
            WHERE 1=1
        """
        params = {}
        
        if search:
            query += " AND (s.title CONTAINS $search OR s.description CONTAINS $search)"
            params['search'] = search
            
        if status_filter:
            if status_filter == 'active':
                query += " AND s.is_active = true"
            elif status_filter == 'inactive':
                query += " AND s.is_active = false"
        
        if category_filter:
            query += " AND s.category = $category"
            params['category'] = category_filter
        
        # Get total count
        count_query = query + " RETURN count(s) as total"
        count_result = safe_run(session, count_query, params)
        total_services = count_result[0]['total'] if count_result else 0
        
        # Get services for current page
        query += """
            OPTIONAL MATCH (u:User)-[:PROVIDES]->(s)
            RETURN s, u.username as provider_name, u.id as provider_id
            ORDER BY s.created_at DESC
            SKIP $skip
            LIMIT $limit
        """
        params['skip'] = (page - 1) * per_page
        params['limit'] = per_page
        
        services_result = safe_run(session, query, params)
        services = []
        for service in services_result or []:
            service_data = _node_to_dict(service['s'])
            service_data['provider_name'] = service.get('provider_name', 'Unknown')
            service_data['provider_id'] = service.get('provider_id')
            services.append(service_data)
        
        # Get category distribution
        categories_result = safe_run(session, """
            MATCH (s:Service)
            RETURN s.category as category, count(s) as count
            ORDER BY count DESC
        """)
        category_distribution = {cat['category']: cat['count'] for cat in categories_result} if categories_result else {}
    
    total_pages = (total_services + per_page - 1) // per_page
    
    return render_template('admin/services.html',
                         services=services,
                         total_services=total_services,
                         page=page,
                         total_pages=total_pages,
                         search=search,
                         status_filter=status_filter,
                         category_filter=category_filter,
                         category_distribution=category_distribution)

@admin_bp.route('/analytics')
@login_required
@admin_required
def analytics():
    """Analytics and reporting dashboard"""
    period = request.args.get('period', '7d')  # 1d, 7d, 30d, 90d
    
    db = get_neo4j_db()
    
    with db.session() as session:
        # Determine time filter
        if period == '1d':
            time_filter = "P1D"
        elif period == '7d':
            time_filter = "P7D"
        elif period == '30d':
            time_filter = "P30D"
        elif period == '90d':
            time_filter = "P90D"
        else:
            time_filter = "P7D"
        
        # User analytics
        user_registrations = safe_run(session, f"""
            MATCH (u:User)
            WHERE u.created_at >= datetime() - duration('{time_filter}')
            RETURN date(u.created_at) as date, count(u) as registrations
            ORDER BY date
        """)
        
        # Business analytics
        business_registrations = safe_run(session, f"""
            MATCH (b:Business)
            WHERE b.created_at >= datetime() - duration('{time_filter}')
            RETURN date(b.created_at) as date, count(b) as registrations
            ORDER BY date
        """)
        
        # Job posting analytics
        job_postings = safe_run(session, f"""
            MATCH (j:Job)
            WHERE j.created_at >= datetime() - duration('{time_filter}')
            RETURN date(j.created_at) as date, count(j) as postings
            ORDER BY date
        """)
        
        # Service posting analytics
        service_postings = safe_run(session, f"""
            MATCH (s:Service)
            WHERE s.created_at >= datetime() - duration('{time_filter}')
            RETURN date(s.created_at) as date, count(s) as postings
            ORDER BY date
        """)
        
        # User engagement metrics
        active_users = safe_run(session, f"""
            MATCH (u:User)
            WHERE u.last_login >= datetime() - duration('{time_filter}')
            RETURN count(u) as active_users
        """)
        
        # Job application metrics
        applications = safe_run(session, f"""
            MATCH (a:JobApplication)
            WHERE a.created_at >= datetime() - duration('{time_filter}')
            RETURN count(a) as total_applications
        """)
        
        # Review metrics
        reviews = safe_run(session, f"""
            MATCH (r:Review)
            WHERE r.created_at >= datetime() - duration('{time_filter}')
            RETURN count(r) as total_reviews
        """)
        
        # Top categories
        top_job_categories = safe_run(session, f"""
            MATCH (j:Job)
            WHERE j.created_at >= datetime() - duration('{time_filter}')
            RETURN j.category as category, count(j) as count
            ORDER BY count DESC
            LIMIT 10
        """)
        
        top_business_categories = safe_run(session, f"""
            MATCH (b:Business)
            WHERE b.created_at >= datetime() - duration('{time_filter}')
            RETURN b.category as category, count(b) as count
            ORDER BY count DESC
            LIMIT 10
        """)
        
        # Geographic distribution
        location_stats = safe_run(session, f"""
            MATCH (u:User)
            WHERE u.created_at >= datetime() - duration('{time_filter}')
            AND u.location IS NOT NULL
            RETURN u.location as location, count(u) as count
            ORDER BY count DESC
            LIMIT 10
        """)
    
    # Prepare chart data
    chart_data = {
        'user_registrations': [{'date': str(r['date']), 'registrations': r['registrations']} for r in user_registrations or []],
        'business_registrations': [{'date': str(r['date']), 'registrations': r['registrations']} for r in business_registrations or []],
        'job_postings': [{'date': str(r['date']), 'postings': r['postings']} for r in job_postings or []],
        'service_postings': [{'date': str(r['date']), 'postings': r['postings']} for r in service_postings or []],
    }
    
    summary_stats = {
        'active_users': active_users[0]['active_users'] if active_users else 0,
        'total_applications': applications[0]['total_applications'] if applications else 0,
        'total_reviews': reviews[0]['total_reviews'] if reviews else 0,
        'top_job_categories': [{'category': r['category'], 'count': r['count']} for r in top_job_categories or []],
        'top_business_categories': [{'category': r['category'], 'count': r['count']} for r in top_business_categories or []],
        'location_stats': [{'location': r['location'], 'count': r['count']} for r in location_stats or []]
    }
    
    return render_template('admin/analytics.html',
                         chart_data=chart_data,
                         summary_stats=summary_stats,
                         period=period)

@admin_bp.route('/settings')
@login_required
@admin_required
def settings():
    """System settings management"""
    # Get current settings from config
    current_settings = {
        'site_name': current_app.config.get('SITE_NAME', 'Catanduanes Connect'),
        'site_url': current_app.config.get('SITE_URL', 'http://localhost:5000'),
        'admin_email': current_app.config.get('ADMIN_EMAIL', ''),
        'max_content_length': current_app.config.get('MAX_CONTENT_LENGTH', 16777216),
        'allowed_extensions': current_app.config.get('ALLOWED_EXTENSIONS', set()),
        'cache_timeout': current_app.config.get('CACHE_DEFAULT_TIMEOUT', 300),
        'rate_limit': '100 per hour',  # Default rate limit
        'maintenance_mode': False,  # Could be stored in database
        'registration_enabled': True,  # Could be stored in database
        'email_verification_required': True,  # Could be stored in database
    }
    
    return render_template('admin/settings.html', settings=current_settings)

@admin_bp.route('/settings/update', methods=['POST'])
@login_required
@admin_required
@json_response
def update_settings():
    """Update system settings"""
    settings_data = request.get_json()
    
    # Validate settings
    required_fields = ['site_name', 'site_url', 'admin_email']
    for field in required_fields:
        if field not in settings_data or not settings_data[field]:
            return {'error': f'{field} is required'}, 400
    
    # Update settings (in a real app, these would be stored in database)
    # For now, we'll just return success
    
    return {'success': True, 'message': 'Settings updated successfully'}

@admin_bp.route('/system-info')
@login_required
@admin_required
@json_response
def system_info():
    """Get system information for monitoring"""
    import os
    import sys
    import shutil
    try:
        import psutil
    except Exception:
        psutil = None
    
    # System metrics
    if psutil:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        cpu_percent = psutil.cpu_percent(interval=1)
    else:
        # Fallback values when psutil is not available
        class _Fallback:
            def __init__(self, percent=0, used=0, total=0):
                self.percent = percent
                self.used = used
                self.total = total
        memory = _Fallback()
        try:
            total, used, free = shutil.disk_usage('/')
            disk = _Fallback(percent=0, used=used, total=total)
        except Exception:
            disk = _Fallback()
        cpu_percent = 0
    
    # Application metrics
    db = get_neo4j_db()
    
    with db.session() as session:
        total_users = safe_run(session, "MATCH (u:User) RETURN count(u) as total")
        total_businesses = safe_run(session, "MATCH (b:Business) RETURN count(b) as total")
        total_jobs = safe_run(session, "MATCH (j:Job) RETURN count(j) as total")
        total_services = safe_run(session, "MATCH (s:Service) RETURN count(s) as total")
    
    system_info = {
        'server': {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_used_gb': memory.used / (1024**3),
            'memory_total_gb': memory.total / (1024**3),
            'disk_percent': disk.percent,
            'disk_used_gb': disk.used / (1024**3),
            'disk_total_gb': disk.total / (1024**3),
            'uptime': 'Running',
            'python_version': sys.version,
            'flask_version': '2.3.3'  # Could be imported
        },
        'application': {
            'total_users': total_users[0]['total'] if total_users else 0,
            'total_businesses': total_businesses[0]['total'] if total_businesses else 0,
            'total_jobs': total_jobs[0]['total'] if total_jobs else 0,
            'total_services': total_services[0]['total'] if total_services else 0,
            'database_status': 'connected',
            'cache_status': 'active',
            'email_status': 'configured'
        }
    }
    
    return system_info