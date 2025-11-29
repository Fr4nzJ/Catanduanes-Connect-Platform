import random
import datetime
from flask import current_app
from database import get_neo4j_db, safe_run
from tasks import send_email_task

# ---------- core helpers ----------
def generate_otp(length: int = 6) -> str:
    return f"{random.randint(0, 10**length - 1):06d}"

def save_otp(user_id: str, otp: str, is_phone: bool = False, ttl: int = 10):
    """Save OTP (email or phone) on user node"""
    expires = (datetime.datetime.utcnow() + datetime.timedelta(minutes=ttl)).isoformat()
    with get_neo4j_db().session() as s:
        if is_phone:
            safe_run(s, """MATCH (u:User {id: $uid})
                           SET u.phone_otp = $otp,
                               u.phone_otp_expires = $exp""",
                    {"uid": user_id, "otp": otp, "exp": expires})
        else:
            safe_run(s, """MATCH (u:User {id: $uid})
                           SET u.email_otp = $otp,
                               u.email_otp_expires = $exp""",
                    {"uid": user_id, "otp": otp, "exp": expires})

def verify_otp(user_id: str, otp: str, is_phone: bool = False) -> bool:
    """Check OTP, mark with pending verification status if correct"""
    with get_neo4j_db().session() as s:
        rec = safe_run(s, f"""MATCH (u:User {{id: $uid}})
                              WHERE u.{'phone' if is_phone else 'email'}_otp = $otp
                                AND datetime(u.{'phone' if is_phone else 'email'}_otp_expires) > datetime()
                              RETURN u.id""", {"uid": user_id, "otp": otp})
        if not rec:
            return False
        safe_run(s, """MATCH (u:User {id: $uid})
                       SET u.verification_status = 'pending'
                       REMOVE u.email_otp, u.phone_otp, u.email_otp_expires, u.phone_otp_expires""",
                {"uid": user_id})
        return True

def send_sms(phone: str, code: str):
    """Send OTP via Semaphore SMS API"""
    try:
        import requests
        
        # Semaphore API configuration
        api_key = "5dc45caa4475c0e877cdfda343b04ed0"
        semaphore_url = "https://api.semaphore.co/api/v4/messages"
        
        # Format phone number for Semaphore (remove + for Philippine numbers)
        if phone.startswith('+63'):
            phone = '0' + phone[3:]  # Convert +63 to 0
        elif not phone.startswith('0'):
            phone = '0' + phone[2:]  # Convert 63 to 0
            
        # Prepare the message payload
        payload = {
            'apikey': api_key,
            'number': phone,
            'message': f"Your Catanduanes Connect verification code is: {code}",
            'sendername': 'CatConnect'
        }
        
        # Send the SMS
        response = requests.post(semaphore_url, data=payload)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Log success
        current_app.logger.info(f"SMS sent successfully to {phone}")
        return True
        
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Failed to send SMS to {phone}: {str(e)}")
        if hasattr(e.response, 'text'):
            current_app.logger.error(f"Semaphore API response: {e.response.text}")
        raise
    except Exception as e:
        current_app.logger.error(f"Failed to send SMS to {phone}: {str(e)}")
        raise

# ---------- convenience wrappers ----------
def save_email_otp(user_id: str, otp: str, ttl: int = 10):
    """Convenience wrapper for saving email OTP"""
    save_otp(user_id, otp, is_phone=False, ttl=ttl)

def save_phone_otp(user_id: str, otp: str, ttl: int = 10):
    """Convenience wrapper for saving phone OTP"""
    save_otp(user_id, otp, is_phone=True, ttl=ttl)

def verify_email_otp(user_id: str, otp: str) -> bool:
    """Convenience wrapper for verifying email OTP"""
    return verify_otp(user_id, otp, is_phone=False)

def verify_phone_otp(user_id: str, otp: str) -> bool:
    """Convenience wrapper for verifying phone OTP"""
    return verify_otp(user_id, otp, is_phone=True)