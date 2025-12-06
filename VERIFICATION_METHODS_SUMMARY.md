# User Verification Methods - Complete Summary

## Overview
The platform has a comprehensive verification system with different flows for **Job Seekers** and **Business Owners**.

---

## 1. JOB SEEKER VERIFICATION

### Verification Flow
```
Registration → Email OTP → Email Code Entry → Approved → Dashboard
   (pending)   (pending)    (pending)      (approved)
```

### Step 1: Registration & Initial OTP
**File:** `blueprints/auth/routes.py` (lines 126-230)

**Process:**
- User creates account with email and password
- User selects "Job Seeker" role
- System generates OTP (6-digit code)
- Initial status: `verification_status = 'pending'`, `is_verified = false`
- User redirected to `/verification/verify-email`

**User Data Created:**
```
User Node {
  id: UUID
  email: user@example.com
  username: username
  password_hash: hashed_password
  role: 'job_seeker'
  verification_status: 'pending'
  is_verified: false
  created_at: timestamp
}
```

### Step 2: Email Code Verification
**File:** `blueprints/verification/routes.py` (lines 24-123)

#### Route 1: `/verification/verify-email` (GET/POST)
- **Purpose:** Request verification code to be sent to email
- **Who:** All non-Google users (email registration only)
- **Action:** System generates 6-digit OTP and sends via email
- **Code Expiration:** 10 minutes
- **Fields Stored:**
  - `email_otp`: 6-digit verification code
  - `email_otp_expires`: Expiration timestamp

#### Route 2: `/verification/verify-code` (GET/POST)
- **Purpose:** User enters 6-digit code they received
- **Validation:**
  - Code must be exactly 6 digits
  - Code must not be expired (10-minute window)
  - Code must match what was generated
- **On Success:**
  - `verification_status` → `'approved'`
  - `is_verified` → `true`
  - User redirected to dashboard
  - Flash message: "Email verified successfully! Your account is now active."

#### Route 3: `/verification/resend-code` (POST)
- **Purpose:** Resend verification code if user didn't receive it or code expired
- **Frequency:** Can be requested anytime during verification process
- **Action:** Generates new OTP and sends to email

### Step 3: Post-Verification Access
**Files:** Various dashboard templates

After verification is approved:

#### Resume Management
**Route:** `/jobs/update-resume` (GET/POST)
**File:** `blueprints/jobs/routes.py` (lines 383-437)

- **Access:** Job seeker can update resume at ANY time
- **Requirements:** Resume file upload (PDF, DOC, DOCX)
- **No verification status check** - resume can be updated before or after email verification
- **Database Update:**
  ```
  User {
    resume_file: path/to/resume.pdf
    resume_updated_at: timestamp
  }
  ```

#### Job Applications
**Route:** `/jobs/<job_id>/apply` (GET/POST)
**File:** `blueprints/jobs/routes.py` (lines 287-332)

- **Access:** Job seeker can apply to jobs regardless of verification status
- **Resume Used:** From profile or upload new one
- **No verification gate** - applications work in pending/approved state

#### Dashboard Display
**File:** `templates/dashboard/job_seeker_dashboard.html`

**Verification Status Indicators:**
```
✅ Verified (Green)
  - Status: verification_status = 'approved'
  - Display: "✓ Verified" badge

⏳ Pending (Yellow)
  - Status: verification_status = 'pending'
  - Display: "Pending" badge with "Upload Documents" link

❌ Rejected (Red)
  - Status: verification_status = 'rejected'
  - Display: "Rejected" badge with "Resubmit" link
```

---

## 2. BUSINESS OWNER VERIFICATION

### Verification Flow
```
Registration → Email OTP → Email Code → Upload Documents → Admin Review → Approved
   (pending)   (pending)   (pending)    (pending)          (pending)     (approved)
```

### Step 1 & 2: Same as Job Seekers
- Email registration with OTP
- Email code verification
- Same routes and process as job seekers

