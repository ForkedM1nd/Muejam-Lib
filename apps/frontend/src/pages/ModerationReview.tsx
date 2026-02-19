import { Navigate, useNavigate, useParams } from "react-router-dom";
import { useUser } from "@clerk/clerk-react";
import { ArrowLeft, Loader2, AlertCircle } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ModerationActionPanel } from "@/components/moderation/ModerationActionPanel";
import { services } from "@/lib/api";
import { formatDistanceToNow } from "date-fns";
import type { ModerationItem } from "@/types";

const severityColors = {
    low: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300",
    medium: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300",
    high: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300",
};

export default function ModerationReview() {
    const { itemId } = useParams<{ itemId: string }>();
    const { user, isLoaded } = useUser();
    const navigate = useNavigate();

    // Check if user has moderator role
    const isModerator = user?.publicMetadata?.role === "moderator" || user?.publicMetadata?.role === "admin";

    // Fetch the specific moderation item
    // Note: This would need to be added to the moderation service
    // For now, we'll fetch the queue and find the item
    const { data: queueData, isLoading, isError } = useQuery({
        queryKey: ["moderation", "queue"],
        queryFn: () => services.moderation.getQueue({ page_size: 100 }),
        enabled: !!itemId && isModerator,
    });

    const item = queueData?.results.find((i: ModerationItem) => i.id === itemId);

    const handleActionComplete = () => {
        // Navigate back to the queue after action is complete
        navigate("/moderation");
    };

    // Show loading state while checking auth
    if (!isLoaded) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    // Redirect non-moderator users
    if (!isModerator) {
        return <Navigate to="/" replace />;
    }

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    if (isError || !item) {
        return (
            <div className="container mx-auto p-6">
                <Card>
                    <CardContent className="flex flex-col items-center justify-center py-12">
                        <AlertCircle className="h-12 w-12 text-destructive mb-4" />
                        <p className="text-lg font-medium mb-2">Item not found</p>
                        <p className="text-sm text-muted-foreground text-center max-w-md mb-4">
                            The moderation item could not be found or has been removed.
                        </p>
                        <Button onClick={() => navigate("/moderation")}>
                            Back to Queue
                        </Button>
                    </CardContent>
                </Card>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-background">
            <div className="container mx-auto p-6 space-y-6">
                {/* Header */}
                <div className="flex items-center gap-4">
                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => navigate("/moderation")}
                    >
                        <ArrowLeft className="h-5 w-5" />
                    </Button>
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight">Review Flagged Content</h1>
                        <p className="text-muted-foreground">
                            Review and take action on this moderation report
                        </p>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Left Column - Content Details */}
                    <div className="lg:col-span-2 space-y-6">
                        {/* Report Information */}
                        <Card>
                            <CardHeader>
                                <CardTitle>Report Information</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="flex items-center gap-2 flex-wrap">
                                    <Badge variant="outline" className="capitalize">
                                        {item.content_type}
                                    </Badge>
                                    <Badge className={severityColors[item.severity]}>
                                        {item.severity} severity
                                    </Badge>
                                    <Badge variant="secondary">
                                        {item.status}
                                    </Badge>
                                </div>

                                <div className="space-y-2">
                                    <div>
                                        <span className="text-sm font-medium">Report Reason:</span>
                                        <p className="text-sm text-muted-foreground mt-1">
                                            {item.report_reason}
                                        </p>
                                    </div>

                                    {item.report_details && (
                                        <div>
                                            <span className="text-sm font-medium">Additional Details:</span>
                                            <p className="text-sm text-muted-foreground mt-1 whitespace-pre-wrap">
                                                {item.report_details}
                                            </p>
                                        </div>
                                    )}

                                    <div className="flex items-center gap-4 text-xs text-muted-foreground pt-2 border-t">
                                        <span>Content ID: {item.content_id}</span>
                                        <span>Reporter ID: {item.reporter_id}</span>
                                        <span>
                                            Reported {formatDistanceToNow(new Date(item.created_at), { addSuffix: true })}
                                        </span>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Content Preview */}
                        <Card>
                            <CardHeader>
                                <CardTitle>Flagged Content</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="bg-muted p-4 rounded-lg">
                                    <p className="text-sm whitespace-pre-wrap">
                                        {item.content_preview}
                                    </p>
                                </div>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Right Column - Action Panel */}
                    <div className="lg:col-span-1">
                        <ModerationActionPanel
                            item={item}
                            onActionComplete={handleActionComplete}
                        />
                    </div>
                </div>
            </div>
        </div>
    );
}
