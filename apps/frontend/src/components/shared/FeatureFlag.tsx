import { ReactNode } from "react";
import { isFeatureEnabled, isExperimentEnabled, config } from "@/lib/config";

/**
 * Props for FeatureFlag component
 */
interface FeatureFlagProps {
    /** The feature flag to check */
    feature?: keyof typeof config.features;
    /** The experiment to check */
    experiment?: string;
    /** Content to render when feature/experiment is enabled */
    children: ReactNode;
    /** Optional fallback content when feature/experiment is disabled */
    fallback?: ReactNode;
}

/**
 * FeatureFlag Component
 * 
 * Conditionally renders children based on feature flags or experiments.
 * 
 * @example
 * // Check a feature flag
 * <FeatureFlag feature="enablePushNotifications">
 *   <PushNotificationSettings />
 * </FeatureFlag>
 * 
 * @example
 * // Check an experiment
 * <FeatureFlag experiment="newDesign">
 *   <NewDesignComponent />
 * </FeatureFlag>
 * 
 * @example
 * // With fallback
 * <FeatureFlag feature="enableAnalytics" fallback={<div>Analytics disabled</div>}>
 *   <AnalyticsDashboard />
 * </FeatureFlag>
 */
export function FeatureFlag({ feature, experiment, children, fallback = null }: FeatureFlagProps) {
    let isEnabled = false;

    if (feature) {
        isEnabled = isFeatureEnabled(feature);
    } else if (experiment) {
        isEnabled = isExperimentEnabled(experiment);
    }

    return isEnabled ? <>{children}</> : <>{fallback}</>;
}

/**
 * Hook to check if a feature is enabled
 * 
 * @example
 * const isPushEnabled = useFeatureFlag("enablePushNotifications");
 */
export function useFeatureFlag(feature: keyof typeof config.features): boolean {
    return isFeatureEnabled(feature);
}

/**
 * Hook to check if an experiment is enabled
 * 
 * @example
 * const isNewDesign = useExperiment("newDesign");
 */
export function useExperiment(experiment: string): boolean {
    return isExperimentEnabled(experiment);
}
