import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Progress } from "@/components/ui/progress";
import { services } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import type { ExportRequest, ExportStatus } from "@/types";
import { Download, FileArchive, Clock, AlertCircle, CheckCircle2, Loader2 } from "lucide-react";

export function DataExport() {
    const [exportRequest, setExportRequest] = useState<ExportRequest | null>(null);
    const [exportStatus, setExportStatus] = useState<ExportStatus | null>(null);
    const [requesting, setRequesting] = useState(false);
    const [polling, setPolling] = useState(false);
    const { toast } = useToast();

    const handleRequestExport = async () => {
        try {
            setRequesting(true);
            const request = await services.gdpr.requestDataExport();
            setExportRequest(request);

            toast({
                title: "Export requested",
                description: "Your data export has been requested. We'll prepare your data for download.",
            });

            // Start polling for status
            startPolling(request.export_id);
        } catch (error) {
            toast({
                title: "Error",
                description: "Failed to request data export. Please try again.",
                variant: "destructive",
            });
        } finally {
            setRequesting(false);
        }
    };

    const startPolling = (exportId: string) => {
        setPolling(true);
        const pollInterval = setInterval(async () => {
            try {
                const status = await services.gdpr.getExportStatus(exportId);
                setExportStatus(status);

                // Stop polling if completed or failed
                if (status.status === "completed" || status.status === "failed") {
                    clearInterval(pollInterval);
                    setPolling(false);

                    if (status.status === "completed") {
                        toast({
                            title: "Export ready",
                            description: "Your data export is ready for download.",
                        });
                    } else {
                        toast({
                            title: "Export failed",
                            description: "Failed to prepare your data export. Please try again.",
                            variant: "destructive",
                        });
                    }
                }
            } catch (error) {
                clearInterval(pollInterval);
                setPolling(false);
                toast({
                    title: "Error",
                    description: "Failed to check export status. Please refresh the page.",
                    variant: "destructive",
                });
            }
        }, 5000); // Poll every 5 seconds

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
                return <Clock className="h-5 w-5 text-blue-600" />;
            case "processing":
                return <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />;
            case "completed":
                return <CheckCircle2 className="h-5 w-5 text-green-600" />;
            case "failed":
                return <AlertCircle className="h-5 w-5 text-red-600" />;
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
            case "failed":
                return "Failed";
            default:
                return status;
        }
    };

    const currentStatus = exportStatus || exportRequest;

    return (
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <FileArchive className="h-5 w-5" />
                    Data Export
                </CardTitle>
                <CardDescription>
                    Request a copy of all your personal data stored on our platform
                </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
                <Alert>
                    <AlertDescription>
                        Your export will include all your stories, chapters, whispers, highlights,
                        profile information, and activity history. The export will be available
                        for download for 7 days after completion.
                    </AlertDescription>
                </Alert>

                {!currentStatus && (
                    <div className="space-y-4">
                        <p className="text-sm text-muted-foreground">
                            Click the button below to request a complete export of your data.
                            This process may take several minutes depending on the amount of data.
                        </p>
                        <Button
                            onClick={handleRequestExport}
                            disabled={requesting}
                            className="w-full sm:w-auto"
                        >
                            {requesting ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    Requesting...
                                </>
                            ) : (
                                <>
                                    <Download className="mr-2 h-4 w-4" />
                                    Request Data Export
                                </>
                            )}
                        </Button>
                    </div>
                )}

                {currentStatus && (
                    <div className="space-y-4">
                        <div className="border rounded-lg p-4 space-y-3">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    {getStatusIcon(currentStatus.status)}
                                    <span className="font-semibold">
                                        Export Status: {getStatusText(currentStatus.status)}
                                    </span>
                                </div>
                            </div>

                            {exportStatus?.progress !== undefined && (
                                <div className="space-y-2">
                                    <div className="flex items-center justify-between text-sm">
                                        <span className="text-muted-foreground">Progress</span>
                                        <span className="font-medium">{exportStatus.progress}%</span>
                                    </div>
                                    <Progress value={exportStatus.progress} />
                                </div>
                            )}

                            <div className="text-sm text-muted-foreground space-y-1">
                                <div className="flex items-center gap-2">
                                    <span className="font-medium">Export ID:</span>
                                    <span className="font-mono">{currentStatus.export_id}</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <span className="font-medium">Requested:</span>
                                    <span>{formatDate(exportRequest?.requested_at || new Date().toISOString())}</span>
                                </div>
                                {currentStatus.status === "completed" && exportStatus?.expires_at && (
                                    <div className="flex items-center gap-2">
                                        <span className="font-medium">Expires:</span>
                                        <span className="text-amber-600 font-medium">
                                            {formatDate(exportStatus.expires_at)}
                                        </span>
                                    </div>
                                )}
                            </div>

                            {currentStatus.status === "completed" && exportStatus?.download_url && (
                                <div className="pt-2">
                                    <Button
                                        asChild
                                        className="w-full sm:w-auto"
                                    >
                                        <a
                                            href={exportStatus.download_url}
                                            download
                                            target="_blank"
                                            rel="noopener noreferrer"
                                        >
                                            <Download className="mr-2 h-4 w-4" />
                                            Download Export
                                        </a>
                                    </Button>
                                </div>
                            )}

                            {currentStatus.status === "failed" && (
                                <Alert variant="destructive">
                                    <AlertCircle className="h-4 w-4" />
                                    <AlertDescription>
                                        The export failed to complete. Please try requesting a new export.
                                    </AlertDescription>
                                </Alert>
                            )}

                            {(currentStatus.status === "pending" || currentStatus.status === "processing") && (
                                <Alert>
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                    <AlertDescription>
                                        Your export is being prepared. This page will update automatically
                                        when your export is ready.
                                    </AlertDescription>
                                </Alert>
                            )}
                        </div>

                        {currentStatus.status === "completed" || currentStatus.status === "failed" ? (
                            <Button
                                onClick={handleRequestExport}
                                disabled={requesting}
                                variant="outline"
                                className="w-full sm:w-auto"
                            >
                                {requesting ? (
                                    <>
                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                        Requesting...
                                    </>
                                ) : (
                                    "Request New Export"
                                )}
                            </Button>
                        ) : null}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
