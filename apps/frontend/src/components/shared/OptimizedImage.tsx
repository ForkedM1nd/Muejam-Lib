import { useState, useEffect } from 'react';

interface OptimizedImageProps extends React.ImgHTMLAttributes<HTMLImageElement> {
    src: string;
    alt: string;
    fallback?: string;
    loading?: 'lazy' | 'eager';
}

/**
 * Optimized image component with lazy loading and alt text
 * Ensures all images have proper alt text for SEO and accessibility
 */
export function OptimizedImage({
    src,
    alt,
    fallback = '/placeholder-image.png',
    loading = 'lazy',
    className,
    ...props
}: OptimizedImageProps) {
    const [imgSrc, setImgSrc] = useState(src);
    const [isLoading, setIsLoading] = useState(true);
    const [hasError, setHasError] = useState(false);

    useEffect(() => {
        setImgSrc(src);
        setIsLoading(true);
        setHasError(false);
    }, [src]);

    const handleLoad = () => {
        setIsLoading(false);
    };

    const handleError = () => {
        setIsLoading(false);
        setHasError(true);
        setImgSrc(fallback);
    };

    return (
        <img
            src={imgSrc}
            alt={alt}
            loading={loading}
            onLoad={handleLoad}
            onError={handleError}
            className={className}
            {...props}
        />
    );
}
