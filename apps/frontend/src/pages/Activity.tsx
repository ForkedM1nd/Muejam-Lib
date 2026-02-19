// ── Activity Page ──
// Displays the activity feed of followed users

import { ActivityFeed } from "@/components/shared/ActivityFeed";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function Activity() {
    return (
        <div className="max-w-4xl mx-auto px-4 py-8">
            <div className="mb-6">
                <h1 className="text-3xl font-bold tracking-tight">Activity Feed</h1>
                <p className="text-muted-foreground mt-2">
                    See what the people you follow are up to
                </p>
            </div>

            <Tabs defaultValue="following" className="space-y-6">
                <TabsList>
                    <TabsTrigger value="following">Following</TabsTrigger>
                    <TabsTrigger value="all" disabled>
                        All Activity
                    </TabsTrigger>
                </TabsList>

                <TabsContent value="following" className="space-y-4">
                    <ActivityFeed />
                </TabsContent>

                <TabsContent value="all">
                    <Card>
                        <CardHeader>
                            <CardTitle>All Activity</CardTitle>
                            <CardDescription>
                                Coming soon: See activity from all users on the platform
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <p className="text-sm text-muted-foreground">
                                This feature is not yet available.
                            </p>
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    );
}
