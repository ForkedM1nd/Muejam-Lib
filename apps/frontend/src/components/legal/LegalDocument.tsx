import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Download, Calendar } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import type { LegalDocument as LegalDocumentType } from '@/types';
import { services } from '@/lib/api';
import PageHeader from '@/components/shared/PageHeader';
import SurfacePanel from '@/components/shared/SurfacePanel';

interface LegalDocumentProps {
    documentType: 'terms' | 'privacy' | 'cookies' | 'guidelines' | 'copyright';
    title: string;
}

export function LegalDocument({ documentType, title }: LegalDocumentProps) {
    const [document, setDocument] = useState<LegalDocumentType | null>(null);
    const [loading, setLoading] = useState(true);
    const [downloading, setDownloading] = useState(false);

    useEffect(() => {
        fetchDocument();
    }, [documentType]);

    const fetchDocument = async () => {
        try {
            setLoading(true);
            const data = await services.legal.getDocument(documentType);
            setDocument(data);
        } catch (error) {
            console.error('Failed to fetch legal document:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleDownloadPDF = async () => {
        if (!document) return;

        try {
            setDownloading(true);
            const blob = await services.legal.downloadPDF(documentType);
            const url = window.URL.createObjectURL(blob);
            const anchor = window.document.createElement('a');
            anchor.href = url;
            anchor.download = `${documentType}-${document.version}.pdf`;
            window.document.body.appendChild(anchor);
            anchor.click();
            window.URL.revokeObjectURL(url);
            window.document.body.removeChild(anchor);
        } catch (error) {
            console.error('Failed to download PDF:', error);
        } finally {
            setDownloading(false);
        }
    };

    if (loading) {
        return (
            <div className="mx-auto max-w-4xl">
                <SurfacePanel className="p-8 text-center">Loading legal document...</SurfacePanel>
            </div>
        );
    }

    if (!document) {
        return (
            <div className="mx-auto max-w-4xl">
                <SurfacePanel className="p-8 text-center">
                    <h2 className="text-2xl font-semibold">Document Not Found</h2>
                    <p className="mt-2 text-muted-foreground">
                        The legal document you're looking for doesn't exist.
                    </p>
                    <div className="mt-5">
                        <Link to="/">
                            <Button>Back to Home</Button>
                        </Link>
                    </div>
                </SurfacePanel>
            </div>
        );
    }

    return (
        <div className="mx-auto max-w-4xl space-y-5">
            <Link to="/" className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
                <ArrowLeft className="h-4 w-4" />
                Back to Home
            </Link>

            <PageHeader
                title={title}
                eyebrow="Legal"
                description={`Version ${document.version} • Effective ${new Date(document.effective_date).toLocaleDateString()}`}
            />

            <SurfacePanel className="p-4 sm:p-5">
                <div className="flex flex-wrap items-center justify-between gap-3">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Calendar className="h-4 w-4" />
                        Last updated: {new Date(document.last_updated).toLocaleDateString()}
                    </div>
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={handleDownloadPDF}
                        disabled={downloading}
                    >
                        <Download className="mr-2 h-4 w-4" />
                        {downloading ? 'Downloading...' : 'Download PDF'}
                    </Button>
                </div>
            </SurfacePanel>

            <SurfacePanel className="p-5 sm:p-6">
                <div className="prose prose-slate max-w-none dark:prose-invert">
                    <ReactMarkdown>{document.content}</ReactMarkdown>
                </div>
            </SurfacePanel>
        </div>
    );
}
