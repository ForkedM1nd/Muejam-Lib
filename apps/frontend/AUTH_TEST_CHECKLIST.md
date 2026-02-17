# Authentication Testing Checklist

Use this checklist to verify that authentication is working correctly.

## Pre-Testing Setup

- [ ] Clerk account created
- [ ] Publishable key added to `.env`
- [ ] Dev server restarted after adding key
- [ ] Browser cache cleared

## Sign-Up Flow

### Basic Sign-Up
- [ ] Navigate to `/sign-up`
- [ ] Sign-up form loads correctly
- [ ] Can enter email and password
- [ ] Password strength indicator works
- [ ] Can submit form
- [ ] Email verification sent (if enabled)
- [ ] After sign-up, redirects to `/discover`
- [ ] User button appears in header

### Sign-Up Validation
- [ ] Cannot sign up with invalid email
- [ ] Cannot sign up with weak password
- [ ] Cannot sign up with existing email
- [ ] Error messages display correctly
- [ ] Can click "Sign in" link to go to sign-in page

### Social Sign-Up (if enabled)
- [ ] Google sign-up button appears
- [ ] GitHub sign-up button appears
- [ ] Social sign-up flow works
- [ ] After social sign-up, redirects correctly

## Sign-In Flow

### Basic Sign-In
- [ ] Navigate to `/sign-in`
- [ ] Sign-in form loads correctly
- [ ] Can enter email and password
- [ ] Can submit form
- [ ] After sign-in, redirects to `/discover`
- [ ] User button appears in header
- [ ] Session persists on page reload

### Sign-In Validation
- [ ] Cannot sign in with wrong password
- [ ] Cannot sign in with non-existent email
- [ ] Error messages display correctly
- [ ] Can click "Sign up" link to go to sign-up page

### Social Sign-In (if enabled)
- [ ] Google sign-in button appears
- [ ] GitHub sign-in button appears
- [ ] Social sign-in flow works
- [ ] After social sign-in, redirects correctly

## Protected Routes

### When Not Signed In
- [ ] Accessing `/library` redirects to `/sign-in`
- [ ] Accessing `/write` redirects to `/sign-in`
- [ ] Accessing `/notifications` redirects to `/sign-in`
- [ ] Accessing `/settings/profile` redirects to `/sign-in`
- [ ] After sign-in, redirects back to original page

### When Signed In
- [ ] Can access `/library`
- [ ] Can access `/write`
- [ ] Can access `/notifications`
- [ ] Can access `/settings/profile`
- [ ] No redirects occur

## Navigation

### Header Navigation
- [ ] When signed out, shows "Sign In" and "Sign Up" buttons
- [ ] When signed in, shows user button and notifications icon
- [ ] Theme toggle works on all pages
- [ ] Search bar works on all pages
- [ ] Mobile menu works correctly

### User Button (when signed in)
- [ ] User button shows profile picture or initials
- [ ] Clicking user button opens menu
- [ ] Menu shows user email
- [ ] Menu has "Manage account" option
- [ ] Menu has "Sign out" option
- [ ] "Sign out" works correctly

## Sign-Out Flow

- [ ] Click "Sign out" in user menu
- [ ] User is signed out
- [ ] Redirects to home page (`/`)
- [ ] User button disappears
- [ ] "Sign In" and "Sign Up" buttons appear
- [ ] Cannot access protected routes
- [ ] Session is cleared

## API Integration

### Token Injection
- [ ] Open browser DevTools → Network tab
- [ ] Make an API call (e.g., visit `/library`)
- [ ] Check request headers
- [ ] `Authorization: Bearer <token>` header is present
- [ ] Token is valid (not empty or "null")

### Token Refresh
- [ ] Stay signed in for 5+ minutes
- [ ] Make another API call
- [ ] Token is still present
- [ ] No 401 errors occur

## Loading States

- [ ] Sign-in page shows loading during submission
- [ ] Sign-up page shows loading during submission
- [ ] Protected routes show loading while checking auth
- [ ] Loading spinner is visible and animated
- [ ] Loading text is appropriate

## Error Handling

