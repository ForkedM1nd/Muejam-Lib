import { SignIn as ClerkSignIn } from "@clerk/clerk-react";
import { useNavigate, useSearchParams, Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { useSafeAuth } from "@/hooks/useSafeAuth";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { CheckCircle2 } from "lucide-react";
import { services } from "@/lib/api";

const CLERK_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY ?? "";

export default function SignIn() {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const { isSignedIn, isLoaded } = useSafeAuth();
    const resetSuccess = searchParams.get("reset") === "success";
    const [checking2FA, setChecking2FA] = useState(false);

    useEffect(() => {
        const check2FAAndRedirect = async () => {
            if (isLoaded && isSignedIn && !checking2FA) {
                setChecking2FA(true);
                try {
                    // Check if 2FA is enabled and needs verification
                    const status = await services.security.check2FAStatus();

                    if (status.enabled && !status.verified) {
                        // 2FA is enabled but not verified - redirect to verification page
                        const redirectTo = searchParams.get("redirect_url") || "/discover";
                        navigate(`/verify-2fa?redirect=${encodeURIComponent(redirectTo)}`, { replace: true });
                    } else {
                        // No 2FA or already verified - proceed to destination
                        const redirectTo = searchParams.get("redirect_url") || "/discover";
                        navigate(redirectTo, { replace: true });
                    }
                } catch (error) {
                    // If 2FA check fails, proceed to discover (fail open for better UX)
                    console.error("Failed to check 2FA status:", error);
                    navigate("/discover", { replace: true });
                } finally {
                    setChecking2FA(false);
                }
            }
        };

        check2FAAndRedirect();
    }, [isLoaded, isSignedIn, navigate, searchParams, checking2FA]);

    if (!CLERK_KEY) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-background">
                <div className="max-w-md w-full p-8 space-y-4 text-center">
                    <h1 className="text-2xl font-bold">Authentication Not Configured</h1>
                    <p className="text-muted-foreground">
                        Please configure Clerk authentication by setting VITE_CLERK_PUBLISHABLE_KEY in your .env file.
                    </p>
                    <button
                        onClick={() => navigate("/")}
                        className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2"
                    >
                        Go Home
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-background">
            <div className="w-full max-w-md p-4 space-y-4">
                {resetSuccess && (
                    <Alert className="bg-green-50 border-green-200">
                        <CheckCircle2 className="h-4 w-4 text-green-600" />
                        <AlertDescription className="text-green-800">
                            Your password has been reset successfully. You can now sign in with your new password.
                        </AlertDescription>
                    </Alert>
                )}
                <ClerkSignIn
                    appearance={{
                        elements: {
                            rootBox: "mx-auto",
                            card: "shadow-lg",
                        },
                    }}
                    routing="path"
                    path="/sign-in"
                    signUpUrl="/sign-up"
                    afterSignInUrl="/discover"
                />
                <div className="text-center text-sm text-muted-foreground">
                    <Link to="/forgot-password" className="text-primary hover:underline">
                        Forgot your password?
                    </Link>
                </div>
            </div>
        </div>
    );
}
