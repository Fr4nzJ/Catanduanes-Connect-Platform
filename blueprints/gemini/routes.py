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

            # Get all available jobs sorted by salary
            jobs_data = safe_run(session, """
                MATCH (j:Job)
                WHERE j.salary_max IS NOT NULL
                RETURN j.id as id, j.title as title, j.salary_min as salary_min, 
                       j.salary_max as salary_max, j.category as category
                ORDER BY j.salary_max DESC
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

