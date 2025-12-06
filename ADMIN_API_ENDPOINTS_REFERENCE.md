# Admin API Endpoints Reference

## Complete Endpoint Specification for Catanduanes Connect Admin System

---

## 📋 Table of Contents
1. [User Management Endpoints](#user-management-endpoints)
2. [Job Management Endpoints](#job-management-endpoints)
3. [Business Management Endpoints](#business-management-endpoints)
4. [Verification Endpoints](#verification-endpoints)
5. [Analytics Endpoints](#analytics-endpoints)
6. [Export Endpoints](#export-endpoints)
7. [Settings Endpoints](#settings-endpoints)
8. [Maintenance Endpoints](#maintenance-endpoints)

---

## User Management Endpoints

### List Users with Filters
```
GET /admin/users-management
```
**Query Parameters**:
- `search` (optional): Search term for username, email, first name, last name
- `role` (optional): Filter by user role (admin, business, jobseeker)
- `status` (optional): Filter by status (verified, banned, suspended, active)
- `sort` (optional): Sort field (username, email, created_date, updated_date)
- `order` (optional): asc or desc (default: asc)
- `page` (optional): Page number (default: 1)

**Response**:
- Renders `admin/users_management.html`
- Context: users list, statistics, filter options, pagination

**Example**:
```
GET /admin/users-management?search=john&role=business&status=verified&page=1
```

---

### Edit User Profile
```
POST /admin/user/<user_id>/edit
```
**Request Body (Form Data)**:
- `first_name`: User's first name
- `last_name`: User's last name
- `email`: User's email address

**Response**:
- Redirect to users-management with success flash message

**Example**:
```
POST /admin/user/user123/edit
Content-Type: application/x-www-form-urlencoded

first_name=John&last_name=Doe&email=john@example.com
```

---

### Suspend User
```
POST /admin/user/<user_id>/suspend
```
**Request Body**: Empty (or optional notes)

**Response**:
- Sets `is_suspended = true`
- Records suspension timestamp
- Prevents user login
- Redirect with success message

**Example**:
```
POST /admin/user/user123/suspend
```

---

### Unsuspend User
```
POST /admin/user/<user_id>/unsuspend
```
**Request Body**: Empty

**Response**:
- Sets `is_suspended = false`
- Restores login access
- Redirect with success message

**Example**:
```
POST /admin/user/user123/unsuspend
```

---

### Ban User
```
POST /admin/user/<user_id>/ban
```
**Request Body** (Form Data):
- `reason` (optional): Reason for ban

**Response**:
- Sets `is_banned = true`
- Records ban timestamp
- Hides user from platform
- Prevents all platform access

**Example**:
```
POST /admin/user/user123/ban
Content-Type: application/x-www-form-urlencoded

reason=Violating%20community%20guidelines
```

---

### Unban User
```
POST /admin/user/<user_id>/unban
```
**Request Body**: Empty

**Response**:
- Sets `is_banned = false`
- Restores user visibility
- Redirect with success message

**Example**:
```
POST /admin/user/user123/unban
```

---

### Delete User
```
POST /admin/user/<user_id>/delete
```
**Request Body**: Empty

**Response**:
- Permanently deletes user account
- Cascade deletes user's jobs, businesses, applications
- **WARNING: Irreversible operation**

**Example**:
```
POST /admin/user/user123/delete
```

---

## Job Management Endpoints

### List Jobs with Advanced Filtering
```
GET /admin/jobs-management
```
**Query Parameters**:
- `search` (optional): Search in job title and description
- `category` (optional): Filter by job category
- `employment_type` (optional): Full-time, Part-time, Contract, Seasonal
- `status` (optional): active, expired, pending, approved, all
- `sort` (optional): title, created_date, featured_date
- `order` (optional): asc or desc
- `page` (optional): Page number (default: 1)

**Response**:
- Renders `admin/jobs_management.html`
- Context: jobs list, statistics, category list, filter options

**Statistics Included**:
- `total_jobs`: All jobs
- `active_jobs`: Non-expired, approved
- `pending_jobs`: Awaiting approval
- `featured_jobs`: Promoted jobs
- `expired_jobs`: Past posting date

**Example**:
```
GET /admin/jobs-management?category=IT&employment_type=Full-time&status=pending&sort=created_date
```

---

### View Job Details
```
GET /admin/job/<job_id>/view
```
**Response**:
- Renders job details page
- Shows all job information
- Displays creator business info
- Shows applicant count

**Example**:
```
GET /admin/job/job456/view
```

---

### Approve Job
```
POST /admin/job/<job_id>/approve
```
**Request Body**: Empty

**Response**:
- Sets `is_approved = true`
- Records `approved_at` timestamp
- Records `approved_by` admin ID
- Job becomes visible to job seekers
- Redirect with success message

**Example**:
```
POST /admin/job/job456/approve
```

---

### Reject Job
```
POST /admin/job/<job_id>/reject
```
**Request Body** (Form Data):
- `reason`: Reason for rejection (required)

**Response**:
- Sets `is_approved = false`
- Records rejection reason
- Stores `rejected_at` timestamp
- Records `rejected_by` admin ID

**Example**:
```
POST /admin/job/job456/reject
Content-Type: application/x-www-form-urlencoded

reason=Inappropriate%20job%20description
```

---

### Feature Job
```
POST /admin/job/<job_id>/feature
```
**Request Body**: Empty

**Response**:
- Sets `is_featured = true`
- Records `featured_at` timestamp
- Job appears at top of listings
- Increased visibility

**Example**:
```
POST /admin/job/job456/feature
```

---

### Unfeature Job
```
POST /admin/job/<job_id>/unfeature
```
**Request Body**: Empty

**Response**:
- Sets `is_featured = false`
- Returns to normal listing position

**Example**:
```
POST /admin/job/job456/unfeature
```

---

## Business Management Endpoints

### List Businesses with Filtering
```
GET /admin/businesses-management
```
**Query Parameters**:
- `search` (optional): Search in business name, description, owner
- `category` (optional): Filter by business category
- `status` (optional): approved, pending, rejected
- `featured` (optional): yes, no, all
- `sort` (optional): name, created_date, rating
- `order` (optional): asc or desc
- `page` (optional): Page number (default: 1)

**Response**:
- Renders `admin/businesses_management.html`
- Context: businesses list, statistics, categories, filter options

**Statistics Included**:
- `total_businesses`: All businesses
- `approved_businesses`: Active on platform
- `pending_businesses`: Awaiting approval
- `featured_businesses`: Promoted listings
- `active_businesses`: Currently operating

**Example**:
```
GET /admin/businesses-management?category=Restaurant&status=pending&sort=created_date
```

---

### View Business Details
```
GET /admin/business/<business_id>/view
```
**Response**:
- Renders business profile page
- Shows all business information
- Displays owner details and verification
- Shows posted jobs and services
- Ratings and reviews

**Example**:
```
GET /admin/business/biz789/view
```

---

### Approve Business
```
POST /admin/business/<business_id>/approve
```
**Request Body**: Empty

**Response**:
- Sets `is_approved = true`
- Records `approved_at` timestamp
- Records `approved_by` admin ID
- Business appears on platform
- Can post jobs and services

**Example**:
```
POST /admin/business/biz789/approve
```

---

### Reject Business
```
POST /admin/business/<business_id>/reject
```
**Request Body** (Form Data):
- `reason`: Reason for rejection (required)

**Response**:
- Sets `is_approved = false`
- Records rejection reason
- Stores rejection timestamp and admin ID
- Business hidden from platform

**Example**:
```
POST /admin/business/biz789/reject
Content-Type: application/x-www-form-urlencoded

reason=Incomplete%20business%20information
```

---

### Feature Business
```
POST /admin/business/<business_id>/feature
```
**Request Body**: Empty

**Response**:
- Sets `is_featured = true`
- Records `featured_at` timestamp
- Business appears in featured section
- Increased visibility in search

**Example**:
```
POST /admin/business/biz789/feature
```

---

### Unfeature Business
```
POST /admin/business/<business_id>/unfeature
```
**Request Body**: Empty

**Response**:
- Sets `is_featured = false`
- Returns to normal listing position

**Example**:
```
POST /admin/business/biz789/unfeature
```

---

### Delete Business
```
POST /admin/business/<business_id>/delete
```
**Request Body**: Empty

**Response**:
- Permanently removes business
- Cascade deletes jobs, services, applications
- **WARNING: Irreversible operation**

**Example**:
```
POST /admin/business/biz789/delete
```

---

## Verification Endpoints

### List Pending Verifications
```
GET /admin/verifications
```
**Response**:
- Renders verifications list page
- Shows pending verification requests
- Filters by status (pending, approved, rejected)
- Pagination support

**Example**:
```
GET /admin/verifications?status=pending&page=1
```

---

### View Verification Document
```
GET /admin/verification/<verification_id>/view-document
```
**Response**:
- Renders document viewing page
- Shows user identity documents
- Displays submitted information
- Shows verification request details

**Example**:
```
GET /admin/verification/ver123/view-document
```

---

### Approve Verification
```
POST /admin/verification/<verification_id>/approve
```
**Request Body**: Empty

**Response**:
- Sets verification status to 'approved'
- Sets user `is_verified = true`
- Records `reviewed_at` timestamp
- Records `reviewer_id` (admin ID)

**Example**:
```
POST /admin/verification/ver123/approve
```

---

### Reject Verification
```
POST /admin/verification/<verification_id>/reject
```
**Request Body** (Form Data):
- `notes`: Reason for rejection

**Response**:
- Sets verification status to 'rejected'
- Records rejection reason
- User remains unverified
- User can resubmit

**Example**:
```
POST /admin/verification/ver123/reject
Content-Type: application/x-www-form-urlencoded

notes=Document%20quality%20too%20low
```

---

## Analytics Endpoints

### Analytics Dashboard
```
GET /admin/reports
```
**Response**:
- Renders `admin/reports_analytics.html`
- Comprehensive statistics dashboard

**Context Includes**:

**User Statistics**:
- `total_users`
- `verified_users`
- `unverified_users`
- `banned_users`
- `suspended_users`
- `users_last_30d`
- `business_users`
- `jobseeker_users`
- `admin_users`

**Job Statistics**:
- `total_jobs`
- `approved_jobs`
- `pending_jobs`
- `featured_jobs`
- `active_jobs`
- `expired_jobs`
- `jobs_last_30d`

**Business Statistics**:
- `total_businesses`
- `approved_businesses`
- `pending_businesses`
- `featured_businesses`
- `active_businesses`
- `businesses_last_30d`

**Verification Statistics**:
- `total_verifications`
- `approved_verifications`
- `pending_verifications`
- `rejected_verifications`

**Categories**:
- `top_job_categories`: Top 10 job categories with counts
- `top_business_categories`: Top 10 business categories with counts

**Example**:
```
GET /admin/reports
```

---

## Export Endpoints

### Export Users to CSV
```
GET /admin/export/users.csv
```
**Response**:
- CSV file download: `users_export.csv`
- Columns: ID, Username, Email, First Name, Last Name, Role, Verified, Banned, Suspended, Created At, Updated At
- All users included

**Example**:
```
GET /admin/export/users.csv
```

---

### Export Jobs to CSV
```
GET /admin/export/jobs.csv
```
**Response**:
- CSV file download: `jobs_export.csv`
- Columns: ID, Title, Category, Employment Type, Business, Approved, Featured, Expired, Created At, Updated At
- All jobs included

**Example**:
```
GET /admin/export/jobs.csv
```

---

### Export Businesses to CSV
```
GET /admin/export/businesses.csv
```
**Response**:
- CSV file download: `businesses_export.csv`
- Columns: ID, Business Name, Category, Email, Phone, Website, Owner, Approved, Featured, Active, Created At, Updated At
- All businesses included

**Example**:
```
GET /admin/export/businesses.csv
```

---

## Settings Endpoints

### Get/Update Platform Settings
```
GET  /admin/settings
POST /admin/settings
```

**GET Response**:
- Renders `admin/settings.html`
- All current settings loaded from database
- Available options (timezones, languages) provided

**POST Request** (Form Data):
- `category` (required): Type of settings (general, email, moderation, features)

**For General Settings**:
- `platform_name`: Platform name
- `timezone`: Select from list
- `language`: Select language

**For Email Settings**:
- `smtp_host`: SMTP server host
- `smtp_port`: SMTP port (default 587)
- `smtp_user`: SMTP username
- `smtp_from`: From email address

**For Moderation Settings**:
- `enable_moderation`: checkbox (on/off)
- `require_verification`: checkbox (on/off)
- `auto_approve_verified`: checkbox (on/off)

**For Feature Settings**:
- `enable_jobs`: checkbox (on/off)
- `enable_businesses`: checkbox (on/off)
- `enable_messaging`: checkbox (on/off)
- `enable_analytics`: checkbox (on/off)

**Response**:
- Saves settings to database
- Records timestamp and admin ID
- Redirect with success message

**Example - General Settings**:
```
POST /admin/settings
Content-Type: application/x-www-form-urlencoded

category=general&platform_name=Catanduanes%20Connect&timezone=Asia/Manila&language=en
```

**Example - Email Settings**:
```
POST /admin/settings
Content-Type: application/x-www-form-urlencoded

category=email&smtp_host=smtp.gmail.com&smtp_port=587&smtp_user=admin@example.com&smtp_from=noreply@example.com
```

---

## Maintenance Endpoints

### Cleanup Database
```
POST /admin/maintenance/cleanup
```
**Response**:
- JSON: `{"status": "success", "message": "..."}`
- Removes expired jobs older than 90 days
- Deletes orphaned data
- Returns count of deleted items

**Example**:
```
POST /admin/maintenance/cleanup
```

**Response**:
```json
{
  "status": "success",
  "message": "cleanup completed"
}
```

---

### Clear Cache
```
POST /admin/maintenance/cache_clear
```
**Response**:
- JSON: `{"status": "success", "message": "Cache cleared successfully"}`
- Clears all application cache
- Forces fresh data load

**Example**:
```
POST /admin/maintenance/cache_clear
```

---

### Optimize Database
```
POST /admin/maintenance/database_optimize
```
**Response**:
- JSON: `{"status": "success", "message": "..."}`
- Resamples Neo4j indices
- Optimizes query performance
- Rebuilds statistics

**Indices Optimized**:
- idx_user_email
- idx_job_category
- idx_business_name

**Example**:
```
POST /admin/maintenance/database_optimize
```

---

### Create Backup
```
POST /admin/maintenance/create_backup
```
**Response**:
- JSON: `{"status": "success", "message": "Backup requested - check with database administrator"}`
- Creates backup request entry
- Records timestamp and admin ID
- Notifies database administrator

**Example**:
```
POST /admin/maintenance/create_backup
```

---

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 302 | Redirect (after successful POST) |
| 400 | Bad request (invalid parameters) |
| 401 | Unauthorized (not logged in) |
| 403 | Forbidden (not admin) |
| 404 | Not found (resource doesn't exist) |
| 500 | Server error |

---

## Authentication Header

All requests require valid authentication. User must be logged in and have admin role.

```
Authentication: Cookie (session-based)
User Role: admin (enforced by @admin_required decorator)
```

---

## Error Response Format

### Flash Messages (HTML responses)
- Shown at top of page
- Categories: 'success' (green), 'danger' (red), 'warning' (yellow), 'info' (blue)

### JSON Error Responses (API endpoints)
```json
{
  "status": "error",
  "message": "Description of error"
}
```

---

## Rate Limiting & Quotas

| Endpoint Type | Recommended Limits |
|---|---|
| List endpoints | 100 requests/hour |
| Action endpoints | 1000 requests/hour |
| Export endpoints | 10 requests/hour |
| Maintenance endpoints | 5 requests/hour |

---

## API Versioning

Current API Version: **1.0**

No versioning prefix in URLs (v1/, v2/ not used).
All endpoints are considered stable for production.

---

## Changelog

### Version 1.0 (Initial Release)
- All 8 route groups implemented
- 40+ individual endpoints
- CSV export functionality
- Analytics dashboard
- Settings management
- Maintenance tools

---

## Support & Documentation

For issues or questions:
1. Check error logs in `current_app.logger`
2. Verify Neo4j database connectivity
3. Ensure admin role assigned to user
4. Check request parameters match specification

---

**Last Updated**: 2024
**Documentation Version**: 1.0
**Status**: Complete ✅
