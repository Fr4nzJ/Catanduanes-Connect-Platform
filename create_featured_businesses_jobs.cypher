// Create 30 Featured Businesses and 1 Featured Job each for user: 6d994a64-141a-462b-a880-03e0228b3ba7

MATCH (user:User {id: "6d994a64-141a-462b-a880-03e0228b3ba7"})
WITH user


CREATE (b1:Business {
    id: apoc.create.uuid(),
    name: "Premium Catering Services",
    category: "catering",
    description: "Professional catering services for events, conferences, and celebrations in Catanduanes",
    address: "123 Main St, Virac, Catanduanes",
    phone: "+63-9123456001",
    email: "catering1@catanduanes.com",
    website: "https://catering1.com",
    is_active: true,
    is_verified: true,
    is_featured: true,
    rating: 4.8,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b1)
CREATE (j1:Job {
    id: apoc.create.uuid(),
    title: "Event Coordinator",
    description: "Coordinate catering events and manage client relationships",
    location: "Virac, Catanduanes",
    salary_range: "₱18,000 - ₱25,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: true,
    requirements: ["2+ years experience", "Event planning knowledge"],
    created_at: datetime()
})
CREATE (b1)-[:HAS_JOB]->(j1)

// Business 2
CREATE (b2:Business {
    id: apoc.create.uuid(),
    name: "Tech Solutions Hub",
    category: "technology",
    description: "Software development and IT consulting services",
    address: "456 Tech Park, San Andres, Catanduanes",
    phone: "+63-9123456002",
    email: "techsolutions@catanduanes.com",
    website: "https://techsolutions.com",
    is_active: true,
    is_verified: true,
    is_featured: true,
    rating: 4.9,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b2)
CREATE (j2:Job {
    id: apoc.create.uuid(),
    title: "Full Stack Developer",
    description: "Develop web applications using modern frameworks",
    location: "San Andres, Catanduanes",
    salary_range: "₱30,000 - ₱45,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: true,
    requirements: ["Node.js", "React", "MongoDB"],
    created_at: datetime()
})
CREATE (b2)-[:HAS_JOB]->(j2)

// Business 3
CREATE (b3:Business {
    id: apoc.create.uuid(),
    name: "Island Wellness Resort",
    category: "hospitality",
    description: "Premium spa and wellness center with oceanview accommodations",
    address: "789 Resort Way, Panglao, Catanduanes",
    phone: "+63-9123456003",
    email: "wellness@catanduanes.com",
    website: "https://islandwellness.com",
    is_active: true,
    is_verified: true,
    is_featured: true,
    rating: 4.7,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b3)
CREATE (j3:Job {
    id: apoc.create.uuid(),
    title: "Spa Therapist",
    description: "Provide professional spa and massage services",
    location: "Panglao, Catanduanes",
    salary_range: "₱16,000 - ₱22,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: true,
    requirements: ["Spa certification", "3+ years experience"],
    created_at: datetime()
})
CREATE (b3)-[:HAS_JOB]->(j3)

// Business 4
CREATE (b4:Business {
    id: apoc.create.uuid(),
    name: "Green Farm Organic Products",
    category: "agriculture",
    description: "Organic vegetables and fruits grown locally in Catanduanes",
    address: "101 Farm Lane, Gigaquit, Catanduanes",
    phone: "+63-9123456004",
    email: "greenfarm@catanduanes.com",
    website: "https://greenfarm.com",
    is_active: true,
    is_verified: true,
    is_featured: true,
    rating: 4.6,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b4)
CREATE (j4:Job {
    id: apoc.create.uuid(),
    title: "Farm Manager",
    description: "Manage daily farm operations and harvest planning",
    location: "Gigaquit, Catanduanes",
    salary_range: "₱17,000 - ₱23,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: true,
    requirements: ["Agricultural knowledge", "Farm management experience"],
    created_at: datetime()
})
CREATE (b4)-[:HAS_JOB]->(j4)

// Business 5
CREATE (b5:Business {
    id: apoc.create.uuid(),
    name: "Creative Design Studio",
    category: "design",
    description: "Graphic design, branding, and digital marketing services",
    address: "202 Artist Ave, Virac, Catanduanes",
    phone: "+63-9123456005",
    email: "creative@catanduanes.com",
    website: "https://creativedesign.com",
    is_active: true,
    is_verified: true,
    is_featured: true,
    rating: 4.8,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b5)
CREATE (j5:Job {
    id: apoc.create.uuid(),
    title: "Graphic Designer",
    description: "Create visual designs for branding and marketing campaigns",
    location: "Virac, Catanduanes",
    salary_range: "₱19,000 - ₱28,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: true,
    requirements: ["Adobe Creative Suite", "3+ years design experience"],
    created_at: datetime()
})
CREATE (b5)-[:HAS_JOB]->(j5)

// Business 6
CREATE (b6:Business {
    id: apoc.create.uuid(),
    name: "Marine Fishing Co.",
    category: "fishing",
    description: "Sustainable fishing and seafood trading business",
    address: "303 Harbor St, San Andres, Catanduanes",
    phone: "+63-9123456006",
    email: "marinetrade@catanduanes.com",
    website: "https://marinefishing.com",
    is_active: true,
    is_verified: true,
    is_featured: true,
    rating: 4.5,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b6)
CREATE (j6:Job {
    id: apoc.create.uuid(),
    title: "Fishing Operations Lead",
    description: "Manage fishing operations and crew coordination",
    location: "San Andres, Catanduanes",
    salary_range: "₱20,000 - ₱30,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: true,
    requirements: ["Maritime experience", "Safety certification"],
    created_at: datetime()
})
CREATE (b6)-[:HAS_JOB]->(j6)

// Business 7
CREATE (b7:Business {
    id: apoc.create.uuid(),
    name: "Bamboo Crafts Cooperative",
    category: "handicrafts",
    description: "Traditional bamboo crafts and home decor items",
    address: "404 Craft Lane, Baras, Catanduanes",
    phone: "+63-9123456007",
    email: "bamboo@catanduanes.com",
    website: "https://bamboocrafts.com",
    is_active: true,
    is_verified: true,
    is_featured: true,
    rating: 4.7,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b7)
CREATE (j7:Job {
    id: apoc.create.uuid(),
    title: "Craft Artisan",
    description: "Create and produce traditional bamboo crafts",
    location: "Baras, Catanduanes",
    salary_range: "₱14,000 - ₱20,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: true,
    requirements: ["Craft skills", "Attention to detail"],
    created_at: datetime()
})
CREATE (b7)-[:HAS_JOB]->(j7)

// Business 8
CREATE (b8:Business {
    id: apoc.create.uuid(),
    name: "Digital Marketing Agency",
    category: "marketing",
    description: "Social media marketing and digital advertising services",
    address: "505 Marketing Blvd, Virac, Catanduanes",
    phone: "+63-9123456008",
    email: "digital@catanduanes.com",
    website: "https://digitalmarketing.com",
    is_active: true,
    is_verified: true,
    is_featured: true,
    rating: 4.9,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b8)
CREATE (j8:Job {
    id: apoc.create.uuid(),
    title: "Social Media Manager",
    description: "Manage social media accounts and create content strategies",
    location: "Virac, Catanduanes",
    salary_range: "₱18,000 - ₱26,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: true,
    requirements: ["Social media expertise", "Content creation skills"],
    created_at: datetime()
})
CREATE (b8)-[:HAS_JOB]->(j8)

// Business 9
CREATE (b9:Business {
    id: apoc.create.uuid(),
    name: "Construction & Engineering",
    category: "construction",
    description: "Building and infrastructure development services",
    address: "606 Build St, Gigaquit, Catanduanes",
    phone: "+63-9123456009",
    email: "construction@catanduanes.com",
    website: "https://construction.com",
    is_active: true,
    is_verified: true,
    is_featured: true,
    rating: 4.6,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b9)
CREATE (j9:Job {
    id: apoc.create.uuid(),
    title: "Project Engineer",
    description: "Oversee construction projects and quality control",
    location: "Gigaquit, Catanduanes",
    salary_range: "₱25,000 - ₱40,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: true,
    requirements: ["Civil engineering degree", "Project management experience"],
    created_at: datetime()
})
CREATE (b9)-[:HAS_JOB]->(j9)

// Business 10
CREATE (b10:Business {
    id: apoc.create.uuid(),
    name: "Local Coffee Roastery",
    category: "food_beverage",
    description: "Specialty coffee roasting and cafe services",
    address: "707 Coffee St, Panglao, Catanduanes",
    phone: "+63-9123456010",
    email: "coffee@catanduanes.com",
    website: "https://coffeeroastery.com",
    is_active: true,
    is_verified: true,
    is_featured: true,
    rating: 4.8,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b10)
CREATE (j10:Job {
    id: apoc.create.uuid(),
    title: "Barista & Cafe Manager",
    description: "Prepare coffee drinks and manage cafe operations",
    location: "Panglao, Catanduanes",
    salary_range: "₱15,000 - ₱21,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: true,
    requirements: ["Barista certification", "Customer service skills"],
    created_at: datetime()
})
CREATE (b10)-[:HAS_JOB]->(j10)

// Business 11
CREATE (b11:Business {
    id: apoc.create.uuid(),
    name: "Education & Tutoring Center",
    category: "education",
    description: "Academic tutoring and skills development programs",
    address: "808 School St, San Andres, Catanduanes",
    phone: "+63-9123456011",
    email: "education@catanduanes.com",
    website: "https://tutoring.com",
    is_active: true,
    is_verified: true,
    is_featured: true,
    rating: 4.7,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b11)
CREATE (j11:Job {
    id: apoc.create.uuid(),
    title: "Subject Tutor",
    description: "Provide academic tutoring in various subjects",
    location: "San Andres, Catanduanes",
    salary_range: "₱16,000 - ₱23,000",
    employment_type: "part_time",
    is_active: true,
    is_featured: true,
    requirements: ["Subject expertise", "Teaching experience"],
    created_at: datetime()
})
CREATE (b11)-[:HAS_JOB]->(j11)

// Business 12
CREATE (b12:Business {
    id: apoc.create.uuid(),
    name: "Fashion & Apparel Store",
    category: "retail",
    description: "Contemporary fashion and clothing retail",
    address: "909 Fashion Ave, Virac, Catanduanes",
    phone: "+63-9123456012",
    email: "fashion@catanduanes.com",
    website: "https://fashionstore.com",
    is_active: true,
    is_verified: true,
    is_featured: true,
    rating: 4.6,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b12)
CREATE (j12:Job {
    id: apoc.create.uuid(),
    title: "Fashion Sales Associate",
    description: "Assist customers and manage inventory",
    location: "Virac, Catanduanes",
    salary_range: "₱14,000 - ₱19,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: true,
    requirements: ["Customer service", "Fashion knowledge"],
    created_at: datetime()
})
CREATE (b12)-[:HAS_JOB]->(j12)

// Business 13
CREATE (b13:Business {
    id: apoc.create.uuid(),
    name: "Fitness & Wellness Center",
    category: "fitness",
    description: "Modern gym and fitness training facility",
    address: "1010 Gym Blvd, Baras, Catanduanes",
    phone: "+63-9123456013",
    email: "fitness@catanduanes.com",
    website: "https://fitnesscenter.com",
    is_active: true,
    is_verified: true,
    is_featured: true,
    rating: 4.8,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b13)
CREATE (j13:Job {
    id: apoc.create.uuid(),
    title: "Fitness Trainer",
    description: "Conduct fitness classes and personal training",
    location: "Baras, Catanduanes",
    salary_range: "₱17,000 - ₱25,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: true,
    requirements: ["Fitness certification", "Personal training experience"],
    created_at: datetime()
})
CREATE (b13)-[:HAS_JOB]->(j13)

// Business 14
CREATE (b14:Business {
    id: apoc.create.uuid(),
    name: "Healthcare Clinic",
    category: "healthcare",
    description: "General medical services and health consultations",
    address: "1111 Medical St, Gigaquit, Catanduanes",
    phone: "+63-9123456014",
    email: "healthcare@catanduanes.com",
    website: "https://healthclinic.com",
    is_active: true,
    is_verified: true,
    is_featured: true,
    rating: 4.9,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b14)
CREATE (j14:Job {
    id: apoc.create.uuid(),
    title: "Registered Nurse",
    description: "Provide nursing care and patient support",
    location: "Gigaquit, Catanduanes",
    salary_range: "₱23,000 - ₱35,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: true,
    requirements: ["RN License", "Healthcare experience"],
    created_at: datetime()
})
CREATE (b14)-[:HAS_JOB]->(j14)

// Business 15
CREATE (b15:Business {
    id: apoc.create.uuid(),
    name: "Real Estate Solutions",
    category: "real_estate",
    description: "Property sales and rental services",
    address: "1212 Property St, Panglao, Catanduanes",
    phone: "+63-9123456015",
    email: "realestate@catanduanes.com",
    website: "https://realestate.com",
    is_active: true,
    is_verified: true,
    is_featured: true,
    rating: 4.7,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b15)
CREATE (j15:Job {
    id: apoc.create.uuid(),
    title: "Real Estate Agent",
    description: "Sell properties and manage client relationships",
    location: "Panglao, Catanduanes",
    salary_range: "₱18,000 - ₱32,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: true,
    requirements: ["Real estate license", "Sales experience"],
    created_at: datetime()
})
CREATE (b15)-[:HAS_JOB]->(j15)

// Business 16
CREATE (b16:Business {
    id: apoc.create.uuid(),
    name: "Automotive Services",
    category: "automotive",
    description: "Car repairs and maintenance services",
    address: "1313 Auto St, San Andres, Catanduanes",
    phone: "+63-9123456016",
    email: "auto@catanduanes.com",
    website: "https://autoservices.com",
    is_active: true,
    is_verified: true,
    is_featured: true,
    rating: 4.6,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b16)
CREATE (j16:Job {
    id: apoc.create.uuid(),
    title: "Automotive Technician",
    description: "Perform vehicle repairs and maintenance",
    location: "San Andres, Catanduanes",
    salary_range: "₱18,000 - ₱27,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: true,
    requirements: ["Mechanical skills", "Automotive certification"],
    created_at: datetime()
})
CREATE (b16)-[:HAS_JOB]->(j16)

// Business 17
CREATE (b17:Business {
    id: apoc.create.uuid(),
    name: "Printing & Publishing",
    category: "printing",
    description: "Commercial printing and publishing services",
    address: "1414 Print St, Virac, Catanduanes",
    phone: "+63-9123456017",
    email: "printing@catanduanes.com",
    website: "https://printing.com",
    is_active: true,
    is_verified: true,
    is_featured: true,
    rating: 4.5,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b17)
CREATE (j17:Job {
    id: apoc.create.uuid(),
    title: "Print Operator",
    description: "Operate printing equipment and manage production",
    location: "Virac, Catanduanes",
    salary_range: "₱16,000 - ₱24,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: true,
    requirements: ["Printing equipment experience", "Technical skills"],
    created_at: datetime()
})
CREATE (b17)-[:HAS_JOB]->(j17)

// Business 18
CREATE (b18:Business {
    id: randomUUID(),
    name: "Travel & Tourism Agency",
    category: "tourism",
    description: "Travel planning and tour services",
    address: "1515 Travel Ave, Baras, Catanduanes",
    phone: "+63-9123456018",
    email: "travel@catanduanes.com",
    website: "https://travelagency.com",
    is_active: true,
    is_verified: true,
    is_featured: true,
    rating: 4.8,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b18)
CREATE (j18:Job {
    id: randomUUID(),
    title: "Travel Consultant",
    description: "Plan and arrange travel itineraries for clients",
    location: "Baras, Catanduanes",
    salary_range: "₱17,000 - ₱26,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: true,
    requirements: ["Travel industry knowledge", "Customer service"],
    created_at: datetime()
})
CREATE (b18)-[:HAS_JOB]->(j18)

// Business 19
CREATE (b19:Business {
    id: randomUUID(),
    name: "Electrical Contractor",
    category: "electrical",
    description: "Electrical installation and repair services",
    address: "1616 Electric St, Gigaquit, Catanduanes",
    phone: "+63-9123456019",
    email: "electric@catanduanes.com",
    website: "https://electric.com",
    is_active: true,
    is_verified: true,
    is_featured: true,
    rating: 4.7,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b19)
CREATE (j19:Job {
    id: randomUUID(),
    title: "Licensed Electrician",
    description: "Install and repair electrical systems",
    location: "Gigaquit, Catanduanes",
    salary_range: "₱19,000 - ₱30,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: true,
    requirements: ["Electrical license", "Safety certification"],
    created_at: datetime()
})
CREATE (b19)-[:HAS_JOB]->(j19)

// Business 20
CREATE (b20:Business {
    id: apoc.create.uuid(),
    name: "Plumbing Services",
    category: "plumbing",
    description: "Plumbing installation and maintenance",
    address: "1717 Plumb St, Panglao, Catanduanes",
    phone: "+63-9123456020",
    email: "plumbing@catanduanes.com",
    website: "https://plumbing.com",
    is_active: true,
    is_verified: true,
    is_featured: true,
    rating: 4.6,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b20)
CREATE (j20:Job {
    id: apoc.create.uuid(),
    title: "Master Plumber",
    description: "Handle plumbing repairs and installations",
    location: "Panglao, Catanduanes",
    salary_range: "₱18,000 - ₱28,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: true,
    requirements: ["Plumbing license", "Technical expertise"],
    created_at: datetime()
})
CREATE (b20)-[:HAS_JOB]->(j20)

// Business 21
CREATE (b21:Business {
    id: apoc.create.uuid(),
    name: "Interior Design Studio",
    category: "design",
    description: "Interior design and space planning services",
    address: "1818 Design St, San Andres, Catanduanes",
    phone: "+63-9123456021",
    email: "interior@catanduanes.com",
    website: "https://interior.com",
    is_active: true,
    is_verified: true,
    is_featured: true,
    rating: 4.9,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b21)
CREATE (j21:Job {
    id: apoc.create.uuid(),
    title: "Interior Designer",
    description: "Design interior spaces and manage projects",
    location: "San Andres, Catanduanes",
    salary_range: "₱22,000 - ₱35,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: true,
    requirements: ["Design degree", "Portfolio experience"],
    created_at: datetime()
})
CREATE (b21)-[:HAS_JOB]->(j21)

// Business 22
CREATE (b22:Business {
    id: apoc.create.uuid(),
    name: "Photography Studio",
    category: "photography",
    description: "Professional photography and videography services",
    address: "1919 Photo Ave, Virac, Catanduanes",
    phone: "+63-9123456022",
    email: "photo@catanduanes.com",
    website: "https://photostudio.com",
    is_active: true,
    is_verified: true,
    is_featured: true,
    rating: 4.8,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b22)
CREATE (j22:Job {
    id: apoc.create.uuid(),
    title: "Photographer",
    description: "Capture events and product photography",
    location: "Virac, Catanduanes",
    salary_range: "₱17,000 - ₱27,000",
    employment_type: "freelance",
    is_active: true,
    is_featured: true,
    requirements: ["Photography skills", "Equipment knowledge"],
    created_at: datetime()
})
CREATE (b22)-[:HAS_JOB]->(j22)

// Business 23
CREATE (b23:Business {
    id: apoc.create.uuid(),
    name: "Laundry & Dry Cleaning",
    category: "services",
    description: "Professional laundry and dry cleaning services",
    address: "2020 Clean St, Baras, Catanduanes",
    phone: "+63-9123456023",
    email: "laundry@catanduanes.com",
    website: "https://laundry.com",
    is_active: true,
    is_verified: true,
    is_featured: true,
    rating: 4.5,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b23)
CREATE (j23:Job {
    id: apoc.create.uuid(),
    title: "Laundry Specialist",
    description: "Process and manage laundry operations",
    location: "Baras, Catanduanes",
    salary_range: "₱13,000 - ₱18,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: true,
    requirements: ["Laundry experience", "Attention to detail"],
    created_at: datetime()
})
CREATE (b23)-[:HAS_JOB]->(j23)

// Business 24
CREATE (b24:Business {
    id: apoc.create.uuid(),
    name: "Pest Control Services",
    category: "services",
    description: "Professional pest management and control",
    address: "2121 Pest St, Gigaquit, Catanduanes",
    phone: "+63-9123456024",
    email: "pestcontrol@catanduanes.com",
    website: "https://pestcontrol.com",
    is_active: true,
    is_verified: true,
    is_featured: true,
    rating: 4.7,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b24)
CREATE (j24:Job {
    id: apoc.create.uuid(),
    title: "Pest Control Technician",
    description: "Execute pest control treatments and inspections",
    location: "Gigaquit, Catanduanes",
    salary_range: "₱15,000 - ₱22,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: true,
    requirements: ["Pest control certification", "Safety training"],
    created_at: datetime()
})
CREATE (b24)-[:HAS_JOB]->(j24)

// Business 25
CREATE (b25:Business {
    id: apoc.create.uuid(),
    name: "Security & Protection",
    category: "security",
    description: "Security services and surveillance systems",
    address: "2222 Security Ave, Panglao, Catanduanes",
    phone: "+63-9123456025",
    email: "security@catanduanes.com",
    website: "https://security.com",
    is_active: true,
    is_verified: true,
    is_featured: true,
    rating: 4.8,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b25)
CREATE (j25:Job {
    id: apoc.create.uuid(),
    title: "Security Guard",
    description: "Provide security services and patrol areas",
    location: "Panglao, Catanduanes",
    salary_range: "₱14,000 - ₱20,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: true,
    requirements: ["Security training", "Alert and responsible"],
    created_at: datetime()
})
CREATE (b25)-[:HAS_JOB]->(j25)

// Business 26
CREATE (b26:Business {
    id: apoc.create.uuid(),
    name: "Logistics & Delivery",
    category: "logistics",
    description: "Courier and delivery services throughout Catanduanes",
    address: "2323 Delivery St, San Andres, Catanduanes",
    phone: "+63-9123456026",
    email: "logistics@catanduanes.com",
    website: "https://logistics.com",
    is_active: true,
    is_verified: true,
    is_featured: true,
    rating: 4.6,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b26)
CREATE (j26:Job {
    id: apoc.create.uuid(),
    title: "Delivery Driver",
    description: "Deliver packages and manage deliveries",
    location: "San Andres, Catanduanes",
    salary_range: "₱15,000 - ₱23,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: true,
    requirements: ["Valid driver license", "Reliable and punctual"],
    created_at: datetime()
})
CREATE (b26)-[:HAS_JOB]->(j26)

// Business 27
CREATE (b27:Business {
    id: apoc.create.uuid(),
    name: "Consulting Firm",
    category: "consulting",
    description: "Business and strategic consulting services",
    address: "2424 Consult Ave, Virac, Catanduanes",
    phone: "+63-9123456027",
    email: "consulting@catanduanes.com",
    website: "https://consulting.com",
    is_active: true,
    is_verified: true,
    is_featured: true,
    rating: 4.9,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b27)
CREATE (j27:Job {
    id: apoc.create.uuid(),
    title: "Business Consultant",
    description: "Provide strategic business consulting",
    location: "Virac, Catanduanes",
    salary_range: "₱28,000 - ₱45,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: true,
    requirements: ["MBA preferred", "Consulting experience"],
    created_at: datetime()
})
CREATE (b27)-[:HAS_JOB]->(j27)

// Business 28
CREATE (b28:Business {
    id: apoc.create.uuid(),
    name: "Pet Care & Veterinary",
    category: "pet_care",
    description: "Veterinary services and pet grooming",
    address: "2525 Pet St, Baras, Catanduanes",
    phone: "+63-9123456028",
    email: "petcare@catanduanes.com",
    website: "https://petcare.com",
    is_active: true,
    is_verified: true,
    is_featured: true,
    rating: 4.8,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b28)
CREATE (j28:Job {
    id: apoc.create.uuid(),
    title: "Veterinary Technician",
    description: "Assist veterinarians and provide pet care",
    location: "Baras, Catanduanes",
    salary_range: "₱18,000 - ₱26,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: true,
    requirements: ["Veterinary training", "Animal care experience"],
    created_at: datetime()
})
CREATE (b28)-[:HAS_JOB]->(j28)

// Business 29
CREATE (b29:Business {
    id: apoc.create.uuid(),
    name: "Insurance Services",
    category: "finance",
    description: "Insurance products and advisory services",
    address: "2626 Insurance Blvd, Gigaquit, Catanduanes",
    phone: "+63-9123456029",
    email: "insurance@catanduanes.com",
    website: "https://insurance.com",
    is_active: true,
    is_verified: true,
    is_featured: true,
    rating: 4.7,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b29)
CREATE (j29:Job {
    id: apoc.create.uuid(),
    title: "Insurance Agent",
    description: "Sell insurance products and manage accounts",
    location: "Gigaquit, Catanduanes",
    salary_range: "₱17,000 - ₱30,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: true,
    requirements: ["Insurance license", "Sales experience"],
    created_at: datetime()
})
CREATE (b29)-[:HAS_JOB]->(j29)

// Business 30
CREATE (b30:Business {
    id: apoc.create.uuid(),
    name: "Entertainment & Events",
    category: "entertainment",
    description: "Event management and entertainment services",
    address: "2727 Event St, Panglao, Catanduanes",
    phone: "+63-9123456030",
    email: "events@catanduanes.com",
    website: "https://events.com",
    is_active: true,
    is_verified: true,
    is_featured: true,
    rating: 4.9,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b30)
CREATE (j30:Job {
    id: apoc.create.uuid(),
    title: "Event Manager",
    description: "Organize and coordinate entertainment events",
    location: "Panglao, Catanduanes",
    salary_range: "₱20,000 - ₱32,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: true,
    requirements: ["Event management experience", "Creative skills"],
    created_at: datetime()
})
CREATE (b30)-[:HAS_JOB]->(j30)

RETURN "Successfully created 30 featured businesses with 1 featured job each, all owned by user 6d994a64-141a-462b-a880-03e0228b3ba7";
