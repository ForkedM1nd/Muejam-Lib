import { createContext, useContext, ReactNode } from 'react';
import { useMobileConfig } from '@/hooks/useMobileConfig';
import { type MobileConfig, DEFAULT_MOBILE_CONFIG } from '@/lib/mobile';

interface MobileConfigContextValue {
    config: MobileConfig;
    isLoading: boolean;
    error: Error | null;
}

const MobileConfigContext = createContext<MobileConfigContextValue>({
    config: DEFAULT_MOBILE_CONFIG,
    isLoading: false,
    error: null,
});

export function MobileConfigProvider({ children }: { children: ReactNode }) {
    const { config, isLoading, error } = useMobileConfig();

    return (
        <MobileConfigContext.Provider value={{ config, isLoading, error }}>
            {children}
        </MobileConfigContext.Provider>
    );
}

export function useMobileConfigContext() {
    const context = useContext(MobileConfigContext);

    if (!context) {
        throw new Error('useMobileConfigContext must be used within MobileConfigProvider');
    }

    return context;
}
