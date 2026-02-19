import { cn } from '@/lib/utils';

interface VisuallyHiddenProps {
    children: React.ReactNode;
    className?: string;
    as?: keyof JSX.IntrinsicElements;
}

/**
 * Component to hide content visually but keep it accessible to screen readers
 */
export function VisuallyHidden({
    children,
    className,
    as: Component = 'span'
}: VisuallyHiddenProps) {
    return (
        <Component className={cn('sr-only', className)}>
            {children}
        </Component>
    );
}
