# Admin Templates - Code Examples & Backend Integration

## Quick Reference Code Snippets

### 1. Flask Route Handlers

#### Users Management Route
```python
@admin_mgmt.route('/users', methods=['GET'])
def users_management():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    role_filter = request.args.get('role', '', type=str)
    status_filter = request.args.get('status', '', type=str)
    sort_by = request.args.get('sort', 'created_at', type=str)
    sort_order = request.args.get('order', 'desc', type=str)
    
    # Build query
    query = User.query
    
    # Apply filters
    if search:
        query = query.filter(or_(
            User.username.ilike(f'%{search}%'),
            User.email.ilike(f'%{search}%'),
            User.full_name.ilike(f'%{search}%')
        ))
    
    if role_filter:
        query = query.filter(User.role == role_filter)
    
    if status_filter == 'active':
        query = query.filter(User.is_active == True, User.is_banned == False)
    elif status_filter == 'inactive':
        query = query.filter(User.is_active == False)
    elif status_filter == 'banned':
        query = query.filter(User.is_banned == True)
    elif status_filter == 'verified':
        query = query.filter(User.is_verified == True)
    
    # Sort
    if sort_by == 'username':
        sort_column = User.username
    elif sort_by == 'email':
        sort_column = User.email
    else:
        sort_column = User.created_at
    
    if sort_order == 'asc':
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())
    
    # Paginate
    paginated = query.paginate(page=page, per_page=50)
    
    return render_template('admin/users_management.html',
        users=paginated.items,
        total_users=paginated.total,
        current_page=page,
        total_pages=paginated.pages,
        search=search,
        role_filter=role_filter,
        status_filter=status_filter,
        sort_by=sort_by,
        sort_order=sort_order
    )

@admin_mgmt.route('/user/<int:user_id>/ban', methods=['POST'])
def ban_user(user_id):
    user = User.query.get_or_404(user_id)
    reason = request.form.get('reason', 'No reason provided')
    
    user.is_banned = True
    user.ban_reason = reason
    user.banned_at = datetime.utcnow()
    
    db.session.commit()
    
    # Log admin action
    admin_log = AdminLog(
        admin_id=current_user.id,
        action='ban_user',
        target_user_id=user_id,
        details=reason
    )
    db.session.add(admin_log)
    db.session.commit()
    
    flash(f'User {user.username} has been banned.', 'success')
    return redirect(url_for('admin_mgmt.users_management'))

@admin_mgmt.route('/user/<int:user_id>/suspend', methods=['POST'])
def suspend_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = False
    db.session.commit()
    
    AdminLog.create_entry(
        admin_id=current_user.id,
        action='suspend_user',
        target_user_id=user_id
    )
    
    flash(f'User {user.username} has been suspended.', 'success')
    return redirect(url_for('admin_mgmt.users_management'))

@admin_mgmt.route('/user/<int:user_id>/unsuspend', methods=['POST'])
def unsuspend_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = True
    db.session.commit()
    
    AdminLog.create_entry(
        admin_id=current_user.id,
        action='unsuspend_user',
        target_user_id=user_id
    )
    
    flash(f'User {user.username} has been unsuspended.', 'success')
    return redirect(url_for('admin_mgmt.users_management'))

@admin_mgmt.route('/user/<int:user_id>/delete', methods=['POST'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    username = user.username
    
    # Cascade delete or archive
    db.session.delete(user)
    db.session.commit()
    
    AdminLog.create_entry(
        admin_id=current_user.id,
        action='delete_user',
        target_id=user_id,
        details=f'Deleted user: {username}'
    )
    
    flash(f'User {username} has been permanently deleted.', 'danger')
    return redirect(url_for('admin_mgmt.users_management'))
```

