MATCH (user:User {id: "6d994a64-141a-462b-a880-03e0228b3ba7"})
WITH user

// Business 1
CREATE (b1:Business {
    id: randomUUID(),
    name: "Local Noodle Shop",
    category: "food_beverage",
    description: "Traditional Filipino noodle dishes",
    address: "100 Street, Virac, Catanduanes",
    phone: "+63-9123456101",
    email: "noodles1@catanduanes.com",
    website: "",
    is_active: true,
    is_verified: false,
    is_featured: false,
    rating: 0.0,
    review_count: 0,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b1)
CREATE (j1:Job {
    id: randomUUID(),
    title: "Noodle Shop Staff",
    description: "Prepare and serve noodle dishes",
    location: "Virac, Catanduanes",
    salary_range: "₱12,000 - ₱18,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: false,
    requirements: ["Food handling", "Customer service"],
    created_at: datetime()
})
CREATE (b1)-[:HAS_JOB]->(j1)

// Business 2
CREATE (b2:Business {
    id: randomUUID(),
    name: "Small Sari-Sari Store",
    category: "retail",
    description: "Community convenience store",
    address: "200 Street, San Andres, Catanduanes",
    phone: "+63-9123456102",
    email: "sari@catanduanes.com",
    website: "",
    is_active: true,
    is_verified: false,
    is_featured: false,
    rating: 0.0,
    review_count: 0,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b2)
CREATE (j2:Job {
    id: randomUUID(),
    title: "Store Attendant",
    description: "Manage store operations and inventory",
    location: "San Andres, Catanduanes",
    salary_range: "₱11,000 - ₱17,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: false,
    requirements: ["Retail experience", "Basic math"],
    created_at: datetime()
})
CREATE (b2)-[:HAS_JOB]->(j2)

// Business 3
CREATE (b3:Business {
    id: randomUUID(),
    name: "Mobile Phone Repair",
    category: "repair",
    description: "Phone repairs and maintenance",
    address: "300 Street, Panglao, Catanduanes",
    phone: "+63-9123456103",
    email: "phonerepair@catanduanes.com",
    website: "",
    is_active: true,
    is_verified: false,
    is_featured: false,
    rating: 0.0,
    review_count: 0,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b3)
CREATE (j3:Job {
    id: randomUUID(),
    title: "Technician",
    description: "Repair mobile devices",
    location: "Panglao, Catanduanes",
    salary_range: "₱15,000 - ₱23,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: false,
    requirements: ["Technical skills", "Phone repair knowledge"],
    created_at: datetime()
})
CREATE (b3)-[:HAS_JOB]->(j3)

// Business 4
CREATE (b4:Business {
    id: randomUUID(),
    name: "Hairdressing Salon",
    category: "beauty",
    description: "Hair styling and grooming services",
    address: "400 Street, Baras, Catanduanes",
    phone: "+63-9123456104",
    email: "salon@catanduanes.com",
    website: "",
    is_active: true,
    is_verified: false,
    is_featured: false,
    rating: 0.0,
    review_count: 0,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b4)
CREATE (j4:Job {
    id: randomUUID(),
    title: "Hair Stylist",
    description: "Provide hair styling services",
    location: "Baras, Catanduanes",
    salary_range: "₱14,000 - ₱21,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: false,
    requirements: ["Cosmetology training", "Styling expertise"],
    created_at: datetime()
})
CREATE (b4)-[:HAS_JOB]->(j4)

// Business 5
CREATE (b5:Business {
    id: randomUUID(),
    name: "Clothing Boutique",
    category: "retail",
    description: "Fashion and clothing retail",
    address: "500 Street, Gigaquit, Catanduanes",
    phone: "+63-9123456105",
    email: "boutique@catanduanes.com",
    website: "",
    is_active: true,
    is_verified: false,
    is_featured: false,
    rating: 0.0,
    review_count: 0,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b5)
CREATE (j5:Job {
    id: randomUUID(),
    title: "Sales Associate",
    description: "Assist customers and manage inventory",
    location: "Gigaquit, Catanduanes",
    salary_range: "₱13,000 - ₱19,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: false,
    requirements: ["Retail experience", "Customer service"],
    created_at: datetime()
})
CREATE (b5)-[:HAS_JOB]->(j5)

// Business 6
CREATE (b6:Business {
    id: randomUUID(),
    name: "Home Cleaning Service",
    category: "services",
    description: "Residential cleaning services",
    address: "600 Street, Virac, Catanduanes",
    phone: "+63-9123456106",
    email: "cleaning@catanduanes.com",
    website: "",
    is_active: true,
    is_verified: false,
    is_featured: false,
    rating: 0.0,
    review_count: 0,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b6)
CREATE (j6:Job {
    id: randomUUID(),
    title: "Cleaning Staff",
    description: "Provide residential cleaning services",
    location: "Virac, Catanduanes",
    salary_range: "₱12,000 - ₱18,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: false,
    requirements: ["Cleaning experience", "Reliability"],
    created_at: datetime()
})
CREATE (b6)-[:HAS_JOB]->(j6)

// Business 7
CREATE (b7:Business {
    id: randomUUID(),
    name: "Bicycle Repair Shop",
    category: "repair",
    description: "Bicycle maintenance and repairs",
    address: "700 Street, San Andres, Catanduanes",
    phone: "+63-9123456107",
    email: "bikes@catanduanes.com",
    website: "",
    is_active: true,
    is_verified: false,
    is_featured: false,
    rating: 0.0,
    review_count: 0,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b7)
CREATE (j7:Job {
    id: randomUUID(),
    title: "Bike Mechanic",
    description: "Repair and maintain bicycles",
    location: "San Andres, Catanduanes",
    salary_range: "₱13,000 - ₱20,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: false,
    requirements: ["Mechanical skills", "Bike expertise"],
    created_at: datetime()
})
CREATE (b7)-[:HAS_JOB]->(j7)

// Business 8
CREATE (b8:Business {
    id: randomUUID(),
    name: "Tailoring Service",
    category: "services",
    description: "Custom tailoring and alterations",
    address: "800 Street, Panglao, Catanduanes",
    phone: "+63-9123456108",
    email: "tailor@catanduanes.com",
    website: "",
    is_active: true,
    is_verified: false,
    is_featured: false,
    rating: 0.0,
    review_count: 0,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b8)
CREATE (j8:Job {
    id: randomUUID(),
    title: "Tailor",
    description: "Create and alter clothing",
    location: "Panglao, Catanduanes",
    salary_range: "₱14,000 - ₱22,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: false,
    requirements: ["Sewing skills", "Tailoring expertise"],
    created_at: datetime()
})
CREATE (b8)-[:HAS_JOB]->(j8)

// Business 9
CREATE (b9:Business {
    id: randomUUID(),
    name: "Small Garden Supplies",
    category: "retail",
    description: "Garden tools and plant supplies",
    address: "900 Street, Baras, Catanduanes",
    phone: "+63-9123456109",
    email: "garden@catanduanes.com",
    website: "",
    is_active: true,
    is_verified: false,
    is_featured: false,
    rating: 0.0,
    review_count: 0,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b9)
CREATE (j9:Job {
    id: randomUUID(),
    title: "Store Staff",
    description: "Manage garden supplies and assist customers",
    location: "Baras, Catanduanes",
    salary_range: "₱12,000 - ₱18,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: false,
    requirements: ["Retail experience", "Garden knowledge"],
    created_at: datetime()
})
CREATE (b9)-[:HAS_JOB]->(j9)

// Business 10
CREATE (b10:Business {
    id: randomUUID(),
    name: "Ice Cream Parlor",
    category: "food_beverage",
    description: "Homemade ice cream and treats",
    address: "1000 Street, Gigaquit, Catanduanes",
    phone: "+63-9123456110",
    email: "icecream@catanduanes.com",
    website: "",
    is_active: true,
    is_verified: false,
    is_featured: false,
    rating: 0.0,
    review_count: 0,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b10)
CREATE (j10:Job {
    id: randomUUID(),
    title: "Ice Cream Vendor",
    description: "Prepare and serve ice cream",
    location: "Gigaquit, Catanduanes",
    salary_range: "₱12,000 - ₱18,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: false,
    requirements: ["Food handling", "Customer service"],
    created_at: datetime()
})
CREATE (b10)-[:HAS_JOB]->(j10)

// Business 11
CREATE (b11:Business {
    id: randomUUID(),
    name: "Keyboard & Computer Repairs",
    category: "repair",
    description: "Computer parts and repair services",
    address: "1100 Street, Virac, Catanduanes",
    phone: "+63-9123456111",
    email: "computer@catanduanes.com",
    website: "",
    is_active: true,
    is_verified: false,
    is_featured: false,
    rating: 0.0,
    review_count: 0,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b11)
CREATE (j11:Job {
    id: randomUUID(),
    title: "IT Support Technician",
    description: "Repair computers and provide tech support",
    location: "Virac, Catanduanes",
    salary_range: "₱16,000 - ₱24,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: false,
    requirements: ["IT knowledge", "Technical troubleshooting"],
    created_at: datetime()
})
CREATE (b11)-[:HAS_JOB]->(j11)

// Business 12
CREATE (b12:Business {
    id: randomUUID(),
    name: "Vegetable Market Stand",
    category: "retail",
    description: "Fresh vegetables and produce",
    address: "1200 Street, San Andres, Catanduanes",
    phone: "+63-9123456112",
    email: "vegetables@catanduanes.com",
    website: "",
    is_active: true,
    is_verified: false,
    is_featured: false,
    rating: 0.0,
    review_count: 0,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b12)
CREATE (j12:Job {
    id: randomUUID(),
    title: "Market Vendor",
    description: "Sell vegetables and manage stand",
    location: "San Andres, Catanduanes",
    salary_range: "₱11,000 - ₱17,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: false,
    requirements: ["Sales experience", "Product knowledge"],
    created_at: datetime()
})
CREATE (b12)-[:HAS_JOB]->(j12)

// Business 13
CREATE (b13:Business {
    id: randomUUID(),
    name: "Shoe Repair & Shoemaking",
    category: "repair",
    description: "Shoe repairs and custom shoes",
    address: "1300 Street, Panglao, Catanduanes",
    phone: "+63-9123456113",
    email: "shoes@catanduanes.com",
    website: "",
    is_active: true,
    is_verified: false,
    is_featured: false,
    rating: 0.0,
    review_count: 0,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b13)
CREATE (j13:Job {
    id: randomUUID(),
    title: "Shoemaker",
    description: "Repair and make shoes",
    location: "Panglao, Catanduanes",
    salary_range: "₱14,000 - ₱21,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: false,
    requirements: ["Shoemaking skills", "Craftsmanship"],
    created_at: datetime()
})
CREATE (b13)-[:HAS_JOB]->(j13)

// Business 14
CREATE (b14:Business {
    id: randomUUID(),
    name: "Home Furniture Store",
    category: "retail",
    description: "Furniture and home decor",
    address: "1400 Street, Baras, Catanduanes",
    phone: "+63-9123456114",
    email: "furniture@catanduanes.com",
    website: "",
    is_active: true,
    is_verified: false,
    is_featured: false,
    rating: 0.0,
    review_count: 0,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b14)
CREATE (j14:Job {
    id: randomUUID(),
    title: "Furniture Sales Associate",
    description: "Sell furniture and assist customers",
    location: "Baras, Catanduanes",
    salary_range: "₱13,000 - ₱20,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: false,
    requirements: ["Sales experience", "Customer service"],
    created_at: datetime()
})
CREATE (b14)-[:HAS_JOB]->(j14)

// Business 15
CREATE (b15:Business {
    id: randomUUID(),
    name: "Small Bakery",
    category: "food_beverage",
    description: "Homemade breads and pastries",
    address: "1500 Street, Gigaquit, Catanduanes",
    phone: "+63-9123456115",
    email: "bakery@catanduanes.com",
    website: "",
    is_active: true,
    is_verified: false,
    is_featured: false,
    rating: 0.0,
    review_count: 0,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b15)
CREATE (j15:Job {
    id: randomUUID(),
    title: "Baker",
    description: "Bake breads and pastries",
    location: "Gigaquit, Catanduanes",
    salary_range: "₱13,000 - ₱20,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: false,
    requirements: ["Baking skills", "Food handling"],
    created_at: datetime()
})
CREATE (b15)-[:HAS_JOB]->(j15)

// Business 16
CREATE (b16:Business {
    id: randomUUID(),
    name: "Watch Repair Shop",
    category: "repair",
    description: "Watch repairs and maintenance",
    address: "1600 Street, Virac, Catanduanes",
    phone: "+63-9123456116",
    email: "watches@catanduanes.com",
    website: "",
    is_active: true,
    is_verified: false,
    is_featured: false,
    rating: 0.0,
    review_count: 0,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b16)
CREATE (j16:Job {
    id: randomUUID(),
    title: "Watch Technician",
    description: "Repair watches and timepieces",
    location: "Virac, Catanduanes",
    salary_range: "₱15,000 - ₱23,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: false,
    requirements: ["Watch repair expertise", "Precision skills"],
    created_at: datetime()
})
CREATE (b16)-[:HAS_JOB]->(j16)

// Business 17
CREATE (b17:Business {
    id: randomUUID(),
    name: "Used Books Store",
    category: "retail",
    description: "Second-hand books and reading materials",
    address: "1700 Street, San Andres, Catanduanes",
    phone: "+63-9123456117",
    email: "books@catanduanes.com",
    website: "",
    is_active: true,
    is_verified: false,
    is_featured: false,
    rating: 0.0,
    review_count: 0,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b17)
CREATE (j17:Job {
    id: randomUUID(),
    title: "Book Store Clerk",
    description: "Manage inventory and sell books",
    location: "San Andres, Catanduanes",
    salary_range: "₱11,000 - ₱17,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: false,
    requirements: ["Book knowledge", "Customer service"],
    created_at: datetime()
})
CREATE (b17)-[:HAS_JOB]->(j17)

// Business 18
CREATE (b18:Business {
    id: randomUUID(),
    name: "Juice & Smoothie Bar",
    category: "food_beverage",
    description: "Fresh juices and smoothies",
    address: "1800 Street, Panglao, Catanduanes",
    phone: "+63-9123456118",
    email: "juice@catanduanes.com",
    website: "",
    is_active: true,
    is_verified: false,
    is_featured: false,
    rating: 0.0,
    review_count: 0,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b18)
CREATE (j18:Job {
    id: randomUUID(),
    title: "Juice Bar Attendant",
    description: "Prepare juices and smoothies",
    location: "Panglao, Catanduanes",
    salary_range: "₱12,000 - ₱18,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: false,
    requirements: ["Food handling", "Beverage preparation"],
    created_at: datetime()
})
CREATE (b18)-[:HAS_JOB]->(j18)

// Business 19
CREATE (b19:Business {
    id: randomUUID(),
    name: "Key & Lock Service",
    category: "services",
    description: "Key making and lock services",
    address: "1900 Street, Baras, Catanduanes",
    phone: "+63-9123456119",
    email: "locks@catanduanes.com",
    website: "",
    is_active: true,
    is_verified: false,
    is_featured: false,
    rating: 0.0,
    review_count: 0,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b19)
CREATE (j19:Job {
    id: randomUUID(),
    title: "Locksmith",
    description: "Make keys and repair locks",
    location: "Baras, Catanduanes",
    salary_range: "₱14,000 - ₱21,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: false,
    requirements: ["Locksmith skills", "Key cutting expertise"],
    created_at: datetime()
})
CREATE (b19)-[:HAS_JOB]->(j19)

// Business 20
CREATE (b20:Business {
    id: randomUUID(),
    name: "Small Bakery Supply Store",
    category: "retail",
    description: "Baking supplies and equipment",
    address: "2000 Street, Gigaquit, Catanduanes",
    phone: "+63-9123456120",
    email: "bakingsupply@catanduanes.com",
    website: "",
    is_active: true,
    is_verified: false,
    is_featured: false,
    rating: 0.0,
    review_count: 0,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b20)
CREATE (j20:Job {
    id: randomUUID(),
    title: "Supply Store Attendant",
    description: "Manage bakery supplies inventory",
    location: "Gigaquit, Catanduanes",
    salary_range: "₱12,000 - ₱18,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: false,
    requirements: ["Inventory management", "Customer service"],
    created_at: datetime()
})
CREATE (b20)-[:HAS_JOB]->(j20)

// Business 21
CREATE (b21:Business {
    id: randomUUID(),
    name: "Photo Printing Service",
    category: "services",
    description: "Photo printing and framing",
    address: "2100 Street, Virac, Catanduanes",
    phone: "+63-9123456121",
    email: "photoprint@catanduanes.com",
    website: "",
    is_active: true,
    is_verified: false,
    is_featured: false,
    rating: 0.0,
    review_count: 0,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b21)
CREATE (j21:Job {
    id: randomUUID(),
    title: "Photo Processing Technician",
    description: "Print and frame photos",
    location: "Virac, Catanduanes",
    salary_range: "₱13,000 - ₱19,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: false,
    requirements: ["Photo printing knowledge", "Attention to detail"],
    created_at: datetime()
})
CREATE (b21)-[:HAS_JOB]->(j21)

// Business 22
CREATE (b22:Business {
    id: randomUUID(),
    name: "Small Pet Shop",
    category: "retail",
    description: "Pet supplies and accessories",
    address: "2200 Street, San Andres, Catanduanes",
    phone: "+63-9123456122",
    email: "pets@catanduanes.com",
    website: "",
    is_active: true,
    is_verified: false,
    is_featured: false,
    rating: 0.0,
    review_count: 0,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b22)
CREATE (j22:Job {
    id: randomUUID(),
    title: "Pet Shop Assistant",
    description: "Sell pet supplies and care for animals",
    location: "San Andres, Catanduanes",
    salary_range: "₱12,000 - ₱18,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: false,
    requirements: ["Pet knowledge", "Animal care"],
    created_at: datetime()
})
CREATE (b22)-[:HAS_JOB]->(j22)

// Business 23
CREATE (b23:Business {
    id: randomUUID(),
    name: "Umbrella Repair & Sales",
    category: "services",
    description: "Repair and sell umbrellas",
    address: "2300 Street, Panglao, Catanduanes",
    phone: "+63-9123456123",
    email: "umbrellas@catanduanes.com",
    website: "",
    is_active: true,
    is_verified: false,
    is_featured: false,
    rating: 0.0,
    review_count: 0,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b23)
CREATE (j23:Job {
    id: randomUUID(),
    title: "Umbrella Repair Specialist",
    description: "Repair and sell umbrellas",
    location: "Panglao, Catanduanes",
    salary_range: "₱12,000 - ₱18,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: false,
    requirements: ["Repair skills", "Attention to detail"],
    created_at: datetime()
})
CREATE (b23)-[:HAS_JOB]->(j23)

// Business 24
CREATE (b24:Business {
    id: randomUUID(),
    name: "Bag & Luggage Repair",
    category: "repair",
    description: "Repair bags and luggage",
    address: "2400 Street, Baras, Catanduanes",
    phone: "+63-9123456124",
    email: "bags@catanduanes.com",
    website: "",
    is_active: true,
    is_verified: false,
    is_featured: false,
    rating: 0.0,
    review_count: 0,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b24)
CREATE (j24:Job {
    id: randomUUID(),
    title: "Bag Repair Technician",
    description: "Repair bags and luggage items",
    location: "Baras, Catanduanes",
    salary_range: "₱13,000 - ₱20,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: false,
    requirements: ["Sewing and repair skills", "Craftsmanship"],
    created_at: datetime()
})
CREATE (b24)-[:HAS_JOB]->(j24)

// Business 25
CREATE (b25:Business {
    id: randomUUID(),
    name: "Canvas & Painting Supplies",
    category: "retail",
    description: "Art supplies and canvases",
    address: "2500 Street, Gigaquit, Catanduanes",
    phone: "+63-9123456125",
    email: "artsupplies@catanduanes.com",
    website: "",
    is_active: true,
    is_verified: false,
    is_featured: false,
    rating: 0.0,
    review_count: 0,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b25)
CREATE (j25:Job {
    id: randomUUID(),
    title: "Art Supply Store Staff",
    description: "Manage art supplies and assist artists",
    location: "Gigaquit, Catanduanes",
    salary_range: "₱12,000 - ₱18,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: false,
    requirements: ["Art knowledge", "Customer service"],
    created_at: datetime()
})
CREATE (b25)-[:HAS_JOB]->(j25)

// Business 26
CREATE (b26:Business {
    id: randomUUID(),
    name: "Candle Making Workshop",
    category: "retail",
    description: "Handmade candles and aromatherapy",
    address: "2600 Street, Virac, Catanduanes",
    phone: "+63-9123456126",
    email: "candles@catanduanes.com",
    website: "",
    is_active: true,
    is_verified: false,
    is_featured: false,
    rating: 0.0,
    review_count: 0,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b26)
CREATE (j26:Job {
    id: randomUUID(),
    title: "Candle Maker",
    description: "Make and sell handmade candles",
    location: "Virac, Catanduanes",
    salary_range: "₱13,000 - ₱20,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: false,
    requirements: ["Candle making skills", "Creativity"],
    created_at: datetime()
})
CREATE (b26)-[:HAS_JOB]->(j26)

// Business 27
CREATE (b27:Business {
    id: randomUUID(),
    name: "Soap & Bath Products Shop",
    category: "retail",
    description: "Handmade soaps and bath products",
    address: "2700 Street, San Andres, Catanduanes",
    phone: "+63-9123456127",
    email: "soap@catanduanes.com",
    website: "",
    is_active: true,
    is_verified: false,
    is_featured: false,
    rating: 0.0,
    review_count: 0,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b27)
CREATE (j27:Job {
    id: randomUUID(),
    title: "Bath Product Specialist",
    description: "Make and sell bath products",
    location: "San Andres, Catanduanes",
    salary_range: "₱13,000 - ₱20,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: false,
    requirements: ["Product knowledge", "Customer service"],
    created_at: datetime()
})
CREATE (b27)-[:HAS_JOB]->(j27)

// Business 28
CREATE (b28:Business {
    id: randomUUID(),
    name: "Wooden Crafts Store",
    category: "retail",
    description: "Wooden furniture and decorative items",
    address: "2800 Street, Panglao, Catanduanes",
    phone: "+63-9123456128",
    email: "wood@catanduanes.com",
    website: "",
    is_active: true,
    is_verified: false,
    is_featured: false,
    rating: 0.0,
    review_count: 0,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b28)
CREATE (j28:Job {
    id: randomUUID(),
    title: "Wood Craft Maker",
    description: "Create wooden crafts and furniture",
    location: "Panglao, Catanduanes",
    salary_range: "₱15,000 - ₱23,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: false,
    requirements: ["Woodworking skills", "Craftsmanship"],
    created_at: datetime()
})
CREATE (b28)-[:HAS_JOB]->(j28)

// Business 29
CREATE (b29:Business {
    id: randomUUID(),
    name: "Knitting & Crochet Studio",
    category: "services",
    description: "Knitting and crochet classes and products",
    address: "2900 Street, Baras, Catanduanes",
    phone: "+63-9123456129",
    email: "knitting@catanduanes.com",
    website: "",
    is_active: true,
    is_verified: false,
    is_featured: false,
    rating: 0.0,
    review_count: 0,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b29)
CREATE (j29:Job {
    id: randomUUID(),
    title: "Knitting Instructor",
    description: "Teach knitting and crochet classes",
    location: "Baras, Catanduanes",
    salary_range: "₱14,000 - ₱21,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: false,
    requirements: ["Knitting expertise", "Teaching skills"],
    created_at: datetime()
})
CREATE (b29)-[:HAS_JOB]->(j29)

// Business 30
CREATE (b30:Business {
    id: randomUUID(),
    name: "Jewelry Making Workshop",
    category: "services",
    description: "Custom jewelry making and repair",
    address: "3000 Street, Gigaquit, Catanduanes",
    phone: "+63-9123456130",
    email: "jewelry@catanduanes.com",
    website: "",
    is_active: true,
    is_verified: false,
    is_featured: false,
    rating: 0.0,
    review_count: 0,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (user)-[:OWNS]->(b30)
CREATE (j30:Job {
    id: randomUUID(),
    title: "Jewelry Artisan",
    description: "Create and repair jewelry",
    location: "Gigaquit, Catanduanes",
    salary_range: "₱16,000 - ₱25,000",
    employment_type: "full_time",
    is_active: true,
    is_featured: false,
    requirements: ["Jewelry making skills", "Precision work", "Creativity"],
    created_at: datetime()
})
CREATE (b30)-[:HAS_JOB]->(j30)

RETURN "Successfully created 30 unverified businesses with 1 job each, all owned by user 6d994a64-141a-462b-a880-03e0228b3ba7";
