# Code Changes Summary - Resume Separation

## Modified Files

### 1. `blueprints/jobs/routes.py`
**Location**: After `my_applications()` route, before `close_job()` route

**New Route Added** (Lines 383-437):
```python
@jobs_bp.route('/resume/update', methods=['GET', 'POST'])
@login_required
@role_required('job_seeker')
def update_resume():
    """Update job seeker resume (separated from verification)"""
    db = get_neo4j_db()
    
    if request.method == 'GET':
        # Show resume update form
        with db.session() as session:
            user_data = safe_run(session, """
                MATCH (u:User {id: $user_id})
                RETURN u.resume_file as resume_file
            """, {'user_id': current_user.id})
        
        resume_file = None
        if user_data:
            resume_file = user_data[0].get('resume_file')
        
        return render_template('jobs/update_resume.html', resume_file=resume_file)
    
    # POST request - handle file upload
    if 'resume' not in request.files:
        return jsonify({'error': 'No resume file provided'}), 400
    
    resume_file = request.files['resume']
    
    if resume_file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Validate file extension
    if not allowed_file(resume_file.filename):
        return jsonify({'error': 'Invalid file type. Only PDF, DOC, DOCX files are allowed'}), 400
    
    try:
        # Save resume file
        filename = secure_filename(resume_file.filename)
        # Generate unique filename to avoid conflicts
        resume_filename = f"{current_user.id}_{uuid.uuid4().hex}_{filename}"
        resume_path = f"resumes/{current_user.id}/{resume_filename}"
        full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], resume_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        resume_file.save(full_path)
        
        # Update user resume in database
        with db.session() as session:
            safe_run(session, """
                MATCH (u:User {id: $user_id})
                SET u.resume_file = $resume_file, u.resume_updated_at = $updated_at
                RETURN u
            """, {
                'user_id': current_user.id,
                'resume_file': resume_path,
                'updated_at': datetime.utcnow().isoformat()
            })
        
        # Update current user object
        current_user.resume_file = resume_path
        current_user.resume_updated_at = datetime.utcnow().isoformat()
        
        return jsonify({
            'message': 'Resume updated successfully',
            'resume_file': resume_path
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Failed to update resume: {str(e)}")
        return jsonify({'error': 'Failed to update resume. Please try again.'}), 500
```

---

### 2. `templates/dashboard/job_seeker_dashboard.html`
**Location**: Line 227 (Resume Management section)

**Before**:
```html
<a href="{{ url_for('verification.upload_verification') }}" 
   class="btn-secondary text-sm w-full text-center block">
    <i class="fas fa-upload mr-1"></i>Update Resume
</a>
```

**After**:
```html
<a href="{{ url_for('jobs.update_resume') }}" 
   class="btn-secondary text-sm w-full text-center block">
    <i class="fas fa-upload mr-1"></i>Update Resume
</a>
```

**Change**: Changed endpoint from `verification.upload_verification` to `jobs.update_resume`

---

### 3. `templates/jobs/update_resume.html` (NEW FILE)
**Location**: `templates/jobs/update_resume.html` (195 lines)

**Features**:
- Drag-and-drop file upload with visual feedback
- File validation (PDF, DOC, DOCX, max 5MB)
- Current resume display if one exists
- Professional UI with tips section
- Auto-format JavaScript for user feedback
- Success confirmation with redirect

---

## No Changes Required

The following files did NOT need changes because they already have proper separation:

✅ `blueprints/verification/routes.py` - Already has role restriction for business_owner
✅ `blueprints/auth/routes.py` - Already sets correct status during OTP
✅ `otp.py` - Already handles verification status correctly
✅ All dashboard templates - Already have null-safe fallbacks

---

## Database Schema Impact

**User Node - No new fields required**

Existing fields used:
- `resume_file` - already existed (string path)
- `resume_updated_at` - added by this route (datetime)

---

## Testing Instructions

### 1. Test Resume Upload (GET)
```bash
# As authenticated job seeker
GET /resume/update
# Expected: Resume update form with current file info (if exists)
```