### Step 3: Document Upload for Business Owners
**File:** `blueprints/verification/routes.py` (lines 141-242)
**Route:** `/verification/upload` (GET/POST)
**Access:** `@role_required('business_owner')`

#### Required Documents:
1. **Government ID**
   - Formats: PDF, PNG, JPG, JPEG
   - Field: `id_document`
   - Additional field: `id_number` (5-50 characters)
   - Optional: `id_expiry` (expiration date)

2. **Business Permit**
   - Formats: PDF, PNG, JPG, JPEG
   - Field: `business_permit`
   - Optional field

3. **DTI Registration**
   - Formats: PDF, PNG, JPG, JPEG
   - Field: `dti_registration`
   - Optional field

4. **Business Address**
   - Field: `business_address`
   - Text format

#### Process:
1. User uploads documents via form
2. Files saved to: `/uploads/verifications/business_owner/<user_id>/`
3. Verification record created in database:
   ```
   Verification Node {
     id: UUID
     user_id: references User
     document_type: 'government_id'|'business_permit'|'dti_registration'
     file_path: path/to/file
     status: 'pending'
     created_at: timestamp
     submitted_at: timestamp
   }
   ```
4. Relationships:
   - `(User)-[:SUBMITTED]->(Verification)`
5. Status: `verification_status = 'pending'`

#### Upload Restrictions:
- Can only upload if status is NOT 'approved'
- If status = 'approved' or is_verified = true: User gets "Your account is already verified" message
- If status = 'rejected': User can resubmit documents

### Step 4: Admin Review Process
**Files:** 
- `blueprints/verification/routes.py` (lines 330-395)
- `templates/verification/verification_review.html`

**Admin Routes:**

#### View Pending Verifications
**Route:** `/admin/verification/review`
**Filters:** Pending | Verified | Rejected

#### Review Individual Verification
**Route:** `/verification/<verification_id>/review` (POST)
**Admin Actions:** Approve | Reject

**Approval Process:**
1. Admin reviews documents
2. Admin selects "Approve" or "Reject"
3. Admin can add review notes (optional)

**On Approval:**
```
User {
  verification_status: 'approved'
  is_verified: true
  verified_at: datetime
}

Verification {
  status: 'verified'
  reviewed_at: datetime
  reviewer_id: admin_user_id
  reviewer_notes: comments
}
```

**On Rejection:**
```
User {
  verification_status: 'rejected'
  is_verified: false  (stays false)
}

Verification {
  status: 'rejected'
  reviewed_at: datetime
  reviewer_id: admin_user_id
  reviewer_notes: reason for rejection
}
```

Business owner can then resubmit documents.

### Step 5: Business Owner Dashboard Display
**File:** `templates/business/business_owner_dashboard.html`

**Status Card:**
- **Pending:** Yellow border, "Documents under review" message
- **Verified:** Green border, "Your business account is fully verified"
- **Rejected:** Red border, "Your verification was rejected" with feedback

---

## 3. SPECIAL CASE: GOOGLE OAUTH USERS

### Registration Flow
**File:** `blueprints/auth/routes.py`

**Initial Setup:**
```
User {
  id: UUID
  email: from_google@domain.com
  username: generated_from_google_name
  role: selected_by_user_on_registration
  google_id: google_oauth_id
  is_verified: false        # ← Changed to false (was true, causing bugs)
  verification_status: 'pending'
  password_hash: generated (user can't login with password)
}
```

**Email Verification Skip:**
**File:** `blueprints/verification/routes.py` (lines 29-50)

- Route `/verification/verify-email` checks for `google_id`
- If google_id exists: "Your email is already verified through Google"
- User skipped to upload documents (business owner) or goes straight to dashboard (job seeker)

**No Email OTP Required** - Google handles email verification

---

## 4. VERIFICATION STATUS VALUES

### Database Field: `verification_status`

