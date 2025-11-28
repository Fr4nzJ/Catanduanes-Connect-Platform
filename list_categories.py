#!/usr/bin/env python3
"""
List all categories and their statistics
"""
from app import create_app
from database import get_neo4j_db, safe_run

app = create_app()
with app.app_context():
    db = get_neo4j_db()
    with db.session() as session:
        # Get all unique categories with stats
        query = """
            MATCH (b:Business)
            WHERE b.is_active = true
            WITH b.category as category, COUNT(b) as count, AVG(b.rating) as avg_rating, COUNT(CASE WHEN b.is_verified THEN 1 END) as verified_count
            RETURN category, count, avg_rating, verified_count
            ORDER BY count DESC
        """
        
        results = safe_run(session, query, {})
        
        print("\n=== Business Categories ===\n")
        print(f"{'Category':<20} {'Count':<8} {'Avg Rating':<12} {'Verified':<10}")
        print("-" * 50)
        
        for record in results:
            category = record['category'] or 'Unknown'
            count = record['count']
            avg_rating = f"{record['avg_rating']:.2f}" if record['avg_rating'] else "N/A"
            verified = record['verified_count']
            
            print(f"{category:<20} {count:<8} {avg_rating:<12} {verified:<10}")
        
        print("\n" + "=" * 50 + "\n")
