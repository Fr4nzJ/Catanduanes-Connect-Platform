"""
Enhanced Admin Management Routes
Handles user management, verification, jobs, and business management
"""
import logging
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, send_file, make_response, current_app
from flask_login import login_required, current_user
from decorators import role_required
from database import get_neo4j_db, safe_run, _node_to_dict
from datetime import datetime
import os

logger = logging.getLogger(__name__)
admin_mgmt = Blueprint('admin_mgmt', __name__, url_prefix='/admin')

admin_required = role_required('admin')

# ============================================================================
# HELPER FUNCTION - GET REAL-TIME STATS
# ============================================================================

def get_realtime_stats():
    """Fetch real-time statistics from database"""
    db = get_neo4j_db()
    
    stats = {
        'users': {'total': 0, 'verified': 0, 'business_owners': 0, 'new_today': 0},
        'jobs': {'total': 0, 'featured': 0, 'active': 0, 'new_today': 0},
        'businesses': {'total': 0, 'featured': 0, 'active': 0, 'new_today': 0},
        'verifications': {'total': 0, 'approved': 0, 'pending': 0, 'rejected': 0}
    }
    
    try:
        with db.session() as session:
            # User stats
            user_result = safe_run(session, """
                MATCH (u:User)
                RETURN 
                    count(*) as total,
                    sum(case when u.is_verified = true then 1 else 0 end) as verified,
                    sum(case when u.role = 'business_owner' then 1 else 0 end) as business_owners,
                    sum(case when u.created_at > datetime() - duration('P1D') then 1 else 0 end) as new_today
            """)
            if user_result:
                user_data = user_result[0]
                stats['users'] = {
                    'total': user_data.get('total') or 0,
                    'verified': user_data.get('verified') or 0,
                    'business_owners': user_data.get('business_owners') or 0,
                    'new_today': user_data.get('new_today') or 0
                }
            
            # Job stats
            job_result = safe_run(session, """
                MATCH (j:Job)
                RETURN 
                    count(*) as total,
                    sum(case when j.is_featured = true then 1 else 0 end) as featured,
                    sum(case when j.is_active = true then 1 else 0 end) as active,
                    sum(case when j.created_at > datetime() - duration('P1D') then 1 else 0 end) as new_today
            """)
            if job_result:
                job_data = job_result[0]
                stats['jobs'] = {
                    'total': job_data.get('total') or 0,
                    'featured': job_data.get('featured') or 0,
                    'active': job_data.get('active') or 0,
                    'new_today': job_data.get('new_today') or 0
                }
            
            # Business stats
            business_result = safe_run(session, """
                MATCH (b:Business)
                RETURN 
                    count(*) as total,
                    sum(case when b.is_featured = true then 1 else 0 end) as featured,
                    sum(case when b.is_active = true then 1 else 0 end) as active,
                    sum(case when b.created_at > datetime() - duration('P1D') then 1 else 0 end) as new_today
            """)
            if business_result:
                business_data = business_result[0]
                stats['businesses'] = {
                    'total': business_data.get('total') or 0,
                    'featured': business_data.get('featured') or 0,
                    'active': business_data.get('active') or 0,
                    'new_today': business_data.get('new_today') or 0
                }
            
            # Verification stats
            try:
                verification_result = safe_run(session, """
                    MATCH (v:Verification)
                    RETURN 
                        count(*) as total,
                        sum(case when v.verification_status = 'approved' then 1 else 0 end) as approved,
                        sum(case when v.verification_status = 'pending' then 1 else 0 end) as pending,
                        sum(case when v.verification_status = 'rejected' then 1 else 0 end) as rejected
                """)
                if verification_result:
                    verification_data = verification_result[0]
                    stats['verifications'] = {
                    'total': verification_data.get('total') or 0,
                    'approved': verification_data.get('approved') or 0,
                    'pending': verification_data.get('pending') or 0,
                    'rejected': verification_data.get('rejected') or 0
                }
            except Exception:
                # Verification nodes don't exist in this system
                stats['verifications'] = {
                    'total': 0,
                    'approved': 0,
                    'pending': 0,
                    'rejected': 0
                }
    
    except Exception as e:
        logger.error(f"Error fetching stats: {str(e)}")
    
    return stats

# ============================================================================
# ADMIN DASHBOARD
# ============================================================================

@admin_mgmt.route('/')
@admin_mgmt.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Main admin dashboard with real-time statistics"""
    stats = get_realtime_stats()
    
    return render_template('admin/admin_dashboard.html', 
                         stats=stats,
                         page_title='Admin Dashboard',
                         nav_section='dashboard')

# ============================================================================
# USERS MANAGEMENT
# ============================================================================

@admin_mgmt.route('/users-management')
@login_required
@admin_required
def users_management():
    """Comprehensive user management page with search, sort, and filter"""
    db = get_neo4j_db()
    
    # Get filters from request
    search = request.args.get('search', '')
    role_filter = request.args.get('role', '')
    status_filter = request.args.get('status', '')
    sort_by = request.args.get('sort', 'created_at')
    sort_order = request.args.get('order', 'desc')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    with db.session() as session:
        # Build query
        query = "MATCH (u:User) WHERE 1=1"
        params = {}
        
        if search:
            query += " AND (u.username CONTAINS $search OR u.email CONTAINS $search OR u.first_name CONTAINS $search OR u.last_name CONTAINS $search)"
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
        
        # Count total - build separate count query with WHERE clause before RETURN
        count_parts = query.split(' WHERE ', 1)
        if len(count_parts) > 1:
            count_query = f"{count_parts[0]} WHERE {count_parts[1]} RETURN COUNT(u) as total"
        else:
            count_query = query + " RETURN COUNT(u) as total"
        
        total_result = safe_run(session, count_query, params)
        total_users = total_result[0]['total'] if total_result else 0
        
        # Sort and paginate
        sort_field = f"u.{sort_by}"
        query += f" RETURN u ORDER BY {sort_field} {sort_order.upper()}"
        query += f" SKIP {(page - 1) * per_page} LIMIT {per_page}"
        
        result = safe_run(session, query, params)
        users = [record['u'] for record in (result or [])]
    
    # Calculate pagination
    total_pages = (total_users + per_page - 1) // per_page
    
    return render_template('admin/users_management.html',
                         users=users,
                         total_users=total_users,
                         current_page=page,
                         total_pages=total_pages,
                         search=search,
                         role_filter=role_filter,
                         status_filter=status_filter,
                         sort_by=sort_by,
                         sort_order=sort_order,
                         stats=get_realtime_stats())


@admin_mgmt.route('/user/<user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Edit user details"""
    db = get_neo4j_db()
    
    with db.session() as session:
        result = safe_run(session, "MATCH (u:User {id: $user_id}) RETURN u", {'user_id': user_id})
        if not result:
            flash('User not found', 'error')
            return redirect(url_for('admin_mgmt.users_management'))
        
        user = result[0]['u']
        
        if request.method == 'POST':
            # Update user
            updates = {}
            for field in ['email', 'username', 'first_name', 'last_name', 'phone', 'location']:
                if field in request.form:
                    updates[field] = request.form.get(field)
            
            update_query = "MATCH (u:User {id: $user_id}) SET"
            params = {'user_id': user_id}
            
            for field, value in updates.items():
                update_query += f" u.{field} = ${field},"
                params[field] = value
            
            update_query = update_query.rstrip(',')
            safe_run(session, update_query, params)
            
            flash('User updated successfully', 'success')
            return redirect(url_for('admin_mgmt.users_management'))
    
    return render_template('admin/edit_user.html', user=user)


