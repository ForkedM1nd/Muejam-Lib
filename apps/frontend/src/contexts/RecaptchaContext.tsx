import { createContext, useContext, ReactNode } from 'react';
import { GoogleReCaptchaProvider } from 'react-google-recaptcha-v3';

const RECAPTCHA_SITE_KEY = import.meta.env.VITE_RECAPTCHA_SITE_KEY ?? '';

interface RecaptchaContextType {
    siteKey: string;
    isEnabled: boolean;
}

const RecaptchaContext = createContext<RecaptchaContextType>({
    siteKey: RECAPTCHA_SITE_KEY,
    isEnabled: !!RECAPTCHA_SITE_KEY,
});

export const useRecaptcha = () => useContext(RecaptchaContext);

interface RecaptchaProviderProps {
    children: ReactNode;
}

export function RecaptchaProvider({ children }: RecaptchaProviderProps) {
    const isEnabled = !!RECAPTCHA_SITE_KEY;

    if (!isEnabled) {
        // If reCAPTCHA is not configured, render children without the provider
        return (
            <RecaptchaContext.Provider value={{ siteKey: '', isEnabled: false }}>
                {children}
            </RecaptchaContext.Provider>
        );
    }

    return (
        <GoogleReCaptchaProvider
            reCaptchaKey={RECAPTCHA_SITE_KEY}
            scriptProps={{
                async: true,
                defer: true,
                appendTo: 'head',
            }}
        >
            <RecaptchaContext.Provider value={{ siteKey: RECAPTCHA_SITE_KEY, isEnabled: true }}>
                {children}
            </RecaptchaContext.Provider>
        </GoogleReCaptchaProvider>
    );
}
