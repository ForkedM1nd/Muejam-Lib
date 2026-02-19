/**
 * DMCA Takedown Request Form Component
 * 
 * Allows copyright holders to submit DMCA takedown requests for infringing content.
 * 
 * Requirements:
 * - 31.1: Provide DMCA takedown request form accessible from footer
 * - 31.2: Require specific fields in DMCA requests
 * - 31.3: Require electronic signature
 */

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useToast } from '@/hooks/use-toast';
import { api } from '@/lib/api';

interface DMCAFormData {
    copyright_holder: string;
    contact_info: string;
    copyrighted_work_description: string;
    infringing_url: string;
    good_faith_statement: boolean;
    signature: string;
}

export default function DMCAForm() {
    const { toast } = useToast();
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isSubmitted, setIsSubmitted] = useState(false);
    const [formData, setFormData] = useState<DMCAFormData>({
        copyright_holder: '',
        contact_info: '',
        copyrighted_work_description: '',
        infringing_url: '',
        good_faith_statement: false,
        signature: '',
    });
    const [errors, setErrors] = useState<Partial<Record<keyof DMCAFormData, string>>>({});

    const handleInputChange = (
        field: keyof DMCAFormData,
        value: string | boolean
    ) => {
        setFormData((prev) => ({ ...prev, [field]: value }));
        // Clear error when user starts typing
        if (errors[field]) {
            setErrors((prev) => ({ ...prev, [field]: undefined }));
        }
    };

    const validateForm = (): boolean => {
        const newErrors: Partial<Record<keyof DMCAFormData, string>> = {};

        if (!formData.copyright_holder.trim()) {
            newErrors.copyright_holder = 'Copyright holder name is required';
        }

        if (!formData.contact_info.trim()) {
            newErrors.contact_info = 'Contact information is required';
        }

        if (!formData.copyrighted_work_description.trim()) {
            newErrors.copyrighted_work_description = 'Description of copyrighted work is required';
        } else if (formData.copyrighted_work_description.trim().length < 20) {
            newErrors.copyrighted_work_description = 'Description must be at least 20 characters';
        }

        if (!formData.infringing_url.trim()) {
            newErrors.infringing_url = 'URL of infringing content is required';
        } else {
            try {
                new URL(formData.infringing_url);
            } catch {
                newErrors.infringing_url = 'Please enter a valid URL';
            }
        }

        if (!formData.good_faith_statement) {
            newErrors.good_faith_statement = 'You must confirm the good faith statement';
        }

        if (!formData.signature.trim()) {
            newErrors.signature = 'Electronic signature is required';
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!validateForm()) {
            toast({
                title: 'Validation Error',
                description: 'Please fix the errors in the form',
                variant: 'destructive',
            });
            return;
        }

        setIsSubmitting(true);

        try {
            await api.submitDMCA(formData);

            setIsSubmitted(true);
            toast({
                title: 'DMCA Request Submitted',
                description: 'Your DMCA takedown request has been submitted successfully. You will receive a confirmation email shortly.',
            });
        } catch (error: any) {
            console.error('Failed to submit DMCA request:', error);
            toast({
                title: 'Submission Failed',
                description: error.response?.data?.error || 'Failed to submit DMCA request. Please try again.',
                variant: 'destructive',
            });
        } finally {
            setIsSubmitting(false);
        }
    };

    if (isSubmitted) {
        return (
            <Card className="max-w-2xl mx-auto">
                <CardHeader>
                    <CardTitle>Request Submitted</CardTitle>
                    <CardDescription>
                        Your DMCA takedown request has been submitted successfully.
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <Alert>
                        <AlertDescription>
                            Thank you for submitting your DMCA takedown request. You will receive a confirmation
                            email shortly. Our designated DMCA agent will review your request and take appropriate
                            action. If you have any questions, please contact us using the information provided in
                            the confirmation email.
                        </AlertDescription>
                    </Alert>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card className="max-w-2xl mx-auto">
            <CardHeader>
                <CardTitle>DMCA Takedown Request</CardTitle>
                <CardDescription>
                    Submit a request to remove content that infringes your copyright. All fields are required.
                </CardDescription>
            </CardHeader>
            <CardContent>
                <form onSubmit={handleSubmit} className="space-y-6">
                    {/* Copyright Holder */}
                    <div className="space-y-2">
                        <Label htmlFor="copyright_holder">
                            Copyright Holder Name <span className="text-red-500">*</span>
                        </Label>
                        <Input
                            id="copyright_holder"
                            value={formData.copyright_holder}
                            onChange={(e) => handleInputChange('copyright_holder', e.target.value)}
                            placeholder="Your full legal name or company name"
                            className={errors.copyright_holder ? 'border-red-500' : ''}
                        />
                        {errors.copyright_holder && (
                            <p className="text-sm text-red-500">{errors.copyright_holder}</p>
                        )}
                    </div>

                    {/* Contact Information */}
                    <div className="space-y-2">
                        <Label htmlFor="contact_info">
                            Contact Information <span className="text-red-500">*</span>
                        </Label>
                        <Textarea
                            id="contact_info"
                            value={formData.contact_info}
                            onChange={(e) => handleInputChange('contact_info', e.target.value)}
                            placeholder="Email, phone number, and mailing address"
                            rows={3}
                            className={errors.contact_info ? 'border-red-500' : ''}
                        />
                        {errors.contact_info && (
                            <p className="text-sm text-red-500">{errors.contact_info}</p>
                        )}
                    </div>

                    {/* Copyrighted Work Description */}
                    <div className="space-y-2">
                        <Label htmlFor="copyrighted_work_description">
                            Description of Copyrighted Work <span className="text-red-500">*</span>
                        </Label>
                        <Textarea
                            id="copyrighted_work_description"
                            value={formData.copyrighted_work_description}
                            onChange={(e) => handleInputChange('copyrighted_work_description', e.target.value)}
                            placeholder="Describe the copyrighted work that you believe has been infringed (minimum 20 characters)"
                            rows={4}
                            className={errors.copyrighted_work_description ? 'border-red-500' : ''}
                        />
                        {errors.copyrighted_work_description && (
                            <p className="text-sm text-red-500">{errors.copyrighted_work_description}</p>
                        )}
                    </div>

                    {/* Infringing URL */}
                    <div className="space-y-2">
                        <Label htmlFor="infringing_url">
                            URL of Infringing Content <span className="text-red-500">*</span>
                        </Label>
                        <Input
                            id="infringing_url"
                            type="url"
                            value={formData.infringing_url}
                            onChange={(e) => handleInputChange('infringing_url', e.target.value)}
                            placeholder="https://example.com/infringing-content"
                            className={errors.infringing_url ? 'border-red-500' : ''}
                        />
                        {errors.infringing_url && (
                            <p className="text-sm text-red-500">{errors.infringing_url}</p>
                        )}
                    </div>

                    {/* Good Faith Statement */}
                    <div className="space-y-2">
                        <div className="flex items-start space-x-2">
                            <Checkbox
                                id="good_faith_statement"
                                checked={formData.good_faith_statement}
                                onCheckedChange={(checked) =>
                                    handleInputChange('good_faith_statement', checked === true)
                                }
                                className={errors.good_faith_statement ? 'border-red-500' : ''}
                            />
                            <div className="grid gap-1.5 leading-none">
                                <Label
                                    htmlFor="good_faith_statement"
                                    className="text-sm font-normal cursor-pointer"
                                >
                                    I have a good faith belief that the use of the material in the manner complained
                                    of is not authorized by the copyright owner, its agent, or the law.{' '}
                                    <span className="text-red-500">*</span>
                                </Label>
                            </div>
                        </div>
                        {errors.good_faith_statement && (
                            <p className="text-sm text-red-500">{errors.good_faith_statement}</p>
                        )}
                    </div>

                    {/* Electronic Signature */}
                    <div className="space-y-2">
                        <Label htmlFor="signature">
                            Electronic Signature <span className="text-red-500">*</span>
                        </Label>
                        <Input
                            id="signature"
                            value={formData.signature}
                            onChange={(e) => handleInputChange('signature', e.target.value)}
                            placeholder="Type your full legal name"
                            className={errors.signature ? 'border-red-500' : ''}
                        />
                        <p className="text-sm text-muted-foreground">
                            By typing your name, you are providing an electronic signature that has the same legal
                            effect as a handwritten signature.
                        </p>
                        {errors.signature && <p className="text-sm text-red-500">{errors.signature}</p>}
                    </div>

                    {/* Legal Notice */}
                    <Alert>
                        <AlertDescription className="text-sm">
                            <strong>Legal Notice:</strong> Under penalty of perjury, I certify that the
                            information in this notification is accurate and that I am the copyright owner or
                            authorized to act on behalf of the owner of an exclusive right that is allegedly
                            infringed. Misrepresentation of copyright infringement may result in legal liability.
                        </AlertDescription>
                    </Alert>

                    {/* Submit Button */}
                    <Button type="submit" disabled={isSubmitting} className="w-full">
                        {isSubmitting ? 'Submitting...' : 'Submit DMCA Request'}
                    </Button>
                </form>
            </CardContent>
        </Card>
    );
}
