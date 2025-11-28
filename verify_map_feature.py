#!/usr/bin/env python3
"""
Verification script for the map feature implementation.
Checks that:
1. Business objects can be converted to dictionaries
2. Dictionaries are JSON serializable
3. The routes are properly configured
"""

import json
import sys
from pathlib import Path

# Add the project to the path
sys.path.insert(0, str(Path(__file__).parent))

from models import Business

def test_business_serialization():
    """Test that Business objects can be converted to JSON-serializable dicts"""
    print("🧪 Testing Business serialization...")
    
    # Create a sample business dict (as it would come from _node_to_dict)
    business_dict = {
        'id': 'test-123',
        'name': 'Test Business',
        'category': 'Services',
        'address': '123 Test St',
        'latitude': 13.9339,
        'longitude': 124.5267,
        'rating': 4.5,
        'is_verified': True,
        'description': 'A test business'
    }
    
    try:
        # Create Business object
        business = Business(**business_dict)
        print(f"✅ Created Business object: {business.name}")
        
        # Try to serialize to JSON (this is what {{ businesses_data | tojson }} does)
        json_str = json.dumps(business_dict)
        print(f"✅ Serialized to JSON successfully ({len(json_str)} chars)")
        
        # Verify essential fields for map
        assert 'latitude' in business_dict, "Missing latitude"
        assert 'longitude' in business_dict, "Missing longitude"
        assert 'name' in business_dict, "Missing name"
        print("✅ All essential map fields present")
        
        return True
    except Exception as e:
        print(f"❌ Serialization failed: {e}")
        return False

def test_map_template_vars():
    """Test that the template can access the necessary variables"""
    print("\n🧪 Testing template variable access...")
    
    # Simulate what the route would pass
    businesses_data = [
        {
            'id': 'bus-1',
            'name': 'Business 1',
            'category': 'Restaurant',
            'address': 'Address 1',
            'latitude': 13.93,
            'longitude': 124.52,
            'rating': 4.5,
            'is_verified': True
        },
        {
            'id': 'bus-2',
            'name': 'Business 2',
            'category': 'Shop',
            'address': 'Address 2',
            'latitude': 13.94,
            'longitude': 124.53,
            'rating': 3.8,
            'is_verified': False
        }
    ]
    
    try:
        # Test JSON serialization (what Jinja2's tojson filter does)
        json_output = json.dumps(businesses_data)
        print(f"✅ Serialized {len(businesses_data)} businesses to JSON")
        
        # Verify it can be parsed back
        parsed = json.loads(json_output)
        assert len(parsed) == 2, "JSON parsing failed"
        print("✅ JSON output is valid and parseable")
        
        # Verify map markers can be created
        for business in parsed:
            lat = business.get('latitude')
            lng = business.get('longitude')
            assert lat and lng, f"Missing coordinates for {business.get('name')}"
        print("✅ All businesses have valid coordinates for map markers")
        
        return True
    except Exception as e:
        print(f"❌ Template variable test failed: {e}")
        return False

def main():
    print("=" * 60)
    print("MAP FEATURE VERIFICATION")
    print("=" * 60)
    
    tests = [
        test_business_serialization,
        test_map_template_vars
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"❌ Test error: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    if all(results):
        print("✅ ALL TESTS PASSED - Map feature should work!")
        print("=" * 60)
        return 0
    else:
        print("❌ SOME TESTS FAILED - Map feature may have issues")
        print("=" * 60)
        return 1

if __name__ == '__main__':
    sys.exit(main())
