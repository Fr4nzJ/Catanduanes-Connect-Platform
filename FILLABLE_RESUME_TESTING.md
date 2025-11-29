# Fillable Resume Template - Testing Guide

## Quick Start - 2 Minutes

### Access the Resume Template
```
1. Login as job seeker
2. Go to: http://localhost:5050/jobs/resume/update
3. Should see fillable resume form
```

### Add Some Data
```
1. Fill in Full Name: "Emily Johnson"
2. Fill in Email: "emily@example.com"
3. Click "Add Interest" → Type "Drawing"
4. Click "Add Skill" → Type "Web Design"
5. Click "Save Resume"
Expected: Success message + data saved
```

### Preview Resume
```
1. Click "Preview" tab
2. Should show formatted resume
3. Only filled sections visible
4. Click "Print Resume" to export
```

---

## Complete Test Suite - 15 Minutes

### Test 1: Load Empty Form
**Steps:**
1. New job seeker account
2. Navigate to /jobs/resume/update
3. Form should load

**Expected:**
- ✅ Form displays
- ✅ All fields empty
- ✅ Add buttons present
- ✅ No previous data shown

---

### Test 2: Add Personal Information
**Steps:**
1. Fill "Full Name": "John Doe"
2. Fill "Email": "john@example.com"
3. Fill "Phone": "(555) 123-4567"
4. Observe footer updates

**Expected:**
- ✅ Footer shows "John Doe"
- ✅ Form remembers values
- ✅ Phone format flexible

---

### Test 3: Add Multiple Interests
**Steps:**
1. Click "Add Interest" (first time)
2. Type "Photography"
3. Click "Add Interest" (second time)
4. Type "Design"
5. Click "Add Interest" (third time)
6. Type "Programming"

**Expected:**
- ✅ Three items visible
- ✅ Each has Remove button
- ✅ Can add more than 3

---

### Test 4: Remove Items
**Steps:**
1. Have 3 interests added
2. Click Remove on second item
3. Observe list updates

**Expected:**
- ✅ Second interest removed
- ✅ Other items remain
- ✅ List re-renders correctly

---

### Test 5: Save Resume (Server)
**Steps:**
1. Fill multiple fields
2. Click "Save Resume"
3. Wait for response

**Expected:**
- ✅ Success message appears
- ✅ Footer updates
- ✅ Data saved to database
- Check database:
  ```cypher
  MATCH (u:User {id: 'your_user_id'})
  RETURN u.resume_data, u.resume_updated_at
  ```

---

### Test 6: Refresh Page (Data Persists)
**Steps:**
1. Refresh browser (F5)
2. Form reloads

**Expected:**
- ✅ All data still there
- ✅ Loaded from database
- ✅ Footer updated with name

---

### Test 7: Preview Tab
**Steps:**
1. Fill in some data
2. Click "Preview" tab
3. Observe resume layout

**Expected:**
- ✅ Professional formatting
- ✅ Only filled sections shown
- ✅ Name in footer
- ✅ Proper hierarchy (h1, h2, etc)
- ✅ Lists formatted correctly

---

### Test 8: Print Resume
**Steps:**
1. At Preview tab
2. Click "Print Resume"
3. Browser print dialog opens

**Expected:**
- ✅ Print dialog shows
- ✅ Resume formatted for print
- ✅ Can save as PDF
- ✅ Clean layout for printing

---

### Test 9: Empty Sections Not Shown
**Steps:**
1. Fill only Name and Email
2. Leave Skills empty
3. Go to Preview tab

**Expected:**
- ✅ Skills section NOT shown
- ✅ Only filled sections visible
- ✅ Clean presentation

---

### Test 10: Clear All Data
**Steps:**
1. Have form filled
2. Click "Clear All"
3. Confirm dialog

**Expected:**
- ✅ Confirmation asked
- ✅ All fields cleared
- ✅ Database updated
- ✅ localStorage cleared

---

### Test 11: Edit After Save
**Steps:**
1. Save resume
2. Go to Preview tab
3. Go back to Edit tab
4. Change a value
5. Save again

**Expected:**
- ✅ Can edit after save
- ✅ New data saved
- ✅ Updated timestamp
- ✅ No conflicts

---

### Test 12: LocalStorage Fallback
**Steps:**
1. Fill form with data
2. Click "Save Resume"
3. Temporarily disable network
4. Add more items
5. Click "Save Resume" again

