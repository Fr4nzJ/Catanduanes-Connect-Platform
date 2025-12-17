# CSV Export Feature - Architecture & Flow Diagrams

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         ADMIN DASHBOARD UI                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │              DATA EXPORT SECTION (NEW)                           │   │
│  ├──────────────────────────────────────────────────────────────────┤   │
│  │                                                                  │   │
│  │  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐         │   │
│  │  │ USERS EXPORT  │ │BUSINESSES     │ │ JOBS EXPORT   │ ...     │   │
│  │  │ [Download CSV]│ │EXPORT         │ │ [Download CSV]│         │   │
│  │  │               │ │[Download CSV] │ │               │         │   │
│  │  └───────┬───────┘ └───────┬───────┘ └───────┬───────┘         │   │
│  └──────────┼───────────────────┼───────────────┼────────────────────┘   │
│             │                   │               │                        │
└─────────────┼───────────────────┼───────────────┼────────────────────────┘
              │                   │               │
              │ GET /admin/       │ GET /admin/   │ GET /admin/
              │ export/users      │ export/       │ export/jobs
              │                   │ businesses    │
              ↓                   ↓               ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                        FLASK BACKEND ROUTES                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐   │
│  │ @admin_req'd │ │ @admin_req'd  │ │ @admin_req'd  │ │ @admin_req'd │   │
│  │              │ │               │ │               │ │              │   │
│  │ export_      │ │ export_       │ │ export_       │ │ export_      │   │
│  │ users_csv()  │ │ businesses_   │ │ jobs_csv()    │ │ all_csv()    │   │
│  │              │ │ csv()         │ │               │ │              │   │
│  │ Neo4j Query  │ │ Neo4j Query   │ │ Neo4j Query   │ │ Zip 3 CSVs   │   │
│  │ ↓            │ │ ↓             │ │ ↓             │ │ ↓            │   │
│  │ CSV Generate │ │ CSV Generate  │ │ CSV Generate  │ │ CSV Gen + Zip│   │
│  │ ↓            │ │ ↓             │ │ ↓             │ │ ↓            │   │
│  │ send_file()  │ │ send_file()   │ │ send_file()   │ │ send_file()  │   │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘   │
│                                                                           │
└──────────┬──────────────────────┬──────────────────────┬────────────────┘
           │                      │                      │
           ↓                      ↓                      ↓
┌────────────────────────────────────────────────────────────────────────┐
│                      NEO4J DATABASE                                     │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Query 1: MATCH (u:User) RETURN ... → [User Data]                    │
│  Query 2: MATCH (b:Business) RETURN ... → [Business Data]            │
│  Query 3: MATCH (j:Job) RETURN ... → [Job Data]                      │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

```
STEP 1: User Action
┌──────────────────┐
│  Admin clicks    │
│  "Export Users"  │
│  button on       │
│  Dashboard       │
└────────┬─────────┘
         │
         ↓
STEP 2: Request Validation
┌──────────────────────────────┐
│  Flask Route Handler         │
│  • Check @admin_required     │
│  • Verify current_user       │
│  • Validate session          │
│  ✓ PASSED → Continue        │
│  ✗ FAILED → Redirect        │
└────────┬─────────────────────┘
         │
         ↓
STEP 3: Database Query
┌──────────────────────────────┐
│  Neo4j Connection            │
│  Execute Cypher Query        │
│  MATCH (u:User) RETURN ...   │
│  ↓                           │
│  Return List of Dicts        │
│  [{id: 1, name: 'John'}, ..]│
└────────┬─────────────────────┘
         │
         ↓
STEP 4: CSV Generation
┌──────────────────────────────┐
│  Python csv.DictWriter       │
│  • Create StringIO buffer    │
│  • Write headers             │
│  • Write data rows           │
│  ↓                           │
│  CSV Content in Memory       │
│  "id,name,email,..."        │
│  "1,John,john@..."          │
└────────┬─────────────────────┘
         │
         ↓
STEP 5: File Conversion
┌──────────────────────────────┐
│  Convert StringIO to BytesIO │
│  • Encode to UTF-8           │
│  • Create bytes buffer       │
│  ↓                           │
│  Binary Data Ready           │
└────────┬─────────────────────┘
         │
         ↓
STEP 6: File Delivery
┌──────────────────────────────┐
│  Flask send_file()           │
│  • Set MIME type             │
│  • Set filename with date    │
│  • Send as attachment        │
│  ↓                           │
│  HTTP Response with File     │
└────────┬─────────────────────┘
         │
         ↓
STEP 7: Logging
┌──────────────────────────────┐
│  Log Export Action           │
│  logger.info(...)            │
│  • Admin username            │
│  • Export type               │
│  • Record count              │
│  • Timestamp                 │
└────────┬─────────────────────┘
         │
         ↓
STEP 8: Browser Download
┌──────────────────────────────┐
│  Browser receives file       │
│  → Auto download starts      │
│  → Saved to Downloads folder │
│  → User can open in Excel    │
└──────────────────────────────┘
```

