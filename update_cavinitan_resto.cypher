// Update Cavinitan Resto - Make it verified, featured, high rating, and add many unique jobs

MATCH (b:Business {id: "07f05620-3345-4a98-92f7-cdc6b070970f"})
SET b.is_verified = true,
    b.is_featured = true,
    b.rating = 4.9,
    b.review_count = 127,
    b.updated_at = datetime()

// Create multiple unique jobs for Cavinitan Resto
CREATE (j1:Job {
    id: randomUUID(),
    title: "Head Chef",
    description: "Lead our kitchen team and develop innovative Filipino dishes",
    location: "Cavinitan, Catanduanes",
    salary_range: "₱28,000 - ₱40,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: true,
    requirements: ["5+ years chef experience", "Filipino cuisine expertise", "Kitchen management"],
    created_at: datetime()
})
CREATE (b)-[:HAS_JOB]->(j1)

CREATE (j2:Job {
    id: randomUUID(),
    title: "Sous Chef",
    description: "Support head chef and manage food preparation",
    location: "Cavinitan, Catanduanes",
    salary_range: "₱20,000 - ₱30,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: true,
    requirements: ["3+ years cooking experience", "Food safety certified", "Team leadership"],
    created_at: datetime()
})
CREATE (b)-[:HAS_JOB]->(j2)

CREATE (j3:Job {
    id: randomUUID(),
    title: "Line Cook - Grill Station",
    description: "Operate grill and prepare grilled items",
    location: "Cavinitan, Catanduanes",
    salary_range: "₱17,000 - ₱24,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: true,
    requirements: ["2+ years cooking experience", "Grill expertise", "Food handling knowledge"],
    created_at: datetime()
})
CREATE (b)-[:HAS_JOB]->(j3)

CREATE (j4:Job {
    id: randomUUID(),
    title: "Line Cook - Sauce Station",
    description: "Prepare sauces and side dishes",
    location: "Cavinitan, Catanduanes",
    salary_range: "₱16,000 - ₱23,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: true,
    requirements: ["2+ years cooking experience", "Sauce and seasoning expertise"],
    created_at: datetime()
})
CREATE (b)-[:HAS_JOB]->(j4)

CREATE (j5:Job {
    id: randomUUID(),
    title: "Prep Cook",
    description: "Prepare ingredients and maintain station cleanliness",
    location: "Cavinitan, Catanduanes",
    salary_range: "₱14,000 - ₱20,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: true,
    requirements: ["1+ years kitchen experience", "Attention to detail"],
    created_at: datetime()
})
CREATE (b)-[:HAS_JOB]->(j5)

CREATE (j6:Job {
    id: randomUUID(),
    title: "Restaurant Manager",
    description: "Oversee daily operations and manage staff",
    location: "Cavinitan, Catanduanes",
    salary_range: "₱23,000 - ₱35,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: true,
    requirements: ["3+ years restaurant management", "Inventory control", "Staff training"],
    created_at: datetime()
})
CREATE (b)-[:HAS_JOB]->(j6)

CREATE (j7:Job {
    id: randomUUID(),
    title: "Front of House Supervisor",
    description: "Manage dining area staff and guest experiences",
    location: "Cavinitan, Catanduanes",
    salary_range: "₱18,000 - ₱27,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: true,
    requirements: ["2+ years restaurant service", "Leadership skills", "Customer service excellence"],
    created_at: datetime()
})
CREATE (b)-[:HAS_JOB]->(j7)

CREATE (j8:Job {
    id: randomUUID(),
    title: "Server - Dining Area",
    description: "Provide excellent service to restaurant guests",
    location: "Cavinitan, Catanduanes",
    salary_range: "₱14,000 - ₱20,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: true,
    requirements: ["1+ years service experience", "Hospitality skills", "Product knowledge"],
    created_at: datetime()
})
CREATE (b)-[:HAS_JOB]->(j8)

CREATE (j9:Job {
    id: randomUUID(),
    title: "Bartender",
    description: "Create cocktails and serve beverages",
    location: "Cavinitan, Catanduanes",
    salary_range: "₱16,000 - ₱26,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: true,
    requirements: ["Mixology knowledge", "2+ years bartending", "Inventory management"],
    created_at: datetime()
})
CREATE (b)-[:HAS_JOB]->(j9)

CREATE (j10:Job {
    id: randomUUID(),
    title: "Host/Hostess",
    description: "Greet guests and manage reservations",
    location: "Cavinitan, Catanduanes",
    salary_range: "₱13,000 - ₱18,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: true,
    requirements: ["Excellent communication", "Hospitality experience", "Reservation system knowledge"],
    created_at: datetime()
})
CREATE (b)-[:HAS_JOB]->(j10)

CREATE (j11:Job {
    id: randomUUID(),
    title: "Cashier",
    description: "Handle payments and manage cash register",
    location: "Cavinitan, Catanduanes",
    salary_range: "₱13,000 - ₱19,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: true,
    requirements: ["POS system experience", "Math skills", "Accuracy and honesty"],
    created_at: datetime()
})
CREATE (b)-[:HAS_JOB]->(j11)

CREATE (j12:Job {
    id: randomUUID(),
    title: "Dishwasher",
    description: "Maintain clean dishes and kitchen equipment",
    location: "Cavinitan, Catanduanes",
    salary_range: "₱12,000 - ₱17,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: true,
    requirements: ["Reliable and hardworking", "Attention to cleanliness"],
    created_at: datetime()
})
CREATE (b)-[:HAS_JOB]->(j12)

CREATE (j13:Job {
    id: randomUUID(),
    title: "Kitchen Cleaner",
    description: "Maintain kitchen cleanliness and sanitation standards",
    location: "Cavinitan, Catanduanes",
    salary_range: "₱12,000 - ₱17,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: true,
    requirements: ["Sanitation knowledge", "Attention to detail", "Responsibility"],
    created_at: datetime()
})
CREATE (b)-[:HAS_JOB]->(j13)

CREATE (j14:Job {
    id: randomUUID(),
    title: "Food Delivery Driver",
    description: "Deliver orders to customers",
    location: "Cavinitan, Catanduanes",
    salary_range: "₱15,000 - ₱23,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: true,
    requirements: ["Valid driver license", "Reliable vehicle", "Good navigation skills"],
    created_at: datetime()
})
CREATE (b)-[:HAS_JOB]->(j14)

CREATE (j15:Job {
    id: randomUUID(),
    title: "Marketing & Social Media Coordinator",
    description: "Manage restaurant social media and promotions",
    location: "Cavinitan, Catanduanes",
    salary_range: "₱17,000 - ₱26,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: true,
    requirements: ["Social media expertise", "Content creation", "Marketing knowledge"],
    created_at: datetime()
})
CREATE (b)-[:HAS_JOB]->(j15)

RETURN "Successfully updated Cavinitan Resto: verified ✓, featured ✓, high rating (4.9) ✓, and added 15 unique jobs ✓";
