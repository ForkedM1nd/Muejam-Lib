# Authentication Quick Start Guide

Get authentication up and running in 5 minutes!

## Step 1: Get Your Clerk Key (2 minutes)

1. Go to [clerk.com](https://clerk.com/) and sign up (free)
2. Click "Add Application"
3. Name it "MueJam Library" (or whatever you like)
4. Copy your **Publishable Key** (starts with `pk_test_`)

## Step 2: Configure Environment (1 minute)

1. In the `frontend` directory, create a `.env` file:

```bash
# Copy the example file
cp .env.example .env
```

2. Edit `.env` and add your Clerk key:

```bash
VITE_CLERK_PUBLISHABLE_KEY=pk_test_your_actual_key_here
VITE_API_BASE_URL=http://localhost:8000/v1
```

## Step 3: Start the App (1 minute)

```bash
# Install dependencies (if not already done)
npm install

# Start the development server
npm run dev
```

## Step 4: Test It Out (1 minute)

1. Open http://localhost:5173
2. Click "Sign Up" in the top right
3. Create an account
4. You should be redirected to `/discover`
5. Try accessing `/library` - you should stay signed in!

## That's It! 🎉

You now have fully working authentication!

## What You Get

✅ Sign-up page at `/sign-up`
✅ Sign-in page at `/sign-in`
✅ Protected routes (Library, Write, Notifications, Settings)
✅ Automatic token injection in API calls
✅ User profile button with sign-out
✅ Session persistence across page reloads

## Common Issues

### "Auth not configured" button shows

**Problem**: Clerk key not set or dev server not restarted

**Fix**:
```bash
# 1. Check .env file has the key
cat .env | grep CLERK

# 2. Restart dev server
# Press Ctrl+C, then:
npm run dev
```

### Sign-in page shows error

**Problem**: Clerk key is invalid

**Fix**:
1. Go to [Clerk Dashboard](https://dashboard.clerk.com/)
2. Select your application
3. Go to "API Keys"
4. Copy the **Publishable Key** (not the Secret Key!)
5. Update `.env` file
6. Restart dev server

### Can't sign up

**Problem**: Email verification might be required

**Fix**:
1. Check your email for verification link
2. Or disable email verification in Clerk dashboard:
   - Go to "User & Authentication" → "Email, Phone, Username"
   - Toggle off "Verify email address"

## Next Steps

### Customize the Experience

1. **Change redirect URLs**:
   ```bash
   # In .env
   VITE_CLERK_AFTER_SIGN_IN_URL=/library
   VITE_CLERK_AFTER_SIGN_UP_URL=/write
   ```

2. **Add social login**:
   - Go to Clerk Dashboard
   - Click "User & Authentication" → "Social Connections"
   - Enable Google, GitHub, etc.

3. **Customize appearance**:
   - Edit `src/pages/SignIn.tsx` and `src/pages/SignUp.tsx`
   - Modify the `appearance` prop

### Configure Backend

Your backend needs to validate Clerk tokens. See `AUTHENTICATION.md` for details.

## Development Without Clerk

Want to develop without setting up Clerk? No problem!

Just don't set `VITE_CLERK_PUBLISHABLE_KEY` and the app will:
- Show "Auth not configured" buttons
- Allow access to all pages
- Skip token injection

This is useful for:
- UI development
- Testing without backend
- Quick prototyping

## Need Help?

1. **Full documentation**: See `AUTHENTICATION.md`
2. **Clerk docs**: https://clerk.com/docs
3. **Troubleshooting**: See `AUTHENTICATION.md` → Troubleshooting section
4. **Ask the team**: Create an issue or ask in chat

---

**Time to complete**: ~5 minutes
**Difficulty**: Easy
**Prerequisites**: Node.js installed, internet connection
