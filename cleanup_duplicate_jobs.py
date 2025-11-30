"""Clean up duplicate jobs and re-seed with correct relationships."""
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

def cleanup_and_verify():
    """Delete all jobs and their relationships, keep businesses."""
    with driver.session() as session:
        # Get count before cleanup
        result = session.run("MATCH (j:Job) RETURN count(j) as count")
        before_jobs = result.single()["count"]
        
        result = session.run("MATCH (b:Business) RETURN count(b) as count")
        before_businesses = result.single()["count"]
        
        print(f"Before cleanup:")
        print(f"  Jobs: {before_jobs}")
        print(f"  Businesses: {before_businesses}")
        
        # Delete all jobs and their relationships
        session.run("MATCH (j:Job) DETACH DELETE j")
        
        # Verify deletion
        result = session.run("MATCH (j:Job) RETURN count(j) as count")
        after_jobs = result.single()["count"]
        
        print(f"\nAfter cleanup:")
        print(f"  Jobs: {after_jobs}")
        print(f"  Businesses (should be same): {before_businesses}")
        
        # Verify OWNS relationships still exist
        result = session.run("MATCH (u:User)-[:OWNS]->(b:Business) RETURN count(*) as count")
        owns_count = result.single()["count"]
        print(f"  OWNS relationships: {owns_count}")

if __name__ == "__main__":
    try:
        cleanup_and_verify()
        print("\n✅ Cleanup complete. Ready to re-seed jobs with correct relationships.")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        driver.close()
