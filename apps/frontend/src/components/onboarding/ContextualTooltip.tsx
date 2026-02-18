import { useState, useEffect } from 'react';
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from '@/components/ui/popover';
import { Button } from '@/components/ui/button';
import { X } from 'lucide-react';

interface ContextualTooltipProps {
    id: string;
    title: string;
    description: string;
    children: React.ReactNode;
    onDismiss?: () => void;
}

export function ContextualTooltip({
    id,
    title,
    description,
    children,
    onDismiss
}: ContextualTooltipProps) {
    const [isOpen, setIsOpen] = useState(false);
    const [hasBeenShown, setHasBeenShown] = useState(false);

    useEffect(() => {
        // Check if this tooltip has been shown before
        const shown = localStorage.getItem(`tooltip-${id}`);
        if (!shown) {
            setIsOpen(true);
            setHasBeenShown(false);
        } else {
            setHasBeenShown(true);
        }
    }, [id]);

    const handleDismiss = () => {
        setIsOpen(false);
        localStorage.setItem(`tooltip-${id}`, 'true');
        setHasBeenShown(true);
        onDismiss?.();
    };

    if (hasBeenShown) {
        return <>{children}</>;
    }

    return (
        <Popover open={isOpen} onOpenChange={setIsOpen}>
            <PopoverTrigger asChild>
                {children}
            </PopoverTrigger>
            <PopoverContent className="w-80">
                <div className="space-y-2">
                    <div className="flex items-start justify-between">
                        <h4 className="font-semibold">{title}</h4>
                        <Button
                            variant="ghost"
                            size="sm"
                            className="h-6 w-6 p-0"
                            onClick={handleDismiss}
                        >
                            <X className="h-4 w-4" />
                        </Button>
                    </div>
                    <p className="text-sm text-muted-foreground">{description}</p>
                    <Button size="sm" onClick={handleDismiss} className="w-full">
                        Got it!
                    </Button>
                </div>
            </PopoverContent>
        </Popover>
    );
}
