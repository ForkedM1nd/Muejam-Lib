import { useState } from "react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { services } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { AlertTriangle, CheckCircle2, Copy, RefreshCw } from "lucide-react";

interface RegenerateBackupCodesProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSuccess: () => void;
}

export function RegenerateBackupCodes({ open, onOpenChange, onSuccess }: RegenerateBackupCodesProps) {
    const [step, setStep] = useState<"confirm" | "display">("confirm");
    const [backupCodes, setBackupCodes] = useState<string[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [copiedCodes, setCopiedCodes] = useState(false);
    const { toast } = useToast();

    const handleRegenerate = async () => {
        try {
            setLoading(true);
            setError(null);
            const codes = await services.security.regenerateBackupCodes();
            setBackupCodes(codes);
            setStep("display");
        } catch (err) {
            setError("Failed to regenerate backup codes. Please try again.");
            toast({
                title: "Error",
                description: "Failed to regenerate backup codes.",
                variant: "destructive",
            });
        } finally {
            setLoading(false);
        }
    };

    const handleCopyBackupCodes = async () => {
        if (!backupCodes.length) return;

        try {
            await navigator.clipboard.writeText(backupCodes.join("\n"));
            setCopiedCodes(true);
            toast({
                title: "Copied",
                description: "Backup codes copied to clipboard.",
            });
            setTimeout(() => setCopiedCodes(false), 2000);
        } catch (err) {
            toast({
                title: "Error",
                description: "Failed to copy backup codes.",
                variant: "destructive",
            });
        }
    };

    const handleComplete = () => {
        onSuccess();
        onOpenChange(false);
        // Reset state for next time
        setTimeout(() => {
            setStep("confirm");
            setBackupCodes([]);
            setError(null);
            setCopiedCodes(false);
        }, 300);
    };

    const handleCancel = () => {
        onOpenChange(false);
        setTimeout(() => {
            setStep("confirm");
            setBackupCodes([]);
            setError(null);
            setCopiedCodes(false);
        }, 300);
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <RefreshCw className="h-5 w-5" />
                        {step === "confirm" ? "Regenerate Backup Codes" : "New Backup Codes"}
                    </DialogTitle>
                    <DialogDescription>
                        {step === "confirm"
                            ? "Generate new backup codes for your account"
                            : "Save these codes in a safe place"
                        }
                    </DialogDescription>
                </DialogHeader>

                {/* Confirm Step */}
                {step === "confirm" && (
                    <div className="space-y-4">
                        <Alert variant="destructive">
                            <AlertTriangle className="h-4 w-4" />
                            <AlertDescription>
                                Regenerating backup codes will invalidate all your existing backup codes.
                                Any unused codes will no longer work.
                            </AlertDescription>
                        </Alert>

                        <p className="text-sm text-muted-foreground">
                            You will receive a new set of 8 backup codes. Make sure to save them securely
                            as they can be used to access your account if you lose your authenticator device.
                        </p>

                        {error && (
                            <Alert variant="destructive">
                                <AlertTriangle className="h-4 w-4" />
                                <AlertDescription>{error}</AlertDescription>
                            </Alert>
                        )}
                    </div>
                )}

                {/* Display Step */}
                {step === "display" && (
                    <div className="space-y-4">
                        <Alert>
                            <CheckCircle2 className="h-4 w-4" />
                            <AlertDescription>
                                New backup codes have been generated successfully!
                            </AlertDescription>
                        </Alert>

                        <div className="space-y-2">
                            <Label>Backup Codes</Label>
                            <div className="p-4 bg-muted rounded-lg space-y-1 font-mono text-sm">
                                {backupCodes.map((code, index) => (
                                    <div key={index} className="flex items-center justify-between">
                                        <span>{code}</span>
                                    </div>
                                ))}
                            </div>
                            <p className="text-xs text-muted-foreground">
                                Save these codes in a safe place. Each code can only be used once.
                            </p>
                        </div>

                        <Alert variant="default">
                            <AlertTriangle className="h-4 w-4" />
                            <AlertDescription className="text-xs">
                                Your old backup codes have been invalidated and will no longer work.
                            </AlertDescription>
                        </Alert>
                    </div>
                )}

                <DialogFooter className="flex gap-2">
                    {step === "confirm" ? (
                        <>
                            <Button
                                variant="outline"
                                onClick={handleCancel}
                                disabled={loading}
                            >
                                Cancel
                            </Button>
                            <Button
                                onClick={handleRegenerate}
                                disabled={loading}
                            >
                                {loading ? "Generating..." : "Regenerate Codes"}
                            </Button>
                        </>
                    ) : (
                        <>
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
                        </>
                    )}
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
