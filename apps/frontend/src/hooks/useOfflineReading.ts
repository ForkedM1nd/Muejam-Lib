import { useState, useEffect, useCallback } from 'react';
import type { Story, Chapter } from '@/types';

const OFFLINE_STORIES_KEY = 'muejam_offline_stories';
const OFFLINE_CHAPTERS_KEY = 'muejam_offline_chapters';
const READING_PROGRESS_KEY = 'muejam_reading_progress';

interface ReadingProgress {
    chapterId: string;
    storyId: string;
    position: number;
    timestamp: number;
    synced: boolean;
}

/**
 * Hook for managing offline reading functionality
 */
export function useOfflineReading() {
    const [cachedStories, setCachedStories] = useState<Story[]>([]);
    const [cachedChapters, setCachedChapters] = useState<Map<string, Chapter>>(new Map());

    // Load cached content on mount
    useEffect(() => {
        loadCachedContent();
    }, []);

    /**
     * Load cached stories and chapters from localStorage
     */
    const loadCachedContent = useCallback(() => {
        try {
            // Load stories
            const storiesData = localStorage.getItem(OFFLINE_STORIES_KEY);
            if (storiesData) {
                const stories = JSON.parse(storiesData) as Story[];
                setCachedStories(stories);
            }

            // Load chapters
            const chaptersData = localStorage.getItem(OFFLINE_CHAPTERS_KEY);
            if (chaptersData) {
                const chapters = JSON.parse(chaptersData) as Chapter[];
                const chaptersMap = new Map(chapters.map(ch => [ch.id, ch]));
                setCachedChapters(chaptersMap);
            }
        } catch (error) {
            console.error('Failed to load cached content:', error);
        }
    }, []);

    /**
     * Cache a story for offline reading
     */
    const cacheStory = useCallback(async (story: Story, chapters: Chapter[]) => {
        try {
            // Add story to cached stories
            const updatedStories = [...cachedStories.filter(s => s.id !== story.id), story];
            localStorage.setItem(OFFLINE_STORIES_KEY, JSON.stringify(updatedStories));
            setCachedStories(updatedStories);

            // Add chapters to cached chapters
            const updatedChapters = new Map(cachedChapters);
            chapters.forEach(chapter => {
                updatedChapters.set(chapter.id, chapter);
            });
            localStorage.setItem(
                OFFLINE_CHAPTERS_KEY,
                JSON.stringify(Array.from(updatedChapters.values()))
            );
            setCachedChapters(updatedChapters);

            console.log(`Cached story ${story.id} with ${chapters.length} chapters`);
            return true;
        } catch (error) {
            console.error('Failed to cache story:', error);
            return false;
        }
    }, [cachedStories, cachedChapters]);

    /**
     * Remove a story from offline cache
     */
    const removeCachedStory = useCallback((storyId: string) => {
        try {
            // Remove story
            const updatedStories = cachedStories.filter(s => s.id !== storyId);
            localStorage.setItem(OFFLINE_STORIES_KEY, JSON.stringify(updatedStories));
            setCachedStories(updatedStories);

            // Remove associated chapters
            const updatedChapters = new Map(cachedChapters);
            Array.from(updatedChapters.values())
                .filter(ch => ch.story_id === storyId)
                .forEach(ch => updatedChapters.delete(ch.id));
            localStorage.setItem(
                OFFLINE_CHAPTERS_KEY,
                JSON.stringify(Array.from(updatedChapters.values()))
            );
            setCachedChapters(updatedChapters);

            console.log(`Removed cached story ${storyId}`);
            return true;
        } catch (error) {
            console.error('Failed to remove cached story:', error);
            return false;
        }
    }, [cachedStories, cachedChapters]);

    /**
     * Check if a story is cached
     */
    const isStoryCached = useCallback((storyId: string): boolean => {
        return cachedStories.some(s => s.id === storyId);
    }, [cachedStories]);

    /**
     * Check if a chapter is cached
     */
    const isChapterCached = useCallback((chapterId: string): boolean => {
        return cachedChapters.has(chapterId);
    }, [cachedChapters]);

    /**
     * Get a cached chapter
     */
    const getCachedChapter = useCallback((chapterId: string): Chapter | undefined => {
        return cachedChapters.get(chapterId);
    }, [cachedChapters]);

    /**
     * Save reading progress
     */
    const saveReadingProgress = useCallback((progress: Omit<ReadingProgress, 'timestamp' | 'synced'>) => {
        try {
            const progressData = localStorage.getItem(READING_PROGRESS_KEY);
            const allProgress: ReadingProgress[] = progressData ? JSON.parse(progressData) : [];

            // Update or add progress
            const existingIndex = allProgress.findIndex(p => p.chapterId === progress.chapterId);
            const newProgress: ReadingProgress = {
                ...progress,
                timestamp: Date.now(),
                synced: false,
            };

            if (existingIndex >= 0) {
                allProgress[existingIndex] = newProgress;
            } else {
                allProgress.push(newProgress);
            }

            localStorage.setItem(READING_PROGRESS_KEY, JSON.stringify(allProgress));
            console.log(`Saved reading progress for chapter ${progress.chapterId}`);
        } catch (error) {
            console.error('Failed to save reading progress:', error);
        }
    }, []);

    /**
     * Get unsynced reading progress
     */
    const getUnsyncedProgress = useCallback((): ReadingProgress[] => {
        try {
            const progressData = localStorage.getItem(READING_PROGRESS_KEY);
            if (!progressData) return [];

            const allProgress: ReadingProgress[] = JSON.parse(progressData);
            return allProgress.filter(p => !p.synced);
        } catch (error) {
            console.error('Failed to get unsynced progress:', error);
            return [];
        }
    }, []);

    /**
     * Mark reading progress as synced
     */
    const markProgressSynced = useCallback((chapterId: string) => {
        try {
            const progressData = localStorage.getItem(READING_PROGRESS_KEY);
            if (!progressData) return;

            const allProgress: ReadingProgress[] = JSON.parse(progressData);
            const progress = allProgress.find(p => p.chapterId === chapterId);

            if (progress) {
                progress.synced = true;
                localStorage.setItem(READING_PROGRESS_KEY, JSON.stringify(allProgress));
                console.log(`Marked progress synced for chapter ${chapterId}`);
            }
        } catch (error) {
            console.error('Failed to mark progress synced:', error);
        }
    }, []);

    /**
     * Clear all cached content
     */
    const clearAllCache = useCallback(() => {
        try {
            localStorage.removeItem(OFFLINE_STORIES_KEY);
            localStorage.removeItem(OFFLINE_CHAPTERS_KEY);
            setCachedStories([]);
            setCachedChapters(new Map());
            console.log('Cleared all cached content');
        } catch (error) {
            console.error('Failed to clear cache:', error);
        }
    }, []);

    return {
        cachedStories,
        cachedChapters: Array.from(cachedChapters.values()),
        cacheStory,
        removeCachedStory,
        isStoryCached,
        isChapterCached,
        getCachedChapter,
        saveReadingProgress,
        getUnsyncedProgress,
        markProgressSynced,
        clearAllCache,
    };
}
