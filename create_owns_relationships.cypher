// Create OWNS relationships between ren user and all 30 businesses
// Run this in Neo4j Browser to link the user to the businesses

MATCH (u:User {id: "6d994a64-141a-462b-a880-03e0228b3ba7"})
MATCH (b:Business)
MERGE (u)-[:OWNS]->(b)
RETURN count(*) as relationships_created;


MATCH (u:User {id: "6d994a64-141a-462b-a880-03e0228b3ba7"})-[:OWNS]->(b:Business)
RETURN u.username as owner, count(b) as businesses_owned;
