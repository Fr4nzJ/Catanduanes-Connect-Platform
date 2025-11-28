# Business Directory - Quick Reference Guide

## 🌐 URLs to Test

### Main Directory Pages
| Feature | URL | Description |
|---------|-----|-------------|
| Main Listing | `/businesses` | Browse all businesses |
| Featured | `/featured` | Top 8 featured businesses |
| Categories | `/categories` | All categories overview |
| Technology | `/category/technology` | Technology businesses |
| Services | `/category/services` | Services businesses |

### Search & Filters
| Feature | URL | Description |
|---------|-----|-------------|
| Filter by Rating | `/businesses?min_rating=4` | 4.0+ rated businesses |
| Filter by Verified | `/businesses?verified_only=true` | Only verified businesses |
| Combined Filter | `/businesses?category=technology&min_rating=4&verified_only=true` | Multiple filters combined |
| Advanced Search | `/search/advanced?q=restaurant` | Text search |

### Sorting
| Feature | URL | Description |
|---------|-----|-------------|
| Newest First | `/businesses?sort_by=created_at` | Recently added |
| Highest Rated | `/businesses?sort_by=rating` | Best ratings first |
| Most Reviewed | `/businesses?sort_by=reviews` | Most reviews first |
| A-Z Name | `/businesses?sort_by=name` | Alphabetical order |

---

## 🔍 Filter Combinations

### Common Filter Scenarios
```
# High-quality verified businesses
/businesses?min_rating=4&verified_only=true

# Technology category with high ratings
/businesses?category=technology&min_rating=3.5

# Specific location searches
/businesses?location=Virac&sort_by=rating

# Search + Filter combination
/businesses?query=hotel&category=services&min_rating=4

# Category + Sorting
/category/restaurant?sort_by=rating
```

---

## 📊 Sorting Options Available

1. **Newest** (`sort_by=created_at`)
   - Recently registered businesses first
   - Default sort order

2. **Highest Rated** (`sort_by=rating`)
   - Best ratings first
   - Great for finding quality businesses

3. **Most Reviewed** (`sort_by=reviews`)
   - Most customer feedback
   - Shows popularity

4. **A-Z** (`sort_by=name`)
   - Alphabetical order
   - Easy to find specific businesses

---

## ⭐ Filter Options Available

### Minimum Rating
- Any Rating (default)
- 3.0+ Stars
- 3.5+ Stars
- 4.0+ Stars ⭐⭐⭐⭐
- 4.5+ Stars ⭐⭐⭐⭐½

### Verification Status
- All businesses (default)
- Verified only ✓

### Category Filter
- All Categories (default)
- Technology
- Services
- Retail
- Manufacturing
- Restaurant
- Healthcare
- Education

---

## 📱 Navigation Tips

### From Home Page
1. Click "Businesses" in main navigation
2. Use Featured button for top businesses
3. Browse by Category for category view

### From Business Detail
1. Click category tag to see similar businesses
2. Use breadcrumbs to go back
3. Click "Similar Category" for more options

### From Category Page
1. Browse all businesses in that category
2. Click business card to view details
3. Use pagination for more results
4. Sort within category using dropdown

---

## 🎨 UI Elements Guide

### Business Card Features
- **Rating Stars**: Visual representation of 1-5 star rating
- **Verification Badge**: Green checkmark = verified business
- **Category Tag**: Clickable to view category page
- **Review Count**: Number of customer reviews
- **Location**: Business address (clickable for maps if available)
- **Contact Icons**: Phone, Email, Website links

### Category Card Features
- **Statistics**: Total count, average rating, verified count
- **Progress Bar**: Visual verification percentage
- **Browse Button**: Enter category detail page

### Featured Business Card Features
- **Star Badge**: Indicates featured status
- **Premium Display**: Featured businesses showcase
- **Quick Links**: Website and View Details buttons
- **Full Details**: Complete business information

---

## 🔧 Helper Scripts

### Mark Featured Businesses
```bash
python mark_featured.py
```
- Automatically selects top 8 highest-rated verified businesses
- Marks them with `is_featured = true`
- Useful for promotional showcase

### List Categories
```bash
python list_categories.py
```
- Shows all categories with statistics
- Displays verification rates
- Shows average ratings per category

---

## 🌟 Featured Businesses (Current)

1. Island Tours & Travel - 4.9★
2. Island Wedding Services - 4.9★
3. Island Pet Care Center - 4.9★
4. Stellar Software Solutions - 4.9★
5. Green Valley Farm - 4.8★
6. Catanduanes Photography Studio - 4.8★
7. Catanduanes Dental Clinic - 4.8★
8. Virac IT Solutions - 4.8★

---

## 📊 Category Statistics

| Category | Count | Avg Rating | Verified | % |
|----------|-------|-----------|----------|---|
| Services | 12 | 4.67★ | 11 | 92% |
| Technology | 5 | 4.78★ | 5 | 100% |
| Retail | 4 | 4.60★ | 4 | 100% |
| Manufacturing | 4 | 4.40★ | 2 | 50% |
| Restaurant | 2 | 4.60★ | 2 | 100% |
| Healthcare | 2 | 4.75★ | 2 | 100% |
| Education | 2 | 4.60★ | 1 | 50% |

---

## 🎯 Quick Access

### For Best Businesses
```
/businesses?min_rating=4.5&verified_only=true
```

### For Category Browse
```
/categories
```

### For Featured
```
/featured
```

### For Search
```
/search/advanced?q=query
```

---

## 💡 Tips & Tricks

1. **Combine Multiple Filters**
   - Use URL parameters to combine filters
   - Example: `?category=technology&min_rating=4&sort_by=rating`

2. **Save Filtered Results**
   - Bookmark your favorite filter combinations
   - Share filtered URLs with others

3. **Mobile Friendly**
   - All pages are responsive
   - Filters adapt to smaller screens
   - Touch-friendly buttons

4. **Performance**
   - Main listing cached for 5 minutes
   - Filtered results cached separately
   - Pagination for large result sets

---

## 🚀 Performance Notes

- **Caching**: Main listing cached 300 seconds
- **Pagination**: 12 businesses per page
- **Query Speed**: Optimized Cypher queries
- **Mobile**: Fully responsive design
- **Browser Support**: All modern browsers

---

**Last Updated**: November 18, 2025
**Version**: 1.0 - All 5 Enhancements Complete
