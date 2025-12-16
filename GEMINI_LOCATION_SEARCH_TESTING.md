# Gemini AI Location Search - Testing Checklist

## Pre-Testing Setup
- [ ] Ensure `static/js/location-search-ai.js` is deployed
- [ ] Verify `/api/location/` endpoints are accessible
- [ ] Confirm Gemini API is configured and working
- [ ] Database has location data for jobs/businesses

## Jobs Page (`/jobs/`)

### Location Input Field
- [ ] Location input shows placeholder "City or area (e.g., Virac, Baras)"
- [ ] Input has autocomplete styling (relative positioning, suggestions below)
- [ ] Suggestions dropdown appears when typing 2+ characters
- [ ] Suggestions dropdown closes when clicking outside

### Autocomplete Functionality
- [ ] Type "V" + one more char → Suggestions appear
- [ ] Suggestions include Catanduanes municipalities
- [ ] Click suggestion → Input auto-fills with suggestion
- [ ] Click suggestion → Search automatically executes
- [ ] Suggestions list disappears after selection

### AI Search Button
- [ ] "Search with AI" button appears next to "Search" button
- [ ] Button has distinct styling (blue gradient)
- [ ] Click "Search with AI" → Loading dialog appears
- [ ] Loading dialog shows "Searching with AI..." message
- [ ] Results display after AI processing completes
- [ ] Loading dialog closes after results load

### Search Results Display
- [ ] Results grid updates with matching jobs
- [ ] Results show AI interpretation banner
- [ ] Banner shows: "🤖 AI Search Result: Interpreted 'X' as 'Y'"
- [ ] Banner shows alternate locations considered
- [ ] Jobs display with correct data (title, salary, location)
- [ ] Job links work and navigate to detail page
- [ ] Empty results show helpful message

### Pagination
- [ ] Pagination appears when results > per_page
- [ ] Pagination buttons are clickable
- [ ] Previous button disabled on first page
- [ ] Next button disabled on last page
- [ ] Page numbers display correctly
- [ ] Clicking page number updates results
- [ ] Results scroll to top after pagination

### Error Handling
- [ ] Empty location shows error: "Please enter a location to search"
- [ ] Network error shows: "An error occurred during search"
- [ ] Invalid locations show appropriate error messages
- [ ] Error messages disappear after 5 seconds
- [ ] Page remains functional after error

## Businesses Page (`/businesses/`)

### Location Input Field
- [ ] Location input shows placeholder with examples
- [ ] Suggestions appear while typing
- [ ] Suggestions close appropriately

### Autocomplete Functionality
- [ ] Same as Jobs page
- [ ] Suggestions work for business locations
- [ ] Auto-fill and search execution works

### AI Search Button
- [ ] "Search with AI" button appears
- [ ] Loading dialog shows while searching
- [ ] Results display with AI interpretation

### Search Results Display
- [ ] Results grid updates with matching businesses
- [ ] Shows AI interpretation banner
- [ ] Businesses display with correct data (name, rating, location)
- [ ] Verified badges show appropriately
- [ ] Business links work and navigate
- [ ] Empty results show helpful message

### Pagination
- [ ] Works same as Jobs page
- [ ] Results scroll correctly after pagination

### Error Handling
- [ ] Error messages appear and disappear correctly
- [ ] Page remains functional after errors

## AI Interpretation Testing

### Location Recognition
- [ ] "Virac" → Recognized as Virac ✓
- [ ] "Baras" → Recognized as Baras ✓
- [ ] "Bagamanoc" → Recognized ✓
- [ ] "Cavinitan" → Recognized ✓
- [ ] "Gigaquit" → Recognized ✓
- [ ] "Panglao" → Recognized ✓
- [ ] "San Andres" → Recognized ✓
- [ ] "Viga" → Recognized ✓
- [ ] "Caramoran" → Recognized ✓

### Typo/Abbreviation Handling
- [ ] "Vrc" → Suggests/interprets as Virac
- [ ] "baraz" → Suggests/interprets as Baras
- [ ] "bagam" → Suggests/interprets as Bagamanoc
- [ ] "cavini" → Suggests/interprets as Cavinitan
- [ ] "giga" → Suggests/interprets as Gigaquit

### Misspelling Tolerance
- [ ] "Virac city" → Matches Virac
- [ ] "downtown Baras" → Matches Baras
- [ ] "in Viga" → Matches Viga
- [ ] Partial spellings get suggestions

