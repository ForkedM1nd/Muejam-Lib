import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ArrowLeft, Mail, CheckCircle } from 'lucide-react';

const SUPPORT_CATEGORIES = [
    { value: 'ACCOUNT', label: 'Account & Login Issues' },
    { value: 'TECHNICAL', label: 'Technical Problems' },
    { value: 'CONTENT', label: 'Content & Stories' },
    { value: 'BILLING', label: 'Billing & Payments' },
    { value: 'PRIVACY', label: 'Privacy & Data' },
    { value: 'MODERATION', label: 'Moderation & Reports' },
    { value: 'FEATURE', label: 'Feature Request' },
    { value: 'OTHER', label: 'Other' },
];

export function ContactSupport() {
    const [formData, setFormData] = useState({
        name: '',
        email: '',
        category: '',
        subject: '',
        message: '',
    });
    const [submitting, setSubmitting] = useState(false);
    const [submitted, setSubmitted] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        if (!formData.name || !formData.email || !formData.category || !formData.subject || !formData.message) {
            setError('Please fill in all fields');
            return;
        }

        try {
            setSubmitting(true);
            const response = await fetch('/v1/help/support/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData),
            });

            if (response.ok) {
                setSubmitted(true);
                setFormData({ name: '', email: '', category: '', subject: '', message: '' });
            } else {
                const data = await response.json();
                setError(data.error || 'Failed to submit support request');
            }
        } catch (err) {
            setError('Failed to submit support request. Please try again.');
        } finally {
            setSubmitting(false);
        }
    };

    if (submitted) {
        return (
            <div className="container mx-auto px-4 py-8 max-w-2xl">
                <Link to="/help" className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground mb-6">
                    <ArrowLeft className="h-4 w-4" />
                    Back to Help Center
                </Link>

                <Card>
                    <CardContent className="p-8 text-center">
                        <CheckCircle className="h-16 w-16 text-green-600 mx-auto mb-4" />
                        <h2 className="text-2xl font-semibold mb-2">Request Submitted</h2>
                        <p className="text-muted-foreground mb-6">
                            Thank you for contacting us. We'll get back to you as soon as possible.
                        </p>
                        <div className="flex gap-3 justify-center">
                            <Link to="/help">
                                <Button variant="outline">Back to Help Center</Button>
                            </Link>
                            <Button onClick={() => setSubmitted(false)}>
                                Submit Another Request
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            </div>
        );
    }

    return (
        <div className="container mx-auto px-4 py-8 max-w-2xl">
            <Link to="/help" className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground mb-6">
                <ArrowLeft className="h-4 w-4" />
                Back to Help Center
            </Link>

            <Card>
                <CardHeader>
                    <div className="flex items-center gap-2 mb-2">
                        <Mail className="h-6 w-6" />
                        <CardTitle className="text-2xl">Contact Support</CardTitle>
                    </div>
                    <CardDescription>
                        Can't find what you're looking for? Send us a message and we'll help you out.
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="name">Name</Label>
                            <Input
                                id="name"
                                type="text"
                                placeholder="Your name"
                                value={formData.name}
                                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                required
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="email">Email</Label>
                            <Input
                                id="email"
                                type="email"
                                placeholder="your.email@example.com"
                                value={formData.email}
                                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                                required
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="category">Category</Label>
                            <Select
                                value={formData.category}
                                onValueChange={(value) => setFormData({ ...formData, category: value })}
                            >
                                <SelectTrigger id="category">
                                    <SelectValue placeholder="Select a category" />
                                </SelectTrigger>
                                <SelectContent>
                                    {SUPPORT_CATEGORIES.map((category) => (
                                        <SelectItem key={category.value} value={category.value}>
                                            {category.label}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="subject">Subject</Label>
                            <Input
                                id="subject"
                                type="text"
                                placeholder="Brief description of your issue"
                                value={formData.subject}
                                onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                                required
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="message">Message</Label>
                            <Textarea
                                id="message"
                                placeholder="Please provide as much detail as possible..."
                                value={formData.message}
                                onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                                rows={8}
                                required
                            />
                        </div>

                        {error && (
                            <div className="text-sm text-red-600 bg-red-50 p-3 rounded">
                                {error}
                            </div>
                        )}

                        <Button type="submit" disabled={submitting} className="w-full">
                            {submitting ? 'Submitting...' : 'Submit Request'}
                        </Button>
                    </form>
                </CardContent>
            </Card>
        </div>
    );
}
