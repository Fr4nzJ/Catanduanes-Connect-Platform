#!/usr/bin/env python3
"""
Mark top-rated businesses as featured
"""
import logging
from app import create_app
from database import get_neo4j_db, safe_run

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def mark_featured_businesses():
    """Mark the top 6-8 highest-rated verified businesses as featured"""
    app = create_app()
    with app.app_context():
        db = get_neo4j_db()
    
    with app.app_context():
        db = get_neo4j_db()
        
        with db.session() as session:
            # Get top 8 highest-rated verified businesses
            query = """
                MATCH (b:Business)
                WHERE b.is_active = true AND b.is_verified = true
                ORDER BY b.rating DESC, b.review_count DESC
                LIMIT 8
                RETURN b.id as id, b.name as name, b.rating as rating
            """
            
            results = safe_run(session, query, {})
            logger.info(f"Found {len(results)} top-rated businesses to feature")
            
            if not results:
                logger.warning("No verified businesses found to mark as featured!")
                return 0
            
            # Mark them as featured
            featured_count = 0
            for record in results:
                business_id = record['id']
                business_name = record['name']
                business_rating = record['rating']
                
                update_query = """
                    MATCH (b:Business {id: $business_id})
                    SET b.is_featured = true
                    RETURN b.id, b.name
                """
                
                update_result = safe_run(session, update_query, {'business_id': business_id})
                if update_result:
                    logger.info(f"✓ Marked as featured: {business_name} (Rating: {business_rating})")
                    featured_count += 1
            
            logger.info(f"\n✅ Successfully marked {featured_count} businesses as featured!")
            return featured_count

if __name__ == '__main__':
    mark_featured_businesses()
