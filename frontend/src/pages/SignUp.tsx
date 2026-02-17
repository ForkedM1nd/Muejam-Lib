import { SignUp as ClerkSignUp } from "@clerk/clerk-react";
import { useNavigate } from "react-router-dom";
import { useEffect } from "react";
import { useSafeAuth } from "@/hooks/useSafeAuth";

const CLERK_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY ?? "";

export default function SignUp() {
    const navigate = useNavigate();
    const { isSignedIn, isLoaded } = useSafeAuth();

    useEffect(() => {
        if (isLoaded && isSignedIn) {
            navigate("/discover");
        }
    }, [isLoaded, isSignedIn, navigate]);

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
            <div className="w-full max-w-md p-4">
                <ClerkSignUp
                    appearance={{
                        elements: {
                            rootBox: "mx-auto",
                            card: "shadow-lg",
                        },
                    }}
                    routing="path"
                    path="/sign-up"
                    signInUrl="/sign-in"
                    afterSignUpUrl="/discover"
                />
            </div>
        </div>
    );
}
