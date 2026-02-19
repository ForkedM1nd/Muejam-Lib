import { useState } from "react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Mail, X, Loader2 } from "lucide-react";
import { api } from "@/lib/api";

interface EmailVerificationPromptProps {
    onDismiss?: () => void;
}

export function EmailVerificationPrompt({ onDismiss }: EmailVerificationPromptProps) {
    const [isResending, setIsResending] = useState(false);
    const [resendSuccess, setResendSuccess] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [isDismissed, setIsDismissed] = useState(false);

    const handleResend = async () => {
        setIsResending(true);
        setResendSuccess(false);
        setError(null);

        try {
            await api.resendVerificationEmail();
            setResendSuccess(true);
        } catch (err: any) {
            setError(err?.error?.message || "Failed to resend verification email");
        } finally {
            setIsResending(false);
        }
    };

    const handleDismiss = () => {
        setIsDismissed(true);
        onDismiss?.();
    };

    if (isDismissed) {
        return null;
    }

    return (
        <Alert className="relative border-yellow-200 bg-yellow-50">
            <Mail className="h-4 w-4 text-yellow-600" />
            <AlertDescription className="flex items-center justify-between gap-4">
                <div className="flex-1">
                    {resendSuccess ? (
                        <span className="text-green-700 font-medium">
                            Verification email sent! Check your inbox.
                        </span>
                    ) : (
                        <>
                            <span className="text-yellow-800 font-medium">
                                Please verify your email address to access all features.
                            </span>
                            {error && (
                                <p className="text-sm text-red-600 mt-1">{error}</p>
                            )}
                        </>
                    )}
                </div>
                <div className="flex items-center gap-2">
                    {!resendSuccess && (
                        <Button
                            size="sm"
                            variant="outline"
                            onClick={handleResend}
                            disabled={isResending}
                            className="border-yellow-300 hover:bg-yellow-100"
                        >
                            {isResending && <Loader2 className="mr-2 h-3 w-3 animate-spin" />}
                            Resend email
                        </Button>
                    )}
                    <button
                        onClick={handleDismiss}
                        className="text-yellow-600 hover:text-yellow-800 transition-colors"
                        aria-label="Dismiss"
                    >
                        <X className="h-4 w-4" />
                    </button>
                </div>
            </AlertDescription>
        </Alert>
    );
}
