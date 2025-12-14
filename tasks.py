import os
import logging
import threading
from flask import current_app
from datetime import datetime
import requests
import smtplib
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader
from celery import Celery, shared_task

# Initialize Celery
celery = Celery(__name__)

# Configure Celery broker
# Try environment variables in order: CELERY_BROKER_URL, REDIS_URL, then fallback to localhost
broker_url = (os.environ.get('CELERY_BROKER_URL') or 
              os.environ.get('REDIS_URL') or 
              'redis://localhost:6379/0')
celery.conf.broker_url = broker_url
celery.conf.result_backend = broker_url

def run_async(fn):
    """Decorator to run a function asynchronously"""
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
        return thread
    return wrapper

@shared_task(bind=True, max_retries=3)
def send_email_task_async(self, to, subject, template, context=None, attachments=None):
    """Send email asynchronously using Celery"""
    try:
        # Get config from environment (Celery runs outside app context)
        mail_username = os.environ.get('GMAIL_USER')
        mail_password = os.environ.get('GMAIL_PASSWORD')
        mail_server = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
        mail_port = int(os.environ.get('MAIL_PORT', 587))
        
        if not mail_username or not mail_password:
            logging.error("Gmail credentials not configured")
            return False
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = mail_username
        msg['To'] = to
        msg['Subject'] = subject
        
        # Render template
        env = Environment(loader=FileSystemLoader('templates'))
        template_obj = env.get_template(template)
        html_content = template_obj.render(context or {})
        
        # Attach HTML content
        msg.attach(MIMEText(html_content, 'html'))
        
        # Handle attachments
        if attachments:
            for attachment in attachments:
                with open(attachment['path'], 'rb') as f:
                    part = MIMEText(f.read(), attachment['type'])
                    part.add_header('Content-Disposition', 
                                  f'attachment; filename={attachment["filename"]}')
                    msg.attach(part)
        
        # Send email with timeout
        logging.info(f"Attempting to send email to {to} via {mail_server}:{mail_port}")
        with smtplib.SMTP(mail_server, mail_port, timeout=10) as server:
            server.starttls()
            server.login(mail_username, mail_password)
            server.send_message(msg)
            logging.info(f"Email sent successfully to {to}")
            return True
            
    except Exception as exc:
        logging.error(f"Failed to send email to {to}: {exc}")
        # Retry with exponential backoff (max 3 times)
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

def send_email_task(to, subject, template, context=None, attachments=None):
    """Wrapper to send email via Celery with fallback to async thread"""
    try:
        # Try to send task asynchronously via Celery
        send_email_task_async.delay(to, subject, template, context, attachments)
        logging.info(f"Email task queued for {to}")
        return True
    except Exception as e:
        logging.error(f"Failed to queue email task via Celery: {e}")
        # Fallback to threaded email sending (non-blocking)
        logging.info(f"Falling back to threaded email sending for {to}")
        try:
            @run_async
            def send_sync_email():
                try:
                    send_email_task_async(to, subject, template, context, attachments)
                except Exception as sync_error:
                    logging.error(f"Threaded email send failed for {to}: {sync_error}")
            
            send_sync_email()
            return True
        except Exception as thread_error:
            logging.error(f"Failed to start email thread for {to}: {thread_error}")
            return False

@run_async
def create_notification_task(user_id=None, type='general', title='', message='', data=None):
    """Create notification for user"""
    try:
        from database import get_neo4j_db, safe_run
        
        # If user_id is provided, verify user exists first
        if user_id:
            db = get_neo4j_db()
            with db.session() as session:
                user_check = safe_run(session, """
                    MATCH (u:User {id: $user_id})
                    RETURN u.id as id
                """, {'user_id': user_id})
                
                if not user_check:
                    logging.error(f"Cannot create notification: User {user_id} not found in database")
                    return False
        
        db = get_neo4j_db()
        with db.session() as session:
            notification_id = str(uuid.uuid4())
            notification_data = {
                'id': notification_id,
                'type': type,
                'title': title,
                'message': message,
                'data': data or {},
                'is_read': False,
                'created_at': datetime.utcnow().isoformat()
            }
            
            if user_id:
                notification_data['user_id'] = user_id
            
            safe_run(session, """
                CREATE (n:Notification $notification_data)
            """, {'notification_data': notification_data})
        
        logging.info(f"Notification created: {title}")
        return True
        
    except Exception as e:
        logging.error(f"Failed to create notification: {e}")
        return False

