import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { services } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import type { ConsentRecord } from "@/types";
import { CheckCircle2, XCircle, AlertTriangle } from "lucide-react";
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from "@/components/ui/alert-dialog";

export function ConsentHistory() {
    const [consents, setConsents] = useState<ConsentRecord[]>([]);
    const [loading, setLoading] = useState(true);
    const [withdrawing, setWithdrawing] = useState<string | null>(null);
    const [consentToWithdraw, setConsentToWithdraw] = useState<string | null>(null);
    const { toast } = useToast();

    useEffect(() => {
        loadConsentHistory();
    }, []);

    const loadConsentHistory = async () => {
        try {
            setLoading(true);
            const data = await services.gdpr.getConsentHistory();
            setConsents(data);
        } catch (error) {
            toast({
                title: "Error",
                description: "Failed to load consent history. Please try again.",
                variant: "destructive",
            });
        } finally {
            setLoading(false);
        }
    };

    const handleWithdrawConsent = async (consentType: string) => {
        try {
            setWithdrawing(consentType);
            await services.gdpr.withdrawConsent(consentType);

            // Update local state to reflect withdrawal
            setConsents(prevConsents =>
                prevConsents.map(consent =>
                    consent.consent_type === consentType
                        ? { ...consent, granted: false, withdrawn_at: new Date().toISOString() }
                        : consent
                )
            );

            toast({
                title: "Consent withdrawn",
                description: "Your consent has been successfully withdrawn.",
            });
        } catch (error) {
            toast({
                title: "Error",
                description: "Failed to withdraw consent. Please try again.",
                variant: "destructive",
            });
        } finally {
            setWithdrawing(null);
            setConsentToWithdraw(null);
        }
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString("en-US", {
            year: "numeric",
            month: "long",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        });
    };

    const getConsentLabel = (consentType: string) => {
        const labels: Record<string, string> = {
            story_recommendations: "Story Recommendations",
            personalized_ads: "Personalized Advertising",
            analytics_tracking: "Analytics Tracking",
            email_notifications: "Email Notifications",
            data_processing: "Data Processing",
            marketing_communications: "Marketing Communications",
        };
        return labels[consentType] || consentType.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase());
    };

    const getConsentDescription = (consentType: string) => {
        const descriptions: Record<string, string> = {
            story_recommendations: "Allow us to recommend stories based on your reading history",
            personalized_ads: "Show ads tailored to your interests",
            analytics_tracking: "Help us improve by tracking how you use the platform",
            email_notifications: "Receive email notifications about your account activity",
            data_processing: "Process your data to provide platform services",
            marketing_communications: "Receive marketing emails and promotional content",
        };
        return descriptions[consentType] || "Consent for platform features";
    };

    if (loading) {
        return (
            <Card>
                <CardHeader>
                    <Skeleton className="h-6 w-48" />
                    <Skeleton className="h-4 w-96" />
                </CardHeader>
                <CardContent className="space-y-4">
                    {[1, 2, 3].map((i) => (
                        <div key={i} className="border rounded-lg p-4">
                            <Skeleton className="h-5 w-64 mb-2" />
                            <Skeleton className="h-4 w-full mb-2" />
                            <Skeleton className="h-4 w-48" />
                        </div>
                    ))}
                </CardContent>
            </Card>
        );
    }

    if (consents.length === 0) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle>Consent History</CardTitle>
                    <CardDescription>
                        View and manage your consent preferences
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <Alert>
                        <AlertDescription>
                            No consent records found. Your consent preferences will appear here.
                        </AlertDescription>
                    </Alert>
                </CardContent>
            </Card>
        );
    }

    return (
        <>
            <Card>
                <CardHeader>
                    <CardTitle>Consent History</CardTitle>
                    <CardDescription>
                        View and manage your consent preferences. You can withdraw consent at any time.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    {consents.map((consent) => (
                        <div
                            key={consent.consent_type}
                            className="border rounded-lg p-4 space-y-3"
                        >
                            <div className="flex items-start justify-between gap-4">
                                <div className="flex-1 space-y-1">
                                    <div className="flex items-center gap-2">
                                        <h3 className="font-semibold">
                                            {getConsentLabel(consent.consent_type)}
                                        </h3>
                                        {consent.granted ? (
                                            <CheckCircle2 className="h-4 w-4 text-green-600" />
                                        ) : (
                                            <XCircle className="h-4 w-4 text-red-600" />
                                        )}
                                    </div>
                                    <p className="text-sm text-muted-foreground">
                                        {getConsentDescription(consent.consent_type)}
                                    </p>
                                </div>
                                {consent.granted && (
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={() => setConsentToWithdraw(consent.consent_type)}
                                        disabled={withdrawing === consent.consent_type}
                                    >
                                        {withdrawing === consent.consent_type ? "Withdrawing..." : "Withdraw"}
                                    </Button>
                                )}
                            </div>

                            <div className="text-xs text-muted-foreground space-y-1">
                                <div className="flex items-center gap-2">
                                    <span className="font-medium">Status:</span>
                                    <span>{consent.granted ? "Active" : "Withdrawn"}</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <span className="font-medium">Granted:</span>
                                    <span>{formatDate(consent.granted_at)}</span>
                                </div>
                                {consent.withdrawn_at && (
                                    <div className="flex items-center gap-2">
                                        <span className="font-medium">Withdrawn:</span>
                                        <span>{formatDate(consent.withdrawn_at)}</span>
                                    </div>
                                )}
                                <div className="flex items-center gap-2">
                                    <span className="font-medium">IP Address:</span>
                                    <span className="font-mono">{consent.ip_address}</span>
                                </div>
                            </div>
                        </div>
                    ))}
                </CardContent>
            </Card>

            <AlertDialog open={!!consentToWithdraw} onOpenChange={(open) => !open && setConsentToWithdraw(null)}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle className="flex items-center gap-2">
                            <AlertTriangle className="h-5 w-5 text-amber-600" />
                            Withdraw Consent
                        </AlertDialogTitle>
                        <AlertDialogDescription>
                            Are you sure you want to withdraw your consent for{" "}
                            <span className="font-semibold">
                                {consentToWithdraw && getConsentLabel(consentToWithdraw)}
                            </span>
                            ? This may affect your experience on the platform.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction
                            onClick={() => consentToWithdraw && handleWithdrawConsent(consentToWithdraw)}
                        >
                            Withdraw Consent
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </>
    );
}
