from app import create_app
from database import get_neo4j_db, safe_run

app = create_app()
with app.app_context():
    db = get_neo4j_db()
    with db.session() as session:
        result = safe_run(session, 'MATCH (b:Business) WHERE b.is_active = true RETURN b.id as id, b.name as name LIMIT 5')
        print("Sample Business IDs from database:")
        for i, record in enumerate(result, 1):
            print(f"{i}. ID Type: {type(record['id']).__name__} | ID: {record['id']}")
            print(f"   Name: {record['name']}")
