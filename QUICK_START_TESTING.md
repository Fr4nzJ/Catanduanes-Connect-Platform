# Quick Start Guide - Testing Resume Separation Feature

## TL;DR
**What Was Fixed**: Job seekers can now update their resumes after verification.

**Where**: `/resume/update` endpoint

**How to Test**: Follow the test cases below

---

## 30-Second Overview

```
Before: Verified users blocked from updating resume ❌
After: All users can update resume anytime ✅

Change: One new route + one dashboard link update
Files: 2 modified, 1 new template, 4 documentation files
```

---

## Quick Test - 5 Minutes

### Test 1: Access Resume Update Form
```
1. Login as job seeker
2. Go to: http://localhost:5050/resume/update
Expected: See resume upload form
```

### Test 2: Upload Resume
```
1. At resume form
2. Select a PDF file
3. Click "Update Resume"
Expected: Success message + file saved
```

### Test 3: Dashboard Link
```
1. Dashboard → Resume Management
2. Click "Update Resume"
Expected: Navigate to form
```

### Test 4: Verified User Can Update
```
1. Login as verified job seeker
2. Go to: /resume/update
Expected: Form loads (not blocked)
3. Upload new resume
Expected: Success
```

---

## Full Test Suite - 15 Minutes

### Setup
```bash
# Start server if not running
cd "c:\Users\User\Downloads\Catanduanes Connect Platform"
python app.py
```

### Test Cases

#### TC1: Unverified User Resume Upload
```
Step 1: Register new job seeker account
Step 2: Go to /resume/update
Step 3: Upload valid PDF
Expected: ✅ Success
```

#### TC2: Verified User Resume Upload
```
Step 1: Login as verified job seeker
Step 2: Go to /resume/update
Step 3: Upload valid PDF
Expected: ✅ Success (was failing before)
```

#### TC3: Invalid File Type
```
Step 1: At resume form
Step 2: Select .txt file
Step 3: Click "Update Resume"
Expected: ❌ Error message
```

#### TC4: File Size Validation
```
Step 1: Create file > 5MB
Step 2: Try to upload
Expected: ❌ Validation error
```

#### TC5: Dashboard Navigation
```
Step 1: Job Seeker Dashboard
Step 2: Find "Resume Management" section
Step 3: Click "Update Resume" button
Expected: ✅ Navigates to /resume/update
```

#### TC6: Role Restriction
```
Step 1: Login as Business Owner
Step 2: Try: GET /resume/update
Expected: ❌ 403 Forbidden
```

#### TC7: Database Update
```
Step 1: Upload resume
Step 2: Check database:
   MATCH (u:User) WHERE u.id = 'user_id'
   RETURN u.resume_file, u.resume_updated_at
Expected: ✅ Fields updated
```

#### TC8: Multiple Uploads
```
Step 1: Upload resume_v1.pdf
Step 2: Wait for success
Step 3: Upload resume_v2.pdf
Expected: ✅ Second upload succeeds
          ✅ Database shows latest version
```

---

## Expected Results

### Success Indicators ✅
- [ ] Form displays without errors
- [ ] Files upload successfully
- [ ] Database updates with file path
- [ ] Success message displays
- [ ] Can upload multiple times
- [ ] Works for verified users
- [ ] Works for unverified users
- [ ] Dashboard link works

### Error Handling ✅
- [ ] Rejects invalid file types
- [ ] Rejects oversized files
- [ ] Shows helpful error messages
- [ ] Doesn't corrupt database on error
- [ ] Logs errors properly

---

## Files Changed

### Code Changes (2 files)
1. `blueprints/jobs/routes.py` - Added `/resume/update` route
2. `templates/dashboard/job_seeker_dashboard.html` - Updated button link

### New Files (1 file)
3. `templates/jobs/update_resume.html` - Resume upload form

---

## Common Issues & Quick Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| Route not found (404) | Flask not restarted | Restart Flask server |
| File upload fails | Wrong permission | Check `/uploads/resumes/` exists |
| Database doesn't update | Neo4j issue | Check database connection |
| Can't access form | Not logged in | Login first |
| Role error (403) | Wrong role | Use job_seeker account |