### Confidence Scores
- [ ] Exact matches show "✓ High match"
- [ ] Similar matches show "≈ Similar"
- [ ] Uncertain matches show "? Possible match"
- [ ] Confidence indicator is visually distinct

## Performance Testing

### Load Times
- [ ] Suggestions appear within 500ms
- [ ] Search results load within 2 seconds
- [ ] No loading delays on subsequent searches (cache working)

### Caching
- [ ] First search: Full AI processing
- [ ] Second identical search: Instant (from cache)
- [ ] Different search: Fresh AI processing

### Memory Usage
- [ ] Page doesn't slow down after multiple searches
- [ ] No console errors or warnings
- [ ] No memory leaks (check DevTools)

## Browser Compatibility

### Desktop Browsers
- [ ] Chrome/Chromium (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

### Responsive Design
- [ ] Mobile (320px width)
  - [ ] Input field responsive
  - [ ] Suggestions dropdown visible
  - [ ] Results grid stacks properly
  - [ ] Buttons accessible

- [ ] Tablet (768px width)
  - [ ] Layout adapts correctly
  - [ ] Touch interactions work

- [ ] Desktop (1024px+ width)
  - [ ] Full layout displays
  - [ ] Suggestions positioned correctly

## Integration with Existing Features

### Jobs Page Integration
- [ ] Category filter still works
- [ ] Employment type filter still works
- [ ] Sort options still work
- [ ] Map toggle still works
- [ ] Traditional search still works
- [ ] Recommended jobs section not affected
- [ ] AI bubble still works

### Businesses Page Integration
- [ ] Category filter still works
- [ ] Rating filter still works
- [ ] Verified filter still works
- [ ] Sort options still work
- [ ] Map toggle still works
- [ ] Recommended businesses section not affected
- [ ] AI bubble still works

## Data Integrity

### Job Results
- [ ] Correct job IDs returned
- [ ] Job titles accurate
- [ ] Salary ranges correct
- [ ] Business names match
- [ ] Locations match job data

### Business Results
- [ ] Correct business IDs returned
- [ ] Business names accurate
- [ ] Ratings display correctly
- [ ] Categories match
- [ ] Verification status correct

## Edge Cases

- [ ] Very long location names handled
- [ ] Special characters in location names (if applicable)
- [ ] Numbers in location search
- [ ] Mixed case inputs (VIRAC, Virac, virac)
- [ ] Leading/trailing whitespace in input
- [ ] Very large result sets (100+ results)
- [ ] Empty database for a location (no results)
- [ ] Rapid successive searches
- [ ] Searching immediately after page load

## Accessibility Testing

- [ ] Keyboard navigation works
  - [ ] Tab through input field
  - [ ] Down arrow navigates suggestions
  - [ ] Enter selects suggestion
  - [ ] Escape closes dropdown
  
- [ ] Screen reader compatibility
  - [ ] Input labels are read
  - [ ] Error messages are announced
  - [ ] Results count is accessible
  - [ ] Navigation buttons are labeled

## Final Validation

- [ ] No console errors on page load
- [ ] No console errors on search
- [ ] No console warnings
- [ ] All API endpoints responding correctly
- [ ] Gemini integration working properly
- [ ] No hardcoded URLs or test data
- [ ] Code follows project conventions
- [ ] Comments and documentation present

---

## Test Results Summary

**Date**: [YYYY-MM-DD]
**Tester**: [Name]
**Environment**: [Development/Staging/Production]

### Overall Status
- [ ] PASS - All tests passed
- [ ] PASS WITH MINOR ISSUES - Minor issues, documented below
- [ ] FAIL - Blocking issues found, documented below

### Issues Found

#### Critical
- [ ] Issue: [Description]
  - [ ] Steps to reproduce: [Steps]
  - [ ] Expected: [Expected behavior]
  - [ ] Actual: [Actual behavior]
  - [ ] Severity: [Critical/High/Medium/Low]
  - [ ] Status: [Open/Fixed/Pending]

#### High
- [ ] Issue: [Description]

#### Medium
- [ ] Issue: [Description]

#### Low
- [ ] Issue: [Description]

### Notes
[Any additional notes, observations, or recommendations]

---

## Sign-Off

- [ ] Testing completed
- [ ] All critical issues resolved
- [ ] Ready for deployment
- [ ] Known issues documented

**Tested By**: [Name]
**Date**: [YYYY-MM-DD]
**Signature**: [Digital/Manual]
