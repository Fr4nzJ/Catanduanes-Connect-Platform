# Fix SendGrid Email Delivery - Debugging Guide

## Issue
Email Status: 202 (Accepted by SendGrid) ✓
Email Received: ✗ (Not arriving in inbox)

## Most Likely Cause: Unverified Sender Email

Your current setup has:
```
SENDGRID_FROM_EMAIL=ermido09a@gmail.com
```

**Problem**: This Gmail address is NOT verified in SendGrid!

---

## Solution: Verify Sender in SendGrid

### Option 1: Verify Your Gmail Address (Recommended for Testing)

1. Go to https://sendgrid.com/
2. Login to your SendGrid account
3. Click **Settings** → **Sender Authentication**
4. Click **"Verify a Single Sender"**
5. Fill in:
   - From Name: "Catanduanes Connect"
   - From Email: **ermido09a@gmail.com**
   - Reply To Email: ermido09a@gmail.com
   - Company: Catanduanes Connect
6. Click **Create**
7. Check your email inbox for verification link
8. Click the verification link in the email
9. ✅ Done! Sender now verified

### Option 2: Use SendGrid's Provided Email

SendGrid may provide you with a test email like:
- `noreply@catandianesconnect.com` (if domain verified)
- Or `notifications@sendgrid.net`

---

## What to Check

### 1. SendGrid Activity Log
1. Go to https://sendgrid.com
2. Click **Activity → Email Activity**
3. Look for the email sent to `akagamiren9@gmail.com`
4. Click on it to see:
   - Status (Delivered, Bounced, etc.)
   - Error message if any
   - Full email content

### 2. Check Email Settings
1. Go to **Settings → Sender Authentication**
2. Look for **Single Sender Verification**
3. Your sender should show as "Verified" ✓

---

## Debug Logs After Fixing

After verifying sender, try signing up again and check logs:

```
railway logs --follow | grep -i "email\|sendgrid"
```

You should see:
```
Template rendered: email/verification_code.html, HTML length: 2847
SendGrid config - From: ermido09a@gmail.com, API Key exists: True
Email sent to akagamiren9@gmail.com via SendGrid. Status: 202
```

If you see this → email should arrive!

---

## Common Reasons Emails Don't Arrive

| Issue | Solution |
|-------|----------|
| Sender not verified | Verify sender in SendGrid settings |
| API key wrong | Check .env and Railway environment variables |
| Invalid recipient email | Verify email address is correct |
| Content filtered as spam | Check "spam filtering" in SendGrid |
| Bounced/unsubscribed | Check SendGrid Activity log for bounce reason |
| Template is empty | Check `templates/email/verification_code.html` exists |

---

## Quick Test

After verifying sender:

1. Go to your app: `https://your-railway-app.com`
2. Sign up with test email
3. Check inbox (including spam folder!)
4. Should receive OTP email within 5 seconds

---

## If Still Not Working

Check SendGrid Activity Log:
- Go to **Activity → Email Activity**
- Find the email you just sent
- Click it to see detailed bounce/error reason
- Common reasons:
  - "550 5.1.1 user unknown" = Invalid email
  - "554 Message rejected" = Content issue
  - "421 RP-001" = Rate limit (unlikely)

---

## Environment Variables Check

### In Railway Dashboard:

Go to **Environment** tab and verify you have:

```
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxx...
SENDGRID_FROM_EMAIL=ermido09a@gmail.com
```

**Note**: Railway environment variables **override** .env file, so make sure they're set there!

---

## Next Steps

1. ✅ Go to SendGrid and verify `ermido09a@gmail.com` as sender
2. ✅ Wait for verification email from SendGrid
3. ✅ Click verification link
4. ✅ Deploy code: `git push origin main`
5. ✅ Try signing up again
6. ✅ Check inbox for OTP

---

**Estimated time to fix: 5 minutes**
