# Business Recommendations Testing Guide

## Quick Start Testing

### 1. Navigate to Businesses Page
1. Go to the main Catanduanes Connect application
2. Click on "Businesses" in the main navigation
3. You should see the businesses listing page

### 2. Locate the AI Bubble
- Look for a purple circular button with a sparkle (✨) icon in the bottom-right corner
- This is the AI Assistant bubble

### 3. Click the AI Bubble Button
- The button should expand to show a popup menu
- Popup header: "🤖 Business AI Assistant"
- Helper text: "How can I help you find better businesses?"

### 4. Test Each Recommendation Button

#### Button 1: "Explore by category" 🏪
1. Click the button
2. Look for a loading state
3. Wait for recommendations section to appear
4. Should show 5 businesses from different categories
5. Each business card shows: name, category, rating, location, contact info, description

#### Button 2: "Find top-rated businesses" ⭐
1. Click the button
2. Wait for recommendations to load
3. Businesses should be sorted by rating (highest first)
4. Each should have a visible rating score

#### Button 3: "Nearby businesses" 📍
1. Click the button
2. Wait for recommendations to load
3. Should show businesses with location information

#### Button 4: "Recently added" 🆕
1. Click the button
2. Wait for recommendations to load
3. Should show newest businesses first

#### Button 5: "Most reviewed" 🔥
1. Click the button
2. Wait for recommendations to load
3. Businesses should be sorted by review count

### 5. Verify Recommendations Section
- Recommended section appears above the main business grid
- Section has:
  - Title: "Recommended for you"
  - AI Powered badge (🧠AI Powered)
  - Close button (✕)
  - Grid of business cards

### 6. Test Business Cards
- Cards should display:
  - Business name
  - Category
  - Rating (if available)
  - Address/Location
  - Phone number (clickable)
  - Email (clickable)
  - Website (if available)
  - Description preview
  - "View Business" button

- Clicking "View Business" should navigate to the business detail page

### 7. Test Close Button
- Click the ✕ button in the recommendations section
- Section should hide
- Can be reopened by clicking another button

### 8. Test Multi-Language Support
1. Look for language selector (usually at top of page)
2. Change language to:
   - English
   - Tagalog
   - Bicol
3. AI bubble text and button labels should change
4. All recommendations should work in all languages

### 9. Test Error Handling
1. Try while logged out (should redirect to login)
2. Check browser console for any errors
3. Should display user-friendly error messages if something fails

### 10. Test Responsive Design
1. Test on desktop browser
2. Test on tablet (resize window to 768px width)
3. Test on mobile (resize window to 375px width)
4. Business cards should adjust layout properly
5. Button spacing should remain readable

## Expected Behavior

### Loading State
- Buttons should show visual feedback when clicked
- Recommendations section should appear with loading indicator or smooth animation

### Success State
- Businesses should load and display correctly
- Cards should be properly formatted with all information
- Images should load (if available)
- Links should be clickable

### Empty State
- If no businesses found, should show: "No businesses found"
- Icon: 📭
- Should still be able to try other buttons

### Error State
- If error occurs, should show: "Error loading businesses"
- Icon: ⚠️
- Should still be able to try other buttons

## Browser Console Checks

Open Developer Tools (F12) and go to Console tab:

1. **No Red Errors**: Should see no console errors in red
2. **Check Network Tab**: 
   - POST requests to `/gemini/get-businesses-by-*` should return 200
   - POST request to `/gemini/fetch-businesses-by-ids` should return 200
3. **Check for Warnings**: May have warnings but should be minor

## Database Verification

If you have Neo4j access, verify:

```cypher
// Check if businesses exist
MATCH (b:Business)
WHERE b.is_active = true
RETURN count(b) as total_active_businesses

// Check sample business
MATCH (b:Business)
WHERE b.is_active = true
RETURN b.name, b.category, b.rating, b.review_count
LIMIT 5
```

## Common Issues and Solutions

### Issue: AI Bubble not visible
**Solution**: 
- Check that you're on the businesses page
- Check CSS is loading (look for styling in page source)
- Check browser console for errors

### Issue: No recommendations appear
**Solution**:
- Verify there are businesses in the database
- Check server logs for errors
- Try refreshing the page
- Check network tab for failed requests

### Issue: Error message appears
**Solution**:
- Check if logged in
- Verify database connection
- Check server logs for details
- Try a different recommendation type

### Issue: Text not translating
**Solution**:
- Verify language is selected
- Check if language code is correct
- Refresh page after changing language

### Issue: Buttons don't respond
**Solution**:
- Check browser console for JavaScript errors
- Verify CSRF token is present
- Try different browser
- Clear browser cache and try again

## Performance Testing

1. **Load Time**: Recommendations should load within 2-3 seconds
2. **Smooth Animation**: Should see smooth slide-in animation
3. **No Lag**: Clicking buttons shouldn't freeze the page
4. **Responsive**: Cards should load progressively

## Accessibility Testing

1. **Keyboard Navigation**: Can tab through buttons
2. **Screen Reader**: Should announce content properly
3. **Color Contrast**: Text should be readable
4. **Font Size**: Should be appropriate on all devices

## Success Criteria

✅ All 5 buttons work and return recommendations
✅ Business cards display complete information
✅ All recommendations are visible in different languages
✅ No errors in console
✅ Responsive on all device sizes
✅ Error handling works gracefully
✅ Links are clickable and functional
✅ Section can be closed and reopened

## Next Steps After Testing

If everything works:
1. Mark testing as complete ✓
2. Update project status
3. Consider additional AI recommendation types
4. Add more filtering options
5. Track user interaction metrics

If issues found:
1. Log the issue
2. Check server logs
3. Review implementation
4. Fix and retest
5. Document the fix
