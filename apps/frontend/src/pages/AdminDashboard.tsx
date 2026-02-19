import { useState } from "react";
import { Navigate } from "react-router-dom";
import { useUser } from "@clerk/clerk-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, BarChart3, FileText, Shield } from "lucide-react";
import { HealthMetrics } from "@/components/admin/HealthMetrics";
import { MetricsDashboard } from "@/components/admin/MetricsDashboard";
import { AuditLogViewer } from "@/components/admin/AuditLogViewer";

export default function AdminDashboard() {
    const { user, isLoaded } = useUser();
    const [activeTab, setActiveTab] = useState("health");

    // Check if user has admin role
    // In Clerk, roles are stored in publicMetadata
    const isAdmin = user?.publicMetadata?.role === "admin";

    // Show loading state while checking auth
    if (!isLoaded) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
        );
    }

    // Redirect non-admin users
    if (!isAdmin) {
        return <Navigate to="/" replace />;
    }

    return (
        <div className="flex h-screen bg-background">
            {/* Sidebar */}
            <aside className="hidden md:flex md:w-64 md:flex-col border-r">
                <div className="flex h-16 items-center border-b px-6">
                    <Shield className="h-6 w-6 mr-2 text-primary" />
                    <h1 className="text-xl font-bold">Admin Dashboard</h1>
                </div>
                <nav className="flex-1 space-y-1 p-4">
                    <button
                        onClick={() => setActiveTab("health")}
                        className={`flex items-center w-full px-4 py-2 text-sm font-medium rounded-md transition-colors ${activeTab === "health"
                            ? "bg-primary text-primary-foreground"
                            : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                            }`}
                    >
                        <Activity className="mr-3 h-5 w-5" />
                        System Health
                    </button>
                    <button
                        onClick={() => setActiveTab("metrics")}
                        className={`flex items-center w-full px-4 py-2 text-sm font-medium rounded-md transition-colors ${activeTab === "metrics"
                            ? "bg-primary text-primary-foreground"
                            : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                            }`}
                    >
                        <BarChart3 className="mr-3 h-5 w-5" />
                        Metrics
                    </button>
                    <button
                        onClick={() => setActiveTab("audit")}
                        className={`flex items-center w-full px-4 py-2 text-sm font-medium rounded-md transition-colors ${activeTab === "audit"
                            ? "bg-primary text-primary-foreground"
                            : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                            }`}
                    >
                        <FileText className="mr-3 h-5 w-5" />
                        Audit Logs
                    </button>
                </nav>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-y-auto">
                <div className="container mx-auto p-6 space-y-6">
                    {/* Mobile Navigation */}
                    <div className="md:hidden">
                        <Tabs value={activeTab} onValueChange={setActiveTab}>
                            <TabsList className="grid w-full grid-cols-3">
                                <TabsTrigger value="health">
                                    <Activity className="h-4 w-4 mr-2" />
                                    Health
                                </TabsTrigger>
                                <TabsTrigger value="metrics">
                                    <BarChart3 className="h-4 w-4 mr-2" />
                                    Metrics
                                </TabsTrigger>
                                <TabsTrigger value="audit">
                                    <FileText className="h-4 w-4 mr-2" />
                                    Audit
                                </TabsTrigger>
                            </TabsList>
                        </Tabs>
                    </div>

                    {/* Health Section */}
                    {activeTab === "health" && (
                        <div className="space-y-6">
                            <div>
                                <h2 className="text-3xl font-bold tracking-tight">System Health</h2>
                                <p className="text-muted-foreground">
                                    Monitor the health and status of platform services
                                </p>
                            </div>
                            <HealthMetrics />
                        </div>
                    )}

                    {/* Metrics Section */}
                    {activeTab === "metrics" && (
                        <div className="space-y-6">
                            <div>
                                <h2 className="text-3xl font-bold tracking-tight">Platform Metrics</h2>
                                <p className="text-muted-foreground">
                                    Business and moderation metrics overview
                                </p>
                            </div>
                            <MetricsDashboard />
                        </div>
                    )}

                    {/* Audit Logs Section */}
                    {activeTab === "audit" && (
                        <div className="space-y-6">
                            <div>
                                <h2 className="text-3xl font-bold tracking-tight">Audit Logs</h2>
                                <p className="text-muted-foreground">
                                    Review system audit logs and security events
                                </p>
                            </div>
                            <AuditLogViewer />
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}
