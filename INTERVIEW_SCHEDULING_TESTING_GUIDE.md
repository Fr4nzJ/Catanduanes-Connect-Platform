# Interview Scheduling Feature - Testing Guide

## Pre-Test Checklist

Before testing, ensure:
- [ ] Database is running (Neo4j)
- [ ] Flask application is running
- [ ] SendGrid API key is configured (for email testing)
- [ ] At least one business owner account exists
- [ ] At least one job seeker account exists
- [ ] A job posting exists
- [ ] A job application has been submitted

## Test Scenario 1: Schedule Online Interview

### Setup
1. Log in as a business owner
2. Go to "My Applicants" in the dashboard
3. Click on an applicant with "accepted" status

### Test Steps
1. **Verify "Schedule Interview" button appears**
   - ✓ Button should only show for accepted applications
   - ✓ Button should be blue with calendar icon
   
2. **Click "Schedule Interview" button**
   - ✓ Modal should open
   - ✓ Modal title: "Schedule Interview"
   - ✓ Applicant name and job title should display
   
3. **Select "Online Interview" (default)**
   - ✓ Radio button should be selected
   - ✓ "Online-only" fields should be visible
   - ✓ "Onsite-only" fields should be hidden
   
4. **Fill in interview details**
   - Interview Date: Select a future date
   - Interview Time: Enter a time (e.g., 14:00)
   - Google Meet Link: (Optional) Paste a Google Meet link or leave empty
   - Instructions: Enter something like "Bring portfolio, technical assessment included"
   
5. **Submit the form**
   - ✓ Modal should close
   - ✓ Success message should appear: "Interview scheduled successfully!"
   - ✓ Page should reload
   
6. **Verify interview data in applicant profile**
   - ✓ Interview Details section should appear
   - ✓ Status should be "Awaiting Response"
   - ✓ Type should show "Online (Google Meet)"
   - ✓ Date and time should match what you entered
   - ✓ Google Meet link should display (if provided)
   - ✓ Instructions should display

### Expected Email
- [ ] Applicant should receive email with subject "Interview Scheduled for {job_title}"
- [ ] Email should contain:
  - Applicant name
  - Job title
  - Date and time
  - Google Meet link (if provided)
  - Instructions
  - Link to view interview details

---

## Test Scenario 2: Schedule Onsite Interview

### Setup
1. Log in as a business owner
2. Go to "My Applicants"
3. Click on a different applicant with "accepted" status

### Test Steps
1. **Click "Schedule Interview" button**
   - ✓ Modal should open
   
2. **Select "Onsite Interview"**
   - ✓ Click the onsite radio button
   - ✓ "Online-only" fields should hide
   - ✓ "Onsite-only" fields should appear:
     - Location input
     - Contact Person input
     - Contact Phone input
   
3. **Fill in interview details**
   - Interview Date: Select a future date
   - Interview Time: Enter a time
   - Location: "Conference Room A, Building 2"
   - Contact Person: "John Manager"
   - Contact Phone: "+63 912 345 6789"
   - Instructions: "Please bring your portfolio and resume"
   
4. **Submit the form**
   - ✓ Modal should close
   - ✓ Success message should appear
   - ✓ Page should reload
   
5. **Verify interview data**
   - ✓ Interview Details section should appear
   - ✓ Type should show "Onsite"
   - ✓ Location should display
   - ✓ Contact Person should display
   - ✓ Contact Phone should be clickable link

### Expected Email
- [ ] Email should contain:
  - Location details
  - Contact person name and phone
  - Interview tips for candidates
  - No Google Meet link

---

## Test Scenario 3: Job Seeker Views and Accepts Interview

### Setup
1. Log in as the job seeker (applicant who received interview invitation)
2. Check inbox for interview notification email

### Test Steps
1. **Navigate to "My Interview Invitations"**
   - Click on "My Interview Invitations" in navigation menu
   - ✓ Page should load with interview list
   
2. **Verify interview displays correctly**
   - ✓ Interview card should show:
     - Job title as heading
     - Business name
     - Interview type badge
     - Date and time
   
3. **Check online interview details** (if testing online)
   - ✓ Google Meet link should display
   - ✓ "Join Google Meet" button should be present
   - ✓ Instructions should display
   
4. **Check onsite interview details** (if testing onsite)
   - ✓ Location should display
   - ✓ Contact person name and phone should display
   - ✓ Phone should be clickable (tel: link)
   - ✓ Instructions should display
   
5. **Accept interview**
   - ✓ Click "Accept Interview" button
   - ✓ Confirmation dialog should appear
   - ✓ Click "Accept" on confirmation
   - ✓ Status should update to "Accepted" (green badge)
   - ✓ "Join Google Meet" button should appear (if online)
   - ✓ Success message should show response date

### Expected Behavior After Accept
- ✓ Status badge changes to green "Accepted"
- ✓ Action buttons disappear
- ✓ "Join Google Meet" button visible (if online)
- ✓ Message shows "You have accepted this interview invitation"
- ✓ Response timestamp displays

---

## Test Scenario 4: Job Seeker Rejects Interview

### Setup
1. Log in as a different job seeker
2. Have an interview invitation in "scheduled" status

