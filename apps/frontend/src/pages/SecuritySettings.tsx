import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { services } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import type { TwoFactorStatus, TrustedDevice } from "@/types";
import { Shield, Smartphone, AlertTriangle } from "lucide-react";
import { Enable2FA } from "@/components/security/Enable2FA";
import { Disable2FA } from "@/components/security/Disable2FA";
import { RegenerateBackupCodes } from "@/components/security/RegenerateBackupCodes";

export default function SecuritySettings() {
    const [twoFactorStatus, setTwoFactorStatus] = useState<TwoFactorStatus | null>(null);
    const [trustedDevices, setTrustedDevices] = useState<TrustedDevice[]>([]);
    const [loading, setLoading] = useState(true);
    const [showEnable2FA, setShowEnable2FA] = useState(false);
    const [showDisable2FA, setShowDisable2FA] = useState(false);
    const [showRegenerateBackupCodes, setShowRegenerateBackupCodes] = useState(false);
    const { toast } = useToast();

    useEffect(() => {
        loadSecuritySettings();
    }, []);

    const loadSecuritySettings = async () => {
        try {
            setLoading(true);
            const [status, devices] = await Promise.all([
                services.security.get2FAStatus(),
                services.security.getTrustedDevices(),
            ]);
            setTwoFactorStatus(status);
            setTrustedDevices(devices);
        } catch (error) {
            toast({
                title: "Error",
                description: "Failed to load security settings. Please try again.",
                variant: "destructive",
            });
        } finally {
            setLoading(false);
        }
    };

    const handleRevokeDevice = async (deviceId: string) => {
        try {
            await services.security.revokeDevice(deviceId);
            setTrustedDevices(devices => devices.filter(d => d.device_id !== deviceId));
            toast({
                title: "Device revoked",
                description: "The device has been removed from your trusted devices.",
            });
        } catch (error) {
            toast({
                title: "Error",
                description: "Failed to revoke device. Please try again.",
                variant: "destructive",
            });
        }
    };

    const handle2FAEnabled = async () => {
        // Reload security settings after 2FA is enabled
        await loadSecuritySettings();
        toast({
            title: "2FA Enabled",
            description: "Two-factor authentication has been enabled for your account.",
        });
    };

    const handle2FADisabled = async () => {
        // Reload security settings after 2FA is disabled
        await loadSecuritySettings();
        toast({
            title: "2FA Disabled",
            description: "Two-factor authentication has been disabled for your account.",
        });
    };

    const handleBackupCodesRegenerated = async () => {
        // Reload security settings after backup codes are regenerated
        await loadSecuritySettings();
        toast({
            title: "Backup Codes Regenerated",
            description: "New backup codes have been generated. Please save them securely.",
        });
    };

    if (loading) {
        return (
            <div className="container max-w-4xl py-8">
                <div className="space-y-6">
                    <div>
                        <Skeleton className="h-8 w-64 mb-2" />
                        <Skeleton className="h-4 w-96" />
                    </div>
                    <Card>
                        <CardHeader>
                            <Skeleton className="h-6 w-48" />
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <Skeleton className="h-20 w-full" />
                        </CardContent>
                    </Card>
                </div>
            </div>
        );
    }

    if (!twoFactorStatus) {
        return (
            <div className="container max-w-4xl py-8">
                <Alert variant="destructive">
                    <AlertDescription>
                        Failed to load security settings. Please refresh the page.
                    </AlertDescription>
                </Alert>
            </div>
        );
    }

    return (
        <div className="container max-w-4xl py-8">
            <div className="space-y-6">
                {/* Header */}
                <div>
                    <h1 className="text-3xl font-bold flex items-center gap-2">
                        <Shield className="h-8 w-8" />
                        Security Settings
                    </h1>
                    <p className="text-muted-foreground mt-2">
                        Manage your account security and two-factor authentication.
                    </p>
                </div>

                {/* Two-Factor Authentication */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Smartphone className="h-5 w-5" />
                            Two-Factor Authentication
                        </CardTitle>
                        <CardDescription>
                            Add an extra layer of security to your account
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="flex items-start justify-between gap-4">
                            <div className="space-y-1 flex-1">
                                <div className="font-medium">Status</div>
                                <p className="text-sm text-muted-foreground">
                                    {twoFactorStatus.enabled ? (
                                        <span className="text-green-600 dark:text-green-400 font-medium">
                                            Enabled
                                        </span>
                                    ) : (
                                        <span className="text-muted-foreground">
                                            Disabled
                                        </span>
                                    )}
                                </p>
                                {twoFactorStatus.enabled && twoFactorStatus.method && (
                                    <p className="text-sm text-muted-foreground">
                                        Method: {twoFactorStatus.method.toUpperCase()}
                                    </p>
                                )}
                                {twoFactorStatus.enabled && (
                                    <p className="text-sm text-muted-foreground">
                                        Backup codes remaining: {twoFactorStatus.backup_codes_remaining}
                                    </p>
                                )}
                            </div>
                            <div className="flex gap-2">
                                {twoFactorStatus.enabled ? (
                                    <>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => setShowRegenerateBackupCodes(true)}
                                        >
                                            Regenerate Backup Codes
                                        </Button>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => setShowDisable2FA(true)}
                                        >
                                            Disable 2FA
                                        </Button>
                                    </>
                                ) : (
                                    <Button size="sm" onClick={() => setShowEnable2FA(true)}>
                                        Enable 2FA
                                    </Button>
                                )}
                            </div>
                        </div>

                        {!twoFactorStatus.enabled && (
                            <Alert>
                                <AlertTriangle className="h-4 w-4" />
                                <AlertDescription>
                                    Two-factor authentication is not enabled. We strongly recommend enabling it to protect your account.
                                </AlertDescription>
                            </Alert>
                        )}

                        {twoFactorStatus.enabled && twoFactorStatus.backup_codes_remaining < 3 && (
                            <Alert>
                                <AlertTriangle className="h-4 w-4" />
                                <AlertDescription>
                                    You have {twoFactorStatus.backup_codes_remaining} backup codes remaining. Consider regenerating them.
                                </AlertDescription>
                            </Alert>
                        )}
                    </CardContent>
                </Card>

                {/* Trusted Devices */}
                <Card>
                    <CardHeader>
                        <CardTitle>Trusted Devices</CardTitle>
                        <CardDescription>
                            Devices that you've marked as trusted for two-factor authentication
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        {trustedDevices.length === 0 ? (
                            <p className="text-sm text-muted-foreground">
                                No trusted devices. Devices will appear here when you mark them as trusted during sign-in.
                            </p>
                        ) : (
                            <div className="space-y-4">
                                {trustedDevices.map((device) => (
                                    <div
                                        key={device.device_id}
                                        className="flex items-start justify-between gap-4 p-4 border rounded-lg"
                                    >
                                        <div className="space-y-1 flex-1">
                                            <div className="font-medium">{device.device_name}</div>
                                            <div className="text-sm text-muted-foreground">
                                                {device.platform} • {device.browser}
                                            </div>
                                            <div className="text-sm text-muted-foreground">
                                                Last active: {new Date(device.last_active).toLocaleDateString()}
                                            </div>
                                            <div className="text-sm text-muted-foreground">
                                                IP: {device.ip_address}
                                            </div>
                                        </div>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => handleRevokeDevice(device.device_id)}
                                        >
                                            Revoke
                                        </Button>
                                    </div>
                                ))}
                            </div>
                        )}
                    </CardContent>
                </Card>

                {/* Info Alert */}
                <Alert>
                    <Shield className="h-4 w-4" />
                    <AlertDescription>
                        Keep your account secure by enabling two-factor authentication and regularly reviewing your trusted devices.
                    </AlertDescription>
                </Alert>
            </div>

            {/* Enable 2FA Dialog */}
            <Enable2FA
                open={showEnable2FA}
                onOpenChange={setShowEnable2FA}
                onSuccess={handle2FAEnabled}
            />

            {/* Disable 2FA Dialog */}
            <Disable2FA
                open={showDisable2FA}
                onOpenChange={setShowDisable2FA}
                onSuccess={handle2FADisabled}
            />

            {/* Regenerate Backup Codes Dialog */}
            <RegenerateBackupCodes
                open={showRegenerateBackupCodes}
                onOpenChange={setShowRegenerateBackupCodes}
                onSuccess={handleBackupCodesRegenerated}
            />
        </div>
    );
}
