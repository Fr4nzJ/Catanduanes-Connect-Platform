"""
Enhanced Location-Based Search with Gemini AI
Provides intelligent location filtering and suggestions for Jobs and Businesses
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from gemini_client import get_gemini_response
from database import get_neo4j_db, safe_run
import logging
import json

location_search_bp = Blueprint('location_search', __name__)
logger = logging.getLogger(__name__)

# Catanduanes municipalities and areas
CATANDUANES_LOCATIONS = {
    'virac': 'Virac',
    'baras': 'Baras',
    'bgy': 'Bagamanoc',
    'bagamanoc': 'Bagamanoc',
    'cavinitan': 'Cavinitan',
    'gigaquit': 'Gigaquit',
    'panglao': 'Panglao',
    'san_andres': 'San Andres',
    'san andres': 'San Andres',
    'viga': 'Viga',
    'caramoran': 'Caramoran',
}

def normalize_location(location_query):
    """Normalize location query to standard Catanduanes locations"""
    query_lower = location_query.lower().strip()
    
    # Direct match
    if query_lower in CATANDUANES_LOCATIONS:
        return CATANDUANES_LOCATIONS[query_lower]
    
    # Partial match
    for key, value in CATANDUANES_LOCATIONS.items():
        if key in query_lower or query_lower in key:
            return value
    
    return None

@location_search_bp.route('/ai-suggest-locations', methods=['POST'])
def ai_suggest_locations():
    """Use Gemini AI to suggest locations based on user query"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'status': 'error', 'message': 'Query is required'}), 400
        
        # Get all available locations from database
        db = get_neo4j_db()
        with db.session() as session:
            locations_result = safe_run(session, """
                MATCH (j:Job)
                WHERE j.location IS NOT NULL
                WITH DISTINCT j.location as location
                RETURN location
                UNION
                MATCH (b:Business)
                WHERE b.address IS NOT NULL
                WITH DISTINCT b.address as location
                RETURN location
                LIMIT 50
            """, {})
            
            available_locations = [record['location'] for record in locations_result if record['location']]
        
        prompt = f"""You are a location assistant for Catanduanes, Philippines. 
        
Available locations in Catanduanes: {', '.join(set(available_locations)[:20])}

User's location search query: "{query}"

Based on the user's query, suggest the most relevant locations from Catanduanes.
Consider:
1. Direct matches
2. Partial matches
3. Nearby municipalities
4. Common abbreviations or local names

Respond in JSON format with this structure:
{{
    "primary_location": "Best match location",
    "alternate_locations": ["Alternative 1", "Alternative 2"],
    "confidence": 0.0-1.0,
    "note": "Explanation of suggestion"
}}

Only return JSON, no additional text."""

        response = get_gemini_response(prompt)
        
        try:
            suggestions = json.loads(response)
        except json.JSONDecodeError:
            suggestions = {
                'primary_location': normalize_location(query) or query,
                'alternate_locations': [],
                'confidence': 0.5,
                'note': 'Direct location match'
            }
        
        return jsonify({
            'status': 'success',
            'suggestions': suggestions
        })
    except Exception as e:
        logger.error(f"Error suggesting locations: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@location_search_bp.route('/search-jobs-by-location', methods=['POST'])
def search_jobs_by_location():
    """Search jobs with AI-enhanced location understanding"""
    try:
        data = request.get_json()
        location_query = data.get('location', '').strip()
        radius = data.get('radius', 'all')  # all, nearby, exact
        category = data.get('category', '')
        min_salary = data.get('min_salary', 0)
        max_salary = data.get('max_salary', 999999)
        page = data.get('page', 1)
        per_page = data.get('per_page', 12)
        
        if not location_query:
            return jsonify({'status': 'error', 'message': 'Location query is required'}), 400
        
        # Use Gemini to understand the location query better
        prompt = f"""Given this location query from Catanduanes, Philippines: "{location_query}"
        
Generate search terms that would match jobs in that location. Consider:
1. Exact municipality names
2. Barangay names
3. District names
4. Local area names
5. Similar sounding places

Respond in JSON format:
{{
    "primary_location": "Main location to search",
    "search_terms": ["term1", "term2", "term3"],
    "is_valid": true/false
}}

Only return JSON, no additional text."""

        ai_response = get_gemini_response(prompt)
        
        try:
            location_data = json.loads(ai_response)
        except json.JSONDecodeError:
            location_data = {
                'primary_location': location_query,
                'search_terms': [location_query],
                'is_valid': True
            }
        
        if not location_data.get('is_valid', True):
            return jsonify({'status': 'error', 'message': 'Location not found in Catanduanes'}), 400
        
        # Build Neo4j query with AI-enhanced search
        db = get_neo4j_db()
        with db.session() as session:
            search_terms = location_data.get('search_terms', [location_query])
            
            # Build location filter
            location_filters = " OR ".join([f"j.location CONTAINS '{term}'" for term in search_terms])
            
            query = f"""
                MATCH (j:Job)-[:POSTED_BY]->(b:Business)
                WHERE j.is_active = true 
                AND ({location_filters})
                AND j.salary_min >= {min_salary}
                AND (j.salary_max IS NULL OR j.salary_max <= {max_salary})
            """
            
            if category:
                query += f" AND j.category = '{category}'"
            
            # Get total count
            count_result = safe_run(session, f"""
                {query.replace('MATCH', 'MATCH')}
                RETURN count(j) as total
            """, {})
            
            total = count_result[0]['total'] if count_result else 0
            
            # Paginate results
            skip = (page - 1) * per_page
            query += f"""
                ORDER BY j.created_at DESC
                SKIP {skip}
                LIMIT {per_page}
                RETURN j, b.name as business_name, b.id as business_id, 
                       b.rating as business_rating
            """
            
            jobs_result = safe_run(session, query, {})
            
            jobs = []
            for record in jobs_result:
                job_node = record['j']
                jobs.append({
                    'id': job_node['id'],
                    'title': job_node['title'],
                    'description': job_node['description'],
                    'location': job_node['location'],
                    'salary_range': job_node.get('salary_range', 'Negotiable'),
                    'type': job_node.get('employment_type'),
                    'business_name': record['business_name'],
                    'business_id': record['business_id'],
                    'business_rating': record['business_rating']
                })
        
        return jsonify({
            'status': 'success',
            'location_data': location_data,
            'jobs': jobs,
            'total': total,
            'page': page,
            'per_page': per_page
        })
    except Exception as e:
        logger.error(f"Error searching jobs by location: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@location_search_bp.route('/search-businesses-by-location', methods=['POST'])
def search_businesses_by_location():
    """Search businesses with AI-enhanced location understanding"""
    try:
        data = request.get_json()
        location_query = data.get('location', '').strip()
        category = data.get('category', '')
        min_rating = data.get('min_rating', 0)
        verified_only = data.get('verified_only', False)
        page = data.get('page', 1)
        per_page = data.get('per_page', 12)
        
        if not location_query:
            return jsonify({'status': 'error', 'message': 'Location query is required'}), 400
        
        # Use Gemini to understand the location query
        prompt = f"""Given this location query from Catanduanes, Philippines: "{location_query}"
        
Generate search terms that would match businesses in that location. Consider:
1. Exact municipality names
2. Barangay names
3. Street names
4. Landmarks
5. Local area names

Respond in JSON format:
{{
    "primary_location": "Main location to search",
    "search_terms": ["term1", "term2", "term3"],
    "is_valid": true/false
}}

Only return JSON, no additional text."""

        ai_response = get_gemini_response(prompt)
        
        try:
            location_data = json.loads(ai_response)
        except json.JSONDecodeError:
            location_data = {
                'primary_location': location_query,
                'search_terms': [location_query],
                'is_valid': True
            }
        
        if not location_data.get('is_valid', True):
            return jsonify({'status': 'error', 'message': 'Location not found in Catanduanes'}), 400
        
        # Build Neo4j query
        db = get_neo4j_db()
        with db.session() as session:
            search_terms = location_data.get('search_terms', [location_query])
            location_filters = " OR ".join([f"b.address CONTAINS '{term}'" for term in search_terms])
            
            query = f"""
                MATCH (b:Business)
                WHERE b.is_active = true
                AND ({location_filters})
                AND b.rating >= {min_rating}
            """
            
            if category:
                query += f" AND b.category = '{category}'"
            
            if verified_only:
                query += " AND b.is_verified = true"
            
            # Get total count
            count_result = safe_run(session, f"""
                {query.replace('MATCH', 'MATCH')}
                RETURN count(b) as total
            """, {})
            
            total = count_result[0]['total'] if count_result else 0
            
            # Paginate results
            skip = (page - 1) * per_page
            query += f"""
                ORDER BY b.rating DESC, b.created_at DESC
                SKIP {skip}
                LIMIT {per_page}
                RETURN b
            """
            
            businesses_result = safe_run(session, query, {})
            
            businesses = []
            for record in businesses_result:
                business_node = record['b']
                businesses.append({
                    'id': business_node['id'],
                    'name': business_node['name'],
                    'description': business_node['description'],
                    'address': business_node['address'],
                    'category': business_node['category'],
                    'rating': business_node.get('rating', 0),
                    'review_count': business_node.get('review_count', 0),
                    'is_verified': business_node.get('is_verified', False),
                    'phone': business_node.get('phone', '')
                })
        
        return jsonify({
            'status': 'success',
            'location_data': location_data,
            'businesses': businesses,
            'total': total,
            'page': page,
            'per_page': per_page
        })
    except Exception as e:
        logger.error(f"Error searching businesses by location: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@location_search_bp.route('/get-location-suggestions', methods=['GET'])
def get_location_suggestions():
    """Get autocomplete suggestions for locations"""
    try:
        query = request.args.get('q', '').strip()
        
        if not query or len(query) < 2:
            return jsonify({'suggestions': []})
        
        # Check against known locations
        matching_locations = []
        query_lower = query.lower()
        
        for key, value in CATANDUANES_LOCATIONS.items():
            if query_lower in key or query_lower in value.lower():
                if value not in matching_locations:
                    matching_locations.append(value)
        
        # Also search database for locations
        db = get_neo4j_db()
        with db.session() as session:
            # Search in Job locations
            job_locations = safe_run(session, f"""
                MATCH (j:Job)
                WHERE j.location CONTAINS '{query}'
                RETURN DISTINCT j.location as location
                LIMIT 10
            """, {})
            
            for record in job_locations:
                if record['location'] and record['location'] not in matching_locations:
                    matching_locations.append(record['location'])
            
            # Search in Business addresses
            business_locations = safe_run(session, f"""
                MATCH (b:Business)
                WHERE b.address CONTAINS '{query}'
                RETURN DISTINCT b.address as address
                LIMIT 10
            """, {})
            
            for record in business_locations:
                if record['address'] and record['address'] not in matching_locations:
                    matching_locations.append(record['address'])
        
        return jsonify({'suggestions': matching_locations[:15]})
    except Exception as e:
        logger.error(f"Error getting location suggestions: {str(e)}")
        return jsonify({'suggestions': []})
