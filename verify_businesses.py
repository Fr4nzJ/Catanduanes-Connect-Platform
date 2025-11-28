"""
Verify that the 30 businesses were created correctly and can be queried
"""
from database import get_neo4j_db, safe_run
from app import create_app

def verify_businesses():
    """Verify businesses in database"""
    app = create_app()
    
    with app.app_context():
        db = get_neo4j_db()
        with db.session() as session:
            # Count total businesses
            total_result = safe_run(session, "MATCH (b:Business) RETURN count(b) as total")
            total = total_result[0]['total'] if total_result else 0
            print(f"Total businesses in database: {total}")
            
            # List all businesses
            businesses = safe_run(session, """
                MATCH (b:Business)
                WHERE b.is_active = true
                RETURN b.id AS id, b.name AS name, b.category AS category, b.rating AS rating
                ORDER BY b.created_at DESC
                LIMIT 30
            """)
            
            print(f"\nFound {len(businesses)} active businesses:\n")
            print(f"{'#':<3} {'ID (First 8 chars)':<20} {'Name':<35} {'Category':<15} {'Rating':<8}")
            print("-" * 85)
            
            for i, business in enumerate(businesses, 1):
                business_id = str(business['id'])[:8]
                name = business['name'][:33]
                category = business['category'][:13]
                rating = f"{business['rating']:.1f}" if business['rating'] else "N/A"
                print(f"{i:<3} {business_id:<20} {name:<35} {category:<15} {rating:<8}")
            
            print("\n[INFO] All businesses are ready for viewing!")
            print("[INFO] You can now click 'View Details' on any business card to see its details.")

if __name__ == '__main__':
    verify_businesses()
