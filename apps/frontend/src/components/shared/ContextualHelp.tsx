import { useState } from 'react';
import { HelpCircle, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from '@/components/ui/popover';
import ReactMarkdown from 'react-markdown';

interface ContextualHelpProps {
    title: string;
    content: string;
    articleSlug?: string;
}

/**
 * Contextual help component that displays help content in a popover
 * Can be embedded anywhere in the UI to provide context-sensitive help
 */
export function ContextualHelp({ title, content, articleSlug }: ContextualHelpProps) {
    const [open, setOpen] = useState(false);

    return (
        <Popover open={open} onOpenChange={setOpen}>
            <PopoverTrigger asChild>
                <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6 rounded-full"
                    aria-label="Help"
                >
                    <HelpCircle className="h-4 w-4 text-muted-foreground" />
                </Button>
            </PopoverTrigger>
            <PopoverContent className="w-80" align="start">
                <div className="space-y-3">
                    <div className="flex items-start justify-between">
                        <h4 className="font-semibold text-sm">{title}</h4>
                        <Button
                            variant="ghost"
                            size="icon"
                            className="h-6 w-6"
                            onClick={() => setOpen(false)}
                        >
                            <X className="h-4 w-4" />
                        </Button>
                    </div>
                    <div className="text-sm text-muted-foreground prose prose-sm max-w-none">
                        <ReactMarkdown>{content}</ReactMarkdown>
                    </div>
                    {articleSlug && (
                        <div className="pt-2 border-t">
                            <a
                                href={`/help/articles/${articleSlug}`}
                                className="text-sm text-primary hover:underline"
                                target="_blank"
                                rel="noopener noreferrer"
                            >
                                Learn more →
                            </a>
                        </div>
                    )}
                </div>
            </PopoverContent>
        </Popover>
    );
}
