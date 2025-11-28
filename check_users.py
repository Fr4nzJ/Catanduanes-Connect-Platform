import os
import sys
from neo4j import GraphDatabase, basic_auth

# Read config from environment with same defaults as config.py
NEO4J_URI = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.environ.get('NEO4J_USERNAME', os.environ.get('NEO4J_USER', 'neo4j'))
NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD', 'password')
NEO4J_DATABASE = os.environ.get('NEO4J_DATABASE', 'neo4j')

print(f"Connecting to Neo4j at {NEO4J_URI} as {NEO4J_USER} (database: {NEO4J_DATABASE})")

try:
    driver = GraphDatabase.driver(NEO4J_URI, auth=basic_auth(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session(database=NEO4J_DATABASE) as session:
        count_result = session.run("MATCH (u:User) RETURN count(u) AS count")
        count = count_result.single().get('count')
        print(f"User node count: {count}")

        if count and count > 0:
            print("Listing up to 10 users (id, email, username):")
            rows = session.run("MATCH (u:User) RETURN u.id AS id, u.email AS email, u.username AS username LIMIT 10")
            for r in rows:
                print(f" - id={r['id']}, email={r['email']}, username={r['username']}")
        else:
            print("No User nodes found in the database.")

    driver.close()
except Exception as e:
    print(f"Failed to connect or query Neo4j: {e}")
    sys.exit(2)