## Component Interaction Diagram

```
Admin User
    │
    │ Clicks Export Button
    ↓
┌────────────────────────────────────┐
│   admin_dashboard.html             │
│   ├─ Export Section (NEW)          │
│   └─ 4 Download Links              │
└────────────┬───────────────────────┘
             │
             │ GET /admin/export/users
             ↓
┌────────────────────────────────────┐
│   routes.py                        │
│   ├─ @admin_bp.route()             │
│   ├─ @admin_required               │
│   └─ export_users_csv()            │
└────────────┬───────────────────────┘
             │
             ├─→ [1] Get DB Connection
             │   └─→ get_neo4j_db()
             │
             ├─→ [2] Execute Query
             │   └─→ safe_run(session, cypher_query)
             │
             ├─→ [3] Convert to CSV
             │   ├─→ csv.DictWriter()
             │   └─→ io.StringIO()
             │
             ├─→ [4] Encode to Bytes
             │   └─→ io.BytesIO()
             │
             ├─→ [5] Send File
             │   └─→ send_file()
             │
             └─→ [6] Log Action
                 └─→ logger.info()
                     Audit Trail
```

## Database Query Flow

```
REQUEST TO EXPORT USERS
                 │
                 ↓
    ┌────────────────────────┐
    │  Neo4j Database        │
    │                        │
    │  MATCH (u:User)       │
    │  RETURN               │
    │   u.id as user_id     │
    │   u.username ...      │
    │   u.email ...         │
    │   ... (9 fields)       │
    │  ORDER BY created_at  │
    │                        │
    │  Results: List[Dict]  │
    └────────────┬──────────┘
                 │
                 │ [{
                 │   'user_id': '123',
                 │   'username': 'john_doe',
                 │   'email': 'john@email.com',
                 │   'role': 'user',
                 │   'full_name': 'John Doe',
                 │   'phone': '+1234567890',
                 │   'is_verified': True,
                 │   'created_at': '2024-01-15',
                 │   'last_login': '2024-01-20'
                 │ }, ...]
                 │
                 ↓
    ┌────────────────────────┐
    │  CSV Generation        │
    │  (Python csv module)   │
    │                        │
    │  Headers:              │
    │  user_id,username,..   │
    │                        │
    │  Data Rows:            │
    │  123,john_doe,john@... │
    │  124,jane_doe,jane@... │
    │  ... (N rows)          │
    └────────────┬──────────┘
                 │
                 ↓
    ┌────────────────────────┐
    │  File Delivery         │
    │                        │
    │  Filename:             │
    │  users_export_         │
    │  20240115_143022.csv   │
    │                        │
    │  MIME Type:            │
    │  text/csv              │
    │                        │
    │  Encoding: UTF-8       │
    └────────────┬──────────┘
                 │
                 ↓
    Browser Downloads File
    to User's Computer
```

## Error Handling Flow

```
Export Request
    │
    ├─→ Try Block Starts
    │   │
    │   ├─→ Get DB Connection
    │   │   ├─ Success → Continue
    │   │   └─ Fail → Catch Exception
    │   │
    │   ├─→ Execute Query
    │   │   ├─ Success → Continue
    │   │   └─ Fail → Catch Exception
    │   │
    │   ├─→ Generate CSV
    │   │   ├─ Success → Continue
    │   │   └─ Fail → Catch Exception
    │   │
    │   └─→ Send File
    │       ├─ Success → Return File
    │       └─ Fail → Catch Exception
    │
    └─→ Except Block
        │
        ├─→ logger.error(exception)
        │   [Log for audit trail]
        │
        ├─→ flash('Error message', 'error')
        │   [Show user message]
        │
        └─→ redirect(url_for('admin.index'))
            [Return to dashboard]
```

## File Structure Overview

