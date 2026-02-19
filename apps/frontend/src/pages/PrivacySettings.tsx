import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { services } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import type { PrivacySettings as PrivacySettingsType } from "@/types";
import { Info, Shield } from "lucide-react";
import { ConsentHistory } from "@/components/gdpr/ConsentHistory";
import { DataExport } from "@/components/gdpr/DataExport";
import { AccountDeletion } from "@/components/gdpr/AccountDeletion";

export default function PrivacySettings() {
    const [settings, setSettings] = useState<PrivacySettingsType | null>(null);
    const [loading, setLoading] = useState(true);
    const [updating, setUpdating] = useState(false);
    const { toast } = useToast();

    useEffect(() => {
        loadSettings();
    }, []);

    const loadSettings = async () => {
        try {
            setLoading(true);
            const data = await services.gdpr.getPrivacySettings();
            setSettings(data);
        } catch (error) {
            toast({
                title: "Error",
                description: "Failed to load privacy settings. Please try again.",
                variant: "destructive",
            });
        } finally {
            setLoading(false);
        }
    };

    const updateSetting = async (key: keyof PrivacySettingsType, value: string | boolean) => {
        if (!settings) return;

        try {
            setUpdating(true);
            const updatedSettings = await services.gdpr.updatePrivacySettings({
                [key]: value,
            });
            setSettings(updatedSettings);
            toast({
                title: "Settings updated",
                description: "Your privacy settings have been saved.",
            });
        } catch (error) {
            toast({
                title: "Error",
                description: "Failed to update settings. Please try again.",
                variant: "destructive",
            });
        } finally {
            setUpdating(false);
        }
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
                            {[1, 2, 3].map((i) => (
                                <div key={i} className="flex items-center justify-between">
                                    <Skeleton className="h-4 w-64" />
                                    <Skeleton className="h-6 w-12" />
                                </div>
                            ))}
                        </CardContent>
                    </Card>
                </div>
            </div>
        );
    }

    if (!settings) {
        return (
            <div className="container max-w-4xl py-8">
                <Alert variant="destructive">
                    <AlertDescription>
                        Failed to load privacy settings. Please refresh the page.
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
                        Privacy Settings
                    </h1>
                    <p className="text-muted-foreground mt-2">
                        Control how your information is shared and used on the platform.
                    </p>
                </div>

                {/* Profile Visibility */}
                <Card>
                    <CardHeader>
                        <CardTitle>Profile Visibility</CardTitle>
                        <CardDescription>
                            Control who can see your profile and activity
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        <div className="space-y-2">
                            <Label htmlFor="profile-visibility">Who can see your profile</Label>
                            <Select
                                value={settings.profile_visibility}
                                onValueChange={(value) => updateSetting("profile_visibility", value)}
                                disabled={updating}
                            >
                                <SelectTrigger id="profile-visibility">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="public">
                                        <div>
                                            <div className="font-medium">Public</div>
                                            <div className="text-sm text-muted-foreground">
                                                Anyone can see your profile
                                            </div>
                                        </div>
                                    </SelectItem>
                                    <SelectItem value="followers">
                                        <div>
                                            <div className="font-medium">Followers Only</div>
                                            <div className="text-sm text-muted-foreground">
                                                Only your followers can see your profile
                                            </div>
                                        </div>
                                    </SelectItem>
                                    <SelectItem value="private">
                                        <div>
                                            <div className="font-medium">Private</div>
                                            <div className="text-sm text-muted-foreground">
                                                Only you can see your profile
                                            </div>
                                        </div>
                                    </SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        <SettingToggle
                            label="Show reading activity"
                            description="Allow others to see what stories you're reading"
                            checked={settings.show_reading_activity}
                            onCheckedChange={(checked) => updateSetting("show_reading_activity", checked)}
                            disabled={updating}
                        />

                        <SettingToggle
                            label="Show followers"
                            description="Display your followers list on your profile"
                            checked={settings.show_followers}
                            onCheckedChange={(checked) => updateSetting("show_followers", checked)}
                            disabled={updating}
                        />

                        <SettingToggle
                            label="Show following"
                            description="Display who you're following on your profile"
                            checked={settings.show_following}
                            onCheckedChange={(checked) => updateSetting("show_following", checked)}
                            disabled={updating}
                        />
                    </CardContent>
                </Card>

                {/* Personalization */}
                <Card>
                    <CardHeader>
                        <CardTitle>Personalization</CardTitle>
                        <CardDescription>
                            Control how we personalize your experience
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        <SettingToggle
                            label="Story recommendations"
                            description="Allow us to recommend stories based on your reading history"
                            checked={settings.allow_story_recommendations}
                            onCheckedChange={(checked) => updateSetting("allow_story_recommendations", checked)}
                            disabled={updating}
                        />

                        <SettingToggle
                            label="Personalized ads"
                            description="Show ads tailored to your interests"
                            checked={settings.allow_personalized_ads}
                            onCheckedChange={(checked) => updateSetting("allow_personalized_ads", checked)}
                            disabled={updating}
                        />

                        <SettingToggle
                            label="Analytics tracking"
                            description="Help us improve by tracking how you use the platform"
                            checked={settings.allow_analytics_tracking}
                            onCheckedChange={(checked) => updateSetting("allow_analytics_tracking", checked)}
                            disabled={updating}
                        />
                    </CardContent>
                </Card>

                {/* Communications */}
                <Card>
                    <CardHeader>
                        <CardTitle>Communications</CardTitle>
                        <CardDescription>
                            Manage how we communicate with you
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        <SettingToggle
                            label="Email notifications"
                            description="Receive email notifications about your account activity"
                            checked={settings.allow_email_notifications}
                            onCheckedChange={(checked) => updateSetting("allow_email_notifications", checked)}
                            disabled={updating}
                        />
                    </CardContent>
                </Card>

                {/* Consent History */}
                <ConsentHistory />

                {/* Data Export */}
                <DataExport />

                {/* Account Deletion */}
                <AccountDeletion />

                {/* Info Alert */}
                <Alert>
                    <Info className="h-4 w-4" />
                    <AlertDescription>
                        Your privacy settings are saved automatically. Changes take effect immediately.
                        For more information about how we handle your data, see our{" "}
                        <a href="/legal/privacy" className="underline">
                            Privacy Policy
                        </a>
                        .
                    </AlertDescription>
                </Alert>
            </div>
        </div>
    );
}

interface SettingToggleProps {
    label: string;
    description: string;
    checked: boolean;
    onCheckedChange: (checked: boolean) => void;
    disabled?: boolean;
}

function SettingToggle({
    label,
    description,
    checked,
    onCheckedChange,
    disabled,
}: SettingToggleProps) {
    return (
        <div className="flex items-start justify-between gap-4">
            <div className="space-y-1 flex-1">
                <Label htmlFor={label.toLowerCase().replace(/\s+/g, "-")}>{label}</Label>
                <p className="text-sm text-muted-foreground">{description}</p>
            </div>
            <Switch
                id={label.toLowerCase().replace(/\s+/g, "-")}
                checked={checked}
                onCheckedChange={onCheckedChange}
                disabled={disabled}
            />
        </div>
    );
}