| Status | Meaning | Next Action | User Can Apply |
|--------|---------|------------|-----------------|
| `'pending'` | Awaiting email code verification | Verify email code | ✓ Yes (job seeker) |
| `'approved'` | Verified and approved | Access full features | ✓ Yes |
| `'rejected'` | Verification failed | Resubmit documents | ✓ Yes (job seeker) |
| `'null'` | Not set (legacy) | Set to 'pending' | ✓ Yes |

### Boolean Field: `is_verified`

| Value | Sync Status | Meaning |
|-------|-------------|---------|
| `true` | In sync | verification_status = 'approved' |
| `false` | In sync | verification_status = 'pending' or 'rejected' |

**Sync Mechanism:**
```python
# Approved users
if verification_status == 'approved':
    is_verified = true

# Other users  
else:
    is_verified = false
```

---

## 5. OTP SYSTEM

**File:** `otp.py`

### Functions:

#### `generate_otp()`
- Returns: 6-digit random code
- Example: `123456`

#### `save_email_otp(user_id, code)`
- Stores OTP in Neo4j User node
- Fields:
  - `email_otp`: The 6-digit code
  - `email_otp_expires`: Current time + 10 minutes
- Duration: 10 minutes

#### `verify_email_otp(user_id, code)`
- Returns: `true` if code is valid and not expired
- Returns: `false` if code is invalid, expired, or missing
- Checks: Code must match AND expiration time must be in future

#### `save_phone_otp()` & `verify_phone_otp()`
- Similar to email OTP
- Not currently used but available for future SMS verification

---

## 6. VERIFICATION DOCUMENT STORAGE

**Upload Directory Structure:**
```
/uploads/verifications/
├── job_seeker/
│   └── <user_id>/
│       ├── id_<filename>.pdf
│       └── resume_<filename>.pdf
├── business_owner/
│   └── <user_id>/
│       ├── id_<filename>.pdf
│       ├── business_permit_<filename>.pdf
│       ├── dti_registration_<filename>.pdf
│       └── business_address_<filename>.txt
└── service_provider/
    └── <user_id>/
        └── ...
```

**File Handling:**
- Filenames secured with `secure_filename()`
- Original extension preserved
- Prefix indicates document type

---

## 7. ADMIN VERIFICATION MANAGEMENT

**File:** `templates/admin/users.html` & `blueprints/admin/routes.py`

### Admin Features:

1. **User Management Page**
   - View all users
   - Toggle user status (active/inactive)
   - View user details
   - Verify user button (for manual override)

2. **Verification Review Page**
   - View pending verifications with document counts
   - Filter by status (Pending | Verified | Rejected)
   - Document viewer
   - Approval/Rejection with notes

3. **Dashboard Stats**
   - Pending verifications count
   - Verified users count
   - Quick links to verification review

---

## 8. VERIFICATION FLOW DECISION TREE

```
┌─ User Registration ─┐
│                     │
├─ Role Selection ────┤
│  ├─ Job Seeker      │
│  └─ Business Owner  │
│                     │
├─ Login Method ──────┤
│  ├─ Email/Password  │
│  │  └─ Send OTP     │
│  └─ Google OAuth    │
│     └─ Skip OTP     │
│                     │
├─ Email Code ────────┤
│  └─ Verify Code     │
│     └─ Status: Approved
│                     │
├─ Job Seeker? ───────┤
│  ├─ Yes             │
│  │  └─ Dashboard    │
│  │     ✓ Can Apply  │
│  │     ✓ Can Update Resume
│  └─ No              │
│     └─ Upload Docs  │
│        └─ Admin     │
│           Review    │
│           └─ Approve
│              └─ Verified
```

---

## 9. KEY DATABASE RELATIONSHIPS