---

## Verification Checklist

Before declaring success, verify:

- [ ] Can upload resume as unverified user
- [ ] Can upload resume as verified user (KEY FIX!)
- [ ] Dashboard button navigates correctly
- [ ] File saves to correct directory
- [ ] Database updates with file path
- [ ] Error messages display properly
- [ ] No verification status blocking occurs
- [ ] Security (role restriction) works

---

## Performance Baseline

Expected performance metrics:
- Form load time: <500ms
- File upload (2MB): ~3-5 seconds
- Database update: <100ms
- Success response: <200ms total
- No database locks

---

## Browser Testing

Test in these browsers:
- [ ] Chrome
- [ ] Firefox
- [ ] Edge
- [ ] Safari
- [ ] Mobile (responsive design)

---

## Database Verification

After upload, check database:
```cypher
// Verify resume file saved
MATCH (u:User)
WHERE u.id = 'your_user_id'
RETURN u.resume_file, u.resume_updated_at

// Should see:
resume_file: "resumes/user_id/abc-def_resume.pdf"
resume_updated_at: "2024-XX-XXT12:34:56.789..."
```

---

## File System Verification

Check file saved correctly:
```
uploads/
└── resumes/
    └── {user_id}/
        └── {uuid}_{original_name}.pdf
```

---

## Logs to Monitor

When testing, watch for these in server logs:

### Good ✅
```
[INFO] Resume file saved successfully
[INFO] Database updated: resume_file, resume_updated_at
[INFO] User response: JSON success
```

### Bad ❌
```
[ERROR] Failed to update resume
[ERROR] File validation failed
[ERROR] Database query error
```

---

## Sample Test Data

Use these for testing:

### Valid Test Files
- `sample_resume.pdf` (created by you)
- `sample_resume.docx` (created by you)
- `sample_resume.doc` (created by you)

### Invalid Test Files
- `test.txt` - should be rejected
- `test.jpg` - should be rejected
- `large_file.pdf` (>5MB) - should be rejected

---

## Success Definition

The feature is working when:

```
✅ Unverified job seeker can upload resume
✅ Verified job seeker can upload resume (KEY!)
✅ File saves to /uploads/resumes/{user_id}/
✅ Database updates with file path and timestamp
✅ Dashboard button links to correct route
✅ Form validates file type and size
✅ Success message displays after upload
✅ Business owners cannot access /resume/update
✅ No verification status blocking occurs
```

---

## Rollback Plan

If issues occur:

1. Stop server
2. Restore `blueprints/jobs/routes.py` from backup
3. Restore `templates/dashboard/job_seeker_dashboard.html` from backup
4. Delete `templates/jobs/update_resume.html`
5. Restart server

---

## Support

### If Upload Fails
1. Check error message
2. Verify file type
3. Check file size
4. Check /uploads/resumes/ directory exists
5. Check server logs

### If Database Doesn't Update
1. Verify Neo4j is running
2. Check database connection
3. Verify user exists in database
4. Check database permissions

### If Role Restriction Fails
1. Verify user role in database
2. Verify @role_required decorator is applied
3. Check user session object
4. Verify user is authenticated

---

## Next Steps After Testing

1. ✅ Run test cases above
2. ✅ Verify all pass
3. ✅ Monitor logs
4. ✅ Check database
5. ✅ Get user feedback
6. ✅ Deploy to production (if all pass)
7. ✅ Monitor in production
8. ✅ Plan enhancements

---

## Quick Reference

**New Route**: `/resume/update`
**Dashboard Button**: "Update Resume" (in Resume Management section)
**Role Required**: `job_seeker` only
**File Types**: PDF, DOC, DOCX
**Max Size**: 5MB
**Key Fix**: Verified users no longer blocked!

---

**Status**: ✅ Ready for Testing
**Estimated Test Time**: 5-15 minutes
**Expected Outcome**: All tests pass ✅
