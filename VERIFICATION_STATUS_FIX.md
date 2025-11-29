# Verification Status Issue - Fixed

## Problem Description

When a job seeker registered using a Google account, they experienced an inconsistency:
- **Dashboard displayed:** "Rejected" (red status badge)
- **Upload page showed:** "Your account is already verified" (blocking upload)

## Root Cause Analysis

The issue was caused by a mismatch between two different fields used to track verification status:

### 1. **Google User Creation Issue** (`blueprints/auth/routes.py` - Line 745-747)
When Google users completed registration, they were created with:
```python
is_verified: true,  # ← This was True
# Missing: verification_status field
```

The `verification_status` field was **not being set**, so it defaulted to `null`/`None`.

### 2. **Field Mismatch**
- **`is_verified`** (boolean): Used by the upload verification route
- **`verification_status`** (string): Used by the dashboard ('pending', 'approved', 'rejected')

These two fields can be out of sync because:
1. Google users are created with `is_verified = true` but `verification_status = null`
2. An admin can then manually set `verification_status = 'rejected'`
3. Now there's a conflict: `is_verified = true` BUT `verification_status = 'rejected'`

### 3. **Upload Route Logic** (`blueprints/verification/routes.py` - Line 23)
The old code checked only `is_verified`:
```python
if current_user.is_verified:  # ← This is True for Google users!
    flash('Your account is already verified.', 'info')
    return redirect(url_for('dashboard.index'))  # Blocks upload
```

## Solution Implemented

### Fix 1: Google User Creation (`blueprints/auth/routes.py`)
Changed:
```python
is_verified: true,
is_active: true,
```

To:
```python
is_verified: false,                    # ← Default to not verified
verification_status: 'pending',        # ← Require document verification
is_active: true,
```

### Fix 2: Upload Verification Route (`blueprints/verification/routes.py`)
Updated to check both fields from the database:
```python
# Check verification status from database
db = get_neo4j_db()
with db.session() as session:
    user_data = safe_run(session, """
        MATCH (u:User {id: $user_id})
        RETURN u.verification_status as status, u.is_verified as is_verified
    """, {'user_id': current_user.id})

user_info = user_data[0] if user_data else {}
verification_status = user_info.get('status', 'pending')
is_verified = user_info.get('is_verified', False)

# Only allow upload if status is not approved
if verification_status == 'approved' or is_verified:
    flash('Your account is already verified.', 'info')
    return redirect(url_for('dashboard.index'))
```

### Fix 3: Allow Resubmission After Rejection
Added logic to delete old rejected verification records:
```python
# Allow resubmission if previously rejected
if current_status == 'rejected':
    # Delete old rejected verification records to allow new submission
    safe_run(session, """
        MATCH (u:User {id: $user_id})-[:SUBMITTED]->(v:Verification)
        WHERE v.status = 'rejected'
        DETACH DELETE v
    """, {'user_id': current_user.id})
```

### Fix 4: Dashboard Status Display (`templates/jobs/job_seeker_dashboard.html`)
Updated template to properly display all status states:
```django
{% if verification_status == 'approved' %}
    <i class="fas fa-check-circle text-green-500"></i>
{% elif verification_status == 'rejected' %}
    <span class="text-red-600 text-xs font-semibold">Rejected</span>
{% else %}
    <a href="{{ url_for('verification.upload_verification') }}" class="text-blue-600...">
        Verify Now
    </a>
{% endif %}
```

## Behavior After Fix

### For Google Users
1. **Registration:** Created with `is_verified = false`, `verification_status = 'pending'`
2. **Dashboard:** Shows "Verify Now" button until documents are approved
3. **Upload Page:** Allows document upload since `verification_status != 'approved'`
4. **After Rejection:** 
   - Dashboard shows "Rejected" status
   - Upload page allows resubmission
   - Old verification records are deleted before new submission

### Verification Status Flow
```
pending → [admin reviews] → approved
       ↓
     rejected → [user resubmits] → pending
```

## Files Modified
1. `blueprints/auth/routes.py` - Fixed Google user creation (Line 745-747)
2. `blueprints/verification/routes.py` - Updated upload route logic (Line 19-73)
3. `templates/jobs/job_seeker_dashboard.html` - Fixed status display (Line 252-262)

## Testing Checklist
- [ ] Register a new account with Google
- [ ] Verify dashboard shows "Verify Now" button
- [ ] Click "Verify Now" button - upload page should be accessible
- [ ] Upload documents
- [ ] Simulate admin rejection of verification
- [ ] Verify dashboard shows "Rejected" status
- [ ] Click "Verify Now" again - should allow resubmission
- [ ] Upload corrected documents
- [ ] Verify admin can approve the resubmission

## Impact
- ✅ Fixes conflicting status messages for Google-registered users
- ✅ Allows users to resubmit after rejection
- ✅ Ensures consistency between `is_verified` and `verification_status`
- ✅ Improves user experience with clear verification flow
