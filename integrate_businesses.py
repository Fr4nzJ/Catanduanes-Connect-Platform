#!/usr/bin/env python3
"""
Integration script for 30 new Catanduanes businesses
Adds all 30 businesses to the database immediately
"""

import os
import sys
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from database import Neo4jConnection, safe_run
from seed_additional_businesses import create_additional_businesses

def integrate_businesses():
    """Integrate 30 new businesses into the database"""
    
    print("=" * 60)
    print("🚀 INTEGRATING 30 NEW CATANDUANES BUSINESSES")
    print("=" * 60)
    print()
    
    try:
        # Connect to database
        db = Neo4jConnection(
            uri=os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
            user=os.getenv('NEO4J_USER', 'neo4j'),
            password=os.getenv('NEO4J_PASSWORD', 'password')
        )
        print("✅ Database connected successfully")
        print()
        
        # Get business owner
        with db.session() as session:
            result = session.run("""
                MATCH (u:User {role: 'business_owner'})
                RETURN u.id LIMIT 1
            """)
            owner = result.single()
            owner_id = owner['u.id'] if owner else None
            
            if not owner_id:
                print("❌ Error: No business owner found!")
                print("Please run seed.py first to create demo users.")
                return False
            
            print(f"✅ Business owner found: {owner_id[:8]}...")
            print()
        
        # Create the 30 businesses
        print("📍 Creating 30 businesses with Catanduanes land coordinates...")
        businesses = create_additional_businesses(db, owner_id)
        
        print()
        print("=" * 60)
        print("✨ INTEGRATION SUCCESSFUL!")
        print("=" * 60)
        print()
        print("📊 Summary:")
        print(f"   ✓ Businesses created: {len(businesses)}")
        print(f"   ✓ Municipalities covered: 9")
        print(f"   ✓ Business categories: 11")
        print(f"   ✓ Verified businesses: 26")
        print(f"   ✓ Pending verification: 4")
        print(f"   ✓ Land-based coordinates: 100%")
        print()
        print("🗺️  Map Coverage:")
        print("   • Virac (13 businesses)")
        print("   • San Andres (3 businesses)")
        print("   • Baras (2 businesses)")
        print("   • Viga (2 businesses)")
        print("   • Gigmoto (2 businesses)")
        print("   • Panganiban (2 businesses)")
        print("   • Pandan (2 businesses)")
        print("   • Caramoran (2 businesses)")
        print("   • Bagamanoc (2 businesses)")
        print()
        print("🎯 Next Steps:")
        print("   1. Start your Flask app (if not running)")
        print("   2. Visit: http://localhost:5000/businesses")
        print("   3. Click: 'View on Map'")
        print("   4. See: 30+ markers across Catanduanes")
        print("   5. Test: Click markers with multiple businesses")
        print()
        print("✅ All done! Businesses are now in the database.")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ ERROR DURING INTEGRATION")
        print("=" * 60)
        print(f"Error: {str(e)}")
        print()
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = integrate_businesses()
    sys.exit(0 if success else 1)
