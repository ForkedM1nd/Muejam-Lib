import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ArrowLeft, Mail, CheckCircle } from 'lucide-react';
import PageHeader from '@/components/shared/PageHeader';
import SurfacePanel from '@/components/shared/SurfacePanel';

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
            setError('Please fill in all fields.');
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
                setError(data.error || 'Failed to submit support request.');
            }
        } catch (err) {
            setError('Failed to submit support request. Please try again.');
        } finally {
            setSubmitting(false);
        }
    };

    if (submitted) {
        return (
            <div className="mx-auto max-w-2xl space-y-5">
                <Link to="/help" className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
                    <ArrowLeft className="h-4 w-4" />
                    Back to Help Center
                </Link>

                <SurfacePanel className="p-8 text-center">
                    <CheckCircle className="mx-auto mb-4 h-16 w-16 text-primary" />
                    <h2 className="text-2xl font-semibold" style={{ fontFamily: 'var(--font-display)' }}>
                        Request Submitted
                    </h2>
                    <p className="mt-2 text-muted-foreground">
                        Thank you for contacting us. We'll get back to you as soon as possible.
                    </p>
                    <div className="mt-6 flex justify-center gap-3">
                        <Link to="/help">
                            <Button variant="outline">Back to Help Center</Button>
                        </Link>
                        <Button onClick={() => setSubmitted(false)}>Submit Another Request</Button>
                    </div>
                </SurfacePanel>
            </div>
        );
    }

    return (
        <div className="mx-auto max-w-3xl space-y-5">
            <Link to="/help" className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
                <ArrowLeft className="h-4 w-4" />
                Back to Help Center
            </Link>

            <PageHeader
                title="Contact Support"
                eyebrow="Support"
                description="Send us a message and our team will help you out."
                action={<Mail className="h-5 w-5 text-primary" />}
            />

            <SurfacePanel className="p-5 sm:p-6">
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
                        <div className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
                            {error}
                        </div>
                    )}

                    <Button type="submit" disabled={submitting} className="w-full">
                        {submitting ? 'Submitting...' : 'Submit Request'}
                    </Button>
                </form>
            </SurfacePanel>
        </div>
    );
}
