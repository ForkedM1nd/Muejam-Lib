// Safe auth hook that works without ClerkProvider
import { useAuth as useClerkAuth } from "@clerk/clerk-react";

const CLERK_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY ?? "";

interface SafeAuth {
  isSignedIn: boolean;
  isLoaded: boolean;
  userId: string | null | undefined;
  getToken: () => Promise<string | null>;
}

export function useSafeAuth(): SafeAuth {
  // If no Clerk key, return mock auth state
  if (!CLERK_KEY) {
    return {
      isSignedIn: false,
      isLoaded: true,
      userId: null,
      getToken: async () => null,
    };
  }

  try {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    const auth = useClerkAuth();
    return {
      isSignedIn: !!auth.isSignedIn,
      isLoaded: auth.isLoaded,
      userId: auth.userId,
      getToken: () => auth.getToken(),
    };
  } catch (error) {
    // If Clerk hook fails (e.g., not wrapped in ClerkProvider), return mock state
    console.warn("Clerk auth hook failed, returning mock auth state:", error);
    return {
      isSignedIn: false,
      isLoaded: true,
      userId: null,
      getToken: async () => null,
    };
  }
}
