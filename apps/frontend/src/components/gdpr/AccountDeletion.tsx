import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
    AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { services } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import type { DeletionRequest, DeletionStatus } from "@/types";
import { Trash2, AlertTriangle, Clock, CheckCircle2, XCircle, Loader2, Calendar } from "lucide-react";

export function AccountDeletion() {
    const [deletionRequest, setDeletionRequest] = useState<DeletionRequest | null>(null);
    const [deletionStatus, setDeletionStatus] = useState<DeletionStatus | null>(null);
    const [requesting, setRequesting] = useState(false);
    const [cancelling, setCancelling] = useState(false);
    const [polling, setPolling] = useState(false);
    const { toast } = useToast();

    const handleRequestDeletion = async () => {
        try {
            setRequesting(true);
            const request = await services.gdpr.requestAccountDeletion();
            setDeletionRequest(request);

            toast({
                title: "Deletion requested",
                description: "Your account deletion has been scheduled. You can cancel this request during the grace period.",
            });

            // Start polling for status
            startPolling(request.deletion_id);
        } catch (error) {
            toast({
                title: "Error",
                description: "Failed to request account deletion. Please try again.",
                variant: "destructive",
            });
        } finally {
            setRequesting(false);
        }
    };

    const handleCancelDeletion = async () => {
        if (!deletionRequest?.deletion_id) return;

        try {
            setCancelling(true);
            await services.gdpr.cancelDeletion(deletionRequest.deletion_id);

            // Clear the deletion request
            setDeletionRequest(null);
            setDeletionStatus(null);

            toast({
                title: "Deletion cancelled",
                description: "Your account deletion has been cancelled. Your account will remain active.",
            });
        } catch (error) {
            toast({
                title: "Error",
                description: "Failed to cancel account deletion. Please try again.",
                variant: "destructive",
            });
        } finally {
            setCancelling(false);
        }
    };

    const startPolling = (deletionId: string) => {
        setPolling(true);
        const pollInterval = setInterval(async () => {
            try {
                const status = await services.gdpr.getDeletionStatus(deletionId);
                setDeletionStatus(status);

                // Stop polling if completed or cancelled
                if (status.status === "completed" || status.status === "cancelled") {
                    clearInterval(pollInterval);
                    setPolling(false);

                    if (status.status === "completed") {
                        toast({
                            title: "Account deleted",
                            description: "Your account has been permanently deleted.",
                        });
                    }
                }
            } catch (error) {
                clearInterval(pollInterval);
                setPolling(false);
                toast({
                    title: "Error",
                    description: "Failed to check deletion status. Please refresh the page.",
                    variant: "destructive",
                });
            }
        }, 10000); // Poll every 10 seconds

        // Clean up on unmount
        return () => clearInterval(pollInterval);
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

    const getStatusIcon = (status: string) => {
        switch (status) {
            case "pending":
                return <Clock className="h-5 w-5 text-amber-600" />;
            case "processing":
                return <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />;
            case "completed":
                return <CheckCircle2 className="h-5 w-5 text-green-600" />;
            case "cancelled":
                return <XCircle className="h-5 w-5 text-gray-600" />;
            default:
                return null;
        }
    };

    const getStatusText = (status: string) => {
        switch (status) {
            case "pending":
                return "Pending";
            case "processing":
                return "Processing";
            case "completed":
                return "Completed";
            case "cancelled":
                return "Cancelled";
            default:
                return status;
        }
    };

    const calculateDaysRemaining = (scheduledFor: string) => {
        const now = new Date();
        const scheduled = new Date(scheduledFor);
        const diffTime = scheduled.getTime() - now.getTime();
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        return diffDays;
    };

    const currentStatus = deletionStatus || deletionRequest;

    return (
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center gap-2 text-red-600">
                    <Trash2 className="h-5 w-5" />
                    Account Deletion
                </CardTitle>
                <CardDescription>
                    Permanently delete your account and all associated data
                </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
                <Alert variant="destructive">
                    <AlertTriangle className="h-4 w-4" />
                    <AlertDescription>
                        <strong>Warning:</strong> Account deletion is permanent and cannot be undone.
                        All your stories, chapters, whispers, highlights, and profile information will be
                        permanently deleted. You will have a grace period to cancel the deletion before
                        it is finalized.
                    </AlertDescription>
                </Alert>

                {!currentStatus && (
                    <div className="space-y-4">
                        <div className="space-y-2">
                            <h4 className="font-semibold">What will be deleted:</h4>
                            <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
                                <li>Your profile and account information</li>
                                <li>All stories and chapters you've written</li>
                                <li>All whispers and comments</li>
                                <li>All highlights and bookmarks</li>
                                <li>Your reading history and preferences</li>
                                <li>All followers and following relationships</li>
                            </ul>
                        </div>

                        <div className="space-y-2">
                            <h4 className="font-semibold">Grace period:</h4>
                            <p className="text-sm text-muted-foreground">
                                After requesting deletion, you will have 30 days to cancel the request.
                                During this time, your account will remain active but will be scheduled
                                for deletion. After the grace period expires, your account will be
                                permanently deleted.
                            </p>
                        </div>

                        <AlertDialog>
                            <AlertDialogTrigger asChild>
                                <Button
                                    variant="destructive"
                                    className="w-full sm:w-auto"
                                    disabled={requesting}
                                >
                                    {requesting ? (
                                        <>
                                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                            Requesting...
                                        </>
                                    ) : (
                                        <>
                                            <Trash2 className="mr-2 h-4 w-4" />
                                            Request Account Deletion
                                        </>
                                    )}
                                </Button>
                            </AlertDialogTrigger>
                            <AlertDialogContent>
                                <AlertDialogHeader>
                                    <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
                                    <AlertDialogDescription>
                                        This action will schedule your account for permanent deletion.
                                        You will have 30 days to cancel this request. After that,
                                        all your data will be permanently deleted and cannot be recovered.
                                    </AlertDialogDescription>
                                </AlertDialogHeader>
                                <AlertDialogFooter>
                                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                                    <AlertDialogAction
                                        onClick={handleRequestDeletion}
                                        className="bg-red-600 hover:bg-red-700"
                                    >
                                        Yes, delete my account
                                    </AlertDialogAction>
                                </AlertDialogFooter>
                            </AlertDialogContent>
                        </AlertDialog>
                    </div>
                )}

                {currentStatus && (
                    <div className="space-y-4">
                        <div className="border rounded-lg p-4 space-y-3">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    {getStatusIcon(currentStatus.status)}
                                    <span className="font-semibold">
                                        Deletion Status: {getStatusText(currentStatus.status)}
                                    </span>
                                </div>
                            </div>

                            <div className="text-sm text-muted-foreground space-y-1">
                                <div className="flex items-center gap-2">
                                    <span className="font-medium">Deletion ID:</span>
                                    <span className="font-mono">{currentStatus.deletion_id}</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <span className="font-medium">Requested:</span>
                                    <span>{formatDate(deletionRequest?.requested_at || new Date().toISOString())}</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <Calendar className="h-4 w-4" />
                                    <span className="font-medium">Scheduled for:</span>
                                    <span className="text-red-600 font-medium">
                                        {formatDate(currentStatus.scheduled_for)}
                                    </span>
                                </div>
                                {currentStatus.status === "pending" && (
                                    <div className="flex items-center gap-2 mt-2">
                                        <Clock className="h-4 w-4 text-amber-600" />
                                        <span className="font-medium text-amber-600">
                                            {calculateDaysRemaining(currentStatus.scheduled_for)} days remaining
                                            to cancel
                                        </span>
                                    </div>
                                )}
                            </div>

                            {currentStatus.status === "pending" && currentStatus.can_cancel && (
                                <Alert>
                                    <AlertTriangle className="h-4 w-4" />
                                    <AlertDescription>
                                        Your account is scheduled for deletion. You can cancel this request
                                        at any time during the grace period. After the scheduled date,
                                        your account will be permanently deleted.
                                    </AlertDescription>
                                </Alert>
                            )}

                            {currentStatus.status === "processing" && (
                                <Alert>
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                    <AlertDescription>
                                        Your account deletion is being processed. This may take a few minutes.
                                    </AlertDescription>
                                </Alert>
                            )}

                            {currentStatus.status === "completed" && (
                                <Alert variant="destructive">
                                    <CheckCircle2 className="h-4 w-4" />
                                    <AlertDescription>
                                        Your account has been permanently deleted. All your data has been removed
                                        from our systems.
                                    </AlertDescription>
                                </Alert>
                            )}

                            {currentStatus.status === "cancelled" && (
                                <Alert>
                                    <XCircle className="h-4 w-4" />
                                    <AlertDescription>
                                        Your account deletion request has been cancelled. Your account remains active.
                                    </AlertDescription>
                                </Alert>
                            )}
                        </div>

                        {currentStatus.status === "pending" && currentStatus.can_cancel && (
                            <AlertDialog>
                                <AlertDialogTrigger asChild>
                                    <Button
                                        variant="outline"
                                        className="w-full sm:w-auto"
                                        disabled={cancelling}
                                    >
                                        {cancelling ? (
                                            <>
                                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                                Cancelling...
                                            </>
                                        ) : (
                                            <>
                                                <XCircle className="mr-2 h-4 w-4" />
                                                Cancel Deletion Request
                                            </>
                                        )}
                                    </Button>
                                </AlertDialogTrigger>
                                <AlertDialogContent>
                                    <AlertDialogHeader>
                                        <AlertDialogTitle>Cancel account deletion?</AlertDialogTitle>
                                        <AlertDialogDescription>
                                            This will cancel your account deletion request. Your account
                                            will remain active and no data will be deleted.
                                        </AlertDialogDescription>
                                    </AlertDialogHeader>
                                    <AlertDialogFooter>
                                        <AlertDialogCancel>Go back</AlertDialogCancel>
                                        <AlertDialogAction onClick={handleCancelDeletion}>
                                            Yes, cancel deletion
                                        </AlertDialogAction>
                                    </AlertDialogFooter>
                                </AlertDialogContent>
                            </AlertDialog>
                        )}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
