from flask import jsonify, current_app
from flask_login import current_user, login_required
from . import api_bp
from database import get_neo4j_db, safe_run
from .realtime import get_platform_stats, get_business_owner_stats, get_job_seeker_stats

@api_bp.route('/homepage/featured-jobs')
def featured_jobs():
    return jsonify({"jobs": []})  # Temporarily return empty list

@api_bp.route('/homepage/stats')
def homepage_stats():
    """Get real-time homepage statistics"""
    stats = get_platform_stats()
    return jsonify(stats)

@api_bp.route('/realtime/stats')
def realtime_stats():
    """Get real-time statistics for dashboard"""
    if not current_user.is_authenticated:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if current_user.role == 'business_owner':
        stats = get_business_owner_stats(current_user.id)
    elif current_user.role == 'job_seeker':
        stats = get_job_seeker_stats(current_user.id)
    else:
        stats = get_platform_stats()
    
    return jsonify(stats)

@api_bp.route('/current-user')
def get_current_user():
    if current_user.is_authenticated:
        return jsonify({
            "authenticated": True,
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "role": current_user.role
        })
    return jsonify({"authenticated": False})

@api_bp.route('/businesses/map-markers')
def get_business_markers():
    """Get all business locations for map display"""
    try:
        db = get_neo4j_db()
        with db.session() as session:
            # Query businesses with location data
            result = safe_run(session, """
                MATCH (b:Business)
                WHERE b.latitude IS NOT NULL 
                AND b.longitude IS NOT NULL
                RETURN b.id AS id,
                       b.name AS name,
                       b.address AS address,
                       b.latitude AS latitude,
                       b.longitude AS longitude,
                       b.category AS category,
                       b.description AS description
            """)
            
            markers = []
            if result:
                for record in result:
                    # Only add markers with valid coordinates
                    if record.get('latitude') and record.get('longitude'):
                        try:
                            lat = float(record['latitude'])
                            lng = float(record['longitude'])
                            markers.append({
                                'id': record['id'],
                                'name': record['name'],
                                'address': record['address'],
                                'latitude': lat,
                                'longitude': lng,
                                'business_type': record.get('business_type', 'Unknown'),
                                'description': record.get('description', '')
                            })
                        except (ValueError, TypeError) as e:
                            current_app.logger.warning(
                                f"Invalid coordinates for business {record.get('id')}: {e}"
                            )
                            continue
            
            return jsonify({
                'success': True,
                'markers': markers
            })
            
    except Exception as e:
        current_app.logger.error(f"Error fetching business markers: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch business locations',
            'markers': []
        })