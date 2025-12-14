// Update 30 Businesses with Unique Descriptions and Locations

MATCH (b:Business {owner_id: "6d994a64-141a-462b-a880-03e0228b3ba7"})
WITH b
ORDER BY b.name
WITH collect(b) as businesses

WITH businesses,
    ["Premium seafood trading with direct access to fishing ports", 
     "Artisanal fishing operations specializing in high-quality catches",
     "Top-tier coconut products manufacturing facility",
     "Modern agricultural supply center for farming communities",
     "Sustainable marine resource management and export hub",
     "Specialty spice production and international distribution",
     "Full-service tourism coordination with island expertise",
     "Custom furniture craftsmanship and design services",
     "Complete home and commercial hardware solutions",
     "Luxury beachfront accommodation with premium amenities",
     "High-quality textile production for local and export markets",
     "Artisan coffee roastery with sustainable sourcing practices",
     "Advanced technology solutions for marine industries",
     "State-of-the-art food processing and preservation facility",
     "Complete agricultural equipment rental and maintenance services",
     "Reliable inter-island transportation and logistics network",
     "Handcrafted home decor and local artisan gallery",
     "Advanced aquaculture farming with modern techniques",
     "Professional printing and document services center",
     "Quality construction materials and building supplies distributor",
     "Comprehensive travel arrangement and tour coordination services",
     "Certified organic farm products with sustainable practices",
     "Full-service hospitality management and event coordination",
     "Central distribution and warehousing hub for island commerce",
     "Heavy manufacturing with specialized production capabilities",
     "Multi-branch retail network serving island communities",
     "Professional services including consultation and support",
     "Community trading post with diverse inventory",
     "Entertainment and recreational facilities for all ages",
     "IT support and technical services for business infrastructure"] as descriptions,
    
    ["123 Barangay Rizal, Virac, Catanduanes 4800",
     "456 Coastal Road, Pandan, Catanduanes 4801",
     "789 Agricultural Zone, Baras, Catanduanes 4802",
     "234 Farm Road, Baras, Catanduanes 4802",
     "567 Harbor District, Viga, Catanduanes 4803",
     "890 Trade Street, Panganiban, Catanduanes 4804",
     "321 Tourism Boulevard, Virac, Catanduanes 4800",
     "654 Industrial Park, Pandan, Catanduanes 4801",
     "987 Commercial Center, Virac, Catanduanes 4800",
     "111 Beachfront Drive, Caramoran, Catanduanes 4805",
     "222 Manufacturing Zone, Pandan, Catanduanes 4801",
     "333 Downtown Plaza, Virac, Catanduanes 4800",
     "444 Technology Park, Virac, Catanduanes 4800",
     "555 Industrial Avenue, Virac, Catanduanes 4800",
     "666 Agricultural Center, Baras, Catanduanes 4802",
     "777 Logistics District, Panganiban, Catanduanes 4804",
     "888 Arts Quarter, Pandan, Catanduanes 4801",
     "999 Aquaculture Zone, Caramoran, Catanduanes 4805",
     "101 Print Hub, Virac, Catanduanes 4800",
     "202 Construction Plaza, Baras, Catanduanes 4802",
     "303 Travel Center, Virac, Catanduanes 4800",
     "404 Organic Farm District, Baras, Catanduanes 4802",
     "505 Hospitality Circle, Pandan, Catanduanes 4801",
     "606 Distribution Hub, Virac, Catanduanes 4800",
     "707 Factory Complex, Viga, Catanduanes 4803",
     "808 Retail Boulevard, Virac, Catanduanes 4800",
     "909 Service Plaza, Pandan, Catanduanes 4801",
     "1010 Main Street, Virac, Catanduanes 4800",
     "1111 Recreation Center, Caramoran, Catanduanes 4805",
     "1212 Tech Boulevard, Virac, Catanduanes 4800"] as locations

UNWIND range(0, size(businesses)-1) as idx
WITH businesses[idx] as b, descriptions[idx] as desc, locations[idx] as loc
SET b.description = desc,
    b.address = loc

RETURN count(*) as updated_count
