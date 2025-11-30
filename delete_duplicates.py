#!/usr/bin/env python3
"""Delete duplicate businesses, keeping only the newer ones"""
from app import create_app
from database import get_neo4j_db, safe_run

app = create_app()
with app.app_context():
    db = get_neo4j_db()
    with db.session() as session:
        # Get all businesses owned by user
        result = safe_run(session, '''
            MATCH (u:User {id: "aba99b14-2236-44a9-92ef-864446009e5e"})-[:OWNS]->(b:Business)
            RETURN b.id as id, b.name as name, b.created_at as created_at
            ORDER BY b.name, b.created_at DESC
        ''')
        
        # Group by name and find duplicates to delete
        from collections import defaultdict
        businesses_by_name = defaultdict(list)
        for rec in result:
            businesses_by_name[rec['name']].append(rec)
        
        to_delete = []
        for name, businesses in businesses_by_name.items():
            if len(businesses) > 1:
                # Keep the latest (last in sorted list), delete the others
                for biz in businesses[1:]:
                    to_delete.append(biz['id'])
                    print(f"Marking for deletion: {name} ({biz['id']})")
        
        # Delete marked businesses
        if to_delete:
            print(f"\nDeleting {len(to_delete)} duplicate businesses...")
            for biz_id in to_delete:
                safe_run(session, "MATCH (b:Business {id: $id}) DETACH DELETE b", {"id": biz_id})
            print("Deletion complete!")
        else:
            print("No duplicates found")
        
        # Verify
        result = safe_run(session, '''
            MATCH (u:User {id: "aba99b14-2236-44a9-92ef-864446009e5e"})-[:OWNS]->(b:Business)
            RETURN COUNT(DISTINCT b.id) as count
        ''')
        print(f"\nBusinesses now: {result[0]['count'] if result else 0}")
