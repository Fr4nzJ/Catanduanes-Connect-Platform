# SendGrid Integration - Deployment Checklist

## Pre-Deployment ✅
- [x] Code changes completed and tested for syntax errors
- [x] All email functions updated to use SendGrid wrapper
- [x] Template rendering helper function added
- [x] Backward compatibility maintained (wrapper function accepts both APIs)
- [x] Fallback mechanism in place (direct SendGrid if Celery unavailable)
- [x] No breaking changes to existing code

## Deployment Steps

### Step 1: Add Environment Variables to Railway
```bash
# In Railway dashboard, add these environment variables:
SENDGRID_API_KEY=your-sendgrid-api-key-here
SENDGRID_FROM_EMAIL=noreply@catandianesconnect.com
```

**To get your SendGrid API Key:**
1. Go to https://sendgrid.com and sign up (free tier available)
2. Once logged in, go to **Settings → API Keys**
3. Click **Create API Key**
4. Give it a name like "Catanduanes Connect"
5. Select **Full Access** or just Email Send access
6. Copy the key and paste into Railway environment variable

### Step 2: Verify Sender Email
In SendGrid dashboard:
1. Go to **Settings → Sender Authentication**
2. Add verified sender: `noreply@catandianesconnect.com`
3. Follow email verification if required

### Step 3: Deploy to Railway
```bash
# In your local repo:
git add .
git commit -m "Integrate SendGrid for reliable email delivery"
git push origin main

# Railway will automatically redeploy with new environment variables
```

### Step 4: Monitor Deployment
```bash
# Check Railway logs in real-time:
railway logs --follow

# Look for messages like:
# "Email sent to user@example.com via SendGrid. Status: 202"
# "Email task queued for user@example.com"
```

## Testing Email Delivery

### Method 1: Test OTP Registration
1. Go to http://your-railway-app.com/register
2. Fill in registration form
3. Use a test email you own (Gmail, etc.)
4. Check inbox for OTP email
5. Verify email works and contains code

### Method 2: Test Password Reset
1. Go to login page
2. Click "Forgot Password"
3. Enter email address
4. Check inbox for reset link
5. Verify email delivery

### Method 3: View SendGrid Dashboard
1. Log into SendGrid dashboard
2. Go to **Activity → Email Activity**
3. View all sent emails, bounces, and delivery status
4. Check if emails were delivered successfully

## Troubleshooting

### Emails Not Sending - Check List:
- [ ] SENDGRID_API_KEY is set in Railway
- [ ] SENDGRID_FROM_EMAIL is set in Railway
- [ ] Sender email is verified in SendGrid
- [ ] Check Railway logs for error messages
- [ ] API key is valid (test in SendGrid dashboard)

### Logs to Check:
```bash
# View specific error lines
railway logs --follow | grep -i email

# Or check in Railway dashboard under Logs tab
```

### Common Issues:

**Issue**: "Failed to send email: Invalid API key"
- **Solution**: Verify SENDGRID_API_KEY is correct in Railway environment

**Issue**: "Email rejected. Invalid sender."
- **Solution**: Verify sender email is registered in SendGrid Settings

**Issue**: "Emails sent but not received"
- **Solution**: Check SendGrid Activity log, may be in spam folder

## Rollback Plan (if needed)

If SendGrid integration has issues:
1. Revert to previous commit: `git revert HEAD`
2. Push to Railway: `git push origin main`
3. Railway will redeploy with old code
4. All email functionality returns to previous state

## Success Indicators

✅ **You know it's working when:**
- OTP emails arrive in inbox within 5 seconds
- SendGrid dashboard shows emails as "Delivered"
- Railway logs show "Email sent via SendGrid. Status: 202"
- Users can complete email verification
- Password reset emails work
- Job application notification emails work

## Performance Expectations

- **Email Delivery**: < 5 seconds (usually instant)
- **SendGrid Response Time**: < 500ms
- **Queue Processing**: < 1 second with Celery
- **Fallback Direct Send**: < 2 seconds without Celery

## Support Resources

- **SendGrid Docs**: https://docs.sendgrid.com/
- **Python Library Docs**: https://github.com/sendgrid/sendgrid-python
- **SendGrid API Status**: https://status.sendgrid.com/
- **Railway Logs**: Check in Railway dashboard → Logs tab

---

## Final Checklist Before Going Live

- [ ] SENDGRID_API_KEY added to Railway
- [ ] SENDGRID_FROM_EMAIL set in Railway
- [ ] Sender email verified in SendGrid
- [ ] Code deployed to Railway
- [ ] Test email sent and received successfully
- [ ] Check Railway logs show "Email sent via SendGrid"
- [ ] OTP registration flow tested end-to-end
- [ ] Password reset flow tested end-to-end
- [ ] Job notification emails tested

**Status**: Ready for deployment ✅
**Estimated Deployment Time**: 5-10 minutes
**Rollback Time**: < 2 minutes
