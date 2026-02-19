import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { services } from '@/lib/api';
import type { UptimeData } from '@/lib/services/status.service';

export function StatusHistory() {
    const [uptimeData, setUptimeData] = useState<UptimeData[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchUptimeHistory();
    }, []);

    const fetchUptimeHistory = async () => {
        try {
            const data = await services.status.getUptimeHistory(90);
            setUptimeData(data);
        } catch (error) {
            console.error('Failed to fetch uptime history:', error);
        } finally {
            setLoading(false);
        }
    };

    const getUptimeColor = (uptime: number) => {
        if (uptime >= 99.9) return 'bg-green-600';
        if (uptime >= 99) return 'bg-yellow-600';
        return 'bg-red-600';
    };

    const calculateAverageUptime = () => {
        if (uptimeData.length === 0) return 0;
        const sum = uptimeData.reduce((acc, day) => acc + day.uptime_percentage, 0);
        return (sum / uptimeData.length).toFixed(2);
    };

    if (loading) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle>Uptime History</CardTitle>
                    <CardDescription>Loading...</CardDescription>
                </CardHeader>
            </Card>
        );
    }

    return (
        <Card>
            <CardHeader>
                <CardTitle>Uptime History</CardTitle>
                <CardDescription>
                    Last 90 days - Average uptime: {calculateAverageUptime()}%
                </CardDescription>
            </CardHeader>
            <CardContent>
                <div className="space-y-4">
                    {/* Uptime bars */}
                    <div className="grid grid-cols-30 gap-1">
                        {uptimeData.slice(-90).map((day, index) => (
                            <div
                                key={index}
                                className={`h-8 rounded ${getUptimeColor(day.uptime_percentage)}`}
                                title={`${new Date(day.date).toLocaleDateString()}: ${day.uptime_percentage}% uptime, ${day.incidents} incidents`}
                            />
                        ))}
                    </div>

                    {/* Legend */}
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <div className="flex items-center gap-2">
                            <div className="w-4 h-4 rounded bg-green-600" />
                            <span>99.9%+</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="w-4 h-4 rounded bg-yellow-600" />
                            <span>99-99.9%</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="w-4 h-4 rounded bg-red-600" />
                            <span>&lt;99%</span>
                        </div>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
