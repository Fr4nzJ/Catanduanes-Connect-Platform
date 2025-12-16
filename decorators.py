from functools import wraps
from flask import abort, redirect, url_for, request, flash, jsonify
from flask_login import current_user, login_required
from typing import Callable, Union, List
from extensions import limiter   # ← no circular dependency

def role_required(*roles: str) -> Callable:
    """Decorator to require specific role(s) for access"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        @login_required
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login', next=request.url))
            
            if current_user.role not in roles:
                flash('You do not have permission to access this page.', 'error')
                return abort(403)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def login_required_optional(func: Callable) -> Callable:
    """Decorator for pages accessible to both guests and logged-in users"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

def verified_required(func: Callable) -> Callable:
    """Decorator to require verified email address"""
    @wraps(func)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_verified:
            flash('Please verify your email address first. Check your email for a verification link.', 'warning')
            return redirect(url_for('auth.login'))
        return func(*args, **kwargs)
    return wrapper

def business_owner_required(func: Callable) -> Callable:
    """Decorator to require business ownership for specific business operations"""
    @wraps(func)
    @login_required
    def wrapper(*args, **kwargs):
        business_id = kwargs.get('business_id') or request.args.get('business_id')
        if not business_id:
            flash('Business ID is required.', 'error')
            return abort(400)
        
        # Check if user owns the business
        from database import get_neo4j_db, safe_run, _node_to_dict
        db = get_neo4j_db()
        with db.session() as session:
            result = safe_run(session, """
                MATCH (u:User {id: $user_id})-[:OWNS]->(b:Business {id: $business_id})
                RETURN b
            """, {'user_id': current_user.id, 'business_id': business_id})
            
            if not result:
                flash('You do not have permission to access this business.', 'error')
                return abort(403)
        
        return func(*args, **kwargs)
    return wrapper

def rate_limit_by_user(default_limit: str = "100 per hour") -> Callable:
    """Rate limiting decorator that uses user ID if authenticated, otherwise IP"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if current_user.is_authenticated:
                # Use user ID for rate limiting
                from flask_limiter.util import get_user_id
                return limiter.limit(default_limit, key_func=get_user_id)(func)(*args, **kwargs)
            else:
                # Use IP address for rate limiting
                return limiter.limit(default_limit)(func)(*args, **kwargs)
        return wrapper
    return decorator

def cache_control(**kwargs) -> Callable:
    """Decorator to set cache control headers"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            response = func(*args, **kwargs)
            for key, value in kwargs.items():
                response.headers[key.replace('_', '-')] = str(value)
            return response
        return wrapper
    return decorator

def json_response(func: Callable) -> Callable:
    """Decorator to convert return value to JSON response"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if isinstance(result, tuple):
            data, status_code = result
            return jsonify(data), status_code
        return jsonify(result)
    return wrapper