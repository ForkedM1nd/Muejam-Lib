import { createContext, useContext, ReactNode } from "react";
import { useAuth } from "@clerk/clerk-react";

const CLERK_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY ?? "";

interface AuthContextType {
    isAuthenticated: boolean;
    isLoading: boolean;
    userId: string | null | undefined;
    getToken: () => Promise<string | null>;
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
            signOut: async () => { },
        };

        return <AuthContext.Provider value={mockAuth}>{children}</AuthContext.Provider>;
    }

    // Use Clerk auth
    return <ClerkAuthProvider>{children}</ClerkAuthProvider>;
}

function ClerkAuthProvider({ children }: { children: ReactNode }) {
    const { isSignedIn, isLoaded, userId, getToken, signOut } = useAuth();

    const value: AuthContextType = {
        isAuthenticated: !!isSignedIn,
        isLoading: !isLoaded,
        userId,
        getToken: () => getToken(),
        signOut: async () => {
            await signOut();
        },
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
