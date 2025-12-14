# Quick Neo4j Seeding Guide

Run these Cypher queries directly in Neo4j Browser at: https://console.neo4j.io

## Step 1: Create 30 Businesses

Copy and paste this query into Neo4j Browser console:

```cypher
WITH "6d994a64-141a-462b-a880-03e0228b3ba7" as owner_id
UNWIND [
  {name: "Virac Seafood Trading", cat: "seafood", pos: 1},
  {name: "Pandan Island Fishing Co.", cat: "seafood", pos: 2},
  {name: "Catanduanes Coconut Products", cat: "agriculture", pos: 3},
  {name: "Baras Agricultural Supply", cat: "agriculture", pos: 4},
  {name: "Viga Marine Resources", cat: "seafood", pos: 5},
  {name: "Island Spice Exports", cat: "agriculture", pos: 6},
  {name: "Catanduanes Tourism Services", cat: "tourism", pos: 7},
  {name: "Pandan Furniture Workshop", cat: "manufacturing", pos: 8},
  {name: "Virac Hardware Store", cat: "retail", pos: 9},
  {name: "Caramoran Beach Resort", cat: "hospitality", pos: 10},
  {name: "Island Textile Industries", cat: "manufacturing", pos: 11},
  {name: "Catanduanes Coffee Roastery", cat: "retail", pos: 12},
  {name: "Marine Tech Solutions", cat: "technology", pos: 13},
  {name: "Virac Food Processing", cat: "manufacturing", pos: 14},
  {name: "Agricultural Equipment Rental", cat: "agriculture", pos: 15},
  {name: "Island Transport Services", cat: "logistics", pos: 16},
  {name: "Pandan Craft Gallery", cat: "retail", pos: 17},
  {name: "Catanduanes Aquaculture", cat: "seafood", pos: 18},
  {name: "Virac Printing Services", cat: "services", pos: 19},
  {name: "Island Construction Materials", cat: "construction", pos: 20},
  {name: "Catanduanes Travel Agency", cat: "tourism", pos: 21},
  {name: "Baras Organic Farm", cat: "agriculture", pos: 22},
  {name: "Pandan Hospitality Services", cat: "hospitality", pos: 23},
  {name: "Virac Logistics Hub", cat: "logistics", pos: 24},
  {name: "Island Manufacturing Co.", cat: "manufacturing", pos: 25},
  {name: "Catanduanes Retail Network", cat: "retail", pos: 26},
  {name: "Pandan Services Group", cat: "services", pos: 27},
  {name: "Virac Trading Post", cat: "retail", pos: 28},
  {name: "Island Entertainment Center", cat: "services", pos: 29},
  {name: "Catanduanes Tech Services", cat: "technology", pos: 30}
] as b
CREATE (business:Business {
  id: randomUuid(),
  name: b.name,
  category: b.cat,
  description: "A leading business in Catanduanes providing quality products and services since 2015.",
  address: "Catanduanes, Philippines",
  phone: "+63" + (900000000 + toInteger(rand() * 100000000)),
  email: "contact@" + replace(lower(b.name), " ", "") + ".ph",
  website: "www." + replace(lower(b.name), " ", "") + ".ph",
  owner_id: owner_id,
  is_active: true,
  is_verified: true,
  verification_status: "verified",
  employee_count: toInteger(20 + rand() * 50),
  established_year: toInteger(2014 + rand() * 6),
  rating: round((3.5 + rand() * 1.5) * 10) / 10,
  reviews_count: toInteger(50 + rand() * 400),
  latitude: 13.5 + rand() * 0.5,
  longitude: 124.1 + rand() * 0.5,
  created_at: toString(datetime()),
  updated_at: toString(datetime()),
  business_hours: "8:00 AM - 5:00 PM",
  permit_number: "PERMIT-" + right("00" + toString(b.pos), 3) + "-2024",
  is_hiring: true
})
RETURN count(*) as businesses_created;
```

**Expected Result:** Should show `businesses_created: 30`

## Step 2: Create OWNS Relationships

```cypher
MATCH (u:User {id: "6d994a64-141a-462b-a880-03e0228b3ba7"})
MATCH (b:Business {owner_id: "6d994a64-141a-462b-a880-03e0228b3ba7"})
MERGE (u)-[:OWNS]->(b)
RETURN count(*) as relationships_created;
```

**Expected Result:** Should show `relationships_created: 30`

## Step 3: Create Sample Jobs for Each Business

Run for EACH business individually (or use a loop). Example:

```cypher
MATCH (b:Business {name: "Virac Seafood Trading"})
WITH b
UNWIND range(1, 30) as job_num
CREATE (job:Job {
  id: randomUuid(),
  title: "Sales Representative - " + b.name + " (" + toString(job_num) + ")",
  description: "We are hiring a Sales Representative for " + b.name + ". Excellent opportunity to grow your career.",
  business_id: b.id,
  category: b.category,
  employment_type: "Full-time",
  salary_min: 15000,
  salary_max: 50000,
  location: "Catanduanes, Philippines",
  skills_required: ["communication", "sales", "teamwork"],
  benefits: ["Health Insurance", "Paid Leave", "Training"],
  deadline: date() + duration({days: 30}),
  posted_date: date(),
  created_at: toString(datetime()),
  updated_at: toString(datetime()),
  is_active: true
})
CREATE (b)-[:POSTS]->(job)
RETURN count(*) as jobs_created;
```

Repeat for each of the 30 businesses (change the business name each time).

---

## Alternative: Run Everything at Once

If Neo4j supports batch operations, you can combine all into one large transaction.

## Verify Results

```cypher
MATCH (b:Business) RETURN count(b) as total_businesses;
MATCH (j:Job) RETURN count(j) as total_jobs;
MATCH (u)-[:OWNS]->(b) RETURN count(*) as owner_relationships;
```
