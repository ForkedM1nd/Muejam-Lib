import { useEffect, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import {
    getSavedSearches,
    updateNewMatchesCount,
} from "@/lib/savedSearches";

/**
 * Hook to check for new matches in saved searches and update notification counts
 * 
 * This hook periodically checks saved searches for new matches and updates
 * the notification count for each search.
 * 
 * Note: This is a simplified implementation that checks if there are any results.
 * A production implementation would need backend support to track result counts
 * and timestamps to accurately detect new matches.
 */
export function useSavedSearchNotifications() {
    const previousResultsRef = useRef<Map<string, number>>(new Map());

    // Get all saved searches
    const savedSearches = getSavedSearches();

    // Check each saved search for new matches
    const { data: searchResults } = useQuery({
        queryKey: ["saved-search-notifications", savedSearches.map((s) => s.id)],
        queryFn: async () => {
            const results = await Promise.all(
                savedSearches.map(async (search) => {
                    try {
                        // Build search params
                        const params: any = {
                            q: search.query,
                            page_size: 10, // Get a small number of results to check
                        };

                        if (search.filters.type) {
                            params.type = search.filters.type;
                        }

                        if (search.filters.genres && search.filters.genres.length > 0) {
                            params.genre = search.filters.genres.join(",");
                        }

                        if (search.filters.status && search.filters.status.length > 0) {
                            params.status = search.filters.status.join(",");
                        }

                        if (search.filters.minWordCount !== undefined) {
                            params.min_word_count = search.filters.minWordCount;
                        }

                        if (search.filters.maxWordCount !== undefined) {
                            params.max_word_count = search.filters.maxWordCount;
                        }

                        if (search.filters.sort) {
                            params.sort = search.filters.sort;
                        }

                        const result = await api.search(params);

                        return {
                            searchId: search.id,
                            resultCount: result.results.length,
                            lastChecked: search.lastChecked || search.createdAt,
                        };
                    } catch (error) {
                        console.error(`Failed to check saved search ${search.id}:`, error);
                        return {
                            searchId: search.id,
                            resultCount: 0,
                            lastChecked: search.lastChecked || search.createdAt,
                        };
                    }
                })
            );

            return results;
        },
        enabled: savedSearches.length > 0,
        refetchInterval: 5 * 60 * 1000, // Check every 5 minutes
        staleTime: 4 * 60 * 1000, // Consider stale after 4 minutes
    });

    // Update notification counts when results change
    useEffect(() => {
        if (!searchResults) return;

        searchResults.forEach((result) => {
            const previousCount = previousResultsRef.current.get(result.searchId);

            if (previousCount !== undefined && result.resultCount > previousCount) {
                // New matches found (simplified - just shows there are new results)
                const newMatchesCount = result.resultCount - previousCount;
                updateNewMatchesCount(result.searchId, newMatchesCount);
            }

            // Update the reference
            previousResultsRef.current.set(result.searchId, result.resultCount);
        });
    }, [searchResults]);

    return {
        isChecking: savedSearches.length > 0 && !searchResults,
        lastChecked: searchResults?.[0]?.lastChecked,
    };
}