@admin_mgmt.route('/user/<user_id>/suspend', methods=['POST'])
@login_required
@admin_required
def suspend_user(user_id):
    """Suspend a user"""
    db = get_neo4j_db()
    
    with db.session() as session:
        safe_run(session, """
            MATCH (u:User {id: $user_id})
            SET u.is_active = false, u.suspended_at = datetime()
        """, {'user_id': user_id})
    
    flash('User suspended successfully', 'success')
    return redirect(url_for('admin_mgmt.users_management'))


@admin_mgmt.route('/user/<user_id>/unsuspend', methods=['POST'])
@login_required
@admin_required
def unsuspend_user(user_id):
    """Unsuspend a user"""
    db = get_neo4j_db()
    
    with db.session() as session:
        safe_run(session, """
            MATCH (u:User {id: $user_id})
            SET u.is_active = true, u.suspended_at = null
        """, {'user_id': user_id})
    
    flash('User unsuspended successfully', 'success')
    return redirect(url_for('admin_mgmt.users_management'))


@admin_mgmt.route('/user/<user_id>/ban', methods=['POST'])
@login_required
@admin_required
def ban_user(user_id):
    """Ban a user"""
    db = get_neo4j_db()
    reason = request.form.get('reason', 'No reason provided')
    
    with db.session() as session:
        safe_run(session, """
            MATCH (u:User {id: $user_id})
            SET u.is_banned = true, u.is_active = false, u.banned_at = datetime(), u.ban_reason = $reason
        """, {'user_id': user_id, 'reason': reason})
    
    flash('User banned successfully', 'success')
    return redirect(url_for('admin_mgmt.users_management'))


@admin_mgmt.route('/user/<user_id>/unban', methods=['POST'])
@login_required
@admin_required
def unban_user(user_id):
    """Unban a user"""
    db = get_neo4j_db()
    
    with db.session() as session:
        safe_run(session, """
            MATCH (u:User {id: $user_id})
            SET u.is_banned = false, u.banned_at = null, u.ban_reason = null
        """, {'user_id': user_id})
    
    flash('User unbanned successfully', 'success')
    return redirect(url_for('admin_mgmt.users_management'))