#### Businesses Management Route
```python
@admin_mgmt.route('/businesses', methods=['GET'])
def businesses_management():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    category_filter = request.args.get('category', '', type=str)
    status_filter = request.args.get('status', '', type=str)
    featured_filter = request.args.get('featured', '', type=str)
    
    query = Business.query
    
    if search:
        query = query.filter(or_(
            Business.name.ilike(f'%{search}%'),
            User.full_name.ilike(f'%{search}%')
        )).join(User, Business.owner_id == User.id)
    
    if category_filter:
        query = query.filter(Business.category == category_filter)
    
    if status_filter == 'approved':
        query = query.filter(Business.is_approved == True)
    elif status_filter == 'pending':
        query = query.filter(Business.is_approved == False, Business.is_rejected == False)
    elif status_filter == 'rejected':
        query = query.filter(Business.is_rejected == True)
    
    if featured_filter == 'yes':
        query = query.filter(Business.is_featured == True)
    elif featured_filter == 'no':
        query = query.filter(Business.is_featured == False)
    
    # Get stats
    total_businesses = Business.query.count()
    approved_count = Business.query.filter_by(is_approved=True).count()
    pending_count = Business.query.filter(
        Business.is_approved == False,
        Business.is_rejected == False
    ).count()
    featured_count = Business.query.filter_by(is_featured=True).count()
    
    paginated = query.paginate(page=page, per_page=20)
    categories = db.session.query(Business.category).distinct()
    
    return render_template('admin/businesses_management.html',
        businesses=paginated.items,
        total_businesses=total_businesses,
        approved_count=approved_count,
        pending_count=pending_count,
        featured_count=featured_count,
        categories=[cat[0] for cat in categories],
        current_page=page,
        total_pages=paginated.pages,
        search=search,
        category_filter=category_filter,
        status_filter=status_filter,
        featured_filter=featured_filter
    )

@admin_mgmt.route('/business/<int:business_id>/approve', methods=['POST'])
def approve_business(business_id):
    business = Business.query.get_or_404(business_id)
    business.is_approved = True
    business.is_rejected = False
    business.approved_at = datetime.utcnow()
    business.approved_by = current_user.id
    
    db.session.commit()
    
    # Send email to owner
    send_business_approved_email(business.owner.email, business.name)
    
    AdminLog.create_entry(
        admin_id=current_user.id,
        action='approve_business',
        target_id=business_id
    )
    
    flash(f'Business "{business.name}" has been approved.', 'success')
    return redirect(url_for('admin_mgmt.businesses_management'))

@admin_mgmt.route('/business/<int:business_id>/reject', methods=['POST'])
def reject_business(business_id):
    business = Business.query.get_or_404(business_id)
    reason = request.form.get('reason', '')
    
    business.is_rejected = True
    business.rejection_reason = reason
    business.rejected_at = datetime.utcnow()
    
    db.session.commit()
    
    # Send email to owner
    send_business_rejected_email(business.owner.email, business.name, reason)
    
    AdminLog.create_entry(
        admin_id=current_user.id,
        action='reject_business',
        target_id=business_id,
        details=reason
    )
    
    flash(f'Business "{business.name}" has been rejected.', 'warning')
    return redirect(url_for('admin_mgmt.businesses_management'))

@admin_mgmt.route('/business/<int:business_id>/feature', methods=['POST'])
def feature_business(business_id):
    business = Business.query.get_or_404(business_id)
    business.is_featured = True
    business.featured_at = datetime.utcnow()
    
    db.session.commit()
    
    AdminLog.create_entry(
        admin_id=current_user.id,
        action='feature_business',
        target_id=business_id
    )
    
    flash(f'Business "{business.name}" is now featured!', 'success')
    return redirect(url_for('admin_mgmt.businesses_management'))

@admin_mgmt.route('/business/<int:business_id>/unfeature', methods=['POST'])
def unfeature_business(business_id):
    business = Business.query.get_or_404(business_id)
    business.is_featured = False
    
    db.session.commit()
    
    AdminLog.create_entry(
        admin_id=current_user.id,
        action='unfeature_business',
        target_id=business_id
    )
    
    flash(f'Business "{business.name}" is no longer featured.', 'info')
    return redirect(url_for('admin_mgmt.businesses_management'))

@admin_mgmt.route('/business/<int:business_id>/delete', methods=['POST'])
def delete_business(business_id):
    business = Business.query.get_or_404(business_id)
    business_name = business.name
    
    db.session.delete(business)
    db.session.commit()
    
    AdminLog.create_entry(
        admin_id=current_user.id,
        action='delete_business',
        target_id=business_id,
        details=f'Deleted: {business_name}'
    )
    
    flash(f'Business "{business_name}" has been deleted.', 'danger')
    return redirect(url_for('admin_mgmt.businesses_management'))
```

