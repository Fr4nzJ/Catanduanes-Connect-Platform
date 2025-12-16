# Interview Scheduling Feature - Complete Implementation Guide

## Overview
The interview scheduling feature allows business owners to schedule interviews with accepted job applicants (online via Google Meet or onsite). Job seekers can then view, accept, or decline interview invitations.

## Components Implemented

### 1. Backend Routes (`blueprints/jobs/routes.py`)

#### Route 1: Schedule Interview
- **Endpoint**: `POST /applicant/<application_id>/schedule-interview`
- **Authentication**: `@login_required`, `@role_required('business_owner')`
- **Purpose**: Business owner schedules an interview for an accepted application
- **Input Parameters**:
  - `interview_type`: 'online' or 'onsite' (required)
  - `interview_date`: Date in YYYY-MM-DD format (required)
  - `interview_time`: Time in HH:MM format (required)
  - `instructions`: Optional additional instructions
  - **If online**:
    - `google_meet_link`: Google Meet URL (optional - can be auto-generated)
  - **If onsite**:
    - `location`: Interview location address (required)
    - `contact_person`: Name of interviewer (required)
    - `contact_phone`: Phone number (required)
- **Response**: JSON with `success: true/false` and interview_id
- **Database Operations**:
  - Verifies application exists and is accepted
  - Creates Interview node with appropriate fields
  - Creates relationships: `JobApplication -[:HAS_INTERVIEW]-> Interview`
  - Creates relationships: `User -[:INVITED_TO]-> Interview`
  - Sends email notification to applicant
- **Error Handling**: Returns 403 if unauthorized, 500 on database error

#### Route 2: View My Interviews
- **Endpoint**: `GET /my-interviews`
- **Authentication**: `@login_required`
- **Purpose**: Job seeker views all interview invitations
- **Query**:
  ```cypher
  MATCH (u:User {id: $user_id})-[:INVITED_TO]->(i:Interview)
  MATCH (i)-[:HAS_INTERVIEW]-(a:JobApplication)-[:FOR_JOB]->(j:Job)
  MATCH (j)-[:POSTED_BY]->(b:Business)
  MATCH (b)<-[:OWNS]-(owner:User)
  RETURN i, a, j, b, owner
  ORDER BY i.interview_datetime DESC
  ```
- **Returns**: Rendered template with interview list, job details, and business info
- **Template**: `interviews/my_interviews.html`

#### Route 3: Accept Interview
- **Endpoint**: `POST /interview/<interview_id>/accept`
- **Authentication**: `@login_required`
- **Purpose**: Job seeker accepts interview invitation
- **Database Operations**:
  - Updates Interview node: `status = 'accepted'`, `applicant_response = 'accepted'`
  - Sets `response_date` to current datetime
- **Response**: JSON with success/error message

#### Route 4: Reject Interview
- **Endpoint**: `POST /interview/<interview_id>/reject`
- **Authentication**: `@login_required`
- **Purpose**: Job seeker declines interview invitation
- **Input Parameters**:
  - `rejection_reason`: Optional reason for declining
- **Database Operations**:
  - Updates Interview node: `status = 'rejected'`, `applicant_response = 'rejected'`
  - Stores `rejection_reason` and `response_date`
- **Response**: JSON with success/error message

### 2. Neo4j Data Model

#### Interview Node Structure
```
Interview {
  id: string (UUID),
  type: string ('online' | 'onsite'),
  interview_datetime: string (ISO 8601 format),
  status: string ('scheduled' | 'accepted' | 'rejected' | 'completed'),
  created_at: datetime,
  updated_at: datetime,
  
  // For online interviews
  google_meet_link: string (optional),
  
  // For onsite interviews
  location: string (optional),
  contact_person: string (optional),
  contact_phone: string (optional),
  
  // Common optional fields
  instructions: string (optional),
  applicant_response: string ('accepted' | 'rejected' | null),
  response_date: datetime (optional),
  rejection_reason: string (optional)
}
```

#### Interview Relationships
```
JobApplication -[:HAS_INTERVIEW]-> Interview
User -[:INVITED_TO]-> Interview
```

### 3. Frontend Templates