```
Project Root
│
├── blueprints/
│   └── admin/
│       ├── routes.py (MODIFIED)
│       │   ├── Imports (line 2-15)
│       │   │   ├── csv
│       │   │   ├── io
│       │   │   └── send_file
│       │   │
│       │   └── New Routes (line 1205-1410)
│       │       ├── export_users_csv()      [206 lines]
│       │       ├── export_businesses_csv() [206 lines]
│       │       ├── export_jobs_csv()       [206 lines]
│       │       └── export_all_csv()        [206 lines]
│       │
│       └── __init__.py
│
├── templates/
│   └── admin/
│       └── admin_dashboard.html (MODIFIED)
│           └── Data Export Section (line 102-180)
│               ├── Section Header
│               ├── 4 Export Cards
│               └── Info Box
│
├── database/
│   └── Neo4j connection (unchanged)
│
├── CSV_EXPORT_FEATURE.md (NEW)
├── CSV_EXPORT_IMPLEMENTATION.md (NEW)
├── CSV_EXPORT_QUICK_START.md (NEW)
└── CSV_EXPORT_FINAL_REPORT.md (NEW)
```

## Security & Access Control Flow

```
HTTP Request to /admin/export/users
│
├─→ Session Check
│   ├─ User logged in? 
│   │   ├─ Yes → Continue
│   │   └─ No → Redirect to login
│   │
│   └─ Valid session?
│       ├─ Yes → Continue
│       └─ No → Session expired
│
├─→ Role Check (@admin_required)
│   ├─ User is admin?
│   │   ├─ Yes → Process export
│   │   └─ No → Access denied
│   │
│   └─ Admin active?
│       ├─ Yes → Continue
│       └─ No → Access denied
│
├─→ Process Export
│   ├─ Query database
│   ├─ Generate CSV
│   └─ Deliver file
│
└─→ Audit Logging
    ├─ Log admin username
    ├─ Log export type
    ├─ Log timestamp
    └─ Log record count
```

## Technology Stack Diagram

```
┌──────────────────────────────────────────────────────────┐
│                    FRONTEND LAYER                        │
├──────────────────────────────────────────────────────────┤
│  HTML5 | CSS3 (Tailwind) | JavaScript                   │
│  └─ admin_dashboard.html (628 lines)                    │
│     ├─ Quick Stats Cards                                │
│     ├─ Data Export Section (NEW)                        │
│     │  ├─ Users Export Card                             │
│     │  ├─ Businesses Export Card                        │
│     │  ├─ Jobs Export Card                              │
│     │  └─ All Data Bundle Card                          │
│     └─ Management Tools                                 │
└──────────────────────────────────────────────────────────┘
                       │
                       │ HTTP Request/Response
                       │
┌──────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                     │
├──────────────────────────────────────────────────────────┤
│  Flask 2.3.3 | Python 3.13                              │
│  └─ blueprints/admin/routes.py (1410 lines)            │
│     ├─ Admin Dashboard Route                            │
│     ├─ Export Users Route (NEW)                         │
│     ├─ Export Businesses Route (NEW)                    │
│     ├─ Export Jobs Route (NEW)                          │
│     └─ Export All Bundle Route (NEW)                    │
└──────────────────────────────────────────────────────────┘
                       │
                       │ Cypher Queries
                       │
┌──────────────────────────────────────────────────────────┐
│                    DATABASE LAYER                        │
├──────────────────────────────────────────────────────────┤
│  Neo4j 5.12+ | Graph Database                           │
│  ├─ User Nodes                                          │
│  ├─ Business Nodes                                      │
│  ├─ Job Nodes                                           │
│  ├─ Review Nodes                                        │
│  ├─ Application Nodes                                   │
│  └─ Relationships (POSTED_BY, HAS_REVIEW, etc.)        │
└──────────────────────────────────────────────────────────┘
```

## Performance Timeline

```
User Clicks Export Button
        │
        ├─→ 0-50ms    : HTTP Request
        │
        ├─→ 50-100ms  : Auth/Session Check
        │
        ├─→ 100-200ms : Neo4j Query
        │
        ├─→ 200-300ms : CSV Generation
        │
        ├─→ 300-350ms : File Encoding
        │
        ├─→ 350-400ms : HTTP Response
        │
        └─→ 400ms+    : Browser Download

        Total Time: < 1 second (typical)
        File Available: User's Downloads folder
```

## Module Dependencies

```
routes.py
│
├─→ from flask import ...
│   ├─ render_template
│   ├─ request
│   ├─ redirect
│   ├─ url_for
│   ├─ flash
│   ├─ send_file ✨ NEW
│   └─ ...
│
├─→ import csv ✨ NEW
│   └─ csv.DictWriter()
│
├─→ import io ✨ NEW
│   ├─ io.StringIO()
│   └─ io.BytesIO()
│
├─→ import zipfile
│   └─ zipfile.ZipFile()
│
├─→ from database import ...
│   ├─ get_neo4j_db()
│   └─ safe_run()
│
├─→ from decorators import ...
│   └─ @admin_required
│
└─→ from datetime import datetime
    └─ datetime.utcnow()
```

---

These diagrams provide a comprehensive visual representation of the CSV export feature architecture, data flows, and component interactions.

