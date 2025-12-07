"""Test the actual users_management query"""
from app import create_app
from database import get_neo4j_db, safe_run

app = create_app('development')

with app.app_context():
    db = get_neo4j_db()
    
    with db.session() as session:
        # Simulate the exact code from users_management()
        query = "MATCH (u:User) WHERE 1=1"
        params = {}
        
        sort_by = 'created_at'
        sort_order = 'desc'
        page = 1
        per_page = 20
        
        # Add the ORDER BY, SKIP, LIMIT (without any filters)
        sort_field = f"u.{sort_by}"
        query += f" RETURN u ORDER BY {sort_field} {sort_order.upper()}"
        query += f" SKIP {(page - 1) * per_page} LIMIT {per_page}"
        
        print(f"Query: {query}")
        print()
        
        result = safe_run(session, query, params)
        users = [record['u'] for record in (result or [])]
        
        print(f"Result count: {len(result) if result else 0}")
        print(f"Users count: {len(users)}")
        
        if users:
            print()
            print(f"First user: {users[0]}")
            print(f"Type: {type(users[0])}")
            if 'username' in users[0]:
                print(f"Username: {users[0]['username']}")
                print(f"Username attr: {users[0].username}")
                print(f"First char: {users[0].username[0]}")
                print(f"First char upper: {users[0].username[0].upper()}")
            else:
                print("ERROR: No username field!")
                print(f"Keys: {list(users[0].keys())}")
