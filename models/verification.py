from datetime import datetime

class Verification:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.user_id = kwargs.get('user_id')
        self.document_type = kwargs.get('document_type')
        self.file_path = kwargs.get('file_path')
        self.status = kwargs.get('status', 'pending')
        self.submitted_at = kwargs.get('submitted_at', datetime.utcnow().isoformat())
        self.reviewed_at = kwargs.get('reviewed_at')
        self.reviewer_id = kwargs.get('reviewer_id')
        self.reviewer_notes = kwargs.get('reviewer_notes')
        self.verification_type = kwargs.get('verification_type')  # business, job_seeker, service_provider

    @staticmethod
    def create_verification(session, user_id, document_type, file_path, verification_type):
        """Create a new verification record in Neo4j"""
        verification_id = str(uuid.uuid4())
        verification_data = {
            'id': verification_id,
            'user_id': user_id,
            'document_type': document_type,
            'file_path': file_path,
            'status': 'pending',
            'submitted_at': datetime.utcnow().isoformat(),
            'verification_type': verification_type
        }
        
        session.run("""
            MATCH (u:User {id: $user_id})
            CREATE (v:Verification $verification_data)
            CREATE (u)-[:SUBMITTED]->(v)
        """, {'user_id': user_id, 'verification_data': verification_data})
        
        return verification_id

    @staticmethod
    def get_user_verifications(session, user_id):
        """Get all verifications for a user"""
        result = session.run("""
            MATCH (u:User {id: $user_id})-[:SUBMITTED]->(v:Verification)
            RETURN v ORDER BY v.submitted_at DESC
        """, {'user_id': user_id})
        
        verifications = []
        for record in result:
            verification_data = record['v']
            verifications.append(Verification(**verification_data))
        
        return verifications

    @staticmethod
    def update_status(session, verification_id, status, reviewer_id=None, notes=None):
        """Update verification status"""
        update_data = {
            'verification_id': verification_id,
            'status': status,
            'reviewed_at': datetime.utcnow().isoformat(),
            'reviewer_id': reviewer_id,
            'reviewer_notes': notes
        }
        
        session.run("""
            MATCH (v:Verification {id: $verification_id})
            SET v.status = $status,
                v.reviewed_at = $reviewed_at,
                v.reviewer_id = $reviewer_id,
                v.reviewer_notes = $reviewer_notes
        """, update_data)