```
User Node (verified job seeker):
  ├─ :HAS_PROFILE -> Profile
  ├─ :HAS_RESUME -> Resume (optional)
  └─ Fields:
      ├─ verification_status: 'approved'
      ├─ is_verified: true
      ├─ email_verified: true
      └─ verified_at: timestamp

Business Owner Node (verified):
  ├─ :OWNS -> Business
  ├─ :SUBMITTED -> Verification
  └─ Fields:
      ├─ verification_status: 'approved'
      ├─ is_verified: true
      ├─ business_verified_at: timestamp
      └─ verified_documents: [files]
```

---

## 10. CURRENT IMPLEMENTATION SUMMARY

### ✅ Working Verification Methods:

**Job Seekers:**
- ✅ Email + Password registration
- ✅ OTP generation and validation
- ✅ 6-digit email code verification
- ✅ Code resend functionality (10-min expiration)
- ✅ Resume upload anytime (no verification gate)
- ✅ Job applications allowed at all verification states
- ✅ Status display in dashboard (Verified/Pending/Rejected)

**Business Owners:**
- ✅ Email + Password registration
- ✅ OTP and email code verification (same as job seekers)
- ✅ Document upload (ID, Business Permit, DTI)
- ✅ Admin review and approval workflow
- ✅ Document resubmission on rejection
- ✅ Status display in dashboard

**Google OAuth:**
- ✅ Email verification bypass
- ✅ Auto-role assignment or selection
- ✅ Proper status initialization (pending, not approved)
- ✅ Same verification flow after registration

**Admin Panel:**
- ✅ Verification review interface
- ✅ Document viewing
- ✅ Approval/Rejection with notes
- ✅ Status filtering
- ✅ User verification stats

---

## 11. VERIFICATION STATE TRANSITIONS

```
┌─────────────────────┐
│   pending (START)   │
└──────────┬──────────┘
           │
           ├─[Enter Code]─────────┐
           │                       │
           ▼                       ▼
      ┌──────────┐          ┌──────────┐
      │ approved │◄─────────│ rejected │
      │(✓ Active)│─[Upload] └──────────┘
      └──────────┘
          ▲ │
          │ └─[Reject]
          │
       [Approve]
```

**For Job Seekers:** Can stay at any state and still use platform
**For Business Owners:** Full features only at 'approved' state

---

## 12. COMMON VERIFICATION FLOWS

### Flow 1: Job Seeker - Email Registration
```
1. Register (email/password) → verification_status='pending'
2. Receive OTP via email
3. Enter OTP in form
4. Receive 6-digit code via email
5. Enter code
6. verification_status='approved' ✓
7. View jobs, apply, update resume
```

### Flow 2: Business Owner - Email Registration
```
1. Register (email/password) → verification_status='pending'
2. Complete OTP & email code verification → verification_status='approved' (for email)
3. Upload ID, Business Permit, DTI
4. Admin reviews documents
5. Admin approves → is_verified=true (for account)
6. Business page fully active
```

### Flow 3: Google User - Business Owner
```
1. Register via Google → google_id set, verification_status='pending'
2. Skip email OTP verification
3. Upload business documents
4. Admin reviews
5. Admin approves → is_verified=true
6. Business page fully active
```

### Flow 4: Verification Rejection
```
1. Business owner uploads documents
2. Admin reviews and rejects with notes
3. verification_status='rejected'
4. User sees rejection message
5. User re-uploads corrected documents
6. New verification created
7. Admin reviews again
8. Admin approves → verified ✓
```

---

## Summary Table

| Aspect | Job Seeker | Business Owner |
|--------|-----------|----------------|
| **Registration** | Email/Google | Email/Google |
| **Email Verification** | Required | Required |
| **Document Upload** | Optional resume | Required (ID, permit, DTI) |
| **Admin Approval** | None (auto-approved) | Required |
| **Can Apply for Jobs** | Yes (any status) | N/A |
| **Full Account Access** | Yes (any status) | Only when approved |
| **Verification Statuses** | pending, approved, rejected | pending, approved, rejected |