**Expected:**
- ✅ Notification about local save
- ✅ Data stored locally
- ✅ Message when restored online

---

### Test 13: Mobile Responsiveness
**Steps:**
1. Resize browser to mobile (< 768px)
2. Navigate to resume form
3. Test form interaction

**Expected:**
- ✅ Form readable
- ✅ Buttons accessible
- ✅ Proper spacing
- ✅ Side panels hidden

---

### Test 14: Add/Remove Education Links
**Steps:**
1. Add education: "https://www.example.com"
2. In preview, should be clickable link
3. Remove and verify

**Expected:**
- ✅ Links accepted as input
- ✅ Preview shows clean text
- ✅ Remove works properly

---

### Test 15: Special Characters
**Steps:**
1. Add name with accent: "François"
2. Add skill with symbols: "C++/C#"
3. Save and preview

**Expected:**
- ✅ Special chars displayed correctly
- ✅ Database stores properly
- ✅ Preview shows correctly

---

## Browser Compatibility Testing

Test in:
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Mobile Safari (iOS)
- [ ] Chrome Mobile (Android)

---

## Database Verification

After saving, check:

```cypher
// Check resume data structure
MATCH (u:User {username: 'testuser'})
RETURN u.resume_data, u.resume_updated_at

// Verify JSON validity
WITH u.resume_data as data
RETURN data CONTAINS 'fullName' as has_fullName,
       data CONTAINS 'interests' as has_interests
```

---

## File System Check

Old file upload system files (should no longer be created):
```
uploads/resumes/  ← Should be empty or not used
```

New data storage:
```
Database field: User.resume_data (JSON format)
Location: Neo4j database (not files)
```

---

## Performance Checklist

- [ ] Form loads < 1 second
- [ ] Add item < 100ms
- [ ] Remove item < 100ms
- [ ] Save to server < 2 seconds
- [ ] Preview renders < 500ms
- [ ] No console errors
- [ ] No network errors
- [ ] Smooth interactions

---

## Edge Cases to Test

### Empty Values
```
Test: Save with empty full name
Expected: Saves, shows empty in preview
```

### Max Items
```
Test: Add 50 items to one section
Expected: All added, preview shows all
```

### Rapid Changes
```
Test: Click Save multiple times rapidly
Expected: Handles gracefully, no duplication
```

### Session Timeout
```
Test: Wait until session expires, try to save
Expected: Redirect to login or error message
```

### Concurrent Edits
```
Test: Edit in two tabs simultaneously
Expected: Last save wins (graceful handling)
```

---

## Expected Outputs

### Successful Save
```json
{
  "status": "success",
  "message": "Resume saved successfully"
}
```

### Form Data Example
```json
{
  "fullName": "Emily Johnson",
  "email": "emily@example.com",
  "phone": "(555) 123-4567",
  "interests": ["Drawing", "Photography", "Design", "Programming"],
  "skills": ["Web Design with HTML & CSS"],
  "education": ["Wilton High School", "Silvermine School of Arts", "Codeacademy"],
  "experience": ["Student Technology Intern", "Babysitter"],
  "extracurriculars": ["Recycling Club", "Gardening Club", "Book Club"]
}
```

---

## Success Criteria

All tests pass when:
- [ ] Form loads without errors
- [ ] Can add/remove items
- [ ] Data persists after refresh
- [ ] Save succeeds (200 OK)
- [ ] Database updated correctly
- [ ] Preview displays properly
- [ ] Print works
- [ ] LocalStorage backup works
- [ ] Mobile responsive
- [ ] No console errors
- [ ] Professional appearance

---

## Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| Form doesn't load | Route not updated | Restart Flask |
| Save fails | Server error | Check server logs |
| Data not persisting | DB issue | Verify Neo4j connection |
| Preview blank | JS error | Check browser console |
| Styling broken | CSS issue | Check template file |
| Mobile broken | Responsive CSS | Check media queries |

---

## Rollback Plan

If major issues found:

1. Keep backup of old template
2. Revert route to file upload
3. Notify users
4. Plan fix for next iteration

---

## Sign-Off

Feature is ready for:
- ✅ Development QA
- ✅ User acceptance testing
- ✅ Production deployment

**Timeline**: ~15 minutes for complete test suite
**Resources**: No special setup needed
**Impact**: High - Improves UX significantly
