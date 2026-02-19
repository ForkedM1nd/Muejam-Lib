import { useQuery } from "@tanstack/react-query";
import { fetchDynamicConfig } from "@/lib/config";

/**
 * Hook to fetch and use dynamic configuration from the backend
 * 
 * @param endpoint - The configuration endpoint to fetch from (default: /config/mobile/)
 * @param ttl - Time to live for the cached configuration in milliseconds (default: 5 minutes)
 * @param enabled - Whether to enable the query (default: true)
 * 
 * @example
 * const { data: mobileConfig, isLoading } = useDynamicConfig("/config/mobile/");
 * 
 * @example
 * // Fetch with custom TTL
 * const { data: config } = useDynamicConfig("/config/mobile/", 10 * 60 * 1000); // 10 minutes
 */
export function useDynamicConfig<T = any>(
    endpoint: string = "/config/mobile/",
    ttl: number = 5 * 60 * 1000,
    enabled: boolean = true
) {
    return useQuery<T>({
        queryKey: ["dynamic-config", endpoint],
        queryFn: () => fetchDynamicConfig(endpoint, ttl),
        staleTime: ttl,
        gcTime: ttl * 2, // Keep in cache for twice the TTL
        enabled,
        retry: 2,
        retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    });
}

/**
 * Hook to fetch mobile-specific configuration
 */
export function useMobileConfig() {
    return useDynamicConfig("/config/mobile/");
}
