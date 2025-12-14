# Business Recommendations API Documentation

## Base URL
```
POST /gemini/{endpoint}
```

All endpoints require:
- User to be logged in (@login_required)
- Content-Type: application/json
- CSRF token in X-CSRFToken header

---

## Endpoints

### 1. Get Businesses by Category
**Endpoint**: `POST /gemini/get-businesses-by-category`

**Purpose**: Get businesses from different categories for browsing

**Request Body**:
```json
{
  "language": "English"  // Optional: English, Tagalog, Bicol
}
```

**Response Success (200)**:
```json
{
  "status": "success",
  "businesses": [
    "business-id-1",
    "business-id-2",
    "business-id-3",
    "business-id-4",
    "business-id-5"
  ]
}
```

**Response Error (500)**:
```json
{
  "status": "error",
  "message": "Error message description"
}
```

**Implementation Details**:
- Returns up to 5 businesses from different categories
- Groups businesses by category
- Selects one business from each category
- Uses database query, not AI

---

### 2. Get Top-Rated Businesses
**Endpoint**: `POST /gemini/get-businesses-by-rating`

**Purpose**: Get highest-rated businesses

**Request Body**:
```json
{
  "language": "English"  // Optional
}
```

**Response Success (200)**:
```json
{
  "status": "success",
  "businesses": [
    "highest-rated-1",
    "highest-rated-2",
    "highest-rated-3",
    "highest-rated-4",
    "highest-rated-5"
  ]
}
```

**Implementation Details**:
- Filters: `is_active = true` and `rating IS NOT NULL`
- Sorts by rating DESC (highest first)
- Returns up to 10 businesses
- Uses database query

---

### 3. Get Nearby Businesses
**Endpoint**: `POST /gemini/get-businesses-by-location`

**Purpose**: Get businesses from available locations

**Request Body**:
```json
{
  "language": "English"  // Optional
}
```

**Response Success (200)**:
```json
{
  "status": "success",
  "businesses": [
    "location-1",
    "location-2",
    "location-3",
    "location-4",
    "location-5"
  ]
}
```

**Implementation Details**:
- Returns businesses with location information
- Up to 10 businesses
- Database query without sorting (arbitrary order)

---

### 4. Get Recently Added Businesses
**Endpoint**: `POST /gemini/get-businesses-by-recent`

**Purpose**: Get newly added businesses

**Request Body**:
```json
{
  "language": "English"  // Optional
}
```

**Response Success (200)**:
```json
{
  "status": "success",
  "businesses": [
    "newest-1",
    "newest-2",
    "newest-3",
    "newest-4",
    "newest-5"
  ]
}
```

**Implementation Details**:
- Filters: `is_active = true`
- Sorts by `created_at DESC` (newest first)
- Returns up to 10 businesses

---

### 5. Get Most Reviewed Businesses
**Endpoint**: `POST /gemini/get-businesses-by-popular`

**Purpose**: Get most-reviewed/most-popular businesses

**Request Body**:
```json
{
  "language": "English"  // Optional
}
```

**Response Success (200)**:
```json
{
  "status": "success",
  "businesses": [
    "most-reviewed-1",
    "most-reviewed-2",
    "most-reviewed-3",
    "most-reviewed-4",
    "most-reviewed-5"
  ]
}
```

**Implementation Details**:
- Filters: `is_active = true` and `review_count IS NOT NULL`
- Sorts by `review_count DESC`
- Returns up to 10 businesses

---

### 6. Fetch Business Details by IDs
**Endpoint**: `POST /gemini/fetch-businesses-by-ids`

**Purpose**: Get complete business information for given IDs

**Request Body**:
```json
{
  "business_ids": [
    "business-id-1",
    "business-id-2",
    "business-id-3"
  ]
}
```

**Response Success (200)**:
```json
{
  "status": "success",
  "businesses": [
    {
      "id": "business-id-1",
      "name": "Business Name",
      "description": "Business description",
      "category": "restaurant",
      "location": "Virac",
      "address": "123 Main St, Virac, Catanduanes",
      "phone": "+63-123-456-7890",
      "email": "contact@business.com",
      "website": "https://business.com",
      "rating": 4.5,
      "review_count": 12,
      "latitude": 13.5896,
      "longitude": 124.1852,
      "image_url": "/static/images/business.jpg"
    }
  ]
}
```

**Response Error (400)**:
```json
{
  "status": "error",
  "message": "business_ids must be a non-empty array"
}
```

**Implementation Details**:
- Fetches full details for all provided IDs
- Returns business objects with all fields
- Non-existent IDs are silently ignored
- No sorting (returns in order provided)

---

### 7. Recommend by Interests (Advanced)
**Endpoint**: `POST /gemini/recommend-businesses-by-interests`

**Purpose**: AI-powered recommendations based on user interests

**Request Body**:
```json
{
  "interests": ["restaurants", "shopping", "entertainment"],
  "language": "English"
}
```

