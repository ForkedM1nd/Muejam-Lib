import { useState, useEffect } from 'react';
import { useAuthContext } from '@/contexts/AuthContext';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { ScrollArea } from '@/components/ui/scroll-area';
import { services } from '@/lib/api';
import type { TermsAcceptance } from '@/types';
import ReactMarkdown from 'react-markdown';

export function TermsAcceptancePrompt() {
    const { isAuthenticated } = useAuthContext();
    const [acceptance, setAcceptance] = useState<TermsAcceptance | null>(null);
    const [termsContent, setTermsContent] = useState<string>('');
    const [loading, setLoading] = useState(true);
    const [hasAgreed, setHasAgreed] = useState(false);
    const [accepting, setAccepting] = useState(false);

    useEffect(() => {
        if (isAuthenticated) {
            checkAcceptanceStatus();
        }
    }, [isAuthenticated]);

    const checkAcceptanceStatus = async () => {
        try {
            setLoading(true);
            const status = await services.legal.getAcceptanceStatus();
            setAcceptance(status);

            // If acceptance is required, fetch the terms content
            if (status.requires_acceptance) {
                const terms = await services.legal.getTermsOfService();
                setTermsContent(terms.content);
            }
        } catch (error) {
            console.error('Failed to check acceptance status:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleAccept = async () => {
        if (!acceptance || !hasAgreed) return;

        try {
            setAccepting(true);
            await services.legal.acceptTerms(acceptance.latest_version);
            // Refresh acceptance status
            await checkAcceptanceStatus();
        } catch (error) {
            console.error('Failed to accept terms:', error);
        } finally {
            setAccepting(false);
        }
    };

    // Don't show if not signed in, loading, or acceptance not required
    if (!isAuthenticated || loading || !acceptance?.requires_acceptance) {
        return null;
    }

    return (
        <Dialog open={true} onOpenChange={() => { }}>
            <DialogContent className="max-w-3xl max-h-[90vh]" onInteractOutside={(e) => e.preventDefault()}>
                <DialogHeader>
                    <DialogTitle>Updated Terms of Service</DialogTitle>
                    <DialogDescription>
                        We've updated our Terms of Service. Please review and accept the new terms to continue using MueJam Library.
                    </DialogDescription>
                </DialogHeader>

                <ScrollArea className="h-[400px] w-full rounded-md border p-4">
                    <div className="prose prose-sm dark:prose-invert max-w-none">
                        <ReactMarkdown>{termsContent}</ReactMarkdown>
                    </div>
                </ScrollArea>

                <div className="flex items-start space-x-2 py-4">
                    <Checkbox
                        id="terms-agreement"
                        checked={hasAgreed}
                        onCheckedChange={(checked) => setHasAgreed(checked === true)}
                    />
                    <label
                        htmlFor="terms-agreement"
                        className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                    >
                        I have read and agree to the updated Terms of Service (Version {acceptance.latest_version})
                    </label>
                </div>

                <DialogFooter>
                    <Button
                        onClick={handleAccept}
                        disabled={!hasAgreed || accepting}
                        className="w-full sm:w-auto"
                    >
                        {accepting ? 'Accepting...' : 'Accept and Continue'}
                    </Button>
                </DialogFooter>

                <p className="text-xs text-muted-foreground text-center">
                    You must accept the updated terms to continue using the platform.
                </p>
            </DialogContent>
        </Dialog>
    );
}
