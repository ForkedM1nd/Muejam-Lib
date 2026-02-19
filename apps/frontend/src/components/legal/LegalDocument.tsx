import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Download, Calendar } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import type { LegalDocument as LegalDocumentType } from '@/types';
import { services } from '@/lib/api';

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
            const a = window.document.createElement('a');
            a.href = url;
            a.download = `${documentType}-${document.version}.pdf`;
            window.document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            window.document.body.removeChild(a);
        } catch (error) {
            console.error('Failed to download PDF:', error);
        } finally {
            setDownloading(false);
        }
    };

    if (loading) {
        return (
            <div className="container mx-auto px-4 py-8">
                <div className="text-center">Loading...</div>
            </div>
        );
    }

    if (!document) {
        return (
            <div className="container mx-auto px-4 py-8">
                <Card>
                    <CardContent className="p-8 text-center">
                        <h2 className="text-2xl font-semibold mb-4">Document Not Found</h2>
                        <p className="text-muted-foreground mb-6">
                            The legal document you're looking for doesn't exist.
                        </p>
                        <Link to="/">
                            <Button>Back to Home</Button>
                        </Link>
                    </CardContent>
                </Card>
            </div>
        );
    }

    return (
        <div className="container mx-auto px-4 py-8 max-w-4xl">
            {/* Back button */}
            <Link to="/" className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground mb-6">
                <ArrowLeft className="h-4 w-4" />
                Back to Home
            </Link>

            {/* Document */}
            <Card>
                <CardHeader>
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                            <Calendar className="h-4 w-4" />
                            Last updated: {new Date(document.last_updated).toLocaleDateString()}
                        </div>
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={handleDownloadPDF}
                            disabled={downloading}
                            className="flex items-center gap-2"
                        >
                            <Download className="h-4 w-4" />
                            {downloading ? 'Downloading...' : 'Download PDF'}
                        </Button>
                    </div>
                    <CardTitle className="text-3xl">{title}</CardTitle>
                    <p className="text-sm text-muted-foreground mt-2">
                        Version {document.version} • Effective {new Date(document.effective_date).toLocaleDateString()}
                    </p>
                </CardHeader>
                <CardContent className="prose prose-slate max-w-none dark:prose-invert">
                    <ReactMarkdown>{document.content}</ReactMarkdown>
                </CardContent>
            </Card>
        </div>
    );
}
