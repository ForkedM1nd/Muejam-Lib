import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { CheckCircle2, XCircle, Loader2, Mail } from "lucide-react";
import { api } from "@/lib/api";

export default function EmailVerification() {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const token = searchParams.get("token");

    const [isVerifying, setIsVerifying] = useState(true);
    const [isVerified, setIsVerified] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [isResending, setIsResending] = useState(false);
    const [resendSuccess, setResendSuccess] = useState(false);

    useEffect(() => {
        if (!token) {
            setIsVerifying(false);
            setError("Invalid or missing verification token");
            return;
        }

        verifyEmail();
    }, [token]);

    const verifyEmail = async () => {
        if (!token) return;

        setIsVerifying(true);
        setError(null);

        try {
            await api.verifyEmail({ token });
            setIsVerified(true);
            // Redirect to home or dashboard after 3 seconds
            setTimeout(() => {
                navigate("/");
            }, 3000);
        } catch (err: any) {
            setError(
                err?.error?.message ||
                "Failed to verify email. The link may have expired or is invalid."
            );
        } finally {
            setIsVerifying(false);
        }
    };

    const handleResendVerification = async () => {
        setIsResending(true);
        setResendSuccess(false);
        setError(null);

        try {
            await api.resendVerificationEmail();
            setResendSuccess(true);
        } catch (err: any) {
            setError(
                err?.error?.message ||
                "Failed to resend verification email. Please try again later."
            );
        } finally {
            setIsResending(false);
        }
    };

    // Loading state while verifying
    if (isVerifying) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
                <Card className="w-full max-w-md">
                    <CardHeader className="text-center">
                        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center">
                            <Loader2 className="h-8 w-8 animate-spin text-primary" />
                        </div>
                        <CardTitle>Verifying your email</CardTitle>
                        <CardDescription>
                            Please wait while we verify your email address...
                        </CardDescription>
                    </CardHeader>
                </Card>
            </div>
        );
    }

    // Success state
    if (isVerified) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
                <Card className="w-full max-w-md">
                    <CardHeader className="text-center">
                        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-green-100">
                            <CheckCircle2 className="h-6 w-6 text-green-600" />
                        </div>
                        <CardTitle>Email verified successfully!</CardTitle>
                        <CardDescription>
                            Your email has been verified. You can now access all features of your account.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            <Alert className="bg-green-50 border-green-200">
                                <AlertDescription className="text-green-800">
                                    Redirecting you to the home page in a few seconds...
                                </AlertDescription>
                            </Alert>
                            <Button asChild className="w-full">
                                <Link to="/">Go to home page</Link>
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            </div>
        );
    }

    // Error state with retry options
    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
            <Card className="w-full max-w-md">
                <CardHeader className="text-center">
                    <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-red-100">
                        <XCircle className="h-6 w-6 text-red-600" />
                    </div>
                    <CardTitle>Verification failed</CardTitle>
                    <CardDescription>
                        We couldn't verify your email address.
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        {error && (
                            <Alert variant="destructive">
                                <AlertDescription>{error}</AlertDescription>
                            </Alert>
                        )}

                        {resendSuccess && (
                            <Alert className="bg-green-50 border-green-200">
                                <Mail className="h-4 w-4 text-green-600" />
                                <AlertDescription className="text-green-800">
                                    Verification email sent! Please check your inbox and spam folder.
                                </AlertDescription>
                            </Alert>
                        )}

                        <div className="space-y-3">
                            <Button
                                onClick={handleResendVerification}
                                className="w-full"
                                disabled={isResending}
                            >
                                {isResending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                Resend verification email
                            </Button>

                            {token && (
                                <Button
                                    onClick={verifyEmail}
                                    variant="outline"
                                    className="w-full"
                                    disabled={isVerifying}
                                >
                                    {isVerifying && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                    Try again
                                </Button>
                            )}

                            <Button asChild variant="ghost" className="w-full">
                                <Link to="/sign-in">Back to sign in</Link>
                            </Button>
                        </div>

                        <div className="text-sm text-gray-600 text-center space-y-2">
                            <p>Common issues:</p>
                            <ul className="text-left space-y-1 ml-4">
                                <li>• The verification link may have expired</li>
                                <li>• You may have already verified your email</li>
                                <li>• Check your spam or junk folder</li>
                            </ul>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
