import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Suppress the Gemini warning
os.environ['SUPPRESS_GEMINI_WARNING'] = '1'

from app import app
from database import get_neo4j_db, safe_run

with app.app_context():
    session = get_neo4j_db()

    # Update user verification
    result = safe_run(session, '''
        MATCH (u:User {id: $user_id})
        SET u.is_verified = true,
            u.verification_status = 'approved',
            u.verified_at = datetime()
        RETURN u.username, u.email, u.is_verified, u.verification_status
    ''', {
        'user_id': 'aba99b14-2236-44a9-92ef-864446009e5e'
    })

    if result:
        user = result[0]
        print('✅ User verification completed:')
        print(f'   Username: {user["u.username"]}')
        print(f'   Email: {user["u.email"]}')
        print(f'   Verified: {user["u.is_verified"]}')
        print(f'   Status: {user["u.verification_status"]}')
    else:
        print('User not found')
