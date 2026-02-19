import { createContext, useContext, ReactNode, useCallback } from "react";
import { useAuth } from "@clerk/clerk-react";
import { useNavigate } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";

const CLERK_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY ?? "";

interface AuthContextType {
    isAuthenticated: boolean;
    isLoading: boolean;
    userId: string | null | undefined;
    getToken: () => Promise<string | null>;
    refreshToken: () => Promise<string | null>;
    signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
    // If no Clerk key, provide mock auth context
    if (!CLERK_KEY) {
        const mockAuth: AuthContextType = {
            isAuthenticated: false,
            isLoading: false,
            userId: null,
            getToken: async () => null,
            refreshToken: async () => null,
            signOut: async () => { },
        };

        return <AuthContext.Provider value={mockAuth}>{children}</AuthContext.Provider>;
    }

    // Use Clerk auth
    return <ClerkAuthProvider>{children}</ClerkAuthProvider>;
}

function ClerkAuthProvider({ children }: { children: ReactNode }) {
    const { isSignedIn, isLoaded, userId, getToken, signOut } = useAuth();
    const navigate = useNavigate();
    const queryClient = useQueryClient();

    // Refresh token function that attempts to get a fresh token
    // If refresh fails (e.g., refresh token expired), redirect to sign-in
    const refreshToken = useCallback(async (): Promise<string | null> => {
        try {
            // Clerk's getToken() automatically handles token refresh
            // Force a fresh token by passing skipCache option
            const token = await getToken({ skipCache: true });

            if (!token) {
                // Token refresh failed - refresh token likely expired
                // Perform full cleanup via handleSignOut
                // Note: We can't call handleSignOut here due to circular dependency
                // So we'll do minimal cleanup and redirect
                await signOut();
                queryClient.clear();
                localStorage.clear();
                sessionStorage.clear();
                navigate('/sign-in', { replace: true });
                return null;
            }

            return token;
        } catch (error) {
            // Token refresh failed - redirect to sign-in
            console.error('Token refresh failed:', error);
            await signOut();
            queryClient.clear();
            localStorage.clear();
            sessionStorage.clear();
            navigate('/sign-in', { replace: true });
            return null;
        }
    }, [getToken, signOut, queryClient, navigate]);

    // Enhanced sign-out with comprehensive cleanup
    const handleSignOut = useCallback(async () => {
        try {
            // 1. Clear all stored tokens (handled by Clerk's signOut)
            await signOut();

            // 2. Clear TanStack Query cache
            queryClient.clear();

            // 3. Clear localStorage (preserve only essential non-auth data)
            // Get list of keys to preserve (if any)
            const keysToPreserve = ['theme', 'language']; // Add any keys that should persist
            const preservedData: Record<string, string> = {};

            keysToPreserve.forEach(key => {
                const value = localStorage.getItem(key);
                if (value !== null) {
                    preservedData[key] = value;
                }
            });

            // Clear all localStorage
            localStorage.clear();

            // Restore preserved keys
            Object.entries(preservedData).forEach(([key, value]) => {
                localStorage.setItem(key, value);
            });

            // 4. Clear sessionStorage
            sessionStorage.clear();

            // 5. Reset global state (currently no Zustand stores, but prepared for future)
            // If Zustand stores are added later, reset them here

            // 6. Redirect to sign-in page
            navigate('/sign-in', { replace: true });
        } catch (error) {
            console.error('Error during sign-out:', error);
            // Even if there's an error, try to redirect to sign-in
            navigate('/sign-in', { replace: true });
        }
    }, [signOut, queryClient, navigate]);

    const value: AuthContextType = {
        isAuthenticated: !!isSignedIn,
        isLoading: !isLoaded,
        userId,
        getToken: () => getToken(),
        refreshToken,
        signOut: handleSignOut,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuthContext() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error("useAuthContext must be used within an AuthProvider");
    }
    return context;
}