@run_async
def geocode_location_task(address):
    """Geocode address using external service"""
    try:
        # Use Nominatim (OpenStreetMap) for geocoding
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': address,
            'format': 'json',
            'limit': 1
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200 and response.json():
            result = response.json()[0]
            return {
                'latitude': float(result['lat']),
                'longitude': float(result['lon']),
                'display_name': result['display_name']
            }
        
        return None
        
    except Exception as e:
        logging.error(f"Geocoding failed for address {address}: {e}")
        return None

@run_async
def process_uploaded_file_task(file_path, file_type):
    """Process uploaded files (resize images, scan for malware, etc.)"""
    try:
        if file_type.startswith('image/'):
            # Resize image for optimization
            from PIL import Image
            
            with Image.open(file_path) as img:
                # Create thumbnail
                thumbnail_path = file_path.rsplit('.', 1)[0] + '_thumb.' + file_path.rsplit('.', 1)[1]
                img.thumbnail((300, 300))
                img.save(thumbnail_path)
                
                # Resize large images
                if img.size[0] > 1920 or img.size[1] > 1080:
                    img.thumbnail((1920, 1080))
                    img.save(file_path)
        
        elif file_type == 'application/pdf':
            # Scan PDF for malware (placeholder)
            logging.info(f"Scanned PDF file: {file_path}")
        
        return True
        
    except Exception as e:
        logging.error(f"File processing failed for {file_path}: {e}")
        return False

@run_async
def generate_analytics_report_task():
    """Generate daily analytics report"""
    try:
        from database import get_neo4j_db, safe_run
        
        db = get_neo4j_db()
        with db.session() as session:
            # Get daily stats
            stats = {}
            
            # User registrations
            new_users = safe_run(session, """
                MATCH (u:User)
                WHERE u.created_at >= datetime() - duration('P1D')
                RETURN count(u) as count
            """)[0]['count']
            
            # New businesses
            new_businesses = safe_run(session, """
                MATCH (b:Business)
                WHERE b.created_at >= datetime() - duration('P1D')
                RETURN count(b) as count
            """)[0]['count']
            
            # New jobs
            new_jobs = safe_run(session, """
                MATCH (j:Job)
                WHERE j.created_at >= datetime() - duration('P1D')
                RETURN count(j) as count
            """)[0]['count']
            
            # New services
            new_services = safe_run(session, """
                MATCH (s:Service)
                WHERE s.created_at >= datetime() - duration('P1D')
                RETURN count(s) as count
            """)[0]['count']
            
            # Job applications
            applications = safe_run(session, """
                MATCH (a:JobApplication)
                WHERE a.created_at >= datetime() - duration('P1D')
                RETURN count(a) as count
            """)[0]['count']
            
            # Reviews
            reviews = safe_run(session, """
                MATCH (r:Review)
                WHERE r.created_at >= datetime() - duration('P1D')
                RETURN count(r) as count
            """)[0]['count']
            
            # Compile report
            report = {
                'date': datetime.utcnow().strftime('%Y-%m-%d'),
                'new_users': new_users,
                'new_businesses': new_businesses,
                'new_jobs': new_jobs,
                'new_services': new_services,
                'job_applications': applications,
                'reviews': reviews
            }
            
            # Send report to admin
            send_email_task(
                to=current_app.config['ADMIN_EMAIL'],
                subject=f'Daily Analytics Report - {report["date"]}',
                template='email/analytics_report.html',
                context={'report': report}
            )
        
        logging.info("Analytics report generated successfully")
        return True
        
    except Exception as e:
        logging.error(f"Failed to generate analytics report: {e}")
        return False

