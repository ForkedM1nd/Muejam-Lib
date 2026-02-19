import { useState, useEffect } from 'react';

interface HelpSuggestion {
    title: string;
    content: string;
    articleSlug?: string;
}

interface ContextMap {
    [key: string]: HelpSuggestion;
}

/**
 * Contextual help suggestions based on current page/context
 */
const CONTEXTUAL_HELP: ContextMap = {
    '/write': {
        title: 'Creating Your Story',
        content: 'Start by giving your story a compelling title and description. You can add chapters later and publish when ready.',
        articleSlug: 'creating-your-first-story',
    },
    '/write/chapter': {
        title: 'Writing Chapters',
        content: 'Write your chapter content using our rich text editor. You can format text, add images, and save drafts.',
        articleSlug: 'writing-chapters',
    },
    '/library': {
        title: 'Your Library',
        content: 'Organize your reading list with shelves. Add stories to different shelves to keep track of what you want to read.',
        articleSlug: 'managing-your-library',
    },
    '/settings/privacy': {
        title: 'Privacy Settings',
        content: 'Control who can see your profile, stories, and activity. You can also manage your data and account deletion here.',
        articleSlug: 'privacy-settings-guide',
    },
    '/settings/security': {
        title: 'Security Settings',
        content: 'Enable two-factor authentication for extra security. You can also manage trusted devices and view login history.',
        articleSlug: 'account-security',
    },
    '/analytics': {
        title: 'Analytics Dashboard',
        content: 'Track your story performance with detailed metrics including views, reads, engagement, and demographics.',
        articleSlug: 'understanding-analytics',
    },
    '/moderation': {
        title: 'Moderation Queue',
        content: 'Review flagged content and take appropriate actions. You can approve, reject, or escalate reports.',
        articleSlug: 'moderation-guide',
    },
};

/**
 * Hook to get contextual help suggestions based on current route
 */
export function useContextualHelp(path: string): HelpSuggestion | null {
    const [suggestion, setSuggestion] = useState<HelpSuggestion | null>(null);

    useEffect(() => {
        // Find exact match first
        if (CONTEXTUAL_HELP[path]) {
            setSuggestion(CONTEXTUAL_HELP[path]);
            return;
        }

        // Find partial match
        const matchingKey = Object.keys(CONTEXTUAL_HELP).find(key =>
            path.startsWith(key)
        );

        if (matchingKey) {
            setSuggestion(CONTEXTUAL_HELP[matchingKey]);
        } else {
            setSuggestion(null);
        }
    }, [path]);

    return suggestion;
}

/**
 * Hook to get help suggestions based on context keywords
 */
export function useHelpSuggestions(context: string): HelpSuggestion[] {
    const [suggestions, setSuggestions] = useState<HelpSuggestion[]>([]);

    useEffect(() => {
        const contextLower = context.toLowerCase();
        const matches: HelpSuggestion[] = [];

        // Search through all help content for relevant suggestions
        Object.entries(CONTEXTUAL_HELP).forEach(([_, help]) => {
            if (
                help.title.toLowerCase().includes(contextLower) ||
                help.content.toLowerCase().includes(contextLower)
            ) {
                matches.push(help);
            }
        });

        setSuggestions(matches.slice(0, 3)); // Limit to 3 suggestions
    }, [context]);

    return suggestions;
}