#### Template 1: Interview Scheduling Modal
- **File**: `templates/jobs/applicant_profile.html`
- **Location**: Added to applicant profile page
- **Visibility**: Shows only when application status is 'accepted'
- **Features**:
  - Radio buttons to select interview type (Online/Onsite)
  - Common fields: Date, Time, Instructions
  - Conditional fields based on interview type:
    - **Online**: Google Meet link input
    - **Onsite**: Location, Contact Person, Contact Phone
  - Form submission via AJAX to `/applicant/<id>/schedule-interview`
  - Dynamic field toggling based on interview type
  - Success/error notifications

#### Template 2: Job Seeker Interviews List
- **File**: `templates/interviews/my_interviews.html`
- **Purpose**: Display all interview invitations for job seeker
- **Features**:
  - Interview status badges (Pending, Accepted, Rejected, Completed)
  - Interview type icons (Online/Onsite)
  - Interview details with date/time formatting
  - Type-specific information display:
    - **Online**: Google Meet link with join button
    - **Onsite**: Location, contact person, contact phone
  - Accept/Reject action buttons
  - Response tracking with response date display
  - Empty state with call-to-action to browse jobs

#### Template 3: Interview Status Display
- **File**: `templates/jobs/applicant_profile.html`
- **Location**: Added to applicant profile page
- **Visibility**: Shows when interview is scheduled
- **Features**:
  - Interview status indicator
  - Interview type display
  - Date and time
  - Type-specific details (Meet link or location/contact info)
  - Instructions display
  - Applicant response status and timestamp

### 4. Email Notifications

#### Email Template 1: Online Interview Notification
- **File**: `templates/email/interview_scheduled_online.html`
- **Subject**: "Interview Scheduled for {job_title}"
- **Triggers**: When business owner schedules online interview
- **Content**:
  - Interview details (position, date, time)
  - Google Meet link
  - Next steps instructions
  - Call-to-action button to view interview details
  - Professional HTML email template with branding

#### Email Template 2: Onsite Interview Notification
- **File**: `templates/email/interview_scheduled_onsite.html`
- **Subject**: "Interview Scheduled for {job_title}"
- **Triggers**: When business owner schedules onsite interview
- **Content**:
  - Interview details (position, date, time, location)
  - Contact information (interviewer name and phone)
  - Interview tips for candidates
  - Next steps instructions
  - Call-to-action button to view interview details
  - Professional HTML email template with branding

### 5. JavaScript Functionality

#### Modal Management
- `showScheduleInterviewModal()`: Opens interview scheduling modal
- `closeScheduleInterviewModal()`: Closes interview scheduling modal
- `toggleInterviewTypeFields()`: Shows/hides fields based on interview type selection
- `showRejectReasonModal(interviewId)`: Opens rejection reason modal
- `closeRejectReasonModal()`: Closes rejection reason modal

#### Form Submission
- Interview scheduling form submission via fetch API
- Automatic form data handling for both online/onsite types
- Error handling with user feedback
- Page reload on success

#### Interview Management (My Interviews Page)
- `acceptInterview(interviewId)`: Submit accept interview form
- `showRejectReasonModal(interviewId)`: Show rejection modal with optional reason
- Form submission for rejection via fetch API

## API Endpoints Summary

| Method | Endpoint | Purpose | Auth | Response |
|--------|----------|---------|------|----------|
| POST | `/applicant/<id>/schedule-interview` | Schedule interview | Business Owner | JSON |
| GET | `/my-interviews` | View interviews | Job Seeker | HTML |
| POST | `/interview/<id>/accept` | Accept invitation | Job Seeker | JSON |
| POST | `/interview/<id>/reject` | Reject invitation | Job Seeker | JSON |

## User Flow

### Business Owner Flow
1. Business owner views applicant profile (after accepting application)
2. Clicks "Schedule Interview" button (visible only for accepted applications)
3. Modal opens with interview type selection
4. Fills in details:
   - Interview date and time
   - Interview type (Online or Onsite)
   - Type-specific information
   - Optional instructions
5. Submits form
6. Interview created in database
7. Email notification sent to applicant
8. Success notification displayed

