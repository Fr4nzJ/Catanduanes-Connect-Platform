"""Unit tests for authentication"""

import pytest
import uuid
from datetime import datetime, timedelta
import bcrypt
from flask import url_for
from unittest.mock import patch, MagicMock
from database import safe_run
import sys
from pathlib import Path
# Add the tests directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))
from conftest import get_csrf_token


class TestAuthRoutes:
    """Test authentication routes"""
    
    def test_login_page_loads(self, client):
        """Test that login page loads successfully"""
        response = client.get('/auth/login')
        assert response.status_code == 200
        assert b'Login' in response.data
    
    def test_signup_page_loads(self, client):
        """Test that signup page loads successfully"""
        response = client.get('/auth/signup')
        assert response.status_code == 200
        assert b'Sign Up' in response.data
    
    def test_login_with_valid_credentials(self, client, neo4j_db):
        """Test login with valid credentials"""
        password = 'Password123!'
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        user_id = str(uuid.uuid4())

        # Create user in database BEFORE GET request
        with neo4j_db.session() as session:
            safe_run(session, """
                CREATE (u:User {
                    id: $user_id,
                    email: 'test@example.com',
                    username: 'testuser',
                    password_hash: $password_hash,
                    role: 'job_seeker',
                    is_verified: true,
                    is_active: true,
                    created_at: $created_at
                })
            """, {
                'user_id': user_id,
                'password_hash': password_hash,
                'created_at': datetime.utcnow().isoformat()
            })

        # Use persistent client context for CSRF/session
        with client:
            login_page = client.get('/auth/login')
            assert login_page.status_code == 200
            csrf_token = get_csrf_token(login_page.data)
            form_data = {
                'email': 'test@example.com',
                'password': password,
                'csrf_token': csrf_token,
                'remember': False
            }
            response = client.post('/auth/login',
                                 data=form_data,
                                 follow_redirects=True,
                                 headers={'Referer': 'http://localhost/auth/login'})
            assert response.status_code == 200
            assert b'You have been logged in successfully' in response.data

        # Clean up
        with neo4j_db.session() as session:
            safe_run(session, """
                MATCH (u:User {id: $user_id})
                DELETE u
            """, {'user_id': user_id})
        def test_login_with_valid_credentials(self, client, neo4j_db):
            """Test login with valid credentials"""
            password = 'Password123!'
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
            user_id = str(uuid.uuid4())

            # Create user in database
            with neo4j_db.session() as session:
                safe_run(session, """
                    CREATE (u:User {
                        id: $user_id,
                        email: 'test@example.com',
                        username: 'testuser',
                        password_hash: $password_hash,
                        role: 'job_seeker',
                        is_verified: true,
                        is_active: true,
                        created_at: $created_at
                    })
                """, {
                    'user_id': user_id,
                    'password_hash': password_hash,
                    'created_at': datetime.utcnow().isoformat()
                })

            # Use persistent client context for CSRF/session
            with client:
                login_page = client.get('/auth/login')
                assert login_page.status_code == 200
                csrf_token = get_csrf_token(login_page.data)
                form_data = {
                    'email': 'test@example.com',
                    'password': password,
                    'csrf_token': csrf_token,
                    'remember': False
                }
                response = client.post('/auth/login',
                                     data=form_data,
                                     follow_redirects=True,
                                     headers={'Referer': 'http://localhost/auth/login'})
                assert response.status_code == 200
                assert b'You have been logged in successfully' in response.data

            # ...existing code...
            with neo4j_db.session() as session:
                safe_run(session, """
                    MATCH (u:User {id: $user_id})
                    DELETE u
                """, {'user_id': user_id})
    
    def test_login_with_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        # Get CSRF token first
        login_page = client.get('/auth/login')
        csrf_token = get_csrf_token(login_page.data)
        
        response = client.post('/auth/login', data={
            'email': 'invalid@example.com',
            'password': 'wrongpassword',
            'remember': False,
            'csrf_token': csrf_token
        })
        
        assert response.status_code == 200
        assert b'Invalid email or password' in response.data
    
    @patch('blueprints.auth.routes.send_email_task')
    def test_signup_with_valid_data(self, mock_email_task, client):
        """Test signup with valid data"""
        # Get the signup form first to get CSRF token
        form_response = client.get('/auth/signup')
        csrf_token = get_csrf_token(form_response.data)
        
        response = client.post('/auth/signup', data=dict(
            username='newuser',
            email='newuser@example.com',
            password='Password123!',
            confirm_password='Password123!',
            role='job_seeker',
            csrf_token=csrf_token
        ), follow_redirects=True)
        
        assert response.status_code == 200  # Should be successful after redirect
        assert b'Registration successful' in response.data
    
    def test_signup_with_weak_password(self, client):
        """Test signup with weak password"""
        # Get CSRF token
        form_response = client.get('/auth/signup')
        csrf_token = get_csrf_token(form_response.data)
        
        response = client.post('/auth/signup', data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'weak',
            'confirm_password': 'weak',
            'role': 'job_seeker',
            'csrf_token': csrf_token
        })
        
        assert response.status_code == 200
        assert b'Password must be at least 8 characters' in response.data
    
    def test_signup_with_mismatched_passwords(self, client):
        """Test signup with mismatched passwords"""
        # Get CSRF token
        form_response = client.get('/auth/signup')
        csrf_token = get_csrf_token(form_response.data)
        
        response = client.post('/auth/signup', data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'Password123!',
            'confirm_password': 'Different123!',
            'role': 'job_seeker',
            'csrf_token': csrf_token
        })
        
        assert response.status_code == 200
        assert b'Passwords must match' in response.data
    
    def test_logout(self, auth_client):
        """Test logout functionality"""
        response = auth_client.get('/auth/logout', follow_redirects=True)
        
        assert response.status_code == 200
        # Should be redirected to home page
        assert b'You have been logged out' in response.data
    
    @patch('requests.post')
    def test_google_oauth_login(self, mock_post, client):
        """Test Google OAuth login flow"""
        # Mock Google OAuth response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'access_token': 'mock_token',
            'id_token': 'mock_id_token'
        }
        mock_post.return_value = mock_response
        
        # Test OAuth callback
        response = client.get('/auth/google/callback?code=mock_code')
        
        # Should redirect to complete OAuth flow
        assert response.status_code in [200, 302]
    

    def test_password_reset_request(self, client):
        """Test password reset request"""
        # Get CSRF token
        form_response = client.get('/auth/reset-password')
        csrf_token = get_csrf_token(form_response.data)
        
        with client.session_transaction() as session:
            response = client.post('/auth/reset-password', data={
                'email': 'test@example.com',
                'csrf_token': csrf_token
            }, follow_redirects=True)

        assert response.status_code == 200
        # Should show success message regardless of email existence
        assert b'If an account exists with' in response.data
        assert b'password reset instructions' in response.data
    
    @pytest.mark.skip("Requires email sending functionality")
    def test_password_reset_with_token(self, auth_client, neo4j_db):
        """Test password reset with valid token"""
        reset_token = str(uuid.uuid4())
        reset_expires = (datetime.utcnow() + timedelta(hours=1)).isoformat()
        user_id = str(uuid.uuid4())
        
        # Create user with reset token
        password_hash = bcrypt.hashpw('Password123!'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        with neo4j_db.session() as session:
            safe_run(session, """
                CREATE (u:User {
                    id: $user_id,
                    email: 'test@example.com',
                    username: 'testuser',
                    password_hash: $password_hash,
                    role: 'job_seeker',
                    is_verified: true,
                    is_active: true,
                    created_at: $created_at,
                    reset_token: $reset_token,
                    reset_expires: $reset_expires
                })
            """, {
                'user_id': user_id,
                'password_hash': password_hash,
                'created_at': datetime.utcnow().isoformat(),
                'reset_token': reset_token,
                'reset_expires': reset_expires
            })
        
        # Test password reset
        response = auth_client.post(f'/auth/reset-password/{reset_token}', data={
            'password': 'NewPassword123!',
            'confirm': 'NewPassword123!'
        })
        
        assert response.status_code == 302  # Should redirect to login
    
    @pytest.mark.skip("Requires email sending functionality")
    def test_password_reset_invalid_token(self, client):
        """Test password reset with invalid token"""
        response = client.post('/auth/reset-password/invalid-token', data={
            'password': 'NewPassword123!',
            'confirm': 'NewPassword123!'
        })
        
        assert response.status_code == 302  # Should redirect
    
    def test_password_reset_invalid_token(self, client):
        """Test password reset with invalid token"""
        response = client.get('/auth/reset-password/invalid-token')
        
        assert response.status_code == 302  # Should redirect for invalid token
        assert response.location == '/auth/login'  # Should redirect to login
        
        # Follow redirect to see flash message
        response = client.get('/auth/reset-password/invalid-token', follow_redirects=True)
        assert b'Invalid or expired reset token' in response.data
    
    def test_change_password_authenticated(self, auth_client):
        """Test changing password while authenticated"""
        # First get the form page to get CSRF token
        form_response = auth_client.get('/auth/change-password')
        assert form_response.status_code == 200
        csrf_token = get_csrf_token(form_response.data)
        
        # Now submit the form
        response = auth_client.post('/auth/change-password', data={
            'current_password': 'Password123!',
            'new_password': 'NewPassword123!',
            'confirm_password': 'NewPassword123!',
            'csrf_token': csrf_token
        }, follow_redirects=True)
        
        assert response.status_code == 200
        def test_change_password_authenticated(self, auth_client):
            """Test changing password while authenticated"""
            with auth_client:
                form_response = auth_client.get('/auth/change-password')
                assert form_response.status_code == 200
                csrf_token = get_csrf_token(form_response.data)
                response = auth_client.post('/auth/change-password', data={
                    'current_password': 'Password123!',
                    'new_password': 'NewPassword123!',
                    'confirm_password': 'NewPassword123!',
                    'csrf_token': csrf_token
                }, follow_redirects=True)
                assert response.status_code == 200
        assert b'Password changed successfully' in response.data
    
    def test_change_password_wrong_current(self, auth_client):
        """Test changing password with wrong current password"""
        # Get CSRF token from the form page
        form_response = auth_client.get('/auth/change-password')
        assert form_response.status_code == 200
        csrf_token = get_csrf_token(form_response.data)
        
        # Submit form with wrong current password
        response = auth_client.post('/auth/change-password', data={
            'current_password': 'WrongPassword123!',
            'new_password': 'NewPassword123!',
            'confirm_password': 'NewPassword123!',
            'csrf_token': csrf_token
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Current password is incorrect' in response.data
    
    def test_change_password_mismatch(self, auth_client):
        """Test changing password with mismatched new passwords"""
        # Get CSRF token from the form page
        form_response = auth_client.get('/auth/change-password')
        assert form_response.status_code == 200
        csrf_token = get_csrf_token(form_response.data)
        
        # Submit form with mismatched new passwords
        response = auth_client.post('/auth/change-password', data={
            'current_password': 'Password123!',
            'new_password': 'NewPassword123!',
            'confirm_password': 'Different123!',
            'csrf_token': csrf_token
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'New passwords do not match' in response.data
        def test_change_password_mismatch(self, auth_client):
            """Test changing password with mismatched new passwords"""
            from bs4 import BeautifulSoup
            with auth_client:
                form_response = auth_client.get('/auth/change-password')
                assert form_response.status_code == 200
                csrf_token = get_csrf_token(form_response.data)
                response = auth_client.post('/auth/change-password', data={
                    'current_password': 'Password123!',
                    'new_password': 'NewPassword123!',
                    'confirm_password': 'Different123!',
                    'csrf_token': csrf_token
                }, follow_redirects=True)
                assert response.status_code == 200
                # Parse HTML and look for error message
                soup = BeautifulSoup(response.data, 'html.parser')
                error_found = b'New passwords do not match' in response.data or b'Passwords do not match' in response.data
                # Also check for error in flash messages
                for div in soup.find_all('div'):
                    if div.get('class') and 'flash-message' in div.get('class'):
                        if 'New passwords do not match' in div.text or 'Passwords do not match' in div.text:
                            error_found = True
                assert error_found
    
    @pytest.mark.skip("Requires email sending functionality")
    def test_resend_verification(self, client):
        """Test verification resend"""
        response = client.post('/auth/resend-verification', data={
            'email': 'test@example.com'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
    def test_authenticated_user_redirected_from_login(self, auth_client):
        """Test that authenticated users are redirected from login page"""
        response = auth_client.get('/auth/login')
        
        # Should redirect to home or dashboard
        assert response.status_code == 302
        # Check redirect location
        assert 'dashboard' in response.location or '/' in response.location
    
    def test_authenticated_user_redirected_from_signup(self, auth_client):
        """Test that authenticated users are redirected from signup page"""
        response = auth_client.get('/auth/signup')
        
        # Should redirect to home or dashboard
        assert response.status_code == 302
        assert 'dashboard' in response.location or '/' in response.location