### Test Steps
1. **Navigate to "My Interview Invitations"**
   - ✓ Find interview in pending status
   
2. **Click "Reject Interview" button**
   - ✓ Modal should open
   - ✓ Modal title: "Reject Interview"
   - ✓ Reason textarea should be present (optional)
   
3. **Enter rejection reason** (optional)
   - Reason: "Already accepted another offer"
   
4. **Submit rejection**
   - ✓ Modal should close
   - ✓ Status should update to "Declined" (red badge)
   - ✓ Reason should display
   - ✓ Response timestamp should display

### Expected Behavior After Reject
- ✓ Status badge changes to red "Declined"
- ✓ Action buttons disappear
- ✓ Message shows "You have declined this interview invitation"
- ✓ Rejection reason displays (if provided)
- ✓ Response timestamp displays

---

## Test Scenario 5: Interview Details in Applicant Profile

### Setup
1. Log in as business owner
2. Navigate to an applicant's profile
3. Have already scheduled an interview for this applicant

### Test Steps
1. **Check for Interview Details section**
   - ✓ Section should appear below action buttons
   - ✓ Title: "Interview Details"
   - ✓ Calendar icon should be visible
   
2. **Verify interview information displays**
   - ✓ Status badge showing current status
   - ✓ Interview type (Online or Onsite)
   - ✓ Date and time
   - Type-specific details:
     - **Online**: Google Meet link
     - **Onsite**: Location, Contact Person, Contact Phone
   - ✓ Instructions (if provided)
   - ✓ Applicant response status and timestamp

---

## Test Scenario 6: Email Template Rendering

### Setup
1. Have SendGrid configured and API key set
2. Schedule an interview

### Test Steps
1. **Check online interview email**
   - [ ] Subject contains job title
   - [ ] Professional HTML formatting
   - [ ] Business info section
   - [ ] Date/time clearly displayed
   - [ ] Google Meet link clickable
   - [ ] Next steps section
   - [ ] Call-to-action button
   - [ ] Footer with company info
   
2. **Check onsite interview email**
   - [ ] Subject contains job title
   - [ ] Professional HTML formatting
   - [ ] Location prominently displayed
   - [ ] Contact person and phone
   - [ ] Interview tips section
   - [ ] Next steps section
   - [ ] Call-to-action button

---

## Error Handling Tests

### Test: Unauthorized Access
1. **Try scheduling interview without business owner role**
   - ✓ Should get 403 error
   - ✓ Message: "Unauthorized"

2. **Try viewing interviews without being logged in**
   - ✓ Should redirect to login page

### Test: Invalid Interview Date
1. **Try scheduling interview with past date**
   - ✓ Should be prevented by HTML5 date picker
   - ✓ Min date should be today

### Test: Missing Required Fields
1. **Onsite interview without location**
   - ✓ Form validation should require location
   - ✓ Submit should be blocked

2. **Onsite interview without contact person**
   - ✓ Form validation should require contact person
   - ✓ Submit should be blocked

### Test: Non-accepted Application
1. **Try scheduling interview for pending application**
   - ✓ "Schedule Interview" button should NOT appear

2. **Try accessing schedule-interview endpoint directly**
   - ✓ Should return 403 error
   - ✓ Message: "Application not accepted"

---

## Database Verification

After tests, verify Neo4j data:

```cypher
// Find all interviews
MATCH (i:Interview) RETURN i LIMIT 10

// Find interviews for a user
MATCH (u:User {username: 'test_user'})-[:INVITED_TO]->(i:Interview) RETURN i

// Verify relationships
MATCH (a:JobApplication)-[:HAS_INTERVIEW]->(i:Interview) RETURN a, i LIMIT 5

// Check interview status
MATCH (i:Interview {status: 'scheduled'}) RETURN COUNT(i) as scheduled_count
```

---

## Performance Tests

1. **Load My Interviews page with 50+ interviews**
   - ✓ Should load in < 2 seconds
   - ✓ All interviews should render correctly
   - ✓ No performance degradation

2. **Schedule interview with 10+ concurrent requests**
   - ✓ No duplicate interviews created
   - ✓ All emails sent
   - ✓ No database conflicts

---

## Accessibility Tests

- [ ] Modal is keyboard navigable
- [ ] Tab order is logical
- [ ] Form labels properly associated with inputs
- [ ] Color contrast is sufficient
- [ ] Radio buttons accessible
- [ ] Buttons have proper focus states
- [ ] Datetime inputs accessible

---

## Browser Compatibility Tests

Test on:
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Mobile browsers

---

## Test Results Summary

| Test Scenario | Status | Notes |
|---|---|---|
| Schedule Online Interview | ⚪ | |
| Schedule Onsite Interview | ⚪ | |
| View Interviews List | ⚪ | |
| Accept Interview | ⚪ | |
| Reject Interview | ⚪ | |
| Interview Details Display | ⚪ | |
| Online Email Sending | ⚪ | |
| Onsite Email Sending | ⚪ | |
| Error Handling | ⚪ | |
| Database Integrity | ⚪ | |
| Performance | ⚪ | |
| Accessibility | ⚪ | |
| Browser Compatibility | ⚪ | |

Legend: ⚪ = Not tested, 🟡 = In progress, ✅ = Passed, ❌ = Failed
