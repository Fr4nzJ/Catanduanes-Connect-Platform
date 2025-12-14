// Catanduanes Connect Platform - Business Seeding Query
// Copy and paste this entire query into Neo4j Browser

// Create 30 businesses for user 'ren' - 6d994a64-141a-462b-a880-03e0228b3ba7
WITH "6d994a64-141a-462b-a880-03e0228b3ba7" as owner_id,
     [
       {name: "Virac Seafood Trading", cat: "seafood", addr: "Virac"},
       {name: "Pandan Island Fishing Co.", cat: "seafood", addr: "Pandan"},
       {name: "Catanduanes Coconut Products", cat: "agriculture", addr: "Baras"},
       {name: "Baras Agricultural Supply", cat: "agriculture", addr: "Baras"},
       {name: "Viga Marine Resources", cat: "seafood", addr: "Viga"},
       {name: "Island Spice Exports", cat: "agriculture", addr: "Panganiban"},
       {name: "Catanduanes Tourism Services", cat: "tourism", addr: "Virac"},
       {name: "Pandan Furniture Workshop", cat: "manufacturing", addr: "Pandan"},
       {name: "Virac Hardware Store", cat: "retail", addr: "Virac"},
       {name: "Caramoran Beach Resort", cat: "hospitality", addr: "Caramoran"},
       {name: "Island Textile Industries", cat: "manufacturing", addr: "Pandan"},
       {name: "Catanduanes Coffee Roastery", cat: "retail", addr: "Virac"},
       {name: "Marine Tech Solutions", cat: "technology", addr: "Virac"},
       {name: "Virac Food Processing", cat: "manufacturing", addr: "Virac"},
       {name: "Agricultural Equipment Rental", cat: "agriculture", addr: "Baras"},
       {name: "Island Transport Services", cat: "logistics", addr: "Panganiban"},
       {name: "Pandan Craft Gallery", cat: "retail", addr: "Pandan"},
       {name: "Catanduanes Aquaculture", cat: "seafood", addr: "Caramoran"},
       {name: "Virac Printing Services", cat: "services", addr: "Virac"},
       {name: "Island Construction Materials", cat: "construction", addr: "Baras"},
       {name: "Catanduanes Travel Agency", cat: "tourism", addr: "Virac"},
       {name: "Baras Organic Farm", cat: "agriculture", addr: "Baras"},
       {name: "Pandan Hospitality Services", cat: "hospitality", addr: "Pandan"},
       {name: "Virac Logistics Hub", cat: "logistics", addr: "Virac"},
       {name: "Island Manufacturing Co.", cat: "manufacturing", addr: "Viga"},
       {name: "Catanduanes Retail Network", cat: "retail", addr: "Virac"},
       {name: "Pandan Services Group", cat: "services", addr: "Pandan"},
       {name: "Virac Trading Post", cat: "retail", addr: "Virac"},
       {name: "Island Entertainment Center", cat: "services", addr: "Caramoran"},
       {name: "Catanduanes Tech Services", cat: "technology", addr: "Virac"}
     ] as businesses
UNWIND range(0, size(businesses)-1) as idx
WITH businesses[idx] as b, idx + 1 as pos, owner_id
CREATE (business:Business {
  id: randomUuid(),
  name: b.name,
  category: b.cat,
  description: "A leading business in Catanduanes providing quality products and services.",
  address: b.addr + ", Catanduanes, Philippines",
  phone: "+63" + toString(toInteger(rand() * 100000000) + 900000000),
  email: "contact@" + replace(lower(b.name), " ", "") + ".ph",
  website: "www." + replace(lower(b.name), " ", "") + ".ph",
  owner_id: owner_id,
  is_active: true,
  is_verified: true,
  verification_status: "verified",
  employee_count: toInteger(rand() * 50) + 15,
  established_year: toInteger(2014 + rand() * 6),
  rating: round((rand() * 1.5 + 3.5) * 10) / 10,
  reviews_count: toInteger(rand() * 400) + 50,
  latitude: round((13.5 + rand() * 0.5) * 10000) / 10000,
  longitude: round((124.1 + rand() * 0.5) * 10000) / 10000,
  created_at: toString(datetime()),
  updated_at: toString(datetime()),
  business_hours: "8:00 AM - 5:00 PM",
  permit_number: "PERMIT-" + apoc.text.lpad(toString(pos), 3, "0") + "-2024",
  is_hiring: true
})
WITH count(*) as businesses_created
RETURN "SUCCESS: " + toString(businesses_created) + " businesses created!";
