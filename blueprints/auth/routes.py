import uuid
import logging
from datetime import datetime, timedelta
from flask import render_template, request, redirect, url_for, flash, jsonify, current_app, session as flask_session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import bcrypt
import requests
from otp import generate_otp, save_email_otp, verify_email_otp
from otp import save_otp, verify_otp as validate_otp_code, send_sms
from . import auth_bp
from database import get_neo4j_db, safe_run, _node_to_dict
from models import User
from decorators import verified_required, json_response
from tasks import send_email_task
from forms import LoginForm, RegistrationForm, PasswordResetForm
from flask import session
from database import get_neo4j_db

logger = logging.getLogger(__name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.lower()
        password = form.password.data
        remember = form.remember.data
        
        logger.info(f"Login attempt for email: {email}")
        
        db = get_neo4j_db()
        with db.session() as session:
            result = safe_run(session, """
                MATCH (u:User)
                WHERE u.email = $email
                RETURN u.id            AS id,
                    u.email         AS email,
                    u.username      AS username,
                    u.password_hash AS password_hash,
                    u.role          AS role,
                    u.is_verified   AS is_verified,
                    u.is_active     AS is_active,
                    u.created_at    AS created_at
                LIMIT 1
            """, {'email': email})
            
            if not result:
                logger.warning(f"No user found with email: {email}")
                flash('Invalid email or password.', 'error')
                return render_template('auth/login.html', form=form)
            
            user_data = result[0]          # result[0] is already a dict
            stored_password = user_data['password_hash']
            
            if not stored_password:
                logger.error(f"User {email} has no password hash")
                flash('Account error. Please contact support.', 'error')
                return render_template('auth/login.html', form=form)
            
            logger.debug(f"Checking password for {email}")
            try:
                password_matches = bcrypt.checkpw(
                    password.encode('utf-8'),
                    stored_password.encode('utf-8')
                )
            except Exception as e:
                logger.error(f"Password check error for {email}: {e}")
                flash('Login error. Please try again.', 'error')
                return render_template('auth/login.html', form=form)
            
            if not password_matches:
                logger.warning(f"Password mismatch for {email}")
                flash('Invalid email or password.', 'error')
                return render_template('auth/login.html', form=form)
            
            # Password matched - check account status
            if not user_data.get('is_active', True):
                logger.info(f"Inactive account login attempt: {email}")
                flash('Your account has been deactivated. Please contact support.', 'error')
                return render_template('auth/login.html', form=form)
            
            user = User(**user_data)
            
            if login_user(user, remember=remember):
                # Set user data in session and make it permanent
                flask_session['user_id'] = user.id
                flask_session['user_role'] = user.role
                flask_session.permanent = True
                
                # Log user info for debugging
                logger.info(f"Login successful - User ID: {user.id}, Role: {user.role}, Username: {user.username}")
                logger.info(f"Session data: user_id={flask_session.get('user_id')}, role={flask_session.get('user_role')}")
                logger.info(f"current_user authenticated: {current_user.is_authenticated}, role: {current_user.role}")
                
                flash('You have been logged in successfully.', 'success')
                logger.info(f"Successful login for {email}")
                
                # Update last login
                safe_run(session, """
                    MATCH (u:User {id: $user_id})
                    SET u.last_login = $now
                """, {'user_id': user.id, 'now': datetime.utcnow().isoformat()})
                
                # Get the next page from args, verify it's a safe URL
                next_page = request.args.get('next')
                if next_page and next_page.startswith('/'):
                    return redirect(next_page)
                
                # Redirect based on role
                if user.role == 'admin':
                    return redirect(url_for('admin.index'))
                return redirect(url_for('dashboard.index'))
            else:
                flash('Login failed. Please try again.', 'error')
        
        flash('Invalid email or password.', 'error')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        email_or_phone = form.email_or_phone.data.strip()
        # Check if it's a Philippine phone number (09XX or +639XX)
        is_phone = email_or_phone.startswith('09') or email_or_phone.startswith('+639')
        
        if is_phone:
            # Convert to E.164 format for Twilio (+639XXXXXXXXX)
            phone = email_or_phone
            if phone.startswith('09'):
                phone = '+63' + phone[1:]  # Convert 09XX to +639XX
            email = None
        else:
            email = email_or_phone.lower()
            phone = None
            
        username = form.username.data
        password = form.password.data
        role = form.role.data

        db = get_neo4j_db()
        with db.session() as session:
            # Check if user exists
            existing = safe_run(session,
                "MATCH (u:User {email:$e}) RETURN 1" if email else
                "MATCH (u:User {phone:$p}) RETURN 1",
                {'e': email} if email else {'p': phone})

            if existing:
                flash('That email/phone is already registered.', 'error')
                return render_template('auth/signup.html', form=form)

            # Create user
            user_id = str(uuid.uuid4())
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode()

            safe_run(session, """
                CREATE (u:User {
                    id: $user_id,
                    email: $email,
                    phone: $phone,
                    username: $username,
                    password_hash: $password_hash,
                    role: $role,
                    is_verified: false,
                    is_active: true,
                    created_at: $created_at
                })
            """, {
                'user_id': user_id,
                'email': email,
                'phone': phone,
                'username': username,
                'password_hash': password_hash,
                'role': role,
                'created_at': datetime.utcnow().isoformat()
            })

            # ---  NEW OTP FLOW  ---
            code = generate_otp()
            save_otp(user_id, code, is_phone=is_phone)
            try:
                if is_phone:
                    current_app.logger.info(f"Sending SMS verification code to {phone}")
                    send_sms(phone, code)
                    current_app.logger.info(f"SMS verification code sent successfully to {phone}")
                    flash('A 6-digit code was sent to your phone.', 'info')
                else:
                    # Send verification email
                    current_app.logger.info(f"Sending verification code to {email}")
                    success = send_email_task(
                        to=email,
                        subject='Your Catanduanes Connect verification code',
                        template='email/verify_code.html',
                        context={'username': username, 'code': code}
                    )
                    if success:
                        current_app.logger.info(f"Verification code sent successfully to {email}")
                        flash('A 6-digit code was sent to your email.', 'info')
                    else:
                        current_app.logger.error(f"Failed to send verification code to {email}")
                        flash('There was an issue sending the verification code. Please try again or contact support.', 'error')
            except Exception as e:
                current_app.logger.error(f"Error sending verification code: {str(e)}")
                if is_phone:
                    flash('Failed to send SMS verification code. Please try again.', 'error')
                else:
                    flash('Failed to send email verification code. Please try again.', 'error')

            # log the user in immediately
            login_user(User(id=user_id, email=email, phone=phone,
                            username=username, role=role,
                            is_verified=False, is_active=True))

            # ➜  REDIRECT ONLY AFTER SUCCESSFUL SUBMISSION
            return redirect(url_for('auth.verify_otp'))

    # GET (or invalid POST) – show the form
    return render_template('auth/signup.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('dashboard.index'))

@auth_bp.route('/verify/<token>')
def verify_email(token):
    """Email verification"""
    db = get_neo4j_db()
    with db.session() as session:
        result = safe_run(session, """
            MATCH (u:User {verification_token: $token})
            RETURN u
        """, {'token': token})
        
        if result:
            user_data = _node_to_dict(result[0]['u'])
            safe_run(session, """
                MATCH (u:User {id: $user_id})
                SET u.is_verified = true
                REMOVE u.verification_token
            """, {'user_id': user_data['id']})
            
            flash('Email verified successfully! You can now log in.', 'success')
        else:
            flash('Invalid or expired verification token.', 'error')
    
    return redirect(url_for('auth.login'))

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Password reset request"""
    form = PasswordResetForm()
    if form.validate_on_submit():
        email = form.email.data.lower()
        
        db = get_neo4j_db()
        with db.session() as session:
            result = safe_run(session, """
            MATCH (u:User)
            WHERE toLower(u.email) = toLower($email)
            RETURN u
        """, {'email': email})

            
            # Send reset instructions regardless of whether email exists
            # This prevents email enumeration
            flash('If an account exists with that email, you will receive password reset instructions.', 'info')
            if result:
                # Generate reset token
                reset_token = str(uuid.uuid4())
                reset_expires = (datetime.utcnow() + timedelta(hours=1)).isoformat()
                
                safe_run(session, """
                    MATCH (u:User {email: $email})
                    SET u.reset_token = $token,
                        u.reset_expires = $expires
                """, {
                    'email': email,
                    'token': reset_token,
                    'expires': reset_expires
                })
                
                # Send reset email
                reset_url = url_for('auth.reset_password_confirm', token=reset_token, _external=True)
                send_email_task(
                    to=email,
                    subject='Password Reset Request',
                    template='email/reset.html',
                    context={
                        'reset_url': reset_url,
                        'site_name': current_app.config['SITE_NAME']
                    }
                )
            
            flash('If an account exists with this email, you will receive password reset instructions.', 'info')
            return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', form=form)

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password_confirm(token):
    """Password reset confirmation"""
    db = get_neo4j_db()
    with db.session() as session:
        result = safe_run(session, """
            MATCH (u:User {reset_token: $token})
            WHERE u.reset_expires > $now
            RETURN u
        """, {'token': token, 'now': datetime.utcnow().isoformat()})
        
        if not result:
            flash('Invalid or expired reset token.', 'error')
            return redirect(url_for('auth.login'))
        
        if request.method == 'POST':
            password = request.form.get('password')
            confirm = request.form.get('confirm')
            
            if password != confirm:
                flash('Passwords do not match.', 'error')
                return render_template('auth/reset_password_confirm.html', token=token)
            
            if len(password) < 8:
                flash('Password must be at least 8 characters long.', 'error')
                return render_template('auth/reset_password_confirm.html', token=token)
            
            # Hash new password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            user_data = _node_to_dict(result[0]['u'])
            
            safe_run(session, """
                MATCH (u:User {id: $user_id})
                SET u.password_hash = $password_hash
                REMOVE u.reset_token, u.reset_expires
            """, {
                'user_id': user_data['id'],
                'password_hash': password_hash
            })
            
            flash('Password reset successful! You can now log in with your new password.', 'success')
            return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password_confirm.html', token=token)

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change password page and handler for logged-in user"""
    if request.method == 'GET':
        return render_template('auth/change_password.html')
    
    # POST method handling
    """Change password for logged-in user"""
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if new_password != confirm_password:
        flash('New passwords do not match', 'error')
        return 'New passwords do not match', 400
    
    if len(new_password) < 8:
        flash('Password must be at least 8 characters long', 'error')
        return 'Password must be at least 8 characters long', 400
    
    db = get_neo4j_db()
    with db.session() as session:
        # Verify current password
        result = safe_run(session, """
            MATCH (u:User {id: $user_id})
            RETURN u.password_hash
        """, {'user_id': current_user.id})
        
        if result:
            stored_password = result[0]['u.password_hash']
            if not bcrypt.checkpw(current_password.encode('utf-8'), stored_password.encode('utf-8')):
                flash('Current password is incorrect', 'error')
                return 'Current password is incorrect', 400
        
        # Update password
        password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        safe_run(session, """
            MATCH (u:User {id: $user_id})
            SET u.password_hash = $password_hash
        """, {
            'user_id': current_user.id,
            'password_hash': password_hash
        })
    
    return jsonify({'message': 'Password changed successfully'}), 200

@auth_bp.route('/resend-verification', methods=['POST'])
def resend_verification():
    """Resend email verification"""
    email = request.form.get('email')
    
    db = get_neo4j_db()
    with db.session() as session:
        result = safe_run(session, """
            MATCH (u:User)
            WHERE toLower(u.email) = toLower($email)
            RETURN u
        """, {'email': email})

        
        if result:
            user_data = _node_to_dict(result[0]['u'])
            verification_token = user_data.get('verification_token') or str(uuid.uuid4())
            
            # Update verification token
            safe_run(session, """
                MATCH (u:User {email: $email})
                SET u.verification_token = $token
            """, {'email': email, 'token': verification_token})
            
            # Send verification email
            verification_url = url_for('auth.verify_email', token=verification_token, _external=True)
            send_email_task.delay(
                to=email,
                subject='Email Verification - Catanduanes Connect',
                template='email/verify.html',
                context={
                    'username': user_data.get('username'),
                    'verification_url': verification_url,
                    'site_name': current_app.config['SITE_NAME']
                }
            )
    
    flash('If your email exists and is not verified, you will receive a new verification email.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/login/google')
def google_login():
    """Handle Google OAuth login redirect"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    try:
        # Clear any existing OAuth state
        flask_session.pop('google_state', None)

        # Load OAuth config from app settings
        client_id = current_app.config.get('GOOGLE_CLIENT_ID')
        client_secret = current_app.config.get('GOOGLE_CLIENT_SECRET')
        redirect_uri = current_app.config.get('GOOGLE_REDIRECT_URI')

        current_app.logger.info("OAuth Configuration Check:")
        current_app.logger.info(f"- Client ID configured: {bool(client_id)}")
        current_app.logger.info(f"- Client Secret configured: {bool(client_secret)}")
        current_app.logger.info(f"- Redirect URI: {redirect_uri}")

        # Validate config
        if not client_id or not client_secret or not redirect_uri:
            current_app.logger.error('Google OAuth credentials not configured.')
            flash('Google OAuth is not configured on the server.', 'danger')
            return redirect(url_for('auth.login'))

        # Import OAuth helper safely
        from references.oauth import get_google_auth_flow_from_config

        # Initialize OAuth flow
        flow = get_google_auth_flow_from_config(client_id, client_secret, redirect_uri)
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )

        # Store state in session
        session['google_state'] = state
        current_app.logger.info("Generated new OAuth state and stored in session")

        base_auth_url = authorization_url.split('?')[0]
        current_app.logger.info(f"Redirecting to Google OAuth: {base_auth_url}")

        # Redirect to Google consent screen
        return redirect(authorization_url)

    except Exception as e:
        current_app.logger.error(f"Error in Google login: {str(e)}", exc_info=True)
        flash("An error occurred during Google login. Please try again.", "danger")
        return redirect(url_for('auth.login'))

@auth_bp.route('/callback/google')
def google_callback():
    """Handle Google OAuth callback."""
    # Redirect authenticated users
    if current_user.is_authenticated:
        if getattr(current_user, 'role', None) == 'admin':
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('dashboard.index'))

    # Check state integrity
    stored_state = session.get("google_state")
    received_state = request.args.get("state")

    current_app.logger.info(
        f"OAuth state check: stored_exists={bool(stored_state)}, "
        f"received_exists={bool(received_state)}"
    )

    if not stored_state:
        current_app.logger.error("No state found in session")
        flash("Session expired. Please try signing in again.", "danger")
        return redirect(url_for("auth.login"))

    if not received_state:
        current_app.logger.error("No state parameter in callback URL")
        flash("No state parameter received. Please try signing in again.", "danger")
        return redirect(url_for("auth.login"))

    if stored_state != received_state:
        current_app.logger.error("State mismatch in OAuth callback")
        flash("Invalid state parameter. Please try signing in again.", "danger")
        return redirect(url_for("auth.login"))

    try:
        # Get OAuth configuration
        client_id = current_app.config.get('GOOGLE_CLIENT_ID')
        client_secret = current_app.config.get('GOOGLE_CLIENT_SECRET')
        redirect_uri = current_app.config.get('GOOGLE_REDIRECT_URI')

        if not client_id or not client_secret:
            current_app.logger.error(
                'Google OAuth credentials not configured on callback.'
            )
            flash(
                'Google OAuth is not configured on the server. '
                'Please contact the administrator.',
                'danger'
            )
            return redirect(url_for('auth.login'))

        # Import safely
        from references.oauth import (
            get_google_auth_flow_from_config,
            get_google_user_info
        )

        # Initialize OAuth flow
        flow = get_google_auth_flow_from_config(client_id, client_secret, redirect_uri)
        flow.state = session.get('google_state')

        # Handle HTTPS proxies (for reverse-proxy setups)
        authorization_response = request.url
        xf_proto = (
            request.headers.get('X-Forwarded-Proto')
            or request.environ.get('HTTP_X_FORWARDED_PROTO')
        )
        if (
            request.scheme != 'https'
            and xf_proto
            and xf_proto.lower() == 'https'
            and not current_app.debug
        ):
            authorization_response = authorization_response.replace('http://', 'https://', 1)
            current_app.logger.info(
                'Overriding authorization_response to https based on X-Forwarded-Proto'
            )

        # Validate code
        if request.args.get('error'):
            error_msg = request.args.get('error_description', request.args.get('error'))
            current_app.logger.error(f"Google OAuth error: {error_msg}")
            flash(f"Authentication error: {error_msg}", "danger")
            return redirect(url_for("auth.login"))

        code = request.args.get('code')
        if not code:
            current_app.logger.error("No authorization code in callback")
            flash("Authorization code missing. Please try again.", "danger")
            return redirect(url_for("auth.login"))

        # Fetch token
        flow.redirect_uri = redirect_uri
        current_app.logger.info("Fetching OAuth tokens from Google...")
        flow.fetch_token(code=code, authorization_response=authorization_response)
        credentials = flow.credentials

        # Extract user info
        user_info = None
        access_token = getattr(credentials, 'token', None)
        if access_token:
            try:
                user_info = get_google_user_info(access_token, logger=current_app.logger)
            except Exception:
                current_app.logger.exception('Error fetching Google user info via access token')

        if not user_info and getattr(credentials, 'id_token', None):
            from google.oauth2 import id_token
            from google.auth.transport import requests as google_requests

            id_info = id_token.verify_oauth2_token(
                credentials.id_token,
                google_requests.Request(),
                client_id
            )
            user_info = {
                'email': id_info.get('email'),
                'given_name': id_info.get('given_name'),
                'family_name': id_info.get('family_name'),
                'picture': id_info.get('picture')
            }

        if not user_info:
            current_app.logger.error('Failed to obtain user profile from Google.')
            flash('Unable to retrieve Google profile. Please try again.', 'danger')
            return redirect(url_for('auth.login'))

        # Extract profile fields
        email = user_info.get('email')
        given_name = user_info.get('given_name')
        family_name = user_info.get('family_name')
        picture = user_info.get('picture')
        google_id = user_info.get('google_id')

        if not email:
            raise ValueError('Missing email in Google response')

        # Handle user creation / login
        from models import User
        user = None

        if google_id:
            user = User.get_by_google_id(google_id)
            @classmethod
            def get_by_google_id(cls, google_id):
                from database import get_neo4j_db, safe_run, _node_to_dict
                db = get_neo4j_db()
                with db.session() as session:
                    result = safe_run(session, """
                        MATCH (u:User)
                        WHERE u.google_id = $google_id
                        RETURN u
                    """, {'google_id': str(google_id)})
                    if result:
                        user_data = _node_to_dict(result[0]['u'])
                        return cls(**user_data)
                return None
        if not user:
            user = User.get_by_email(email)

        if user:
            # Update user info if needed
            if google_id and not getattr(user, 'google_id', None):
                user.google_id = google_id
            if picture and not getattr(user, 'profile_picture', None):
                user.profile_picture = picture
            # update the node in DB instead of user.save()
            
            google_id_str = str(google_id) if google_id else None

            db = get_neo4j_db()
            with db.session() as neo_session:
                safe_run(neo_session, """
                    MATCH (u:User {id: $user_id})
                    SET u.google_id  = $google_id,
                        u.profile_picture = $picture
                """, {
                    'user_id': user.id,
                    'google_id': google_id_str,   # ← string
                    'picture': picture
                })

            login_user(user)
            flash('Successfully logged in with Google!', 'success')
            return redirect(url_for('dashboard.index'))

        # If user doesn’t exist, save info to session and ask for registration
        session['google_user'] = {
            'email': email,
            'given_name': given_name,
            'family_name': family_name,
            'picture': picture,
            'google_id': google_id
        }
        return redirect(url_for('auth.complete_registration'))

    except Exception as e:
        import traceback
        current_app.logger.error(
            f"Google callback error: {str(e)}\n{traceback.format_exc()}"
        )
        flash('Failed to log in with Google.', 'danger')
        return redirect(url_for('auth.login'))
    
    
@auth_bp.route('/complete-registration', methods=['GET', 'POST'])
def complete_registration():
    """Complete registration for Google users who don’t have a local account yet."""
    google_user = session.get('google_user')
    if not google_user:
        flash('No Google account data found. Please sign in again.', 'danger')
        return redirect(url_for('auth.login'))

    # If user is already logged in, just go to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))


    form = RegistrationForm()
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        role = request.form.get('role', 'job_seeker')

        if not username:
            flash('Username is required.', 'danger')
            return render_template('auth/complete_registration.html', google_user=google_user, form=form)

        # Optional: check username uniqueness in DB (prevent duplicates)
        db = get_neo4j_db()
        with db.session() as session_db:
            existing = safe_run(session_db, """
                MATCH (u:User {username: $username})
                RETURN u
            """, {'username': username})
            if existing:
                flash('Username already taken. Please choose another.', 'danger')
                return render_template('auth/complete_registration.html', google_user=google_user, form=form)

            # Create user in Neo4j
            user_id = str(uuid.uuid4())
            safe_run(session_db, """
                CREATE (u:User {
                    id: $id,
                    email: $email,
                    username: $username,
                    role: $role,
                    google_id: $google_id,
                    profile_picture: $picture,
                    is_verified: false,
                    verification_status: 'pending',
                    is_active: true,
                    created_at: $created_at
                })
            """, {
                'id': user_id,
                'email': google_user['email'],
                'username': username,
                'role': role,
                'google_id': google_user.get('google_id'),
                'picture': google_user.get('picture'),
                'created_at': datetime.utcnow().isoformat()
            })

        # Create a minimal User object and log the user in
        user = User(id=user_id,
                    email=google_user['email'],
                    username=username,
                    role=role,
                    profile_picture=google_user.get('picture'),
                    is_verified=False,
                    is_active=True)
        login_user(user)

        # Clean up session and redirect
        flask_session.pop('google_state', None)
        flash('Registration completed! Welcome!', 'success')
        return redirect(url_for('dashboard.index'))

    # Render registration form prefilled with Google info (GET or after POST fallthrough)
    return render_template('auth/complete_registration.html', google_user=google_user, form=form)
@auth_bp.route('/profile')
@login_required
def profile():
    """Show logged-in user’s profile"""
    return render_template('auth/profile.html')

@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    from flask_wtf import FlaskForm
    
    class OTPForm(FlaskForm):
        pass
    
    form = OTPForm()
    
    if request.method == 'GET':
        return render_template('auth/verify_otp.html', form=form)
        
    if not form.validate_on_submit():
        flash('Invalid request. Please try again.', 'error')
        return redirect(url_for('auth.verify_otp'))
        
    code = request.form.get('otp', '').strip()
    if not code.isdigit() or len(code) != 6:
        flash('Enter the 6-digit code.', 'error')
        return redirect(url_for('auth.verify_otp'))
        
    is_phone = bool(current_user.phone)
    # Using renamed function to avoid naming conflict with the route
    if validate_otp_code(str(current_user.id), code, is_phone):
        # Set verification_status to 'pending' (OTP just confirmed contact info)
        db = get_neo4j_db()
        with db.session() as session:
            safe_run(session, """
                MATCH (u:User {id: $user_id})
                SET u.verification_status = 'pending'
            """, {'user_id': current_user.id})
        
        flash('OTP verified successfully! Now proceed to email verification.', 'success')
        return redirect(url_for('verification.verify_email'))
    else:
        flash('Invalid or expired code.', 'error')
        return redirect(url_for('auth.verify_otp'))


@auth_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    """Resend OTP code to user's email or phone"""
    from flask_wtf import FlaskForm
    
    class ResendForm(FlaskForm):
        pass
    
    form = ResendForm()
    
    if not form.validate_on_submit():
        flash('Invalid request. Please try again.', 'error')
        return redirect(url_for('auth.verify_otp'))
        
    is_phone = bool(current_user.phone)
    code = generate_otp()
    save_otp(current_user.id, code, is_phone=is_phone)
    
    try:
        if is_phone:
            current_app.logger.info(f"Resending SMS verification code to {current_user.phone}")
            send_sms(current_user.phone, code)
            current_app.logger.info(f"SMS verification code resent successfully to {current_user.phone}")
            flash('A new code has been sent to your phone.', 'info')
        else:
            current_app.logger.info(f"Resending email verification code to {current_user.email}")
            success = send_email_task(
                to=current_user.email,
                subject='Your new verification code',
                template='email/verify_code.html',
                context={'username': current_user.username, 'code': code}
            )
            if success:
                current_app.logger.info(f"Email verification code resent successfully to {current_user.email}")
                flash('A new code has been sent to your email.', 'info')
            else:
                raise Exception("Failed to send email verification code")
    except Exception as e:
        current_app.logger.error(f"Failed to send OTP: {str(e)}")
        if is_phone:
            flash('Failed to send SMS code. Please try again.', 'error')
        else:
            flash('Failed to send email code. Please try again.', 'error')
        
    return redirect(url_for('auth.verify_otp'))