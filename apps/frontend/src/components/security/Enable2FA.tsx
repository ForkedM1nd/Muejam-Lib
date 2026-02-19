import { useState, useEffect, useRef } from "react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { services } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import type { TwoFactorSetup } from "@/types";
import { CheckCircle2, Copy, AlertTriangle } from "lucide-react";

interface Enable2FAProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSuccess: () => void;
}

export function Enable2FA({ open, onOpenChange, onSuccess }: Enable2FAProps) {
    const [step, setStep] = useState<"setup" | "verify" | "backup">("setup");
    const [setupData, setSetupData] = useState<TwoFactorSetup | null>(null);
    const [verificationCode, setVerificationCode] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [copiedCodes, setCopiedCodes] = useState(false);
    const { toast } = useToast();
    const timeoutRef = useRef<NodeJS.Timeout | null>(null);

    // Cleanup timeout on unmount
    useEffect(() => {
        return () => {
            if (timeoutRef.current) {
                clearTimeout(timeoutRef.current);
            }
        };
    }, []);

    // Fetch QR code when dialog opens
    useEffect(() => {
        if (open && !setupData) {
            const fetchSetupData = async () => {
                try {
                    setLoading(true);
                    setError(null);
                    const data = await services.security.enable2FA();
                    setSetupData(data);
                } catch (err) {
                    setError("Failed to initialize 2FA setup. Please try again.");
                    toast({
                        title: "Error",
                        description: "Failed to initialize 2FA setup.",
                        variant: "destructive",
                    });
                } finally {
                    setLoading(false);
                }
            };
            fetchSetupData();
        }
    }, [open, setupData, toast]);

    // Verify the code before enabling
    const handleVerify = async () => {
        if (!verificationCode || verificationCode.length !== 6) {
            setError("Please enter a valid 6-digit code.");
            return;
        }

        try {
            setLoading(true);
            setError(null);
            await services.security.verify2FA(verificationCode);
            setStep("backup");
        } catch (err) {
            setError("Invalid verification code. Please try again.");
            toast({
                title: "Verification failed",
                description: "The code you entered is incorrect. Please try again.",
                variant: "destructive",
            });
        } finally {
            setLoading(false);
        }
    };

    // Copy backup codes to clipboard
    const handleCopyBackupCodes = async () => {
        if (!setupData?.backup_codes) return;

        try {
            await navigator.clipboard.writeText(setupData.backup_codes.join("\n"));
            setCopiedCodes(true);
            toast({
                title: "Copied",
                description: "Backup codes copied to clipboard.",
            });
            if (timeoutRef.current) {
                clearTimeout(timeoutRef.current);
            }
            timeoutRef.current = setTimeout(() => setCopiedCodes(false), 2000);
        } catch (err) {
            toast({
                title: "Error",
                description: "Failed to copy backup codes.",
                variant: "destructive",
            });
        }
    };

    // Complete setup
    const handleComplete = () => {
        onSuccess();
        onOpenChange(false);
        // Reset state for next time
        timeoutRef.current = setTimeout(() => {
            setStep("setup");
            setSetupData(null);
            setVerificationCode("");
            setError(null);
            setCopiedCodes(false);
        }, 300);
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <DialogTitle>
                        {step === "setup" && "Enable Two-Factor Authentication"}
                        {step === "verify" && "Verify Your Code"}
                        {step === "backup" && "Save Your Backup Codes"}
                    </DialogTitle>
                    <DialogDescription>
                        {step === "setup" && "Scan the QR code with your authenticator app"}
                        {step === "verify" && "Enter the 6-digit code from your authenticator app"}
                        {step === "backup" && "Store these codes in a safe place"}
                    </DialogDescription>
                </DialogHeader>

                {/* Setup Step - Display QR Code */}
                {step === "setup" && (
                    <div className="space-y-4">
                        {loading ? (
                            <div className="flex flex-col items-center space-y-4">
                                <Skeleton className="h-64 w-64" />
                                <Skeleton className="h-4 w-48" />
                            </div>
                        ) : setupData ? (
                            <>
                                <div className="flex flex-col items-center space-y-4">
                                    <div className="p-4 bg-white rounded-lg">
                                        <img
                                            src={setupData.qr_code_url}
                                            alt="2FA QR Code"
                                            className="w-64 h-64"
                                        />
                                    </div>
                                    <p className="text-sm text-muted-foreground text-center">
                                        Scan this QR code with your authenticator app (Google Authenticator, Authy, etc.)
                                    </p>
                                </div>

                                <Alert>
                                    <AlertDescription className="text-xs">
                                        <strong>Manual entry:</strong> {setupData.secret}
                                    </AlertDescription>
                                </Alert>

                                {error && (
                                    <Alert variant="destructive">
                                        <AlertTriangle className="h-4 w-4" />
                                        <AlertDescription>{error}</AlertDescription>
                                    </Alert>
                                )}

                                <Button
                                    onClick={() => setStep("verify")}
                                    className="w-full"
                                >
                                    Continue to Verification
                                </Button>
                            </>
                        ) : null}
                    </div>
                )}

                {/* Verify Step - Enter Code */}
                {step === "verify" && (
                    <div className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="verification-code">Verification Code</Label>
                            <Input
                                id="verification-code"
                                type="text"
                                inputMode="numeric"
                                pattern="[0-9]*"
                                maxLength={6}
                                placeholder="000000"
                                value={verificationCode}
                                onChange={(e) => {
                                    const value = e.target.value.replace(/\D/g, "");
                                    setVerificationCode(value);
                                    setError(null);
                                }}
                                className="text-center text-2xl tracking-widest"
                                autoFocus
                            />
                            <p className="text-xs text-muted-foreground">
                                Enter the 6-digit code from your authenticator app
                            </p>
                        </div>

                        {error && (
                            <Alert variant="destructive">
                                <AlertTriangle className="h-4 w-4" />
                                <AlertDescription>{error}</AlertDescription>
                            </Alert>
                        )}

                        <div className="flex gap-2">
                            <Button
                                variant="outline"
                                onClick={() => {
                                    setStep("setup");
                                    setVerificationCode("");
                                    setError(null);
                                }}
                                className="flex-1"
                            >
                                Back
                            </Button>
                            <Button
                                onClick={handleVerify}
                                disabled={loading || verificationCode.length !== 6}
                                className="flex-1"
                            >
                                {loading ? "Verifying..." : "Verify"}
                            </Button>
                        </div>
                    </div>
                )}

                {/* Backup Codes Step */}
                {step === "backup" && setupData && (
                    <div className="space-y-4">
                        <Alert>
                            <CheckCircle2 className="h-4 w-4" />
                            <AlertDescription>
                                Two-factor authentication has been enabled successfully!
                            </AlertDescription>
                        </Alert>

                        <div className="space-y-2">
                            <Label>Backup Codes</Label>
                            <div className="p-4 bg-muted rounded-lg space-y-1 font-mono text-sm">
                                {setupData.backup_codes.map((code, index) => (
                                    <div key={index} className="flex items-center justify-between">
                                        <span>{code}</span>
                                    </div>
                                ))}
                            </div>
                            <p className="text-xs text-muted-foreground">
                                Save these codes in a safe place. You can use them to access your account if you lose your authenticator device.
                            </p>
                        </div>

                        <Alert variant="default">
                            <AlertTriangle className="h-4 w-4" />
                            <AlertDescription className="text-xs">
                                Each backup code can only be used once. You can regenerate new codes from your security settings.
                            </AlertDescription>
                        </Alert>

                        <div className="flex gap-2">
                            <Button
                                variant="outline"
                                onClick={handleCopyBackupCodes}
                                className="flex-1"
                            >
                                {copiedCodes ? (
                                    <>
                                        <CheckCircle2 className="h-4 w-4 mr-2" />
                                        Copied
                                    </>
                                ) : (
                                    <>
                                        <Copy className="h-4 w-4 mr-2" />
                                        Copy Codes
                                    </>
                                )}
                            </Button>
                            <Button onClick={handleComplete} className="flex-1">
                                Done
                            </Button>
                        </div>
                    </div>
                )}
            </DialogContent>
        </Dialog>
    );
}