### Network Errors
- [ ] Disconnect internet
- [ ] Try to sign in
- [ ] Appropriate error message shows
- [ ] Reconnect internet
- [ ] Can retry sign-in

### Invalid Credentials
- [ ] Enter wrong password
- [ ] Error message is clear
- [ ] Can try again
- [ ] No page crash

### Session Expiry
- [ ] Sign in
- [ ] Wait for session to expire (or manually clear in Clerk dashboard)
- [ ] Try to access protected route
- [ ] Redirects to sign-in
- [ ] Can sign in again

## Mobile Responsiveness

### Sign-In Page (Mobile)
- [ ] Form is readable on mobile
- [ ] Inputs are easy to tap
- [ ] Buttons are appropriately sized
- [ ] No horizontal scrolling
- [ ] Keyboard doesn't cover inputs

### Sign-Up Page (Mobile)
- [ ] Form is readable on mobile
- [ ] Inputs are easy to tap
- [ ] Buttons are appropriately sized
- [ ] No horizontal scrolling
- [ ] Keyboard doesn't cover inputs

### Header (Mobile)
- [ ] Mobile menu button appears
- [ ] Mobile menu opens correctly
- [ ] Auth buttons visible in mobile menu
- [ ] User button works in mobile menu

## Browser Compatibility

### Chrome/Edge
- [ ] Sign-in works
- [ ] Sign-up works
- [ ] Protected routes work
- [ ] No console errors

### Firefox
- [ ] Sign-in works
- [ ] Sign-up works
- [ ] Protected routes work
- [ ] No console errors

### Safari
- [ ] Sign-in works
- [ ] Sign-up works
- [ ] Protected routes work
- [ ] No console errors

## Development Mode (No Clerk Key)

- [ ] Remove `VITE_CLERK_PUBLISHABLE_KEY` from `.env`
- [ ] Restart dev server
- [ ] "Auth not configured" button shows
- [ ] Protected routes show message instead of redirecting
- [ ] No crashes or errors
- [ ] Can still navigate the app

## Edge Cases

### Multiple Tabs
- [ ] Sign in on Tab 1
- [ ] Open Tab 2
- [ ] Tab 2 shows signed-in state
- [ ] Sign out on Tab 1
- [ ] Tab 2 updates to signed-out state

### Back Button
- [ ] Sign in
- [ ] Navigate to protected route
- [ ] Click browser back button
- [ ] Still signed in
- [ ] No redirect loops

### Direct URL Access
- [ ] Copy URL of protected route
- [ ] Sign out
- [ ] Paste URL in new tab
- [ ] Redirects to sign-in
- [ ] After sign-in, goes to original URL

### Refresh During Sign-In
- [ ] Start sign-in process
- [ ] Refresh page mid-process
- [ ] Can complete sign-in
- [ ] No errors occur

## Performance

- [ ] Sign-in page loads in < 2 seconds
- [ ] Sign-up page loads in < 2 seconds
- [ ] Auth check completes in < 500ms
- [ ] No layout shift during auth check
- [ ] No flickering of auth buttons

## Accessibility

- [ ] Can tab through sign-in form
- [ ] Can submit with Enter key
- [ ] Form labels are present
- [ ] Error messages are announced
- [ ] Focus management works correctly
- [ ] Screen reader compatible

## Security

- [ ] Password is masked by default
- [ ] Can toggle password visibility
- [ ] No sensitive data in URL
- [ ] No sensitive data in console logs
- [ ] Tokens not visible in DevTools
- [ ] HTTPS used in production

## Summary

**Total Tests**: 150+
**Critical Tests**: 50
**Nice-to-Have Tests**: 100

### Test Results

- **Passed**: _____ / _____
- **Failed**: _____ / _____
- **Skipped**: _____ / _____

### Issues Found

1. _____________________________________
2. _____________________________________
3. _____________________________________

### Notes

_____________________________________
_____________________________________
_____________________________________

---

**Tested By**: _____________________
**Date**: _____________________
**Environment**: Development / Staging / Production
**Browser**: _____________________
**Status**: ✅ Pass / ❌ Fail / ⚠️ Partial
