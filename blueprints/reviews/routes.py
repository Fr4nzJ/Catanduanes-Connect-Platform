"""
System Reviews Routes - Users can submit reviews and ratings about the platform
"""

import uuid
import logging
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from . import reviews_bp
from database import get_neo4j_db, safe_run, _node_to_dict
from decorators import role_required

logger = logging.getLogger(__name__)

# ============================================================================
# SYSTEM REVIEWS ROUTES
# ============================================================================

@reviews_bp.route('/reviews')
def list_reviews():
    """Display all system reviews with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    sort_by = request.args.get('sort', 'recent')  # recent, highest_rated, helpful
    
    db = get_neo4j_db()
    
    with db.session() as session:
        # Build query based on sort preference
        if sort_by == 'highest_rated':
            order_by = "r.rating DESC"
        elif sort_by == 'helpful':
            order_by = "r.helpful_count DESC"
        else:  # recent
            order_by = "r.created_at DESC"
        
        # Get total count
        count_result = safe_run(session, """
            MATCH (r:SystemReview)
            RETURN count(r) as total
        """)
        total = count_result[0]['total'] if count_result else 0
        
        # Get reviews with user information
        reviews_result = safe_run(session, f"""
            MATCH (r:SystemReview)
            MATCH (u:User)-[:SUBMITTED]->(r)
            RETURN r, u.username as username, u.id as user_id
            ORDER BY {order_by}
            SKIP $skip
            LIMIT $limit
        """, {'skip': (page - 1) * per_page, 'limit': per_page})
        
        reviews = []
        if reviews_result:
            for record in reviews_result:
                review_data = _node_to_dict(record['r'])
                review_data['username'] = record['username']
                review_data['user_id'] = record['user_id']
                reviews.append(review_data)
        
        # Calculate pagination
        total_pages = (total + per_page - 1) // per_page
        
        return render_template('reviews/list_reviews.html',
                             reviews=reviews,
                             page=page,
                             total_pages=total_pages,
                             total=total,
                             sort_by=sort_by)


@reviews_bp.route('/reviews/submit', methods=['GET', 'POST'])
@login_required
def submit_review():
    """Submit a new system review (non-admin users only)"""
    
    # Prevent admins from submitting reviews
    if current_user.role == 'admin':
        flash('Admins cannot submit reviews about the system.', 'warning')
        return redirect(url_for('reviews.list_reviews'))
    
    if request.method == 'POST':
        rating = request.form.get('rating', type=int)
        comment = request.form.get('comment', '').strip()
        
        # Validation
        if not rating or rating < 1 or rating > 5:
            flash('Please provide a rating between 1 and 5 stars.', 'error')
            return redirect(url_for('reviews.submit_review'))
        
        if not comment or len(comment) < 10:
            flash('Please provide a comment with at least 10 characters.', 'error')
            return redirect(url_for('reviews.submit_review'))
        
        if len(comment) > 1000:
            flash('Comment must not exceed 1000 characters.', 'error')
            return redirect(url_for('reviews.submit_review'))
        
        db = get_neo4j_db()
        review_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat()
        
        try:
            with db.session() as session:
                # Create the SystemReview node
                result = safe_run(session, """
                    CREATE (r:SystemReview {
                        id: $id,
                        rating: $rating,
                        comment: $comment,
                        created_at: $created_at,
                        helpful_count: 0,
                        status: 'active'
                    })
                    RETURN r
                """, {
                    'id': review_id,
                    'rating': rating,
                    'comment': comment,
                    'created_at': created_at
                })
                
                if result:
                    # Create relationship from user to review
                    safe_run(session, """
                        MATCH (u:User {id: $user_id})
                        MATCH (r:SystemReview {id: $review_id})
                        CREATE (u)-[:SUBMITTED]->(r)
                    """, {
                        'user_id': current_user.id,
                        'review_id': review_id
                    })
                    
                    flash('Your review has been submitted successfully! Thank you for your feedback.', 'success')
                    logger.info(f"User {current_user.id} submitted a system review with {rating} stars")
                    return redirect(url_for('reviews.list_reviews'))
                else:
                    flash('Error submitting review. Please try again.', 'error')
                    
        except Exception as e:
            logger.error(f"Error submitting review: {str(e)}")
            flash('An error occurred while submitting your review.', 'error')
        
        return redirect(url_for('reviews.submit_review'))
    
    return render_template('reviews/submit_review.html')


@reviews_bp.route('/reviews/<review_id>/helpful', methods=['POST'])
@login_required
def mark_helpful(review_id):
    """Mark a review as helpful"""
    db = get_neo4j_db()
    
    try:
        with db.session() as session:
            # Check if user already marked this as helpful
            check_result = safe_run(session, """
                MATCH (u:User {id: $user_id})-[:FOUND_HELPFUL]->(r:SystemReview {id: $review_id})
                RETURN count(*) as count
            """, {
                'user_id': current_user.id,
                'review_id': review_id
            })
            
            if check_result and check_result[0]['count'] > 0:
                return jsonify({'success': False, 'message': 'You already marked this as helpful'}), 400
            
            # Mark as helpful
            result = safe_run(session, """
                MATCH (u:User {id: $user_id})
                MATCH (r:SystemReview {id: $review_id})
                CREATE (u)-[:FOUND_HELPFUL]->(r)
                SET r.helpful_count = r.helpful_count + 1
                RETURN r.helpful_count as helpful_count
            """, {
                'user_id': current_user.id,
                'review_id': review_id
            })
            
            if result:
                helpful_count = result[0]['helpful_count']
                return jsonify({'success': True, 'helpful_count': helpful_count}), 200
            else:
                return jsonify({'success': False, 'message': 'Review not found'}), 404
                
    except Exception as e:
        logger.error(f"Error marking review as helpful: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred'}), 500


@reviews_bp.route('/reviews/<review_id>/delete', methods=['POST'])
@login_required
def delete_review(review_id):
    """Delete a review (review author or admin only)"""
    db = get_neo4j_db()
    
    try:
        with db.session() as session:
            # Get review and check ownership
            review_result = safe_run(session, """
                MATCH (u:User)-[:SUBMITTED]->(r:SystemReview {id: $review_id})
                RETURN r, u.id as user_id
            """, {'review_id': review_id})
            
            if not review_result:
                flash('Review not found.', 'error')
                return redirect(url_for('reviews.list_reviews'))
            
            user_id = review_result[0]['user_id']
            
            # Check if user owns the review or is admin
            if current_user.id != user_id and current_user.role != 'admin':
                flash('You do not have permission to delete this review.', 'error')
                return redirect(url_for('reviews.list_reviews'))
            
            # Delete the review and its relationships
            safe_run(session, """
                MATCH (r:SystemReview {id: $review_id})
                DETACH DELETE r
            """, {'review_id': review_id})
            
            flash('Review deleted successfully.', 'success')
            logger.info(f"Review {review_id} deleted by user {current_user.id}")
            
    except Exception as e:
        logger.error(f"Error deleting review: {str(e)}")
        flash('An error occurred while deleting the review.', 'error')
    
    return redirect(url_for('reviews.list_reviews'))


@reviews_bp.route('/api/reviews/stats')
def get_reviews_stats():
    """Get system reviews statistics"""
    db = get_neo4j_db()
    
    try:
        with db.session() as session:
            stats_result = safe_run(session, """
                MATCH (r:SystemReview)
                RETURN 
                    count(r) as total_reviews,
                    round(avg(r.rating), 1) as average_rating,
                    max(r.rating) as highest_rating,
                    min(r.rating) as lowest_rating,
                    sum(CASE WHEN r.rating = 5 THEN 1 ELSE 0 END) as five_stars,
                    sum(CASE WHEN r.rating = 4 THEN 1 ELSE 0 END) as four_stars,
                    sum(CASE WHEN r.rating = 3 THEN 1 ELSE 0 END) as three_stars,
                    sum(CASE WHEN r.rating = 2 THEN 1 ELSE 0 END) as two_stars,
                    sum(CASE WHEN r.rating = 1 THEN 1 ELSE 0 END) as one_star
            """)
            
            if stats_result:
                stats = stats_result[0]
                return jsonify({
                    'total_reviews': stats['total_reviews'] or 0,
                    'average_rating': stats['average_rating'] or 0,
                    'highest_rating': stats['highest_rating'] or 0,
                    'lowest_rating': stats['lowest_rating'] or 0,
                    'five_stars': stats['five_stars'] or 0,
                    'four_stars': stats['four_stars'] or 0,
                    'three_stars': stats['three_stars'] or 0,
                    'two_stars': stats['two_stars'] or 0,
                    'one_star': stats['one_star'] or 0
                }), 200
            else:
                return jsonify({'error': 'No data'}), 404
                
    except Exception as e:
        logger.error(f"Error getting reviews stats: {str(e)}")
        return jsonify({'error': 'An error occurred'}), 500
