import { useState, useRef, useEffect } from "react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { services } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { AlertTriangle, ShieldOff } from "lucide-react";

interface Disable2FAProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSuccess: () => void;
}

export function Disable2FA({ open, onOpenChange, onSuccess }: Disable2FAProps) {
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
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

    const handleDisable = async () => {
        if (!password) {
            setError("Please enter your password.");
            return;
        }

        try {
            setLoading(true);
            setError(null);
            await services.security.disable2FA(password);
            onSuccess();
            onOpenChange(false);
            // Reset state
            timeoutRef.current = setTimeout(() => {
                setPassword("");
                setError(null);
            }, 300);
        } catch (err) {
            setError("Failed to disable 2FA. Please check your password and try again.");
            toast({
                title: "Error",
                description: "Failed to disable two-factor authentication.",
                variant: "destructive",
            });
        } finally {
            setLoading(false);
        }
    };

    const handleCancel = () => {
        onOpenChange(false);
        timeoutRef.current = setTimeout(() => {
            setPassword("");
            setError(null);
        }, 300);
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <ShieldOff className="h-5 w-5 text-destructive" />
                        Disable Two-Factor Authentication
                    </DialogTitle>
                    <DialogDescription>
                        Enter your password to confirm disabling 2FA
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-4">
                    <Alert variant="destructive">
                        <AlertTriangle className="h-4 w-4" />
                        <AlertDescription>
                            Disabling two-factor authentication will make your account less secure.
                            You will no longer need a verification code to sign in.
                        </AlertDescription>
                    </Alert>

                    <div className="space-y-2">
                        <Label htmlFor="password">Password</Label>
                        <Input
                            id="password"
                            type="password"
                            placeholder="Enter your password"
                            value={password}
                            onChange={(e) => {
                                setPassword(e.target.value);
                                setError(null);
                            }}
                            onKeyDown={(e) => {
                                if (e.key === "Enter" && password) {
                                    handleDisable();
                                }
                            }}
                            autoFocus
                        />
                        <p className="text-xs text-muted-foreground">
                            Confirm your identity by entering your account password
                        </p>
                    </div>

                    {error && (
                        <Alert variant="destructive">
                            <AlertTriangle className="h-4 w-4" />
                            <AlertDescription>{error}</AlertDescription>
                        </Alert>
                    )}
                </div>

                <DialogFooter className="flex gap-2">
                    <Button
                        variant="outline"
                        onClick={handleCancel}
                        disabled={loading}
                    >
                        Cancel
                    </Button>
                    <Button
                        variant="destructive"
                        onClick={handleDisable}
                        disabled={loading || !password}
                    >
                        {loading ? "Disabling..." : "Disable 2FA"}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