### Job Seeker Flow
1. Job seeker receives email with interview invitation
2. Logs into platform and visits "My Interview Invitations"
3. Sees list of all scheduled interviews
4. Reviews interview details:
   - Date/time
   - Interview type
   - Location (if onsite) or Meet link (if online)
   - Contact information
5. Accepts or rejects interview
6. If accepting: can join Google Meet (if online)
7. If rejecting: can provide optional reason

## Database Queries

### Create Interview (Online)
```cypher
CREATE (i:Interview {
  id: $interview_id,
  type: 'online',
  interview_datetime: $interview_datetime,
  google_meet_link: $google_meet_link,
  instructions: $instructions,
  status: 'scheduled',
  created_at: datetime(),
  updated_at: datetime()
})
CREATE (a)-[:HAS_INTERVIEW]->(i)
CREATE (applicant)-[:INVITED_TO]->(i)
```

### Create Interview (Onsite)
```cypher
CREATE (i:Interview {
  id: $interview_id,
  type: 'onsite',
  interview_datetime: $interview_datetime,
  location: $location,
  contact_person: $contact_person,
  contact_phone: $contact_phone,
  instructions: $instructions,
  status: 'scheduled',
  created_at: datetime(),
  updated_at: datetime()
})
CREATE (a)-[:HAS_INTERVIEW]->(i)
CREATE (applicant)-[:INVITED_TO]->(i)
```

### Get Interviews for User
```cypher
MATCH (u:User {id: $user_id})-[:INVITED_TO]->(i:Interview)
MATCH (i)-[:HAS_INTERVIEW]-(a:JobApplication)-[:FOR_JOB]->(j:Job)
MATCH (j)-[:POSTED_BY]->(b:Business)
MATCH (b)<-[:OWNS]-(owner:User)
RETURN i, a, j, b, owner
ORDER BY i.interview_datetime DESC
```

### Update Interview Status
```cypher
MATCH (u:User {id: $user_id})-[:INVITED_TO]->(i:Interview {id: $interview_id})
SET i.status = 'accepted', i.applicant_response = 'accepted', i.response_date = datetime()
```

## Email Configuration

The email system uses:
- **Service**: SendGrid
- **Function**: `send_email_task_wrapper()` from `tasks.py`
- **Template Rendering**: Jinja2 template rendering via `render_email_template()`
- **Async Execution**: Celery task queue with retry support (3 retries)

## Validation Rules

- Interview date must be in the future
- Interview time must be valid (HH:MM format)
- For onsite interviews: location, contact_person, and contact_phone are required
- For online interviews: google_meet_link can be auto-generated if empty
- Application must be in 'accepted' status to schedule interview
- User must own the business posting the job

## Features Included

✅ Online interview scheduling with Google Meet integration  
✅ Onsite interview scheduling with location and contact details  
✅ Email notifications for both interview types  
✅ Job seeker interview management interface  
✅ Interview status tracking (scheduled, accepted, rejected)  
✅ Interview details display in applicant profile  
✅ Dynamic form fields based on interview type  
✅ Rejection reason capture  
✅ Response date tracking  
✅ Professional email templates with styling  
✅ AJAX-based form submission with error handling  
✅ Modal dialogs for scheduling and responses  
✅ Database integrity with proper relationships  

## Testing Checklist

- [ ] Business owner can schedule online interview
- [ ] Business owner can schedule onsite interview
- [ ] Email sent to applicant with correct details
- [ ] Job seeker receives email
- [ ] Job seeker can view all interviews
- [ ] Job seeker can accept interview invitation
- [ ] Job seeker can reject interview with reason
- [ ] Interview details display correctly in applicant profile
- [ ] Interview status updates properly
- [ ] Google Meet link works (if provided)
- [ ] Onsite location and contact info display correctly
- [ ] Rejection reason is captured and stored
- [ ] Response date is recorded
- [ ] Modal closes on success
- [ ] Error messages display correctly

## Future Enhancement Ideas

- Interview outcome tracking (no-show, passed, failed)
- Multiple interviews per application
- Interview feedback form
- Calendar integration
- Interview reminders (24 hours before)
- Automatic Google Meet link generation
- Interview rescheduling capability
- Interview notes/feedback from interviewer
- Interview attendance confirmation
