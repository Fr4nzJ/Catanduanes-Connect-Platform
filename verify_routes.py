import re

with open('templates/admin/admin_dashboard.html', 'r') as f:
    content = f.read()

# Find all url_for calls with admin_mgmt
matches = re.findall(r"url_for\('admin_mgmt\.(\w+)'\)", content)

print('[OK] Routes found in template:')
for route in sorted(set(matches)):
    print(f'  - admin_mgmt.{route}')

# Now verify all are valid
from blueprints.admin.management_routes import (
    dashboard, users_management, jobs_management, 
    business_management, verifications, reports_analytics
)

valid_routes = {
    'dashboard': dashboard,
    'users_management': users_management,
    'jobs_management': jobs_management,
    'business_management': business_management,
    'verifications': verifications,
    'reports_analytics': reports_analytics
}

print('\n[OK] Verifying all template routes are valid:')
for route in sorted(set(matches)):
    if route in valid_routes:
        print(f'  [PASS] {route}')
    else:
        print(f'  [FAIL] {route} not found')
