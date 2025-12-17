# CSV Export Feature - Quick Start Guide

## 🎯 What's New?

The admin dashboard now has **4 export buttons** to download platform data as CSV files.

## 📍 Where to Find It?

**Location**: Admin Dashboard → Data Export Section (below Quick Stats)

```
┌─────────────────────────────────────────────────┐
│         ADMIN DASHBOARD - DATA EXPORT            │
├─────────────────────────────────────────────────┤
│                                                   │
│  [👥 Users]    [🏪 Businesses]  [💼 Jobs]  [📦 All]
│                                                   │
│  Export platform data in CSV format for analysis │
└─────────────────────────────────────────────────┘
```

## 📥 How to Download Data?

### Step 1: Go to Admin Dashboard
- Login as admin user
- Click on "Admin Dashboard" in navigation

### Step 2: Locate Export Section
- Scroll down below the Quick Stats cards
- Find the "Data Export" section (light purple/indigo background)

### Step 3: Click Export Button
- **Users Data**: Downloads all registered users
- **Businesses Data**: Downloads all business profiles
- **Jobs Data**: Downloads all job listings
- **All Data Bundle**: Downloads all three as a ZIP file

### Step 4: File Downloads
- Browser downloads file automatically
- Filename includes timestamp: `users_export_20240115_143022.csv`
- Files ready to open in Excel, Google Sheets, etc.

## 📊 What Data Is Included?

### 👥 Users Export
Includes user information needed for analytics:
- User ID, Username, Email, Role
- Full Name, Phone, Verification Status
- Created Date, Last Login Date

### 🏪 Businesses Export
Includes complete business profile data:
- Business ID, Name, Category
- Contact Info (Address, Phone, Email, Website)
- Verification & Featured Status
- Rating, Review Count, Description
- Location (Latitude, Longitude)
- Creation Date

### 💼 Jobs Export
Includes job listing details:
- Job ID, Title, Description
- Company Name, Location
- Salary Range, Employment Type
- Experience Level Required
- Status, Featured Status
- Application Count
- Deadline, Posted Date

### 📦 All Data Bundle (ZIP)
Single ZIP file containing all three CSV files:
- users.csv
- businesses.csv
- jobs.csv

## 💾 File Specifications

| Property | Value |
|----------|-------|
| **Format** | CSV (Comma-Separated Values) |
| **Encoding** | UTF-8 |
| **Headers** | Yes (Column names in first row) |
| **Line Endings** | Standard for your OS |
| **Timestamp** | Included in filename |
| **Size** | Varies by data size |

## 🔒 Security Notes

- ✓ Only administrators can access exports
- ✓ All exports logged with admin username
- ✓ Files are generated securely in memory
- ✓ No temporary files created on disk
- ✓ Timestamps help track export history

## ⚡ Performance

| Export Type | Typical Time | File Size |
|-------------|--------------|-----------|
| Users | < 1 second | 100 KB - 1 MB |
| Businesses | < 2 seconds | 200 KB - 2 MB |
| Jobs | < 3 seconds | 500 KB - 5 MB |
| All Data (ZIP) | 5-10 seconds | 1-8 MB |

## 📱 Opening CSV Files

### Option 1: Microsoft Excel
1. Download the CSV file
2. Double-click to open in Excel
3. Choose UTF-8 encoding if prompted
4. Data appears in spreadsheet format

### Option 2: Google Sheets
1. Download the CSV file
2. Go to Google Sheets
3. Click "File" → "Open" → "Upload"
4. Select downloaded CSV file
5. Spreadsheet loads with all data

### Option 3: LibreOffice Calc
1. Download the CSV file
2. Right-click and select "Open With" → LibreOffice Calc
3. Choose UTF-8 encoding
4. Data appears in spreadsheet format

## 🛠️ Troubleshooting

### Problem: Export buttons not showing
**Solution**: Clear browser cache or try different browser

### Problem: CSV file opens with weird characters
**Solution**: Open with UTF-8 encoding (not ANSI/ASCII)

### Problem: File won't download
**Solution**: 
- Check browser download settings
- Ensure admin role is active
- Try a different browser
- Check internet connection

### Problem: ZIP file is empty
**Solution**: 
- Database connection issue
- Restart application
- Check Neo4j database status

### Problem: Numbers formatted as text
**Solution**: This is normal for CSV. Format cells as numbers in spreadsheet app

## 💡 Use Cases

### 1. Data Analysis
Export and analyze user growth, business metrics, or job trends

### 2. Reporting
Create reports using the exported data in spreadsheet tools

### 3. Backup
Regular exports serve as backup of platform data

### 4. Data Migration
Export for migrating data to other systems

### 5. Auditing
Track data changes over time with timestamped exports

### 6. Integration
Import CSV data into other business intelligence tools

## 📋 Admin Checklist

- [ ] Found the Data Export section on dashboard
- [ ] Clicked one export button to test
- [ ] File downloaded to your computer
- [ ] Opened CSV file in spreadsheet application
- [ ] Verified data looks correct
- [ ] Checked that all columns are present
- [ ] Confirmed UTF-8 encoding is working
- [ ] Tested ZIP bundle export
- [ ] Verified all three files are in ZIP

## 🔗 Related Documentation

For more detailed information, see:
- **CSV_EXPORT_FEATURE.md** - Complete technical documentation
- **CSV_EXPORT_IMPLEMENTATION.md** - Implementation details

## ❓ FAQ

**Q: How often can I export?**
A: As often as needed. There are no rate limits.

**Q: Is exported data real-time?**
A: Yes, exports pull current database data at time of download.

**Q: Can I schedule automatic exports?**
A: Not currently, but can be added as future enhancement.

**Q: What if I export the same data twice?**
A: You'll get complete current snapshot each time. Timestamps help identify which export is newer.

**Q: Can other users access exports?**
A: No, only administrators with admin_required permissions can access exports.

**Q: Are exports stored on the server?**
A: No, files are generated in memory and sent directly to your browser.

**Q: Can I export specific date ranges?**
A: Not currently, exports all data. Can be added as future feature.

**Q: What's the maximum file size?**
A: Depends on platform data, typically under 10 MB for all data.

## 🚀 Quick Reference

```
USERS EXPORT
URL: /admin/export/users
Data: 9 columns × (number of users)
Name: users_export_TIMESTAMP.csv

BUSINESSES EXPORT
URL: /admin/export/businesses
Data: 14 columns × (number of businesses)
Name: businesses_export_TIMESTAMP.csv

JOBS EXPORT
URL: /admin/export/jobs
Data: 13 columns × (number of jobs)
Name: jobs_export_TIMESTAMP.csv

ALL DATA EXPORT
URL: /admin/export/all
Format: ZIP with 3 CSV files
Name: catanduanes_export_TIMESTAMP.zip
```

---

**Feature**: CSV Export for Admin Dashboard
**Status**: ✓ Ready to Use
**Last Updated**: Current Session

