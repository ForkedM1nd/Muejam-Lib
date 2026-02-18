import { useGoogleReCaptcha } from 'react-google-recaptcha-v3';
import { useRecaptcha } from '@/contexts/RecaptchaContext';
import { useCallback } from 'react';

/**
 * Hook to execute reCAPTCHA v3 and get a token
 * @param action - The action name for reCAPTCHA (e.g., 'submit_story', 'post_whisper')
 * @returns A function that executes reCAPTCHA and returns the token, or null if disabled
 */
export function useRecaptchaToken(action: string) {
    const { executeRecaptcha } = useGoogleReCaptcha();
    const { isEnabled } = useRecaptcha();

    const getToken = useCallback(async (): Promise<string | null> => {
        if (!isEnabled) {
            // reCAPTCHA is not configured, return null
            return null;
        }

        if (!executeRecaptcha) {
            console.warn('reCAPTCHA not yet available');
            return null;
        }

        try {
            const token = await executeRecaptcha(action);
            return token;
        } catch (error) {
            console.error('Failed to execute reCAPTCHA:', error);
            return null;
        }
    }, [executeRecaptcha, isEnabled, action]);

    return getToken;
}