### 2. Test Resume Upload (POST)
```bash
# Upload new resume
POST /resume/update
Content-Type: multipart/form-data
Form data: resume=<file>

# Expected: JSON response
{
  "message": "Resume updated successfully",
  "resume_file": "resumes/user_id/file.pdf"
}
```

### 3. Test Role Restriction
```bash
# As non-job-seeker user
GET /resume/update
# Expected: 403 Forbidden (role_required decorator)
```

### 4. Test File Validation
```bash
# Upload invalid file type
POST /resume/update with .txt file
# Expected: 400 Bad Request
{"error": "Invalid file type. Only PDF, DOC, DOCX files are allowed"}
```

### 5. Test After Verification
```bash
# After user verification_status = 'approved'
GET /resume/update
# Expected: Form loads normally (no blocking)
POST /resume/update with valid resume
# Expected: Upload succeeds (no verification checks)
```

---

## URL Mappings

| Purpose | Route | Method | Decorator | File |
|---------|-------|--------|-----------|------|
| Resume form | `/resume/update` | GET | @login_required, @role_required('job_seeker') | jobs/routes.py |
| Upload resume | `/resume/update` | POST | @login_required, @role_required('job_seeker') | jobs/routes.py |
| Dashboard button | `jobs.update_resume` | Link | - | job_seeker_dashboard.html |

---

## Verification Flow Comparison

### Before
```
Email Verification → (try to update resume) → Redirected to verification upload
                                              → Cannot access (business owner only)
                                              → Status=approved blocked from uploading
```

### After
```
Email Verification → Can always update resume via /resume/update
                   → No verification status checks
                   → Works regardless of verification state
```

---

## Error Handling

The route handles these error cases:

1. **No file provided**
   ```json
   {"error": "No resume file provided"}
   400
   ```

2. **Empty filename**
   ```json
   {"error": "No file selected"}
   400
   ```

3. **Invalid file type**
   ```json
   {"error": "Invalid file type. Only PDF, DOC, DOCX files are allowed"}
   400
   ```

4. **Server error**
   ```json
   {"error": "Failed to update resume. Please try again."}
   500
   ```

---

## File Storage

**Resume files stored in**:
```
uploads/resumes/{user_id}/{uuid}_{original_filename}
```

**Job application files stored in**:
```
uploads/applications/{user_id}/{job_id}/{filename}
```

---

## Key Differences from Verification Upload

| Aspect | Verification Upload | Resume Update |
|--------|-------------------|----------------|
| Route | `/verification/upload` | `/resume/update` |
| Role | business_owner only | job_seeker only |
| Status check | Blocks if approved | No check |
| File types | PDF, PNG, JPG, JPEG | PDF, DOC, DOCX |
| Max size | Not specified | 5MB |
| Purpose | Document verification | Profile resume |
| Frequency | One-time submission | Anytime updates |

---

## Complete Request/Response Examples

### Example 1: Get Resume Form
```
GET /resume/update HTTP/1.1
Cookie: session=abc123...
Accept: text/html

HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8
(renders update_resume.html)
```

### Example 2: Upload Resume
```
POST /resume/update HTTP/1.1
Content-Type: multipart/form-data; boundary=---
Cookie: session=abc123...

-----
Content-Disposition: form-data; name="resume"; filename="John_Doe_Resume.pdf"
Content-Type: application/pdf
[binary file content]
-----

HTTP/1.1 200 OK
Content-Type: application/json
{
  "message": "Resume updated successfully",
  "resume_file": "resumes/user_123/abc-def-456_John_Doe_Resume.pdf"
}
```

### Example 3: Role Restriction (Business Owner)
```
GET /resume/update HTTP/1.1
Cookie: session=business_owner_session...

HTTP/1.1 403 Forbidden
Content-Type: application/json
{"error": "Unauthorized"}
```

---

## Deployment Checklist

- [x] Route added to jobs_bp blueprint
- [x] Template created with form and JavaScript
- [x] Dashboard button updated to new route
- [x] File validation implemented
- [x] Database update logic included
- [x] Error handling complete
- [x] No breaking changes
- [x] Role-based security applied
- [x] Documentation complete