#### Reports & Analytics Route
```python
@admin_mgmt.route('/reports', methods=['GET'])
def reports_analytics():
    # User stats
    total_users = User.query.count()
    active_users_30d = User.query.filter(
        User.last_login >= datetime.utcnow() - timedelta(days=30)
    ).count()
    
    # Calculate growth
    users_last_month = User.query.filter(
        User.created_at >= datetime.utcnow() - timedelta(days=30)
    ).count()
    prev_month_users = User.query.filter(
        User.created_at >= datetime.utcnow() - timedelta(days=60),
        User.created_at < datetime.utcnow() - timedelta(days=30)
    ).count()
    user_growth = ((users_last_month - prev_month_users) / max(prev_month_users, 1)) * 100
    
    # User breakdown
    job_seekers = User.query.filter_by(role='job_seeker').count()
    business_owners = User.query.filter_by(role='business_owner').count()
    verified_users = User.query.filter_by(is_verified=True).count()
    banned_users = User.query.filter_by(is_banned=True).count()
    
    active_percentage = (active_users_30d / max(total_users, 1)) * 100
    job_seekers_percentage = (job_seekers / max(total_users, 1)) * 100
    business_owners_percentage = (business_owners / max(total_users, 1)) * 100
    verified_percentage = (verified_users / max(total_users, 1)) * 100
    banned_percentage = (banned_users / max(total_users, 1)) * 100
    
    # Business stats
    total_businesses = Business.query.count()
    approved_businesses = Business.query.filter_by(is_approved=True).count()
    pending_businesses = Business.query.filter(
        Business.is_approved == False,
        Business.is_rejected == False
    ).count()
    rejected_businesses = Business.query.filter_by(is_rejected=True).count()
    featured_businesses = Business.query.filter_by(is_featured=True).count()
    
    # Calculate business growth
    businesses_last_month = Business.query.filter(
        Business.created_at >= datetime.utcnow() - timedelta(days=30)
    ).count()
    prev_month_businesses = Business.query.filter(
        Business.created_at >= datetime.utcnow() - timedelta(days=60),
        Business.created_at < datetime.utcnow() - timedelta(days=30)
    ).count()
    business_growth = ((businesses_last_month - prev_month_businesses) / max(prev_month_businesses, 1)) * 100
    
    # Job stats
    total_jobs = Job.query.count()
    active_jobs = Job.query.filter_by(is_active=True).count()
    pending_jobs = Job.query.filter_by(is_approved=False, is_rejected=False).count()
    featured_jobs = Job.query.filter_by(is_featured=True).count()
    expired_jobs = Job.query.filter(Job.deadline < datetime.utcnow()).count()
    
    # Top categories
    top_job_cats = db.session.query(Job.category, func.count(Job.id)).group_by(
        Job.category
    ).order_by(func.count(Job.id).desc()).limit(5).all()
    
    top_biz_cats = db.session.query(Business.category, func.count(Business.id)).group_by(
        Business.category
    ).order_by(func.count(Business.id).desc()).limit(5).all()
    
    # Recent activity (last 7 days)
    recent_activity = AdminLog.query.filter(
        AdminLog.created_at >= datetime.utcnow() - timedelta(days=7)
    ).order_by(AdminLog.created_at.desc()).limit(20).all()
    
    return render_template('admin/reports_analytics.html',
        total_users=total_users,
        active_users_30d=active_users_30d,
        user_growth=round(user_growth, 1),
        active_percentage=round(active_percentage, 1),
        job_seekers=job_seekers,
        job_seekers_percentage=round(job_seekers_percentage, 1),
        business_owners=business_owners,
        business_owners_percentage=round(business_owners_percentage, 1),
        verified_users=verified_users,
        verified_percentage=round(verified_percentage, 1),
        banned_users=banned_users,
        banned_percentage=round(banned_percentage, 1),
        total_businesses=total_businesses,
        approved_businesses=approved_businesses,
        approved_business_percentage=round((approved_businesses/max(total_businesses,1))*100, 1),
        pending_businesses=pending_businesses,
        pending_business_percentage=round((pending_businesses/max(total_businesses,1))*100, 1),
        rejected_businesses=rejected_businesses,
        rejected_business_percentage=round((rejected_businesses/max(total_businesses,1))*100, 1),
        featured_businesses=featured_businesses,
        featured_business_percentage=round((featured_businesses/max(total_businesses,1))*100, 1),
        business_growth=round(business_growth, 1),
        total_jobs=total_jobs,
        active_jobs=active_jobs,
        pending_jobs=pending_jobs,
        featured_jobs=featured_jobs,
        expired_jobs=expired_jobs,
        job_growth=round((total_jobs/max(total_jobs,1))*100, 1),
        top_job_categories=top_job_cats,
        top_business_categories=top_biz_cats,
        recent_activity=recent_activity
    )

@admin_mgmt.route('/export/users.csv')
def export_users_report():
    users = User.query.all()
    
    # Create CSV
    csv_data = []
    csv_data.append(['Username', 'Email', 'Full Name', 'Role', 'Verified', 'Active', 'Banned', 'Created'])
    
    for user in users:
        csv_data.append([
            user.username,
            user.email,
            user.full_name,
            user.role,
            'Yes' if user.is_verified else 'No',
            'Yes' if user.is_active else 'No',
            'Yes' if user.is_banned else 'No',
            user.created_at.strftime('%Y-%m-%d')
        ])
    
    # Create response
    output = StringIO()
    writer = csv.writer(output)
    writer.writerows(csv_data)
    
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=users_report.csv"
    response.headers["Content-Type"] = "text/csv"
    
    return response
```

