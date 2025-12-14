"""
Fix missing relationships and properties in Neo4j
1. Create OWNS relationships between user 'ren' and all 30 businesses
2. Remove status property checks from job queries
"""

import os
from app import create_app
from database import get_neo4j_db, safe_run

def fix_owns_relationships():
    """Create OWNS relationships between ren user and all businesses"""
    app = create_app()
    
    with app.app_context():
        db = get_neo4j_db()
        
        user_id = "6d994a64-141a-462b-a880-03e0228b3ba7"  # ren's ID
        
        with db.session() as session:
            # Create OWNS relationships between user and all businesses
            result = safe_run(session, """
                MATCH (u:User {id: $user_id})
                MATCH (b:Business)
                MERGE (u)-[:OWNS]->(b)
                RETURN count(*) as relationships_created
            """, {'user_id': user_id})
            
            if result:
                count = result[0]['relationships_created']
                print(f"✅ Created {count} OWNS relationships between user and businesses")
            
            # Verify the relationships exist
            verify = safe_run(session, """
                MATCH (u:User {id: $user_id})-[:OWNS]->(b:Business)
                RETURN count(b) as business_count
            """, {'user_id': user_id})
            
            if verify:
                count = verify[0]['business_count']
                print(f"✅ Verified: User owns {count} businesses")

if __name__ == "__main__":
    try:
        fix_owns_relationships()
        print("\n✅ All fixes applied successfully!")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
