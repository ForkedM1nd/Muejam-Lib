import { createContext, useContext, ReactNode, useState, useEffect } from "react";
import { config, fetchDynamicConfig } from "@/lib/config";

/**
 * Feature flag context value
 */
interface FeatureFlagContextValue {
    /** Check if a feature is enabled */
    isFeatureEnabled: (feature: keyof typeof config.features) => boolean;
    /** Check if an experiment is enabled */
    isExperimentEnabled: (experiment: string) => boolean;
    /** Get all enabled features */
    getEnabledFeatures: () => string[];
    /** Get all enabled experiments */
    getEnabledExperiments: () => string[];
    /** Refresh feature flags from backend */
    refreshFlags: () => Promise<void>;
    /** Loading state */
    isLoading: boolean;
}

const FeatureFlagContext = createContext<FeatureFlagContextValue | undefined>(undefined);

/**
 * Feature Flag Provider Props
 */
interface FeatureFlagProviderProps {
    children: ReactNode;
    /** Whether to fetch dynamic flags from backend on mount */
    fetchDynamic?: boolean;
}

/**
 * Feature Flag Provider
 * 
 * Provides feature flag context to the application.
 * Can optionally fetch dynamic flags from the backend.
 * 
 * @example
 * <FeatureFlagProvider fetchDynamic>
 *   <App />
 * </FeatureFlagProvider>
 */
export function FeatureFlagProvider({ children, fetchDynamic = false }: FeatureFlagProviderProps) {
    const [dynamicFlags, setDynamicFlags] = useState<Record<string, any>>({});
    const [isLoading, setIsLoading] = useState(fetchDynamic);

    const refreshFlags = async () => {
        if (!fetchDynamic) return;

        try {
            setIsLoading(true);
            const flags = await fetchDynamicConfig("/config/features/", 5 * 60 * 1000);
            setDynamicFlags(flags);
        } catch (error) {
            console.error("[FeatureFlags] Failed to fetch dynamic flags:", error);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        if (fetchDynamic) {
            refreshFlags();
        }
    }, [fetchDynamic]);

    const isFeatureEnabled = (feature: keyof typeof config.features): boolean => {
        // Check dynamic flags first, then fall back to static config
        if (dynamicFlags.features && feature in dynamicFlags.features) {
            return dynamicFlags.features[feature];
        }
        return config.features[feature];
    };

    const isExperimentEnabled = (experiment: string): boolean => {
        // Check dynamic flags first, then fall back to static config
        if (dynamicFlags.experiments && experiment in dynamicFlags.experiments) {
            return dynamicFlags.experiments[experiment];
        }
        return config.experiments[experiment] === true;
    };

    const getEnabledFeatures = (): string[] => {
        const staticFeatures = Object.entries(config.features)
            .filter(([, enabled]) => enabled)
            .map(([feature]) => feature);

        const dynamicFeatures = dynamicFlags.features
            ? Object.entries(dynamicFlags.features)
                .filter(([, enabled]) => enabled)
                .map(([feature]) => feature)
            : [];

        return Array.from(new Set([...staticFeatures, ...dynamicFeatures]));
    };

    const getEnabledExperiments = (): string[] => {
        const staticExperiments = Object.entries(config.experiments)
            .filter(([, enabled]) => enabled)
            .map(([experiment]) => experiment);

        const dynamicExperiments = dynamicFlags.experiments
            ? Object.entries(dynamicFlags.experiments)
                .filter(([, enabled]) => enabled)
                .map(([experiment]) => experiment)
            : [];

        return Array.from(new Set([...staticExperiments, ...dynamicExperiments]));
    };

    const value: FeatureFlagContextValue = {
        isFeatureEnabled,
        isExperimentEnabled,
        getEnabledFeatures,
        getEnabledExperiments,
        refreshFlags,
        isLoading,
    };

    return <FeatureFlagContext.Provider value={value}>{children}</FeatureFlagContext.Provider>;
}

/**
 * Hook to use feature flag context
 * 
 * @example
 * const { isFeatureEnabled, isExperimentEnabled } = useFeatureFlags();
 * 
 * if (isFeatureEnabled("enablePushNotifications")) {
 *   // Show push notification settings
 * }
 */
export function useFeatureFlags(): FeatureFlagContextValue {
    const context = useContext(FeatureFlagContext);
    if (!context) {
        throw new Error("useFeatureFlags must be used within a FeatureFlagProvider");
    }
    return context;
}
