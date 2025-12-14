from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from gemini_client import get_gemini_response
import logging

gemini_bp = Blueprint('gemini', __name__)
logger = logging.getLogger(__name__)


@gemini_bp.route('/improve-business-description', methods=['POST'])
@login_required
def improve_business_description():
    """Improve business description using AI"""
    try:
        data = request.get_json()
        description = data.get('description', '').strip()
        category = data.get('category', '')
        language = data.get('language', 'English')

        if not description:
            return jsonify({'status': 'error', 'message': 'Description is required'}), 400

        prompt = f"""You are a business consultant helping improve business descriptions for a local business platform.

Business Category: {category}
Current Description: {description}

Please improve this business description to make it more compelling and professional. The improved description should:
1. Be clear and engaging
2. Highlight unique value proposition
3. Include key services or products
4. Be optimized for search visibility
5. Be between 50-200 words

Respond in {language} language.

Provide ONLY the improved description without any additional commentary."""

        response = get_gemini_response(prompt)
        
        return jsonify({
            'status': 'success',
            'improvements': response
        })
    except Exception as e:
        logger.error(f"Error improving business description: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@gemini_bp.route('/registration-tips', methods=['POST'])
@login_required
def registration_tips():
    """Get registration tips for business category"""
    try:
        data = request.get_json()
        category = data.get('category', 'General')
        language = data.get('language', 'English')

        prompt = f"""You are an expert business advisor helping new businesses register on a local platform.

Business Category: {category}

Please provide 5 key tips for successfully registering a {category} business on our platform. Focus on:
1. What information to emphasize
2. Common mistakes to avoid
3. How to make the business stand out
4. Documentation best practices
5. Maximizing visibility

Respond in {language} language.

Format as a numbered list with brief explanations for each tip."""

        response = get_gemini_response(prompt)
        
        return jsonify({
            'status': 'success',
            'tips': response
        })
    except Exception as e:
        logger.error(f"Error generating registration tips: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@gemini_bp.route('/review-business-info', methods=['POST'])
@login_required
def review_business_info():
    """Review and validate business information"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        category = data.get('category', '')
        language = data.get('language', 'English')

        if not name or not description:
            return jsonify({'status': 'error', 'message': 'Name and description are required'}), 400

        prompt = f"""You are a business registration reviewer. Review the following business information and provide constructive feedback.

Business Name: {name}
Category: {category}
Description: {description}

Please provide:
1. Overall quality score (1-10)
2. Strengths of the submission
3. Areas for improvement
4. Specific suggestions for enhancement
5. Whether it's ready for listing (Yes/No)

Respond in {language} language.

Be encouraging but honest. Provide actionable feedback."""

        response = get_gemini_response(prompt)
        
        return jsonify({
            'status': 'success',
            'review': response
        })
    except Exception as e:
        logger.error(f"Error reviewing business info: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ===== Job Recommendation Endpoints =====

@gemini_bp.route('/recommend-jobs-by-resume', methods=['POST'])
@login_required
def recommend_jobs_by_resume():
    """Recommend jobs based on user's resume"""
    try:
        from database import get_neo4j_db, safe_run
        
        db = get_neo4j_db()
        with db.session() as session:
            # Get user's resume data
            user_data = safe_run(session, """
                MATCH (u:User {id: $user_id})
                OPTIONAL MATCH (u)-[:HAS_RESUME]->(r:Resume)
                RETURN u.name as name, u.role as role, r.text as resume_text, r.skills as skills
            """, {'user_id': current_user.id})
            
            if not user_data:
                return jsonify({'status': 'error', 'message': 'User not found'}), 404
            
            user_info = user_data[0]
            resume_text = user_info.get('resume_text', '')
            
            if not resume_text:
                return jsonify({'status': 'error', 'message': 'No resume found'}), 400
            
            # Get all available jobs
            jobs_data = safe_run(session, """
                MATCH (j:Job)
                RETURN j.id as id, j.title as title, j.description as description, 
                       j.category as category, j.requirements as requirements, j.salary_min as salary_min,
                       j.salary_max as salary_max, j.type as job_type
                LIMIT 50
            """)
            
            jobs_list = [dict(j) for j in jobs_data] if jobs_data else []
            
            logger.info(f"Resume recommendation: found {len(jobs_list)} jobs for user")

            # If no jobs found, return empty
            if not jobs_list:
                logger.warning("No jobs found in database for resume recommendation")
                return jsonify({
                    'status': 'success',
                    'recommended_jobs': []
                })

            # Return top 5 jobs directly from database
            recommended_job_ids = [job.get('id') for job in jobs_list[:5]]
            
            logger.info(f"Resume recommendation returning job IDs: {recommended_job_ids}")
            
            return jsonify({
                'status': 'success',
                'recommended_jobs': recommended_job_ids
            })
    except Exception as e:
        logger.error(f"Error recommending jobs by resume: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@gemini_bp.route('/recommend-jobs-by-skills', methods=['POST'])
@login_required
def recommend_jobs_by_skills():
    """Recommend jobs based on user's skills"""
    try:
        from database import get_neo4j_db, safe_run
        
        db = get_neo4j_db()
        with db.session() as session:
            # Get user's skills
            user_data = safe_run(session, """
                MATCH (u:User {id: $user_id})
                RETURN u.skills as skills, u.role as role
            """, {'user_id': current_user.id})
            
            if not user_data or not user_data[0].get('skills'):
                return jsonify({'status': 'error', 'message': 'No skills found in profile'}), 400
            
            user_skills = user_data[0]['skills']
            
            # Get all available jobs
            jobs_data = safe_run(session, """
                MATCH (j:Job)
                RETURN j.id as id, j.title as title, j.description as description, 
                       j.requirements as requirements, j.category as category
                LIMIT 50
            """)
            
            jobs_list = [dict(j) for j in jobs_data] if jobs_data else []
            
            logger.info(f"Skills recommendation: found {len(jobs_list)} jobs for user skills: {user_skills}")

            # If no jobs found, return empty
            if not jobs_list:
                logger.warning("No jobs found in database for skills recommendation")
                return jsonify({
                    'status': 'success',
                    'recommended_jobs': []
                })

            # Return top 5 jobs directly from database
            recommended_job_ids = [job.get('id') for job in jobs_list[:5]]
            
            logger.info(f"Skills recommendation returning job IDs: {recommended_job_ids}")
            
            return jsonify({
                'status': 'success',
                'recommended_jobs': recommended_job_ids
            })
                        
            return jsonify({
                'status': 'success',
                'recommended_jobs': recommended_job_ids
            })
    except Exception as e:
        logger.error(f"Error recommending jobs by skills: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@gemini_bp.route('/recommend-jobs-by-experience', methods=['POST'])
@login_required
def recommend_jobs_by_experience():
    """Recommend jobs based on experience level"""
    try:
        from database import get_neo4j_db, safe_run
        
        db = get_neo4j_db()
        with db.session() as session:
            # Get user's experience
            user_data = safe_run(session, """
                MATCH (u:User {id: $user_id})
                RETURN u.experience_years as experience_years, u.role as role
            """, {'user_id': current_user.id})
            
            if not user_data:
                return jsonify({'status': 'error', 'message': 'User not found'}), 404
            
            experience = user_data[0].get('experience_years', 0) or 0
            
            # Get all available jobs
            jobs_data = safe_run(session, """
                MATCH (j:Job)
                RETURN j.id as id, j.title as title, j.description as description, 
                       j.type as job_type, j.category as category
                LIMIT 50
            """)
            
            jobs_list = [dict(j) for j in jobs_data] if jobs_data else []
            
            logger.info(f"Experience recommendation: found {len(jobs_list)} jobs for experience level: {experience}")

            # If no jobs found, return empty
            if not jobs_list:
                logger.warning("No jobs found in database for experience recommendation")
                return jsonify({
                    'status': 'success',
                    'recommended_jobs': []
                })

            # Return top 5 jobs directly from database
            recommended_job_ids = [job.get('id') for job in jobs_list[:5]]
            
            logger.info(f"Experience recommendation returning job IDs: {recommended_job_ids}")
            
            return jsonify({
                'status': 'success',
                'recommended_jobs': recommended_job_ids
            })
    except Exception as e:
        logger.error(f"Error recommending jobs by experience: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@gemini_bp.route('/recommend-jobs-by-role', methods=['POST'])
@login_required
def recommend_jobs_by_role():
    """Recommend career-focused jobs"""
    try:
        from database import get_neo4j_db, safe_run
        
        db = get_neo4j_db()
        with db.session() as session:
            # Get user's role
            user_data = safe_run(session, """
                MATCH (u:User {id: $user_id})
                RETURN u.role as role, u.name as name
            """, {'user_id': current_user.id})
            
            if not user_data:
                return jsonify({'status': 'error', 'message': 'User not found'}), 404
            
            user_role = user_data[0].get('role', '')
            
            # Get all available jobs
            jobs_data = safe_run(session, """
                MATCH (j:Job)
                RETURN j.id as id, j.title as title, j.category as category, 
                       j.description as description
                LIMIT 50
            """)
            
            jobs_list = [dict(j) for j in jobs_data] if jobs_data else []
            
            logger.info(f"Role recommendation: found {len(jobs_list)} jobs for user role: {user_role}")

            # If no jobs found, return empty
            if not jobs_list:
                logger.warning("No jobs found in database for role recommendation")
                return jsonify({
                    'status': 'success',
                    'recommended_jobs': []
                })

            # Return top 5 jobs directly (first 5 from database)
            recommended_job_ids = [job.get('id') for job in jobs_list[:5]]
            
            logger.info(f"Role recommendation returning job IDs: {recommended_job_ids}")
            
            return jsonify({
                'status': 'success',
                'recommended_jobs': recommended_job_ids
            })
    except Exception as e:
        logger.error(f"Error recommending jobs by role: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@gemini_bp.route('/recommend-jobs-by-salary', methods=['POST'])
@login_required
def recommend_jobs_by_salary():
    """Recommend high-paying jobs"""
    try:
        from database import get_neo4j_db, safe_run
        
        db = get_neo4j_db()
        with db.session() as session:
            # Get user's salary preference (handle missing property safely)
            user_data = safe_run(session, """
                MATCH (u:User {id: $user_id})
                RETURN coalesce(u.salary_expectation, 0) as salary_expectation
            """, {'user_id': current_user.id})
            salary_expectation = 0
            if user_data and len(user_data) > 0:
                salary_expectation = user_data[0].get('salary_expectation', 0)

            # Get all available jobs sorted by salary (or by ID if salary not available)
            jobs_data = safe_run(session, """
                MATCH (j:Job)
                RETURN j.id as id, j.title as title, j.salary_min as salary_min, 
                       j.salary_max as salary_max, j.category as category
                ORDER BY coalesce(j.salary_max, j.salary_min, 0) DESC
                LIMIT 50
            """)

            jobs_list = [dict(j) for j in jobs_data] if jobs_data else []
            
            logger.info(f"Salary recommendation: found {len(jobs_list)} jobs, user salary expectation: {salary_expectation}")

            # If no jobs found, return empty
            if not jobs_list:
                logger.warning("No jobs found in database for salary recommendation")
                return jsonify({
                    'status': 'success',
                    'recommended_jobs': []
                })

            # Return top 5 high-paying jobs directly (sorted by salary_max DESC)
            recommended_job_ids = [job.get('id') for job in jobs_list[:5]]
            
            logger.info(f"Salary recommendation returning job IDs: {recommended_job_ids}")
            
            return jsonify({
                'status': 'success',
                'recommended_jobs': recommended_job_ids
            })
    except Exception as e:
        logger.error(f"Error recommending jobs by salary: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@gemini_bp.route('/fetch-jobs-by-ids', methods=['POST'])
@login_required
def fetch_jobs_by_ids():
    """Fetch full job details for given job IDs"""
    try:
        from database import get_neo4j_db, safe_run
        
        data = request.get_json()
        job_ids = data.get('job_ids', [])
        
        if not job_ids or not isinstance(job_ids, list):
            return jsonify({'status': 'error', 'message': 'job_ids must be a non-empty array'}), 400
        
        db = get_neo4j_db()
        with db.session() as session:
            # Fetch job details for all provided IDs
            jobs_data = safe_run(session, """
                MATCH (j:Job)
                WHERE j.id IN $job_ids
                OPTIONAL MATCH (j)-[:POSTED_BY]->(b:Business)
                RETURN j.id as id, j.title as title, j.description as description,
                       j.type as type_val, j.setup as setup, j.category as category,
                       j.location as location, j.salary_min as salary_min,
                       j.salary_max as salary_max, j.latitude as latitude,
                       j.longitude as longitude,
                       COALESCE(b.name, 'Company') as business_name
            """, {'job_ids': job_ids})
            
            # Format jobs for frontend
            jobs_list = []
            if jobs_data:
                for job in jobs_data:
                    # Determine display values
                    job_type_map = {
                        'full_time': 'Full-time',
                        'part_time': 'Part-time',
                        'contract': 'Contract',
                        'internship': 'Internship'
                    }
                    job_setup_map = {
                        'on_site': 'On-site',
                        'remote': 'Remote',
                        'hybrid': 'Hybrid'
                    }
                    
                    type_display = job_type_map.get(job.get('type_val'), job.get('type_val', 'Full-time'))
                    setup_display = job_setup_map.get(job.get('setup'), job.get('setup', 'On-site'))
                    
                    # Format salary
                    salary_range = ''
                    if job.get('salary_min') or job.get('salary_max'):
                        if job.get('salary_min') and job.get('salary_max'):
                            salary_range = f"₱{job.get('salary_min'):,} - ₱{job.get('salary_max'):,}/month"
                        elif job.get('salary_max'):
                            salary_range = f"Up to ₱{job.get('salary_max'):,}/month"
                        elif job.get('salary_min'):
                            salary_range = f"From ₱{job.get('salary_min'):,}/month"
                    
                    job_dict = {
                        'id': job.get('id'),
                        'title': job.get('title'),
                        'description': job.get('description'),
                        'business_name': job.get('business_name'),
                        'type_display': type_display,
                        'setup_display': setup_display,
                        'salary_range_display': salary_range,
                        'category': job.get('category'),
                        'location': job.get('location'),
                        'latitude': job.get('latitude'),
                        'longitude': job.get('longitude')
                    }
                    jobs_list.append(job_dict)
            
            logger.info(f"Fetched {len(jobs_list)} job details for IDs: {job_ids}")
            
            return jsonify({
                'status': 'success',
                'jobs': jobs_list
            })
    except Exception as e:
        logger.error(f"Error fetching jobs by IDs: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ===== Business Recommendation Endpoints (Template-Compatible Names) =====

@gemini_bp.route('/get-businesses-by-category', methods=['POST'])
@login_required
def get_businesses_by_category():
    """Recommend businesses by category preference (template-compatible)"""
    try:
        from database import get_neo4j_db, safe_run
        
        data = request.get_json()
        language = data.get('language', 'English')
        
        # Get all business categories
        db = get_neo4j_db()
        with db.session() as session:
            categories = safe_run(session, """
                MATCH (b:Business)
                WHERE b.is_active = true
                RETURN DISTINCT b.category as category
                LIMIT 20
            """)
        
            # Get businesses from each category
            businesses_info = safe_run(session, """
                MATCH (b:Business)
                WHERE b.is_active = true
                RETURN b.id as id, b.name as name, b.category as category
                LIMIT 100
            """)
        
        # Group by category and select best from each
        category_groups = {}
        if businesses_info:
            for biz in businesses_info:
                cat = biz['category']
                if cat not in category_groups:
                    category_groups[cat] = []
                category_groups[cat].append(biz['id'])
        
        # Get up to 5 businesses from different categories
        recommended_ids = []
        for cat, ids in list(category_groups.items())[:5]:
            if ids:
                recommended_ids.append(ids[0])
        
        logger.info(f"Recommended businesses by category: {recommended_ids}")
        
        return jsonify({
            'status': 'success',
            'businesses': recommended_ids
        })
    except Exception as e:
        logger.error(f"Error getting businesses by category: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@gemini_bp.route('/get-businesses-by-rating', methods=['POST'])
@login_required
def get_businesses_by_rating():
    """Get top-rated businesses (template-compatible)"""
    try:
        from database import get_neo4j_db, safe_run
        
        db = get_neo4j_db()
        with db.session() as session:
            businesses_data = safe_run(session, """
                MATCH (b:Business)
                WHERE b.is_active = true AND b.rating IS NOT NULL
                RETURN b.id as id, b.name as name, b.rating as rating
                ORDER BY b.rating DESC
                LIMIT 10
            """)
        
        recommended_ids = [b['id'] for b in (businesses_data or [])]
        
        logger.info(f"Top-rated businesses: {recommended_ids}")
        
        return jsonify({
            'status': 'success',
            'businesses': recommended_ids
        })
    except Exception as e:
        logger.error(f"Error getting top-rated businesses: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@gemini_bp.route('/get-businesses-by-location', methods=['POST'])
@login_required
def get_businesses_by_location():
    """Get nearby businesses (template-compatible)"""
    try:
        from database import get_neo4j_db, safe_run
        
        db = get_neo4j_db()
        with db.session() as session:
            businesses_data = safe_run(session, """
                MATCH (b:Business)
                WHERE b.is_active = true
                RETURN b.id as id, b.name as name, b.location as location
                LIMIT 10
            """)
        
        recommended_ids = [b['id'] for b in (businesses_data or [])]
        
        logger.info(f"Nearby businesses: {recommended_ids}")
        
        return jsonify({
            'status': 'success',
            'businesses': recommended_ids
        })
    except Exception as e:
        logger.error(f"Error getting nearby businesses: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@gemini_bp.route('/get-businesses-by-recent', methods=['POST'])
@login_required
def get_businesses_by_recent():
    """Get recently added businesses (template-compatible)"""
    try:
        from database import get_neo4j_db, safe_run
        
        db = get_neo4j_db()
        with db.session() as session:
            businesses_data = safe_run(session, """
                MATCH (b:Business)
                WHERE b.is_active = true
                RETURN b.id as id, b.name as name, b.created_at as created_at
                ORDER BY b.created_at DESC
                LIMIT 10
            """)
        
        recommended_ids = [b['id'] for b in (businesses_data or [])]
        
        logger.info(f"Recently added businesses: {recommended_ids}")
        
        return jsonify({
            'status': 'success',
            'businesses': recommended_ids
        })
    except Exception as e:
        logger.error(f"Error getting recently added businesses: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@gemini_bp.route('/get-businesses-by-popular', methods=['POST'])
@login_required
def get_businesses_by_popular():
    """Get most reviewed businesses (template-compatible)"""
    try:
        from database import get_neo4j_db, safe_run
        
        db = get_neo4j_db()
        with db.session() as session:
            businesses_data = safe_run(session, """
                MATCH (b:Business)
                WHERE b.is_active = true AND b.review_count IS NOT NULL
                RETURN b.id as id, b.name as name, b.review_count as review_count
                ORDER BY b.review_count DESC
                LIMIT 10
            """)
        
        recommended_ids = [b['id'] for b in (businesses_data or [])]
        
        logger.info(f"Most reviewed businesses: {recommended_ids}")
        
        return jsonify({
            'status': 'success',
            'businesses': recommended_ids
        })
    except Exception as e:
        logger.error(f"Error getting most reviewed businesses: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ===== Advanced Business Recommendation Endpoints =====

@gemini_bp.route('/recommend-businesses-by-interests', methods=['POST'])
@login_required
def recommend_businesses_by_interests():
    """Recommend businesses based on user interests"""
    try:
        from database import get_neo4j_db, safe_run
        
        data = request.get_json()
        interests = data.get('interests', [])
        language = data.get('language', 'English')
        
        if not interests or not isinstance(interests, list):
            return jsonify({'status': 'error', 'message': 'interests must be a non-empty array'}), 400
        
        # Get all available business categories and names
        db = get_neo4j_db()
        with db.session() as session:
            businesses_info = safe_run(session, """
                MATCH (b:Business)
                WHERE b.is_active = true
                RETURN b.id as id, b.name as name, b.category as category, 
                       b.description as description, b.location as location,
                       b.rating as rating, b.review_count as review_count
                LIMIT 50
            """)
        
        # Format business data for AI
        business_list_str = "\n".join([
            f"- {b['name']} (Category: {b['category']}, Location: {b['location']}, Rating: {b['rating'] or 'N/A'}, ID: {b['id']})"
            for b in (businesses_info or [])
        ])
        
        interests_str = ", ".join(interests)
        
        prompt = f"""Based on the user's interests in: {interests_str}

Here are available businesses in our platform:
{business_list_str}

Please recommend the top 5 businesses that best match the user's interests. 
Respond ONLY with the business IDs (one per line, no other text or explanations).
Example format:
business-id-1
business-id-2
business-id-3
business-id-4
business-id-5

If fewer than 5 businesses match, return as many as possible."""

        response = get_gemini_response(prompt)
        
        # Parse response to get business IDs
        recommended_business_ids = [
            line.strip() for line in response.strip().split('\n') 
            if line.strip() and line.strip().startswith('business-')
        ]
        
        logger.info(f"AI recommended businesses: {recommended_business_ids}")
        
        return jsonify({
            'status': 'success',
            'recommended_businesses': recommended_business_ids
        })
    except Exception as e:
        logger.error(f"Error recommending businesses by interests: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@gemini_bp.route('/recommend-businesses-by-category', methods=['POST'])
@login_required
def recommend_businesses_by_category():
    """Recommend businesses by category preference"""
    try:
        from database import get_neo4j_db, safe_run
        
        data = request.get_json()
        preferred_categories = data.get('categories', [])
        language = data.get('language', 'English')
        
        if not preferred_categories or not isinstance(preferred_categories, list):
            return jsonify({'status': 'error', 'message': 'categories must be a non-empty array'}), 400
        
        db = get_neo4j_db()
        with db.session() as session:
            businesses_info = safe_run(session, """
                MATCH (b:Business)
                WHERE b.is_active = true
                RETURN b.id as id, b.name as name, b.category as category, 
                       b.description as description, b.location as location,
                       b.rating as rating, b.review_count as review_count
                LIMIT 50
            """)
        
        business_list_str = "\n".join([
            f"- {b['name']} (Category: {b['category']}, Location: {b['location']}, ID: {b['id']})"
            for b in (businesses_info or [])
        ])
        
        categories_str = ", ".join(preferred_categories)
        
        prompt = f"""The user is interested in the following business categories: {categories_str}

Available businesses in our platform:
{business_list_str}

Please recommend the top 5 businesses that match these categories, prioritizing higher-rated businesses.
Respond ONLY with the business IDs (one per line, no other text).
Example format:
business-id-1
business-id-2
business-id-3
business-id-4
business-id-5"""

        response = get_gemini_response(prompt)
        
        # Parse response to get business IDs
        recommended_business_ids = [
            line.strip() for line in response.strip().split('\n') 
            if line.strip() and line.strip().startswith('business-')
        ]
        
        logger.info(f"AI recommended businesses by category: {recommended_business_ids}")
        
        return jsonify({
            'status': 'success',
            'recommended_businesses': recommended_business_ids
        })
    except Exception as e:
        logger.error(f"Error recommending businesses by category: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@gemini_bp.route('/recommend-businesses-by-location', methods=['POST'])
@login_required
def recommend_businesses_by_location():
    """Recommend businesses by location"""
    try:
        from database import get_neo4j_db, safe_run
        
        data = request.get_json()
        preferred_location = data.get('location', '').strip()
        language = data.get('language', 'English')
        
        if not preferred_location:
            return jsonify({'status': 'error', 'message': 'location is required'}), 400
        
        db = get_neo4j_db()
        with db.session() as session:
            businesses_info = safe_run(session, """
                MATCH (b:Business)
                WHERE b.is_active = true
                RETURN b.id as id, b.name as name, b.category as category, 
                       b.location as location, b.address as address,
                       b.rating as rating
                LIMIT 50
            """)
        
        business_list_str = "\n".join([
            f"- {b['name']} (Category: {b['category']}, Location: {b['location']}, Address: {b['address']}, ID: {b['id']})"
            for b in (businesses_info or [])
        ])
        
        prompt = f"""The user is looking for businesses near: {preferred_location}

Available businesses in our platform:
{business_list_str}

Please recommend the top 5 businesses that are located in or near {preferred_location}.
Respond ONLY with the business IDs (one per line, no other text).
Example format:
business-id-1
business-id-2
business-id-3
business-id-4
business-id-5"""

        response = get_gemini_response(prompt)
        
        # Parse response to get business IDs
        recommended_business_ids = [
            line.strip() for line in response.strip().split('\n') 
            if line.strip() and line.strip().startswith('business-')
        ]
        
        logger.info(f"AI recommended businesses by location: {recommended_business_ids}")
        
        return jsonify({
            'status': 'success',
            'recommended_businesses': recommended_business_ids
        })
    except Exception as e:
        logger.error(f"Error recommending businesses by location: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@gemini_bp.route('/fetch-businesses-by-ids', methods=['POST'])
@login_required
def fetch_businesses_by_ids():
    """Fetch full business details for given business IDs"""
    try:
        from database import get_neo4j_db, safe_run
        
        data = request.get_json()
        business_ids = data.get('business_ids', [])
        
        if not business_ids or not isinstance(business_ids, list):
            return jsonify({'status': 'error', 'message': 'business_ids must be a non-empty array'}), 400
        
        db = get_neo4j_db()
        with db.session() as session:
            # Fetch business details for all provided IDs
            businesses_data = safe_run(session, """
                MATCH (b:Business)
                WHERE b.id IN $business_ids
                RETURN b.id as id, b.name as name, b.description as description,
                       b.category as category, b.location as location,
                       b.address as address, b.phone as phone,
                       b.email as email, b.website as website,
                       b.rating as rating, b.review_count as review_count,
                       b.latitude as latitude, b.longitude as longitude,
                       b.image_url as image_url
            """, {'business_ids': business_ids})
            
            # Format businesses for frontend
            businesses_list = []
            if businesses_data:
                for business in businesses_data:
                    business_dict = {
                        'id': business.get('id'),
                        'name': business.get('name'),
                        'description': business.get('description'),
                        'category': business.get('category'),
                        'location': business.get('location'),
                        'address': business.get('address'),
                        'phone': business.get('phone'),
                        'email': business.get('email'),
                        'website': business.get('website'),
                        'rating': business.get('rating') or 'N/A',
                        'review_count': business.get('review_count') or 0,
                        'latitude': business.get('latitude'),
                        'longitude': business.get('longitude'),
                        'image_url': business.get('image_url')
                    }
                    businesses_list.append(business_dict)
            
            logger.info(f"Fetched {len(businesses_list)} business details for IDs: {business_ids}")
            
            return jsonify({
                'status': 'success',
                'businesses': businesses_list
            })
    except Exception as e:
        logger.error(f"Error fetching businesses by IDs: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500