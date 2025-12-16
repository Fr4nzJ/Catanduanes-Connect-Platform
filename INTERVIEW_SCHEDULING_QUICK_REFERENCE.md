# Interview Scheduling - Quick Reference

## URLs & Endpoints

### Business Owner Routes
```
GET  /my-applicants                           → View applicants
GET  /applicant/<application_id>              → View applicant profile
POST /applicant/<application_id>/schedule-interview  → Schedule interview
```

### Job Seeker Routes
```
GET  /my-interviews                           → View interview invitations
POST /interview/<interview_id>/accept         → Accept interview
POST /interview/<interview_id>/reject         → Reject interview
```

## Form Data Format

### Schedule Interview Request
```javascript
{
  interview_type: 'online' | 'onsite',
  interview_date: 'YYYY-MM-DD',
  interview_time: 'HH:MM',
  instructions: 'Optional text',
  
  // If online:
  google_meet_link: 'https://meet.google.com/...' // optional
  
  // If onsite:
  location: 'Room 123',
  contact_person: 'John Doe',
  contact_phone: '+63 912 345 6789'
}
```

## API Responses

### Success Response (200/201)
```json
{
  "success": true,
  "message": "Interview scheduled successfully!",
  "interview_id": "uuid-string"
}
```

### Error Response (4xx/5xx)
```json
{
  "success": false,
  "error": "Error message description"
}
```

## Neo4j Queries

### Create Interview
```cypher
CREATE (i:Interview {
  id: $interview_id,
  type: 'online' | 'onsite',
  interview_datetime: $interview_datetime,
  status: 'scheduled',
  created_at: datetime(),
  updated_at: datetime()
})
CREATE (a)-[:HAS_INTERVIEW]->(i)
CREATE (u)-[:INVITED_TO]->(i)
```

### Get User Interviews
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
SET i.status = 'accepted',
    i.applicant_response = 'accepted',
    i.response_date = datetime()
RETURN i
```

## Template Usage

### Include Scheduling Modal in Form
```html
<!-- Add this where business owner can schedule interviews -->
<button onclick="showScheduleInterviewModal()" class="btn-primary">
  Schedule Interview
</button>

<!-- Modal is defined in applicant_profile.html -->
```

### Link to Interviews Page
```html
<a href="{{ url_for('jobs.my_interviews') }}">My Interview Invitations</a>
```

## JavaScript Functions

### Modal Control
```javascript
showScheduleInterviewModal()      // Open scheduling modal
closeScheduleInterviewModal()     // Close scheduling modal
toggleInterviewTypeFields()       // Show/hide fields based on type
```

### Interview Management (My Interviews Page)
```javascript
acceptInterview(interviewId)      // Accept interview
showRejectReasonModal(interviewId) // Show rejection dialog
closeRejectReasonModal()          // Close rejection dialog
```

## Email Template Variables

### Online Interview Context
```python
{
    'applicant_name': str,
    'job_title': str,
    'interview_date': str,        # YYYY-MM-DD
    'interview_time': str,        # HH:MM
    'google_meet_link': str,      # URL
    'instructions': str,          # Optional
    'interview_url': str,         # Link to view details
    'year': int
}
```

### Onsite Interview Context
```python
{
    'applicant_name': str,
    'job_title': str,
    'interview_date': str,        # YYYY-MM-DD
    'interview_time': str,        # HH:MM
    'location': str,
    'contact_person': str,
    'contact_phone': str,
    'instructions': str,          # Optional
    'interview_url': str,         # Link to view details
    'year': int
}
```

## Common Issues & Solutions

### Email Not Sending
```bash
# Check SendGrid API key
echo $SENDGRID_API_KEY

# Check Celery task queue
celery -A app.celery worker --loglevel=info

# Check Flask logs
tail -f flask.log | grep "interview"
```

### Interview Not Showing
```cypher
# Verify relationships
MATCH (a:JobApplication)-[:HAS_INTERVIEW]->(i:Interview)
RETURN a, i LIMIT 5

# Check application status
MATCH (a:JobApplication {id: $app_id})
RETURN a.status
```

### Form Validation Issues
```javascript
// Check form fields
console.log(document.getElementById('interviewDate').value)
console.log(document.getElementById('interviewType').value)

// Check CSRF token
console.log(document.querySelector('input[name="csrf_token"]').value)
```

## Testing Checklist

- [ ] Schedule online interview
- [ ] Schedule onsite interview  
- [ ] Verify email received
- [ ] Accept interview invitation
- [ ] Reject interview invitation
- [ ] Check interview details in profile
- [ ] Verify status updates
- [ ] Test error scenarios
- [ ] Test form validation
- [ ] Test on mobile device

## Deployment Checklist

- [ ] Set `SENDGRID_API_KEY`
- [ ] Set `SENDGRID_FROM_EMAIL`
- [ ] Create Neo4j indexes:
  ```cypher
  CREATE INDEX on :Interview(id)
  CREATE INDEX on :Interview(status)
  ```
- [ ] Run database migrations
- [ ] Test email sending
- [ ] Clear browser cache
- [ ] Run all tests
- [ ] Monitor logs

## Performance Tips

1. **Neo4j Query Optimization**
   - Limit results in my_interviews
   - Use proper indexes
   - Avoid unnecessary OPTIONAL MATCH

2. **Email Optimization**
   - Use Celery for async sending
   - Batch email sending if possible
   - Monitor queue depth

3. **Frontend Optimization**
   - Lazy load interview details
   - Cache interview list
   - Minify CSS/JS

## Security Notes

- ✅ Always verify user ownership before updating interviews
- ✅ Check application status is 'accepted' before scheduling
- ✅ Validate date/time inputs
- ✅ Sanitize interview instructions text
- ✅ Use CSRF tokens on all forms
- ✅ Log all interview-related actions

## File Locations

```
Backend:
- blueprints/jobs/routes.py (Schedule + Management routes)

Frontend:
- templates/jobs/applicant_profile.html (Business owner UI)
- templates/interviews/my_interviews.html (Job seeker UI)
- templates/email/interview_scheduled_online.html (Email)
- templates/email/interview_scheduled_onsite.html (Email)

Documentation:
- INTERVIEW_SCHEDULING_IMPLEMENTATION.md (Technical reference)
- INTERVIEW_SCHEDULING_TESTING_GUIDE.md (Testing procedures)
- INTERVIEW_SCHEDULING_COMPLETE.md (Overview)
- INTERVIEW_SCHEDULING_VERIFICATION.md (Checklist)
```

## Related Documentation

- **Full Implementation**: See INTERVIEW_SCHEDULING_IMPLEMENTATION.md
- **Testing Guide**: See INTERVIEW_SCHEDULING_TESTING_GUIDE.md
- **Verification**: See INTERVIEW_SCHEDULING_VERIFICATION.md

## Support

For issues or questions:
1. Check documentation files above
2. Review Flask/Neo4j logs
3. Check browser console for JS errors
4. Verify environment variables are set
5. Test database connectivity

---

**Quick Start**: 
1. Business owner accepts application
2. Clicks "Schedule Interview"
3. Fills form (online/onsite)
4. Submits
5. Job seeker gets email
6. Job seeker views and accepts/rejects
7. Status updates automatically
