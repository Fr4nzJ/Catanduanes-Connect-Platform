import os
from datetime import datetime
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from database import get_neo4j_db, safe_run, _node_to_dict
from tasks import send_email_task, create_notification_task
from decorators import role_required
from otp import generate_otp, save_email_otp, verify_email_otp
from forms import VerificationForm

admin_required = role_required('admin')
verification_bp = Blueprint('verification', __name__)

def allowed_file(filename):
    """Check if the file extension is allowed"""
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ============================================================================
# EMAIL VERIFICATION ROUTES (For all non-Google users)
# ============================================================================

@verification_bp.route('/verification/verify-email', methods=['GET', 'POST'])
@login_required
def verify_email():
    """Send verification code to user's email"""
    db = get_neo4j_db()
    
    with db.session() as session:
        user_data = safe_run(session, """
            MATCH (u:User {id: $user_id})
            RETURN u.google_id, u.verification_status, u.is_verified
        """, {'user_id': current_user.id})
    
    if not user_data:
        flash('User not found.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    user_info = user_data[0]
    google_id = user_info.get('u.google_id')
    verification_status = user_info.get('u.verification_status')
    is_verified = user_info.get('u.is_verified')
    
    # Google users are automatically verified, skip email verification
    if google_id:
        flash('Your email is already verified through Google.', 'info')
        return redirect(url_for('dashboard.index'))
    
    # If already approved, skip
    if verification_status == 'approved' or is_verified:
        flash('Your account is already verified.', 'info')
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        # Generate and send OTP
        code = generate_otp()
        save_email_otp(current_user.id, code)
        
        try:
            from tasks import send_email_task_wrapper
            send_email_task_wrapper(
                to=current_user.email,
                subject='Verify your Catanduanes Connect Account',
                template='email/verification_code.html',
                context={
                    'username': current_user.username,
                    'code': code,
                    'role': current_user.role
                }
            )
            
            flash('Verification code sent to your email. Please check your inbox.', 'success')
            return redirect(url_for('verification.verify_email_code'))
        except Exception as e:
            current_app.logger.error(f"Failed to send verification email: {str(e)}")
            flash('Failed to send verification code. Please try again.', 'danger')
            return redirect(request.url)
    
    return render_template('verification/verify_email.html')

@verification_bp.route('/verification/verify-code', methods=['GET', 'POST'])
@login_required
def verify_email_code():
    """Verify email code entered by user"""
    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        
        if not code or len(code) != 6 or not code.isdigit():
            flash('Please enter a valid 6-digit verification code.', 'danger')
            return render_template('verification/verify_code.html')
        
        # Verify the OTP
        if verify_email_otp(current_user.id, code):
            # Update user verification status
            db = get_neo4j_db()
            with db.session() as session:
                safe_run(session, """
                    MATCH (u:User {id: $user_id})
                    SET u.verification_status = 'approved',
                        u.is_verified = true
                """, {'user_id': current_user.id})
            
            flash('Email verified successfully! Your account is now active.', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash('Invalid or expired verification code. Please try again.', 'danger')
            return render_template('verification/verify_code.html')
    
    return render_template('verification/verify_code.html')

@verification_bp.route('/verification/resend-code', methods=['POST'])
@login_required
def resend_verification_code():
    """Resend verification code to email"""
    code = generate_otp()
    save_email_otp(current_user.id, code)
    
    try:
        from tasks import send_email_task_wrapper
        send_email_task_wrapper(
            to=current_user.email,
            subject='Your Catanduanes Connect Verification Code',
            template='email/verification_code.html',
            context={
                'username': current_user.username,
                'code': code,
                'role': current_user.role
            }
        )
        flash('Verification code resent to your email.', 'success')
        return redirect(url_for('verification.verify_email_code'))
    except Exception as e:
        current_app.logger.error(f"Failed to resend verification email: {str(e)}")
        flash('Failed to resend verification code. Please try again.', 'danger')
        return redirect(request.url)

# ============================================================================
# BUSINESS OWNER DOCUMENT UPLOAD ROUTES
# ============================================================================

@verification_bp.route('/verification/upload', methods=['GET', 'POST'])
@login_required
@role_required('business_owner')
def upload_verification():
    # Check verification status from database
    db = get_neo4j_db()
    with db.session() as session:
        user_data = safe_run(session, """
            MATCH (u:User {id: $user_id})
            RETURN u.verification_status as status
        """, {'user_id': current_user.id})
    
    user_info = user_data[0] if user_data else {}
    verification_status = user_info.get('status', 'pending')
    
    # Only block if already approved
    if verification_status == 'approved':
        flash('Your account is already verified.', 'info')
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        form = VerificationForm()
        
        # Validate form
        if not form.validate_on_submit():
            flash('Form validation failed. Please check all required fields.', 'danger')
            return render_template('verification_upload.html', form=form)

        # Collect files from form
        files_to_upload = []
        file_fields = [
            ('id_document', 'ID Document'),
            ('business_permit', 'Business Permit'),
            ('dti_registration', 'DTI Registration'),
            ('resume', 'Resume'),
            ('certifications', 'Certifications'),
            ('address_proof', 'Address Proof'),
        ]
        
        for field_name, doc_type in file_fields:
            file_field = getattr(form, field_name, None)
            if file_field and file_field.data:
                files_to_upload.append((file_field.data, doc_type))

        if not files_to_upload:
            flash('No valid documents were uploaded. Please select at least one document.', 'danger')
            return render_template('verification_upload.html', form=form)

        db = get_neo4j_db()
        with db.session() as session:
            # Check current verification status
            current_status = safe_run(session, """
                MATCH (u:User {id: $user_id})
                RETURN u.verification_status as status
            """, {'user_id': current_user.id})
            
            current_status = current_status[0].get('status', 'pending') if current_status else 'pending'
            
            # Check if user already has a pending verification
            existing = safe_run(session, """
                MATCH (u:User {id: $user_id})-[:SUBMITTED]->(v:Verification)
                WHERE v.status = 'pending'
                RETURN v
            """, {'user_id': current_user.id})

            if existing:
                flash('You already have a pending verification request.', 'warning')
                return redirect(url_for('verification.status'))
            
            # Allow resubmission if previously rejected
            if current_status == 'rejected':
                # Delete old rejected verification records to allow new submission
                safe_run(session, """
                    MATCH (u:User {id: $user_id})-[:SUBMITTED]->(v:Verification)
                    WHERE v.status = 'rejected'
                    DETACH DELETE v
                """, {'user_id': current_user.id})

            # Create verification record
            verification_id = str(uuid.uuid4())
            query = """
                MATCH (u:User {id: $user_id})
                CREATE (v:Verification {
                    id: $v_id,
                    status: 'pending',
                    created_at: datetime(),
                    user_type: $user_type
                })
                CREATE (u)-[:SUBMITTED]->(v)
                RETURN v
            """
            result = safe_run(session, query, {
                'user_id': current_user.id,
                'v_id': verification_id,
                'user_type': request.form.get('user_type', 'user')
            })

            if not result:
                flash('Error creating verification request.', 'danger')
                return redirect(request.url)

            # Save uploaded files
            saved_files = []
            upload_path = os.path.join(
                current_app.root_path, 
                'static', 
                'uploads', 
                'verification', 
                str(current_user.id),
                verification_id
            )
            os.makedirs(upload_path, exist_ok=True)

            for file, doc_type in files_to_upload:
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_id = str(uuid.uuid4())
                    file_ext = os.path.splitext(filename)[1]
                    new_filename = f"{file_id}{file_ext}"
                    file.save(os.path.join(upload_path, new_filename))
                    
                    # Create document record
                    doc_query = """
                        MATCH (v:Verification {id: $v_id})
                        CREATE (d:Document {
                            id: $doc_id,
                            filename: $filename,
                            document_type: $doc_type,
                            uploaded_at: datetime()
                        })
                        CREATE (v)-[:HAS_DOCUMENT]->(d)
                    """
                    safe_run(session, doc_query, {
                        'v_id': verification_id,
                        'doc_id': file_id,
                        'filename': new_filename,
                        'doc_type': doc_type
                    })
                    saved_files.append(new_filename)

            if not saved_files:
                # If no files were saved, delete the verification record
                safe_run(session, """
                    MATCH (v:Verification {id: $v_id})
                    DETACH DELETE v
                """, {'v_id': verification_id})
                flash('No valid documents were uploaded.', 'danger')
                return redirect(request.url)

            flash('Documents uploaded successfully. Your verification is pending review.', 'success')
            return redirect(url_for('verification.status'))

    # GET request - show upload form
    form = VerificationForm()
    return render_template('verification_upload.html', form=form)

@verification_bp.route('/verification/status')
@login_required
def status():
    """Show verification status to user"""
    db = get_neo4j_db()
    with db.session() as session:
        # Get latest verification request
        result = safe_run(session, """
            MATCH (u:User {id: $user_id})-[:SUBMITTED]->(v:Verification)
            RETURN v
            ORDER BY v.created_at DESC
            LIMIT 1
        """, {'user_id': current_user.id})

        verification = _node_to_dict(result[0]['v']) if result else None

    return render_template('verification/status.html', 
                         verification=verification,
                         is_verified=current_user.is_verified)

@verification_bp.route('/verification/document/<doc_id>')
@login_required
def view_document(doc_id):
    """View a verification document. Only accessible by document owner or admins."""
    db = get_neo4j_db()
    
    with db.session() as session:
        # Get document info and check permissions
        result = safe_run(session, """
            MATCH (d:Document {id: $doc_id})<-[:HAS_DOCUMENT]-(v:Verification)<-[:SUBMITTED]-(u:User)
            RETURN d, u.id as user_id
        """, {'doc_id': doc_id})
        
        if not result:
            flash('Document not found.', 'error')
            return redirect(url_for('verification.status'))
            
        doc = _node_to_dict(result[0]['d'])
        user_id = result[0]['user_id']
        
        # Check permissions
        if not current_user.is_admin and current_user.id != user_id:
            flash('You do not have permission to view this document.', 'error')
            return redirect(url_for('verification.status'))
            
        # Get file path
        file_path = os.path.join(
            current_app.root_path,
            'static',
            'uploads',
            'verification',
            str(user_id),
            doc['verification_id'],
            doc['filename']
        )
        
        if not os.path.exists(file_path):
            flash('Document file not found.', 'error')
            return redirect(url_for('verification.status'))
            
        # Send file with proper content type
        directory = os.path.dirname(file_path)
        filename = os.path.basename(file_path)
        return send_from_directory(directory, filename)

@verification_bp.route('/verification/<verification_id>/review', methods=['POST'])
@login_required
@admin_required
def review_verification(verification_id):
    """Admin route to review a verification request"""
    action = request.form.get('action')
    reviewer_notes = request.form.get('reviewer_notes', '').strip()
    
    if action not in ['approve', 'reject']:
        flash('Invalid action.', 'error')
        return redirect(url_for('admin.verification_review'))
        
    if action == 'reject' and not reviewer_notes:
        flash('Rejection reason is required.', 'error')
        return redirect(url_for('admin.verification_review'))
        
    db = get_neo4j_db()
    
    with db.session() as session:
        # Update verification status
        update_query = """
            MATCH (v:Verification {id: $verification_id})
            MATCH (u:User)-[:SUBMITTED]->(v)
            SET v.status = $status,
                v.reviewed_at = datetime(),
                v.reviewed_by = $reviewer_id,
                v.reviewer_notes = $notes
        """
        
        if action == 'approve':
            # Also mark the user as verified
            update_query += """
                SET u.is_verified = true,
                    u.verified_at = datetime()
            """
            
        params = {
            'verification_id': verification_id,
            'status': 'verified' if action == 'approve' else 'rejected',
            'reviewer_id': current_user.id,
            'notes': reviewer_notes or None
        }
        
        result = safe_run(session, update_query, params)
        
        if not result:
            flash('Verification not found.', 'error')
            return redirect(url_for('admin.verification_review'))
            
        # Get user info for notification
        user_query = """
            MATCH (u:User)-[:SUBMITTED]->(v:Verification {id: $verification_id})
            RETURN u.id as user_id, u.email as email, u.first_name as first_name
        """
        user_result = safe_run(session, user_query, {'verification_id': verification_id})
        
        if user_result:
            user_info = user_result[0]
            
            # Send notification
            notification_data = {
                'title': 'Verification Update',
                'body': 'Your verification has been approved!' if action == 'approve' else f'Your verification was rejected. Reason: {reviewer_notes}',
                'type': 'verification_update',
                'user_id': user_info['user_id'],
                'link': url_for('verification.status', _external=True)
            }
            create_notification_task(**notification_data)
            
            # Send email
            email_data = {
                'to_email': user_info['email'],
                'subject': 'Verification Status Update - Catanduanes Connect',
                'template': 'verification_update',
                'data': {
                    'first_name': user_info['first_name'],
                    'status': 'approved' if action == 'approve' else 'rejected',
                    'reason': reviewer_notes if action == 'reject' else None,
                    'status_url': url_for('verification.status', _external=True)
                }
            }
            send_email_task.delay(**email_data)
            
        flash(f'Verification has been {"approved" if action == "approve" else "rejected"}.', 'success')
        return redirect(url_for('admin.verification_review'))
