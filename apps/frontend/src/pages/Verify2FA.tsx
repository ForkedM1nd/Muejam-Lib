import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { services } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { AlertTriangle, Shield, KeyRound } from "lucide-react";
import { useSafeAuth } from "@/hooks/useSafeAuth";

export default function Verify2FA() {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const { isSignedIn, isLoaded } = useSafeAuth();
    const { toast } = useToast();

    const [totpCode, setTotpCode] = useState("");
    const [backupCode, setBackupCode] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<"totp" | "backup">("totp");

    // Redirect destination after successful verification
    const redirectTo = searchParams.get("redirect") || "/discover";

    // Redirect if not signed in
    useEffect(() => {
        if (isLoaded && !isSignedIn) {
            navigate("/sign-in");
        }
    }, [isLoaded, isSignedIn, navigate]);

    // Handle TOTP code verification
    const handleVerifyTOTP = async () => {
        if (!totpCode || totpCode.length !== 6) {
            setError("Please enter a valid 6-digit code.");
            return;
        }

        try {
            setLoading(true);
            setError(null);
            await services.security.verify2FALogin(totpCode);

            toast({
                title: "Verification successful",
                description: "You have been authenticated successfully.",
            });

            // Redirect to original destination
            navigate(redirectTo, { replace: true });
        } catch (err: any) {
            const errorMessage = err?.error?.message || "Invalid verification code. Please try again.";
            setError(errorMessage);
            toast({
                title: "Verification failed",
                description: errorMessage,
                variant: "destructive",
            });
        } finally {
            setLoading(false);
        }
    };

    // Handle backup code verification
    const handleVerifyBackupCode = async () => {
        if (!backupCode || backupCode.length < 8) {
            setError("Please enter a valid backup code.");
            return;
        }

        try {
            setLoading(true);
            setError(null);
            const result = await services.security.verifyBackupCode(backupCode);

            toast({
                title: "Backup code verified",
                description: `You have ${result.remaining_codes} backup codes remaining.`,
            });

            // Redirect to original destination
            navigate(redirectTo, { replace: true });
        } catch (err: any) {
            const errorMessage = err?.error?.message || "Invalid backup code. Please try again.";
            setError(errorMessage);
            toast({
                title: "Verification failed",
                description: errorMessage,
                variant: "destructive",
            });
        } finally {
            setLoading(false);
        }
    };

    // Handle Enter key press
    const handleKeyPress = (e: React.KeyboardEvent, handler: () => void) => {
        if (e.key === "Enter") {
            handler();
        }
    };

    if (!isLoaded) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-background">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
                    <p className="mt-4 text-muted-foreground">Loading...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-background p-4">
            <Card className="w-full max-w-md">
                <CardHeader className="text-center">
                    <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                        <Shield className="h-6 w-6 text-primary" />
                    </div>
                    <CardTitle>Two-Factor Authentication</CardTitle>
                    <CardDescription>
                        Enter your authentication code to continue
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as "totp" | "backup")}>
                        <TabsList className="grid w-full grid-cols-2">
                            <TabsTrigger value="totp">
                                <Shield className="h-4 w-4 mr-2" />
                                Authenticator
                            </TabsTrigger>
                            <TabsTrigger value="backup">
                                <KeyRound className="h-4 w-4 mr-2" />
                                Backup Code
                            </TabsTrigger>
                        </TabsList>

                        {/* TOTP Code Tab */}
                        <TabsContent value="totp" className="space-y-4">
                            <div className="space-y-2">
                                <Label htmlFor="totp-code">Authentication Code</Label>
                                <Input
                                    id="totp-code"
                                    type="text"
                                    inputMode="numeric"
                                    pattern="[0-9]*"
                                    maxLength={6}
                                    placeholder="000000"
                                    value={totpCode}
                                    onChange={(e) => {
                                        const value = e.target.value.replace(/\D/g, "");
                                        setTotpCode(value);
                                        setError(null);
                                    }}
                                    onKeyPress={(e) => handleKeyPress(e, handleVerifyTOTP)}
                                    className="text-center text-2xl tracking-widest"
                                    autoFocus
                                    disabled={loading}
                                />
                                <p className="text-xs text-muted-foreground">
                                    Enter the 6-digit code from your authenticator app
                                </p>
                            </div>

                            {error && activeTab === "totp" && (
                                <Alert variant="destructive">
                                    <AlertTriangle className="h-4 w-4" />
                                    <AlertDescription>{error}</AlertDescription>
                                </Alert>
                            )}

                            <Button
                                onClick={handleVerifyTOTP}
                                disabled={loading || totpCode.length !== 6}
                                className="w-full"
                            >
                                {loading ? "Verifying..." : "Verify Code"}
                            </Button>
                        </TabsContent>

                        {/* Backup Code Tab */}
                        <TabsContent value="backup" className="space-y-4">
                            <div className="space-y-2">
                                <Label htmlFor="backup-code">Backup Code</Label>
                                <Input
                                    id="backup-code"
                                    type="text"
                                    placeholder="XXXX-XXXX"
                                    value={backupCode}
                                    onChange={(e) => {
                                        setBackupCode(e.target.value.toUpperCase());
                                        setError(null);
                                    }}
                                    onKeyPress={(e) => handleKeyPress(e, handleVerifyBackupCode)}
                                    className="text-center font-mono"
                                    disabled={loading}
                                />
                                <p className="text-xs text-muted-foreground">
                                    Enter one of your backup codes
                                </p>
                            </div>

                            <Alert>
                                <AlertDescription className="text-xs">
                                    Each backup code can only be used once. After using a backup code, you should regenerate new codes from your security settings.
                                </AlertDescription>
                            </Alert>

                            {error && activeTab === "backup" && (
                                <Alert variant="destructive">
                                    <AlertTriangle className="h-4 w-4" />
                                    <AlertDescription>{error}</AlertDescription>
                                </Alert>
                            )}

                            <Button
                                onClick={handleVerifyBackupCode}
                                disabled={loading || backupCode.length < 8}
                                className="w-full"
                            >
                                {loading ? "Verifying..." : "Verify Backup Code"}
                            </Button>
                        </TabsContent>
                    </Tabs>

                    <div className="mt-6 text-center">
                        <Button
                            variant="ghost"
                            onClick={() => navigate("/sign-in")}
                            className="text-sm text-muted-foreground"
                        >
                            Back to Sign In
                        </Button>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
