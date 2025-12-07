"""Test safe_run return structure"""
from app import create_app
from database import get_neo4j_db, safe_run

app = create_app('development')

with app.app_context():
    db = get_neo4j_db()
    
    with db.session() as session:
        # Test what safe_run returns
        query = "MATCH (u:User) RETURN u LIMIT 1"
        result = safe_run(session, query)
        
        print("=" * 60)
        print("safe_run result:")
        print("=" * 60)
        print(f"type(result) = {type(result)}")
        print(f"result = {result}")
        
        if result:
            print()
            print("=" * 60)
            print("First item in result:")
            print("=" * 60)
            first_item = result[0]
            print(f"type(first_item) = {type(first_item)}")
            print(f"first_item = {first_item}")
            print(f"first_item.keys() = {list(first_item.keys())}")
            
            print()
            print("=" * 60)
            print("Accessing result[0]['u']:")
            print("=" * 60)
            user = first_item['u']
            print(f"type(user) = {type(user)}")
            print(f"user = {user}")
            if user:
                print(f"'username' in user = {'username' in user}")
                if 'username' in user:
                    print(f"user['username'] = {user['username']}")
                    print(f"user.username = {user.username}")
                else:
                    print(f"user.keys() = {list(user.keys())}")
            
            print()
            print("=" * 60)
            print("What our code extracts:")
            print("=" * 60)
            users = [record['u'] for record in result]
            print(f"users = {users}")
            if users:
                print(f"users[0] = {users[0]}")
                print(f"type(users[0]) = {type(users[0])}")
                if isinstance(users[0], dict):
                    print(f"'username' in users[0] = {'username' in users[0]}")
                    if 'username' in users[0]:
                        print(f"users[0].username = {users[0].username}")
                        print(f"users[0].username[0].upper() = {users[0].username[0].upper()}")