@admin_mgmt.route('/user/<user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete a user"""
    db = get_neo4j_db()
    
    with db.session() as session:
        # Delete all relationships and the user
        safe_run(session, """
            MATCH (u:User {id: $user_id})
            DETACH DELETE u
        """, {'user_id': user_id})
    
    flash('User deleted successfully', 'success')
    return redirect(url_for('admin_mgmt.users_management'))


# ============================================================================
# JOBS MANAGEMENT
# ============================================================================

@admin_mgmt.route('/jobs-management')
@login_required
@admin_required
def jobs_management():
    """Manage all jobs in the platform"""
    db = get_neo4j_db()
    
    search = request.args.get('search', '')
    category_filter = request.args.get('category', '')
    employment_type_filter = request.args.get('employment_type', '')
    status_filter = request.args.get('status', '')
    sort_by = request.args.get('sort', 'created_at')
    sort_order = request.args.get('order', 'desc')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    try:
        with db.session() as session:
            # Build query
            query = "MATCH (j:Job) WHERE 1=1"
            params = {}
            
            if search:
                query += " AND (j.title CONTAINS $search OR j.description CONTAINS $search)"
                params['search'] = search
            
            if category_filter:
                query += " AND j.category = $category"
                params['category'] = category_filter
            
            if employment_type_filter:
                query += " AND j.employment_type = $employment_type"
                params['employment_type'] = employment_type_filter
            
            if status_filter:
                if status_filter == 'active':
                    query += " AND j.is_active = true AND (j.deadline IS NULL OR j.deadline > datetime())"
                elif status_filter == 'expired':
                    query += " AND (j.is_active = false OR (j.deadline IS NOT NULL AND j.deadline <= datetime()))"
                elif status_filter == 'pending':
                    query += " AND j.is_approved = false"
                elif status_filter == 'approved':
                    query += " AND j.is_approved = true"
            
            # Count - build separate count query with WHERE clause before RETURN
            count_parts = query.split(' WHERE ', 1)
            if len(count_parts) > 1:
                count_query = f"{count_parts[0]} WHERE {count_parts[1]} RETURN COUNT(j) as total"
            else:
                count_query = query + " RETURN COUNT(j) as total"
            
            total_result = safe_run(session, count_query, params)
            total_jobs = total_result[0]['total'] if total_result else 0
            
            # Sort and paginate
            sort_field = f"j.{sort_by}"
            query += f" RETURN j ORDER BY {sort_field} {sort_order.upper()}"
            query += f" SKIP {(page - 1) * per_page} LIMIT {per_page}"
            
            result = safe_run(session, query, params)
            jobs = [record['j'] for record in (result or [])]
            
            # Get categories for filter
            cat_result = safe_run(session, "MATCH (j:Job) WHERE j.category IS NOT NULL RETURN DISTINCT j.category as category")
            categories = [rec['category'] for rec in (cat_result or [])]
            
            # Get stats - must be inside the session context
            active_result = safe_run(session, "MATCH (j:Job) WHERE j.is_active = true RETURN COUNT(j) as count")
            pending_result = safe_run(session, "MATCH (j:Job) WHERE j.is_approved = false RETURN COUNT(j) as count")
            featured_result = safe_run(session, "MATCH (j:Job) WHERE j.is_featured = true RETURN COUNT(j) as count")
            expired_result = safe_run(session, "MATCH (j:Job) WHERE j.deadline < datetime() RETURN COUNT(j) as count")
        
        total_pages = (total_jobs + per_page - 1) // per_page
        
        stats = {
            'total_jobs': total_jobs,
            'active_jobs': active_result[0]['count'] if active_result else 0,
            'pending_jobs': pending_result[0]['count'] if pending_result else 0,
            'featured_jobs': featured_result[0]['count'] if featured_result else 0,
            'expired_jobs': expired_result[0]['count'] if expired_result else 0,
        }
        
        return render_template('admin/jobs_management.html',
                                 jobs=jobs,
                                 total_jobs=total_jobs,
                                 active_jobs=stats['active_jobs'],
                                 pending_jobs=stats['pending_jobs'],
                                 featured_jobs=stats['featured_jobs'],
                                 expired_jobs=stats['expired_jobs'],
                                 categories=categories,
                                 current_page=page,
                                 total_pages=total_pages,
                                 search=search,
                                 category_filter=category_filter,
                                 employment_type_filter=employment_type_filter,
                                 status_filter=status_filter,
                                 sort_by=sort_by,
                                 sort_order=sort_order,
                                 stats=get_realtime_stats())
    except Exception as e:
        logger.error(f"Error in jobs_management: {e}")
        flash('Error loading jobs management page', 'error')
        return redirect(url_for('admin_mgmt.dashboard'))


@admin_mgmt.route('/job/<job_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_job(job_id):
    """Delete a job"""
    db = get_neo4j_db()
    
    with db.session() as session:
        safe_run(session, """
            MATCH (j:Job {id: $job_id})
            DETACH DELETE j
        """, {'job_id': job_id})
    
    flash('Job deleted successfully', 'success')
    return redirect(url_for('admin_mgmt.jobs_management'))


@admin_mgmt.route('/job/<job_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_job(job_id):
    """Approve a job"""
    db = get_neo4j_db()
    
    with db.session() as session:
        result = safe_run(session, "MATCH (j:Job {id: $job_id}) RETURN j", {'job_id': job_id})
        if not result:
            flash('Job not found', 'error')
            return redirect(url_for('admin_mgmt.jobs_management'))
        
        job = _node_to_dict(result[0]['j'])
        
        safe_run(session, """
            MATCH (j:Job {id: $job_id})
            SET j.status = 'active', j.is_approved = true, j.approved_at = datetime(), j.approved_by = $admin_id
        """, {'job_id': job_id, 'admin_id': current_user.id})
        
        # Get job owner email
        owner_result = safe_run(session, """
            MATCH (u:User)-[:OWNS]->(b:Business)-[:POSTED]->(j:Job {id: $job_id})
            RETURN u.email as email
        """, {'job_id': job_id})
        
        if owner_result:
            owner_email = owner_result[0].get('email')
            if owner_email:
                try:
                    from tasks import send_email_task
                    send_email_task.delay(
                        subject="Job Approved - " + job.get('title', 'Your Job'),
                        body=f"""Your job posting "{job.get('title')}" has been approved and is now active on the platform.

You can now start receiving applications from interested candidates.

Best regards,
Catanduanes Connect Team""",
                        to_email=owner_email
                    )
                except Exception as e:
                    logger.error(f"Failed to send email notification: {e}")
    
    flash('Job approved successfully', 'success')
    return redirect(url_for('admin_mgmt.jobs_management'))


@admin_mgmt.route('/job/<job_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_job(job_id):
    """Reject a job"""
    db = get_neo4j_db()
    reason = request.form.get('reason', '')
    
    with db.session() as session:
        result = safe_run(session, "MATCH (j:Job {id: $job_id}) RETURN j", {'job_id': job_id})
        if not result:
            flash('Job not found', 'error')
            return redirect(url_for('admin_mgmt.jobs_management'))
        
        job = _node_to_dict(result[0]['j'])
        
        safe_run(session, """
            MATCH (j:Job {id: $job_id})
            SET j.status = 'rejected', j.is_approved = false, j.rejected_at = datetime(), j.rejection_reason = $reason, j.rejected_by = $admin_id
        """, {'job_id': job_id, 'reason': reason, 'admin_id': current_user.id})
        
        # Get job owner email
        owner_result = safe_run(session, """
            MATCH (u:User)-[:OWNS]->(b:Business)-[:POSTED]->(j:Job {id: $job_id})
            RETURN u.email as email
        """, {'job_id': job_id})
        
        if owner_result:
            owner_email = owner_result[0].get('email')
            if owner_email:
                try:
                    from tasks import send_email_task
                    send_email_task.delay(
                        subject="Job Rejected - " + job.get('title', 'Your Job'),
                        body=f"""Your job posting "{job.get('title')}" has been rejected.

Reason: {reason}

Please review the feedback and make necessary adjustments before resubmitting.

Best regards,
Catanduanes Connect Team""",
                        to_email=owner_email
                    )
                except Exception as e:
                    logger.error(f"Failed to send email notification: {e}")
    
    flash('Job rejected successfully', 'success')
    return redirect(url_for('admin_mgmt.jobs_management'))


@admin_mgmt.route('/job/<job_id>/feature', methods=['POST'])
@login_required
@admin_required
def feature_job(job_id):
    """Feature a job"""
    db = get_neo4j_db()
    
    with db.session() as session:
        safe_run(session, """
            MATCH (j:Job {id: $job_id})
            SET j.is_featured = true, j.featured_at = datetime()
        """, {'job_id': job_id})
    
    flash('Job featured successfully', 'success')
    return redirect(url_for('admin_mgmt.jobs_management'))


@admin_mgmt.route('/job/<job_id>/unfeature', methods=['POST'])
@login_required
@admin_required
def unfeature_job(job_id):
    """Unfeature a job"""
    db = get_neo4j_db()
    
    with db.session() as session:
        safe_run(session, """
            MATCH (j:Job {id: $job_id})
            SET j.is_featured = false, j.featured_at = null
        """, {'job_id': job_id})
    
    flash('Job unfeatured successfully', 'success')
    return redirect(url_for('admin_mgmt.jobs_management'))


@admin_mgmt.route('/job/<job_id>/view', methods=['GET'])
@login_required
@admin_required
def view_job(job_id):
    """View job details"""
    db = get_neo4j_db()
    
    with db.session() as session:
        result = safe_run(session, "MATCH (j:Job {id: $job_id}) RETURN j", {'job_id': job_id})
        if not result:
            flash('Job not found', 'error')
            return redirect(url_for('admin_mgmt.jobs_management'))
        
        job = _node_to_dict(result[0]['j'])
    
    return render_template('jobs/job_detail.html', job=job)


# ============================================================================
# BUSINESS MANAGEMENT
# ============================================================================

@admin_mgmt.route('/business-management')
@login_required
@admin_required
def business_management():
    """Manage all businesses in the platform"""
    db = get_neo4j_db()
    
    search = request.args.get('search', '')
    category_filter = request.args.get('category', '')
    status_filter = request.args.get('status', '')
    featured_filter = request.args.get('featured', '')
    sort_by = request.args.get('sort', 'created_at')
    sort_order = request.args.get('order', 'desc')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    try:
        with db.session() as session:
            query = "MATCH (b:Business) WHERE 1=1"
            params = {}
            
            if search:
                query += " AND (b.name CONTAINS $search OR b.description CONTAINS $search)"
                params['search'] = search
            
            if category_filter:
                query += " AND b.category = $category"
                params['category'] = category_filter
            
            if status_filter:
                if status_filter == 'approved':
                    query += " AND b.is_approved = true"
                elif status_filter == 'pending':
                    query += " AND b.is_approved = false AND b.is_rejected = false"
                elif status_filter == 'rejected':
                    query += " AND b.is_rejected = true"
            
            if featured_filter:
                query += f" AND b.is_featured = {featured_filter == 'yes'}"
            
            # Count - build separate count query with WHERE clause before RETURN
            count_parts = query.split(' WHERE ', 1)
            if len(count_parts) > 1:
                count_query = f"{count_parts[0]} WHERE {count_parts[1]} RETURN COUNT(b) as total"
            else:
                count_query = query + " RETURN COUNT(b) as total"
            
            total_result = safe_run(session, count_query, params)
            total_businesses = total_result[0]['total'] if total_result else 0
            
            # Sort and paginate
            sort_field = f"b.{sort_by}"
            query += f" RETURN b ORDER BY {sort_field} {sort_order.upper()}"
            query += f" SKIP {(page - 1) * per_page} LIMIT {per_page}"
            
            result = safe_run(session, query, params)
            businesses = [record['b'] for record in (result or [])]
            
            # Get categories for filter
            cat_result = safe_run(session, "MATCH (b:Business) WHERE b.category IS NOT NULL RETURN DISTINCT b.category as category")
            categories = [rec['category'] for rec in (cat_result or [])]
            
            # Get stats - must be inside the session context
            approved_result = safe_run(session, "MATCH (b:Business) WHERE b.is_approved = true RETURN COUNT(b) as count")
            pending_result = safe_run(session, "MATCH (b:Business) WHERE b.is_approved = false AND b.is_rejected = false RETURN COUNT(b) as count")
            featured_result = safe_run(session, "MATCH (b:Business) WHERE b.is_featured = true RETURN COUNT(b) as count")
        
        total_pages = (total_businesses + per_page - 1) // per_page
        
        stats = {
            'total_businesses': total_businesses,
            'approved_count': approved_result[0]['count'] if approved_result else 0,
            'pending_count': pending_result[0]['count'] if pending_result else 0,
            'featured_count': featured_result[0]['count'] if featured_result else 0,
        }
        
        return render_template('admin/businesses_management.html',
                                 businesses=businesses,
                                 total_businesses=total_businesses,
                                 approved_count=stats['approved_count'],
                                 pending_count=stats['pending_count'],
                                 featured_count=stats['featured_count'],
                                 categories=categories,
                                 current_page=page,
                                 total_pages=total_pages,
                                 search=search,
                                 category_filter=category_filter,
                                 status_filter=status_filter,
                                 featured_filter=featured_filter,
                                 sort_by=sort_by,
                                 sort_order=sort_order,
                                 stats=get_realtime_stats())
    except Exception as e:
        logger.error(f"Error in business_management: {e}")
        flash('Error loading business management page', 'error')
        return redirect(url_for('admin_mgmt.dashboard'))
@admin_mgmt.route('/business/<business_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_business(business_id):
    """Edit business details"""
    db = get_neo4j_db()
    
    with db.session() as session:
        result = safe_run(session, "MATCH (b:Business {id: $business_id}) RETURN b", {'business_id': business_id})
        if not result:
            flash('Business not found', 'error')
            return redirect(url_for('admin_mgmt.business_management'))
        
        business = _node_to_dict(result[0]['b'])
        
        if request.method == 'POST':
            updates = {}
            for field in ['name', 'description', 'email', 'phone', 'location', 'category']:
                if field in request.form:
                    updates[field] = request.form.get(field)
            
            update_query = "MATCH (b:Business {id: $business_id}) SET"
            params = {'business_id': business_id}
            
            for field, value in updates.items():
                update_query += f" b.{field} = ${field},"
                params[field] = value
            
            update_query = update_query.rstrip(',')
            safe_run(session, update_query, params)
            
            flash('Business updated successfully', 'success')
            return redirect(url_for('admin_mgmt.business_management'))
    
    return render_template('admin/edit_business.html', business=business)


@admin_mgmt.route('/business/<business_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_business(business_id):
    """Delete a business"""
    db = get_neo4j_db()
    
    with db.session() as session:
        safe_run(session, """
            MATCH (b:Business {id: $business_id})
            DETACH DELETE b
        """, {'business_id': business_id})
    
    flash('Business deleted successfully', 'success')
    return redirect(url_for('admin_mgmt.business_management'))


@admin_mgmt.route('/business/<business_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_business(business_id):
    """Approve a business"""
    db = get_neo4j_db()
    
    with db.session() as session:
        safe_run(session, """
            MATCH (b:Business {id: $business_id})
            SET b.is_approved = true, b.is_rejected = false, b.approved_at = datetime(), b.approved_by = $admin_id
        """, {'business_id': business_id, 'admin_id': current_user.id})
    
    flash('Business approved successfully', 'success')
    return redirect(url_for('admin_mgmt.business_management'))


@admin_mgmt.route('/business/<business_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_business(business_id):
    """Reject a business"""
    db = get_neo4j_db()
    reason = request.form.get('reason', '')
    
    with db.session() as session:
        safe_run(session, """
            MATCH (b:Business {id: $business_id})
            SET b.is_rejected = true, b.is_approved = false, b.rejected_at = datetime(), b.rejection_reason = $reason, b.rejected_by = $admin_id
        """, {'business_id': business_id, 'reason': reason, 'admin_id': current_user.id})
    
    flash('Business rejected successfully', 'success')
    return redirect(url_for('admin_mgmt.business_management'))


@admin_mgmt.route('/business/<business_id>/feature', methods=['POST'])
@login_required
@admin_required
def feature_business(business_id):
    """Feature a business"""
    db = get_neo4j_db()
    
    with db.session() as session:
        safe_run(session, """
            MATCH (b:Business {id: $business_id})
            SET b.is_featured = true, b.featured_at = datetime()
        """, {'business_id': business_id})
    
    flash('Business featured successfully', 'success')
    return redirect(url_for('admin_mgmt.business_management'))


@admin_mgmt.route('/business/<business_id>/unfeature', methods=['POST'])
@login_required
@admin_required
def unfeature_business(business_id):
    """Unfeature a business"""
    db = get_neo4j_db()
    
    with db.session() as session:
        safe_run(session, """
            MATCH (b:Business {id: $business_id})
            SET b.is_featured = false, b.featured_at = null
        """, {'business_id': business_id})
    
    flash('Business unfeatured successfully', 'success')
    return redirect(url_for('admin_mgmt.business_management'))


@admin_mgmt.route('/business/<business_id>/view', methods=['GET'])
@login_required
@admin_required
def view_business(business_id):
    """View business details"""
    db = get_neo4j_db()
    
    with db.session() as session:
        result = safe_run(session, "MATCH (b:Business {id: $business_id}) RETURN b", {'business_id': business_id})
        if not result:
            flash('Business not found', 'error')
            return redirect(url_for('admin_mgmt.business_management'))
        
        business = _node_to_dict(result[0]['b'])
    
    return render_template('admin/view_business.html', business=business)


# ============================================================================
# VERIFICATION MANAGEMENT
# ============================================================================

@admin_mgmt.route('/verifications')
@login_required
@admin_required
def verifications():
    """Manage all verifications"""
    db = get_neo4j_db()
    
    status_filter = request.args.get('status', 'pending')
    user_type_filter = request.args.get('user_type', '')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    with db.session() as session:
        query = """
            MATCH (u:User)-[:SUBMITTED]->(v:Verification)
            WHERE v.verification_status = $status
            RETURN v, u
        """
        params = {'status': status_filter}
        
        if user_type_filter:
            query += " AND u.role = $user_type"
            params['user_type'] = user_type_filter
        
        # Count - properly structured with WHERE before RETURN
        count_query = """
            MATCH (u:User)-[:SUBMITTED]->(v:Verification)
            WHERE v.verification_status = $status
        """
        if user_type_filter:
            count_query += " AND u.role = $user_type"
        count_query += " RETURN COUNT(v) as total"
        
        total_result = safe_run(session, count_query, params)
        total = total_result[0]['total'] if total_result else 0
        
        # Paginate
        query += f" SKIP {(page - 1) * per_page} LIMIT {per_page}"
        result = safe_run(session, query, params)
        
        verifications = []
        if result:
            for record in result:
                ver_data = record['v']
                user_data = record['u']
                verifications.append({
                    'verification': ver_data,
                    'user': user_data
                })
    
    total_pages = (total + per_page - 1) // per_page
    
    return render_template('admin/verifications.html',
                         verifications=verifications,
                         total=total,
                         current_page=page,
                         total_pages=total_pages,
                         status_filter=status_filter,
                         user_type_filter=user_type_filter,
                         stats=get_realtime_stats())


@admin_mgmt.route('/verification/<verification_id>/view-document')
@login_required
@admin_required
def view_document(verification_id):
    """View verification document"""
    db = get_neo4j_db()
    
    with db.session() as session:
        result = safe_run(session, """
            MATCH (v:Verification {id: $verification_id})
            RETURN v.file_path as file_path
        """, {'verification_id': verification_id})
        
        if result and result[0]['file_path']:
            file_path = result[0]['file_path']
            if os.path.exists(file_path):
                return send_file(file_path, as_attachment=True)
    
    flash('Document not found', 'error')
    return redirect(url_for('admin_mgmt.verifications'))


@admin_mgmt.route('/verification/<verification_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_verification(verification_id):
    """Approve a verification"""
    db = get_neo4j_db()
    notes = request.form.get('notes', '')
    
    with db.session() as session:
        # Update verification
        safe_run(session, """
            MATCH (v:Verification {id: $verification_id})
            SET v.status = 'verified',
                v.reviewed_at = datetime(),
                v.reviewer_id = $reviewer_id,
                v.reviewer_notes = $notes
        """, {
            'verification_id': verification_id,
            'reviewer_id': current_user.id,
            'notes': notes
        })
        
        # Update user
        safe_run(session, """
            MATCH (u:User)-[:SUBMITTED]->(v:Verification {id: $verification_id})
            SET u.is_verified = true,
                u.verification_status = 'approved',
                u.verified_at = datetime()
        """, {'verification_id': verification_id})
    
    flash('Verification approved', 'success')
    return redirect(url_for('admin_mgmt.verifications'))


@admin_mgmt.route('/verification/<verification_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_verification(verification_id):
    """Reject a verification"""
    db = get_neo4j_db()
    notes = request.form.get('notes', '')
    
    with db.session() as session:
        # Update verification
        safe_run(session, """
            MATCH (v:Verification {id: $verification_id})
            SET v.status = 'rejected',
                v.reviewed_at = datetime(),
                v.reviewer_id = $reviewer_id,
                v.reviewer_notes = $notes
        """, {
            'verification_id': verification_id,
            'reviewer_id': current_user.id,
            'notes': notes
        })
        
        # Update user
        safe_run(session, """
            MATCH (u:User)-[:SUBMITTED]->(v:Verification {id: $verification_id})
            SET u.is_verified = false,
                u.verification_status = 'rejected'
        """, {'verification_id': verification_id})
    
    flash('Verification rejected', 'success')
    return redirect(url_for('admin_mgmt.verifications'))


# ====================== ANALYTICS & REPORTING ROUTES ======================

@admin_mgmt.route('/reports', methods=['GET'])
@login_required
@admin_required
def reports_analytics():
    """Analytics and reporting dashboard with system statistics"""
    session = get_neo4j_db()
    
    try:
        # Get user statistics
        user_stats = safe_run(session, """
            MATCH (u:User)
            RETURN 
                count(*) as total_users,
                sum(case when u.is_verified = true then 1 else 0 end) as verified_users,
                sum(case when u.is_verified = false then 1 else 0 end) as unverified_users,
                sum(case when u.is_banned = true then 1 else 0 end) as banned_users,
                sum(case when u.is_suspended = true then 1 else 0 end) as suspended_users,
                sum(case when u.created_at > datetime() - duration('P30D') then 1 else 0 end) as users_last_30d,
                sum(case when u.role = 'business' then 1 else 0 end) as business_users,
                sum(case when u.role = 'jobseeker' then 1 else 0 end) as jobseeker_users,
                sum(case when u.role = 'admin' then 1 else 0 end) as admin_users
        """)[0] if safe_run(session, "MATCH (u:User) RETURN count(*) as count")[0]['count'] > 0 else None
        
        # Get job statistics
        job_stats = safe_run(session, """
            MATCH (j:Job)
            RETURN 
                count(*) as total_jobs,
                sum(case when j.is_approved = true then 1 else 0 end) as approved_jobs,
                sum(case when j.is_approved = false then 1 else 0 end) as pending_jobs,
                sum(case when j.is_featured = true then 1 else 0 end) as featured_jobs,
                sum(case when j.is_expired = false then 1 else 0 end) as active_jobs,
                sum(case when j.is_expired = true then 1 else 0 end) as expired_jobs,
                sum(case when j.created_at > datetime() - duration('P30D') then 1 else 0 end) as jobs_last_30d
        """)[0] if safe_run(session, "MATCH (j:Job) RETURN count(*) as count")[0]['count'] > 0 else None
        
        # Get business statistics
        business_stats = safe_run(session, """
            MATCH (b:Business)
            RETURN 
                count(*) as total_businesses,
                sum(case when b.is_approved = true then 1 else 0 end) as approved_businesses,
                sum(case when b.is_approved = false then 1 else 0 end) as pending_businesses,
                sum(case when b.is_featured = true then 1 else 0 end) as featured_businesses,
                sum(case when b.is_active = true then 1 else 0 end) as active_businesses,
                sum(case when b.created_at > datetime() - duration('P30D') then 1 else 0 end) as businesses_last_30d
        """)[0] if safe_run(session, "MATCH (b:Business) RETURN count(*) as count")[0]['count'] > 0 else None
        
        # Get top job categories
        top_job_categories = safe_run(session, """
            MATCH (j:Job)
            RETURN j.category as category, count(*) as count
            ORDER BY count DESC
            LIMIT 10
        """)
        
        # Get top business categories
        top_business_categories = safe_run(session, """
            MATCH (b:Business)
            RETURN b.category as category, count(*) as count
            ORDER BY count DESC
            LIMIT 10
        """)
        
        # Get verification statistics
        try:
            verification_result = safe_run(session, "MATCH (v:Verification) RETURN count(*) as count")
            has_verifications = verification_result and verification_result[0]['count'] > 0
            if has_verifications:
                verification_stats = safe_run(session, """
                    MATCH (v:Verification)
                    RETURN 
                        count(*) as total_verifications,
                        sum(case when v.status = 'approved' then 1 else 0 end) as approved_verifications,
                        sum(case when v.status = 'pending' then 1 else 0 end) as pending_verifications,
                        sum(case when v.status = 'rejected' then 1 else 0 end) as rejected_verifications
                """)[0]
            else:
                verification_stats = None
        except Exception:
            # Verification nodes don't exist in this system
            verification_stats = None
        
        # Build context dictionary
        context = {
            'user_stats': user_stats or {},
            'job_stats': job_stats or {},
            'business_stats': business_stats or {},
            'verification_stats': verification_stats or {},
            'top_job_categories': top_job_categories,
            'top_business_categories': top_business_categories,
            'page_title': 'Reports & Analytics',
            'nav_section': 'analytics',
            'stats': get_realtime_stats()
        }
        
        return render_template('admin/reports_analytics.html', **context)
        
    except Exception as e:
        current_app.logger.error(f"Analytics error: {str(e)}")
        flash('Error loading analytics', 'danger')
        return redirect(url_for('admin_mgmt.dashboard'))


# ====================== EXPORT ROUTES ======================

@admin_mgmt.route('/export/users.csv')
@login_required
@admin_required
def export_users_csv():
    """Export all users to CSV"""
    from io import StringIO
    import csv
    
    session = get_neo4j_db()
    
    try:
        # Get all users
        users = safe_run(session, """
            MATCH (u:User)
            RETURN u.id, u.username, u.email, u.first_name, u.last_name, 
                   u.role, u.is_verified, u.is_banned, u.is_suspended,
                   u.created_at, u.updated_at
            ORDER BY u.created_at DESC
        """)
        
        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['ID', 'Username', 'Email', 'First Name', 'Last Name', 
                        'Role', 'Verified', 'Banned', 'Suspended', 'Created At', 'Updated At'])
        
        # Write data
        for user in users:
            writer.writerow([
                user['u.id'],
                user['u.username'],
                user['u.email'],
                user['u.first_name'],
                user['u.last_name'],
                user['u.role'],
                'Yes' if user['u.is_verified'] else 'No',
                'Yes' if user['u.is_banned'] else 'No',
                'Yes' if user['u.is_suspended'] else 'No',
                user['u.created_at'],
                user['u.updated_at']
            ])
        
        # Return as download
        output.seek(0)
        return make_response(output.getvalue(),
                           200,
                           {
                               'Content-Disposition': 'attachment;filename=users_export.csv',
                               'Content-type': 'text/csv'
                           })
    
    except Exception as e:
        current_app.logger.error(f"Export users error: {str(e)}")
        flash('Error exporting users', 'danger')
        return redirect(url_for('admin_mgmt.users_management'))


@admin_mgmt.route('/export/jobs.csv')
@login_required
@admin_required
def export_jobs_csv():
    """Export all jobs to CSV"""
    from io import StringIO
    import csv
    
    session = get_neo4j_db()
    
    try:
        # Get all jobs
        jobs = safe_run(session, """
            MATCH (j:Job)<-[:POSTED]-(b:Business)
            RETURN j.id, j.title, j.description, j.category, j.employment_type,
                   j.is_approved, j.is_featured, j.is_expired, 
                   b.business_name as business_name,
                   j.created_at, j.updated_at
            ORDER BY j.created_at DESC
        """)
        
        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['ID', 'Title', 'Category', 'Employment Type', 
                        'Business', 'Approved', 'Featured', 'Expired', 'Created At', 'Updated At'])
        
        # Write data
        for job in jobs:
            writer.writerow([
                job['j.id'],
                job['j.title'],
                job['j.category'],
                job['j.employment_type'],
                job['business_name'],
                'Yes' if job['j.is_approved'] else 'No',
                'Yes' if job['j.is_featured'] else 'No',
                'Yes' if job['j.is_expired'] else 'No',
                job['j.created_at'],
                job['j.updated_at']
            ])
        
        # Return as download
        output.seek(0)
        return make_response(output.getvalue(),
                           200,
                           {
                               'Content-Disposition': 'attachment;filename=jobs_export.csv',
                               'Content-type': 'text/csv'
                           })
    
    except Exception as e:
        current_app.logger.error(f"Export jobs error: {str(e)}")
        flash('Error exporting jobs', 'danger')
        return redirect(url_for('admin_mgmt.jobs_management'))


@admin_mgmt.route('/export/businesses.csv')
@login_required
@admin_required
def export_businesses_csv():
    """Export all businesses to CSV"""
    from io import StringIO
    import csv
    
    session = get_neo4j_db()
    
    try:
        # Get all businesses
        businesses = safe_run(session, """
            MATCH (b:Business)<-[:OWNS]-(u:User)
            RETURN b.id, b.business_name, b.description, b.category, b.email,
                   b.phone, b.website, b.is_approved, b.is_featured, b.is_active,
                   u.username as owner_username,
                   b.created_at, b.updated_at
            ORDER BY b.created_at DESC
        """)
        
        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['ID', 'Business Name', 'Category', 'Email', 'Phone', 
                        'Website', 'Owner', 'Approved', 'Featured', 'Active', 'Created At', 'Updated At'])
        
        # Write data
        for business in businesses:
            writer.writerow([
                business['b.id'],
                business['b.business_name'],
                business['b.category'],
                business['b.email'],
                business['b.phone'],
                business['b.website'],
                business['owner_username'],
                'Yes' if business['b.is_approved'] else 'No',
                'Yes' if business['b.is_featured'] else 'No',
                'Yes' if business['b.is_active'] else 'No',
                business['b.created_at'],
                business['b.updated_at']
            ])
        
        # Return as download
        output.seek(0)
        return make_response(output.getvalue(),
                           200,
                           {
                               'Content-Disposition': 'attachment;filename=businesses_export.csv',
                               'Content-type': 'text/csv'
                           })
    
    except Exception as e:
        current_app.logger.error(f"Export businesses error: {str(e)}")
        flash('Error exporting businesses', 'danger')
        return redirect(url_for('admin_mgmt.businesses_management'))


# ====================== SETTINGS MANAGEMENT ROUTES ======================

@admin_mgmt.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    """Platform settings management"""
    session = get_neo4j_db()
    
    if request.method == 'POST':
        setting_category = request.form.get('category', 'general')
        
        try:
            if setting_category == 'general':
                platform_name = request.form.get('platform_name', 'Catanduanes Connect')
                timezone = request.form.get('timezone', 'Asia/Manila')
                language = request.form.get('language', 'en')
                
                safe_run(session, """
                    MERGE (s:Settings {type: 'general'})
                    SET s.platform_name = $platform_name,
                        s.timezone = $timezone,
                        s.language = $language,
                        s.updated_at = datetime(),
                        s.updated_by = $admin_id
                """, {
                    'platform_name': platform_name,
                    'timezone': timezone,
                    'language': language,
                    'admin_id': current_user.id
                })
                
            elif setting_category == 'email':
                smtp_host = request.form.get('smtp_host')
                smtp_port = int(request.form.get('smtp_port', 587))
                smtp_user = request.form.get('smtp_user')
                smtp_from = request.form.get('smtp_from')
                
                safe_run(session, """
                    MERGE (s:Settings {type: 'email'})
                    SET s.smtp_host = $smtp_host,
                        s.smtp_port = $smtp_port,
                        s.smtp_user = $smtp_user,
                        s.smtp_from = $smtp_from,
                        s.updated_at = datetime(),
                        s.updated_by = $admin_id
                """, {
                    'smtp_host': smtp_host,
                    'smtp_port': smtp_port,
                    'smtp_user': smtp_user,
                    'smtp_from': smtp_from,
                    'admin_id': current_user.id
                })
                
            elif setting_category == 'moderation':
                enable_moderation = request.form.get('enable_moderation') == 'on'
                require_verification = request.form.get('require_verification') == 'on'
                auto_approve_verified = request.form.get('auto_approve_verified') == 'on'
                
                safe_run(session, """
                    MERGE (s:Settings {type: 'moderation'})
                    SET s.enable_moderation = $enable_moderation,
                        s.require_verification = $require_verification,
                        s.auto_approve_verified = $auto_approve_verified,
                        s.updated_at = datetime(),
                        s.updated_by = $admin_id
                """, {
                    'enable_moderation': enable_moderation,
                    'require_verification': require_verification,
                    'auto_approve_verified': auto_approve_verified,
                    'admin_id': current_user.id
                })
                
            elif setting_category == 'features':
                enable_jobs = request.form.get('enable_jobs') == 'on'
                enable_businesses = request.form.get('enable_businesses') == 'on'
                enable_messaging = request.form.get('enable_messaging') == 'on'
                enable_analytics = request.form.get('enable_analytics') == 'on'
                
                safe_run(session, """
                    MERGE (s:Settings {type: 'features'})
                    SET s.enable_jobs = $enable_jobs,
                        s.enable_businesses = $enable_businesses,
                        s.enable_messaging = $enable_messaging,
                        s.enable_analytics = $enable_analytics,
                        s.updated_at = datetime(),
                        s.updated_by = $admin_id
                """, {
                    'enable_jobs': enable_jobs,
                    'enable_businesses': enable_businesses,
                    'enable_messaging': enable_messaging,
                    'enable_analytics': enable_analytics,
                    'admin_id': current_user.id
                })
            
            flash(f'{setting_category.capitalize()} settings updated successfully', 'success')
            
        except Exception as e:
            current_app.logger.error(f"Settings error: {str(e)}")
            flash('Error updating settings', 'danger')
        
        return redirect(url_for('admin_mgmt.settings'))
    
    # GET request - load current settings
    try:
        general_settings = safe_run(session, """
            MATCH (s:Settings {type: 'general'})
            RETURN s
        """)
        general_settings = _node_to_dict(general_settings[0]['s']) if general_settings else {}
        
        email_settings = safe_run(session, """
            MATCH (s:Settings {type: 'email'})
            RETURN s
        """)
        email_settings = _node_to_dict(email_settings[0]['s']) if email_settings else {}
        
        moderation_settings = safe_run(session, """
            MATCH (s:Settings {type: 'moderation'})
            RETURN s
        """)
        moderation_settings = _node_to_dict(moderation_settings[0]['s']) if moderation_settings else {}
        
        feature_settings = safe_run(session, """
            MATCH (s:Settings {type: 'features'})
            RETURN s
        """)
        feature_settings = _node_to_dict(feature_settings[0]['s']) if feature_settings else {}
        
        context = {
            'page_title': 'Platform Settings',
            'nav_section': 'settings',
            'general_settings': general_settings,
            'email_settings': email_settings,
            'moderation_settings': moderation_settings,
            'feature_settings': feature_settings,
            'timezones': [
                'Asia/Manila', 'UTC', 'America/New_York', 'Europe/London', 
                'Australia/Sydney', 'Asia/Bangkok', 'Asia/Singapore'
            ],
            'languages': [
                {'code': 'en', 'name': 'English'},
                {'code': 'tl', 'name': 'Tagalog'},
                {'code': 'es', 'name': 'Spanish'}
            ]
        }
        
        return render_template('admin/settings.html', **context)
        
    except Exception as e:
        current_app.logger.error(f"Load settings error: {str(e)}")
        flash('Error loading settings', 'danger')
        return redirect(url_for('admin_mgmt.dashboard'))


# ====================== MAINTENANCE ROUTES ======================

@admin_mgmt.route('/maintenance/<action>', methods=['POST'])
@login_required
@admin_required
def maintenance(action):
    """System maintenance operations"""
    session = get_neo4j_db()
    
    try:
        if action == 'cleanup':
            # Remove expired jobs older than 90 days
            result = safe_run(session, """
                MATCH (j:Job)
                WHERE j.is_expired = true AND 
                      j.updated_at < datetime() - duration('P90D')
                DETACH DELETE j
                RETURN count(*) as deleted
            """)
            deleted_count = result[0]['deleted'] if result else 0
            flash(f'Cleanup completed: {deleted_count} expired jobs removed', 'success')
            
        elif action == 'cache_clear':
            # Clear any cached data (application-level)
            from flask import cache
            if hasattr(current_app, 'cache'):
                current_app.cache.clear()
            flash('Cache cleared successfully', 'success')
            
        elif action == 'database_optimize':
            # Optimize Neo4j database
            safe_run(session, "CALL db.resampleIndex('idx_user_email')")
            safe_run(session, "CALL db.resampleIndex('idx_job_category')")
            safe_run(session, "CALL db.resampleIndex('idx_business_name')")
            flash('Database optimization completed', 'success')
            
        elif action == 'create_backup':
            # Log backup request (actual backup should be handled by db admin)
            safe_run(session, """
                CREATE (b:BackupLog {
                    id: apoc.create.uuid(),
                    timestamp: datetime(),
                    type: 'manual',
                    requested_by: $admin_id,
                    status: 'requested'
                })
            """, {'admin_id': current_user.id})
            flash('Backup requested - check with database administrator', 'info')
        
        return jsonify({'status': 'success', 'message': f'{action} completed'})
        
    except Exception as e:
        current_app.logger.error(f"Maintenance error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