**Response Success (200)**:
```json
{
  "status": "success",
  "recommended_businesses": [
    "business-id-1",
    "business-id-2",
    "business-id-3",
    "business-id-4",
    "business-id-5"
  ]
}
```

**Implementation Details**:
- Uses Gemini AI to analyze interests
- Fetches up to 50 businesses from database
- AI selects top 5 matching businesses
- Requires Gemini API key

---

### 8. Recommend by Category (Advanced)
**Endpoint**: `POST /gemini/recommend-businesses-by-category`

**Purpose**: AI-powered recommendations by preferred categories

**Request Body**:
```json
{
  "categories": ["restaurant", "retail"],
  "language": "English"
}
```

**Response Success (200)**:
```json
{
  "status": "success",
  "recommended_businesses": [
    "business-id-1",
    "business-id-2",
    "business-id-3",
    "business-id-4",
    "business-id-5"
  ]
}
```

**Implementation Details**:
- Uses Gemini AI to select best matches
- Prioritizes higher-rated businesses
- Returns up to 5 recommendations
- Requires Gemini API key

---

### 9. Recommend by Location (Advanced)
**Endpoint**: `POST /gemini/recommend-businesses-by-location`

**Purpose**: AI-powered recommendations by preferred location

**Request Body**:
```json
{
  "location": "Virac",
  "language": "English"
}
```

**Response Success (200)**:
```json
{
  "status": "success",
  "recommended_businesses": [
    "business-id-1",
    "business-id-2",
    "business-id-3",
    "business-id-4",
    "business-id-5"
  ]
}
```

**Implementation Details**:
- Uses Gemini AI to match locations
- Returns up to 5 recommendations
- Works with city names and area names
- Requires Gemini API key

---

## Error Responses

### Unauthorized (401)
```json
{
  "status": "error",
  "message": "Unauthorized"
}
```
**Cause**: User not logged in

### Bad Request (400)
```json
{
  "status": "error",
  "message": "business_ids must be a non-empty array"
}
```
**Cause**: Invalid request parameters

### Server Error (500)
```json
{
  "status": "error",
  "message": "Error description"
}
```
**Cause**: Server error during processing

---

## Usage Examples

### Example 1: Get and Display Recommendations
```javascript
// Step 1: Get business IDs
const response = await fetch('/gemini/get-businesses-by-category', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': getCsrfToken()
  }
});

const data = await response.json();
const businessIds = data.businesses;

// Step 2: Fetch full details
const detailsResponse = await fetch('/gemini/fetch-businesses-by-ids', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': getCsrfToken()
  },
  body: JSON.stringify({ business_ids: businessIds })
});

const businessDetails = await detailsResponse.json();
// businessDetails.businesses now contains full business info
```

### Example 2: AI Recommendations
```javascript
// Get AI recommendations based on interests
const response = await fetch('/gemini/recommend-businesses-by-interests', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': getCsrfToken()
  },
  body: JSON.stringify({
    interests: ['food', 'shopping', 'entertainment'],
    language: 'English'
  })
});

const data = await response.json();
// data.recommended_businesses contains IDs
```

### Example 3: Using cURL
```bash
# Get businesses by rating
curl -X POST http://localhost:5000/gemini/get-businesses-by-rating \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: your-csrf-token" \
  -d '{"language": "English"}'

# Fetch full details
curl -X POST http://localhost:5000/gemini/fetch-businesses-by-ids \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: your-csrf-token" \
  -d '{"business_ids": ["id1", "id2", "id3"]}'
```

---

## Performance Considerations

### Query Optimization
- Database queries limit results to 10-100 for performance
- Use appropriate indexes on Neo4j for category, location, rating

### Caching
- Consider caching frequently accessed recommendations
- Cache AI responses for 1 hour

### Rate Limiting
- Consider rate limiting AI endpoints (expensive API calls)
- Database endpoints can handle more requests

---

## Fields in Business Object

```json
{
  "id": "string - unique business identifier",
  "name": "string - business name",
  "description": "string - business description",
  "category": "string - business category",
  "location": "string - city/area",
  "address": "string - full address",
  "phone": "string - phone number",
  "email": "string - email address",
  "website": "string - website URL",
  "rating": "number - average rating (0-5)",
  "review_count": "number - count of reviews",
  "latitude": "number - GPS latitude",
  "longitude": "number - GPS longitude",
  "image_url": "string - business image URL"
}
```

---

## Testing

### Using Postman
1. Create POST request to endpoint
2. Add header: `X-CSRFToken: <token-value>`
3. Set Content-Type: application/json
4. Add request body
5. Send request

### Using Browser Console
```javascript
fetch('/gemini/get-businesses-by-category', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': document.querySelector('[name="csrf_token"]').value
  }
})
.then(r => r.json())
.then(d => console.log(d))
```

---

## Support

For issues or questions:
1. Check browser console for errors
2. Check server logs: `tail -f app.log`
3. Verify database connection
4. Test with sample data
5. Review implementation code