### 2. Database Models

```python
class AdminLog(db.Model):
    """Track admin actions"""
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)  # ban_user, approve_business, etc
    target_id = db.Column(db.Integer)
    target_type = db.Column(db.String(50))  # user, business, job
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @staticmethod
    def create_entry(admin_id, action, target_id=None, target_type=None, details=None):
        log = AdminLog(
            admin_id=admin_id,
            action=action,
            target_id=target_id,
            target_type=target_type,
            details=details
        )
        db.session.add(log)
        db.session.commit()
        return log
```

### 3. Email Notification Functions

```python
def send_business_approved_email(email, business_name):
    """Send approval email to business owner"""
    subject = f"Your business '{business_name}' has been approved!"
    body = f"""
    <h2>Business Approved</h2>
    <p>Your business "{business_name}" has been reviewed and approved.</p>
    <p>It is now visible on the platform for users to discover.</p>
    <a href="{url_for('business.view', _external=True)}">View your business</a>
    """
    send_email(email, subject, body)

def send_user_banned_email(email, username, reason):
    """Send ban notification email"""
    subject = "Account Banned"
    body = f"""
    <h2>Account Suspended</h2>
    <p>Your account has been banned for the following reason:</p>
    <p><strong>{reason}</strong></p>
    <p>If you believe this is a mistake, please contact support.</p>
    """
    send_email(email, subject, body)
```

### 4. Settings Model

```python
class PlatformSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.String(255))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @staticmethod
    def get(key, default=None):
        setting = PlatformSettings.query.filter_by(key=key).first()
        return setting.value if setting else default
    
    @staticmethod
    def set(key, value, description=None):
        setting = PlatformSettings.query.filter_by(key=key).first()
        if setting:
            setting.value = value
            setting.updated_at = datetime.utcnow()
        else:
            setting = PlatformSettings(key=key, value=value, description=description)
            db.session.add(setting)
        db.session.commit()
        return setting
```

---

## JavaScript Examples

### Modal Handling

```javascript
// Ban User Modal
function showBanModal(userId) {
    const modal = document.getElementById('banModal');
    const form = document.getElementById('banForm');
    form.action = `/admin/user/${userId}/ban`;
    modal.classList.remove('hidden');
}

function closeBanModal() {
    document.getElementById('banModal').classList.add('hidden');
}

// Close on outside click
document.getElementById('banModal')?.addEventListener('click', function(e) {
    if (e.target === this) closeBanModal();
});

// Close on Escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeBanModal();
        closeRejectModal();
        closeDeleteModal();
    }
});
```

### Settings Tab Switching

```javascript
function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.settings-content').forEach(el => 
        el.classList.add('hidden')
    );
    document.querySelectorAll('.settings-tab').forEach(el => 
        el.classList.remove('border-l-4', 'border-gray-800')
    );
    
    // Show selected tab
    const tab = document.getElementById(tabName);
    if (tab) {
        tab.classList.remove('hidden');
    }
    
    // Update tab styling
    event.target.closest('.settings-tab')?.classList.add(
        'border-l-4', 'border-gray-800'
    );
}

// Initialize first tab
document.addEventListener('DOMContentLoaded', () => {
    switchTab('general');
});
```

---

## Testing Examples

### Unit Test

```python
import unittest
from app import create_app
from models import User, Business, Job

class AdminTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
    
    def tearDown(self):
        self.ctx.pop()
    
    def test_ban_user(self):
        # Create test user
        user = User(username='testuser', email='test@example.com')
        db.session.add(user)
        db.session.commit()
        
        # Ban user
        response = self.client.post(f'/admin/user/{user.id}/ban',
            data={'reason': 'Test ban'}, follow_redirects=True)
        
        # Verify
        user = User.query.get(user.id)
        self.assertTrue(user.is_banned)
        self.assertEqual(user.ban_reason, 'Test ban')

    def test_approve_business(self):
        # Create test business
        owner = User(username='owner', email='owner@example.com', role='business_owner')
        business = Business(name='Test Business', owner=owner)
        db.session.add(owner)
        db.session.add(business)
        db.session.commit()
        
        # Approve business
        response = self.client.post(f'/admin/business/{business.id}/approve',
            follow_redirects=True)
        
        # Verify
        business = Business.query.get(business.id)
        self.assertTrue(business.is_approved)
```

---

**These code examples provide a solid foundation for implementing the admin management system. Adapt them to your specific database models and business logic.**
