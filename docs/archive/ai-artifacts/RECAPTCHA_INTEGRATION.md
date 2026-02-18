# reCAPTCHA v3 Integration

This document describes the reCAPTCHA v3 integration for the MueJam Library frontend.

## Overview

reCAPTCHA v3 has been integrated to protect against bots and abuse on:
1. **Signup forms** (via Clerk)
2. **Login forms** (via Clerk)
3. **Content submission forms** (stories, chapters, whispers)

## Configuration

### 1. Get reCAPTCHA v3 Keys

1. Go to [Google reCAPTCHA Admin Console](https://www.google.com/recaptcha/admin)
2. Register a new site with reCAPTCHA v3
3. Add your domain(s) (e.g., `localhost`, `yourdomain.com`)
4. Copy the **Site Key** and **Secret Key**

### 2. Configure Frontend

Add the reCAPTCHA site key to your `.env` file:

```env
VITE_RECAPTCHA_SITE_KEY=your-recaptcha-site-key-here
```

### 3. Configure Clerk (for Signup/Login)

Clerk provides built-in CAPTCHA support. To enable it:

1. Go to your [Clerk Dashboard](https://dashboard.clerk.com)
2. Navigate to **User & Authentication** → **Attack Protection**
3. Enable **CAPTCHA** protection
4. Select **reCAPTCHA v3** as the provider
5. Enter your reCAPTCHA **Site Key** and **Secret Key**
6. Configure the score threshold (recommended: 0.5)

Clerk will automatically add reCAPTCHA to:
- Sign up forms
- Sign in forms
- Password reset forms

### 4. Configure Backend

The backend needs the reCAPTCHA secret key to verify tokens. Add to your backend `.env`:

```env
RECAPTCHA_SECRET_KEY=your-recaptcha-secret-key-here
```

## Implementation Details

### Content Submission Forms

For content submission (stories, chapters, whispers), reCAPTCHA v3 is integrated using the `react-google-recaptcha-v3` library.

**How it works:**

1. The `RecaptchaProvider` wraps the entire app in `App.tsx`
2. The `useRecaptchaToken` hook executes reCAPTCHA before form submission
3. The token is sent to the backend with the API request
4. The backend validates the token with Google's API

**Example usage:**

```typescript
import { useRecaptchaToken } from '@/hooks/useRecaptchaToken';

function MyForm() {
  const getRecaptchaToken = useRecaptchaToken('submit_form');
  
  const handleSubmit = async () => {
    const token = await getRecaptchaToken();
    await api.submitForm({ data, recaptcha_token: token });
  };
}
```

### Actions

The following reCAPTCHA actions are used:
- `submit_story` - Creating or updating stories
- `submit_chapter` - Creating or updating chapters
- `post_whisper` - Posting whispers

### Graceful Degradation

If reCAPTCHA is not configured (no site key in `.env`), the app will:
- Continue to function normally
- Skip reCAPTCHA token generation
- Send `null` as the token to the backend
- Backend should handle this gracefully (allow in dev, block in production)

## Testing

### Local Development

For local development without reCAPTCHA:
1. Don't set `VITE_RECAPTCHA_SITE_KEY` in `.env`
2. The app will work without CAPTCHA protection
3. Backend should allow `null` tokens in development mode

### With reCAPTCHA

1. Set up reCAPTCHA keys as described above
2. Test form submissions
3. Check browser console for reCAPTCHA errors
4. Verify tokens are being sent to backend

### Testing Score Thresholds

reCAPTCHA v3 returns a score from 0.0 (bot) to 1.0 (human):
- **0.9-1.0**: Very likely human
- **0.5-0.9**: Likely human (recommended threshold)
- **0.0-0.5**: Likely bot

To test different scenarios:
1. Normal usage should score 0.7-1.0
2. Automated scripts will score 0.0-0.3
3. Suspicious behavior scores 0.3-0.7

## Troubleshooting

### reCAPTCHA not loading

- Check that `VITE_RECAPTCHA_SITE_KEY` is set correctly
- Verify the domain is registered in reCAPTCHA admin console
- Check browser console for errors

### Low scores for legitimate users

- Review user behavior patterns
- Consider lowering the threshold (e.g., 0.3)
- Check for browser extensions blocking reCAPTCHA

### Backend rejecting tokens

- Verify backend has correct secret key
- Check token expiration (tokens expire after 2 minutes)
- Ensure backend is making correct API call to Google

## Security Considerations

1. **Never expose the secret key** - Only use it on the backend
2. **Validate tokens server-side** - Never trust client-side validation
3. **Set appropriate thresholds** - Balance security vs. user experience
4. **Monitor scores** - Track score distribution to detect attacks
5. **Rate limiting** - Use reCAPTCHA alongside rate limiting, not as replacement

## References

- [reCAPTCHA v3 Documentation](https://developers.google.com/recaptcha/docs/v3)
- [Clerk CAPTCHA Documentation](https://clerk.com/docs/security/captcha)
- [react-google-recaptcha-v3](https://github.com/t49tran/react-google-recaptcha-v3)
