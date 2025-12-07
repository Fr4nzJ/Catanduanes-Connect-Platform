#!/usr/bin/env python
"""Quick validation of the admin routes fixes"""

# Test 1: Cypher query syntax validation
print("=" * 60)
print("TEST 1: Validating Cypher query syntax fixes")
print("=" * 60)

# Simulate the user management query building
query = "MATCH (u:User) WHERE 1=1"
filters = [" AND u.is_active = true", " AND u.role = 'admin'"]

for filter_clause in filters:
    query += filter_clause

print(f"Original query: {query}")

# Test count query building
count_parts = query.split(' WHERE ', 1)
print(f"Split parts: {len(count_parts)}")
if len(count_parts) > 1:
    count_query = f"{count_parts[0]} WHERE {count_parts[1]} RETURN COUNT(u) as total"
else:
    count_query = query + " RETURN COUNT(u) as total"

print(f"Count query: {count_query}")
print()

# Test 2: Validate imports
print("=" * 60)
print("TEST 2: Validating Python imports")
print("=" * 60)

try:
    from blueprints.admin import management_routes
    print("✓ management_routes imported successfully")
except Exception as e:
    print(f"✗ Error importing management_routes: {e}")

try:
    from chatbot_core import chatbot
    print("✓ chatbot_core imported successfully")
except Exception as e:
    print(f"✗ Error importing chatbot_core: {e}")

try:
    from gemini_client import GeminiChat
    print("✓ gemini_client imported successfully")
except Exception as e:
    print(f"✗ Error importing gemini_client: {e}")

print()
print("=" * 60)
print("Validation complete!")
print("=" * 60)