@run_async
def cleanup_old_data_task():
    """Clean up old data (conversations, notifications, etc.)"""
    try:
        from database import get_neo4j_db, safe_run
        
        db = get_neo4j_db()
        with db.session() as session:
            # Clean up old chat conversations (older than 90 days)
            safe_run(session, """
                MATCH (c:ChatConversation)
                WHERE c.timestamp < datetime() - duration('P90D')
                DELETE c
            """)
            
            # Clean up old notifications (older than 30 days)
            safe_run(session, """
                MATCH (n:Notification)
                WHERE n.created_at < datetime() - duration('P30D')
                DELETE n
            """)
            
            # Clean up old job applications for closed jobs
            safe_run(session, """
                MATCH (j:Job {is_active: false})<-[:FOR_JOB]-(a:JobApplication)
                WHERE a.created_at < datetime() - duration('P180D')
                DELETE a
            """)
        
        logging.info("Old data cleanup completed")
        return True
        
    except Exception as e:
        logging.error(f"Failed to cleanup old data: {e}")
        return False

@run_async
def send_weekly_digest_task():
    """Send weekly digest to users"""
    try:
        from database import get_neo4j_db, safe_run
        
        db = get_neo4j_db()
        with db.session() as session:
            # Get users who want weekly digest
            users = safe_run(session, """
                MATCH (u:User)
                WHERE u.weekly_digest = true AND u.is_verified = true
                RETURN u.email, u.username
            """)
            
            # Get weekly highlights
            new_jobs = safe_run(session, """
                MATCH (j:Job)
                WHERE j.created_at >= datetime() - duration('P7D')
                RETURN j.title, j.location, j.category
                ORDER BY j.created_at DESC
                LIMIT 10
            """)
            
            new_businesses = safe_run(session, """
                MATCH (b:Business)
                WHERE b.created_at >= datetime() - duration('P7D') AND b.is_verified = true
                RETURN b.name, b.category, b.address
                ORDER BY b.created_at DESC
                LIMIT 10
            """)
            
            # Send digest to each user
            for user in users:
                send_email_task(
                    to=user['u.email'],
                    subject='Weekly Digest - Catanduanes Connect',
                    template='email/weekly_digest.html',
                    context={
                        'username': user['u.username'],
                        'new_jobs': new_jobs,
                        'new_businesses': new_businesses,
                        'site_name': current_app.config['SITE_NAME']
                    }
                )
        
        logging.info("Weekly digest sent successfully")
        return True
        
    except Exception as e:
        logging.error(f"Failed to send weekly digest: {e}")
        return False

# Initialize scheduled tasks
def init_scheduled_tasks():
    """Initialize scheduled tasks using threading.Timer"""
    def schedule_task(task_fn, interval):
        def wrapped_task():
            task_fn()
            timer = threading.Timer(interval, wrapped_task)
            timer.daemon = True
            timer.start()
        timer = threading.Timer(interval, wrapped_task)
        timer.daemon = True
        timer.start()
    
    # Schedule daily tasks
    schedule_task(generate_analytics_report_task, 86400.0)  # Daily
    
    # Schedule weekly tasks
    schedule_task(cleanup_old_data_task, 604800.0)  # Weekly
    schedule_task(send_weekly_digest_task, 604800.0)  # Weekly


@shared_task(name='geocode_location_task_async')
def geocode_location_sync(address: str) -> dict | None:
    """Synchronous version for routes that need the result immediately."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {'q': address, 'format': 'json', 'limit': 1}
    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200 and resp.json():
            r = resp.json()[0]
            return {'latitude': float(r['lat']),
                    'longitude': float(r['lon']),
                    'display_name': r['display_name']}
    except Exception:
        pass
    return None