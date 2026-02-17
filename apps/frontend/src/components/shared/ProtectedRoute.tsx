import { useSafeAuth } from "@/hooks/useSafeAuth";
import { Navigate, useLocation } from "react-router-dom";
import { LoadingPage } from "@/components/shared/LoadingSpinner";
import type { ReactNode } from "react";

const CLERK_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY ?? "";

export default function ProtectedRoute({ children }: { children: ReactNode }) {
  const { isSignedIn, isLoaded } = useSafeAuth();
  const location = useLocation();

  if (!isLoaded) {
    return <LoadingPage text="Checking authentication..." />;
  }

  if (!isSignedIn) {
    if (!CLERK_KEY) {
      return (
        <div className="flex flex-col items-center justify-center min-h-[50vh] gap-4">
          <p className="text-muted-foreground">
            Authentication is not configured yet.
          </p>
          <p className="text-sm text-muted-foreground">
            Please set VITE_CLERK_PUBLISHABLE_KEY in your .env file.
          </p>
        </div>
      );
    }

    // Redirect to sign-in with return URL
    return <Navigate to="/sign-in" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}
