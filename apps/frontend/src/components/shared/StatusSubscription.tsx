import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Mail, CheckCircle } from 'lucide-react';
import { services } from '@/lib/api';

export function StatusSubscription() {
    const [email, setEmail] = useState('');
    const [loading, setLoading] = useState(false);
    const [subscribed, setSubscribed] = useState(false);
    const [error, setError] = useState('');

    const handleSubscribe = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        if (!email || !email.includes('@')) {
            setError('Please enter a valid email address');
            return;
        }

        try {
            setLoading(true);
            await services.status.subscribeToUpdates(email);
            setSubscribed(true);
            setEmail('');
        } catch (err) {
            setError('Failed to subscribe. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    if (subscribed) {
        return (
            <Card>
                <CardContent className="pt-6">
                    <div className="flex items-center gap-3 text-green-600">
                        <CheckCircle className="h-5 w-5" />
                        <div>
                            <p className="font-medium">Successfully subscribed!</p>
                            <p className="text-sm text-muted-foreground">
                                You'll receive email notifications about system status updates.
                            </p>
                        </div>
                    </div>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <Mail className="h-5 w-5" />
                    Subscribe to Status Updates
                </CardTitle>
                <CardDescription>
                    Get notified via email when there are incidents or maintenance windows
                </CardDescription>
            </CardHeader>
            <CardContent>
                <form onSubmit={handleSubscribe} className="space-y-4">
                    <div className="space-y-2">
                        <Label htmlFor="email">Email Address</Label>
                        <Input
                            id="email"
                            type="email"
                            placeholder="your.email@example.com"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                        />
                    </div>

                    {error && (
                        <Alert variant="destructive">
                            <AlertDescription>{error}</AlertDescription>
                        </Alert>
                    )}

                    <Button type="submit" disabled={loading} className="w-full">
                        {loading ? 'Subscribing...' : 'Subscribe'}
                    </Button>

                    <p className="text-xs text-muted-foreground">
                        You can unsubscribe at any time from the emails we send.
                    </p>
                </form>
            </CardContent>
        </Card>
    );
}
