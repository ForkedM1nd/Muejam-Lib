import { useState, useEffect } from "react";

const RATE_LIMIT_KEY = "report_submissions";
const MAX_REPORTS_PER_HOUR = 5;
const MAX_REPORTS_PER_DAY = 20;
const HOUR_IN_MS = 60 * 60 * 1000;
const DAY_IN_MS = 24 * HOUR_IN_MS;

interface ReportSubmission {
    timestamp: number;
    contentId: string;
}

export function useReportRateLimit() {
    const [submissions, setSubmissions] = useState<ReportSubmission[]>([]);
    const [isRateLimited, setIsRateLimited] = useState(false);
    const [rateLimitMessage, setRateLimitMessage] = useState<string | null>(null);

    // Load submissions from localStorage on mount
    useEffect(() => {
        const stored = localStorage.getItem(RATE_LIMIT_KEY);
        if (stored) {
            try {
                const parsed = JSON.parse(stored) as ReportSubmission[];
                // Filter out old submissions (older than 24 hours)
                const now = Date.now();
                const recent = parsed.filter((s) => now - s.timestamp < DAY_IN_MS);
                setSubmissions(recent);
                localStorage.setItem(RATE_LIMIT_KEY, JSON.stringify(recent));
            } catch {
                localStorage.removeItem(RATE_LIMIT_KEY);
            }
        }
    }, []);

    // Check rate limits whenever submissions change
    useEffect(() => {
        const now = Date.now();
        const recentHour = submissions.filter((s) => now - s.timestamp < HOUR_IN_MS);
        const recentDay = submissions.filter((s) => now - s.timestamp < DAY_IN_MS);

        if (recentHour.length >= MAX_REPORTS_PER_HOUR) {
            setIsRateLimited(true);
            const oldestInHour = Math.min(...recentHour.map((s) => s.timestamp));
            const minutesUntilReset = Math.ceil((HOUR_IN_MS - (now - oldestInHour)) / 60000);
            setRateLimitMessage(
                `You've reached the hourly report limit (${MAX_REPORTS_PER_HOUR} reports per hour). Please try again in ${minutesUntilReset} minute${minutesUntilReset !== 1 ? "s" : ""}.`
            );
        } else if (recentDay.length >= MAX_REPORTS_PER_DAY) {
            setIsRateLimited(true);
            const oldestInDay = Math.min(...recentDay.map((s) => s.timestamp));
            const hoursUntilReset = Math.ceil((DAY_IN_MS - (now - oldestInDay)) / 3600000);
            setRateLimitMessage(
                `You've reached the daily report limit (${MAX_REPORTS_PER_DAY} reports per day). Please try again in ${hoursUntilReset} hour${hoursUntilReset !== 1 ? "s" : ""}.`
            );
        } else {
            setIsRateLimited(false);
            setRateLimitMessage(null);
        }
    }, [submissions]);

    // Record a new submission
    const recordSubmission = (contentId: string) => {
        const newSubmission: ReportSubmission = {
            timestamp: Date.now(),
            contentId,
        };
        const updated = [...submissions, newSubmission];
        setSubmissions(updated);
        localStorage.setItem(RATE_LIMIT_KEY, JSON.stringify(updated));
    };

    // Check if a specific content has been reported recently (within last hour)
    const hasReportedRecently = (contentId: string): boolean => {
        const now = Date.now();
        return submissions.some(
            (s) => s.contentId === contentId && now - s.timestamp < HOUR_IN_MS
        );
    };

    // Get remaining reports for the current hour
    const getRemainingReportsThisHour = (): number => {
        const now = Date.now();
        const recentHour = submissions.filter((s) => now - s.timestamp < HOUR_IN_MS);
        return Math.max(0, MAX_REPORTS_PER_HOUR - recentHour.length);
    };

    // Get remaining reports for the current day
    const getRemainingReportsToday = (): number => {
        const now = Date.now();
        const recentDay = submissions.filter((s) => now - s.timestamp < DAY_IN_MS);
        return Math.max(0, MAX_REPORTS_PER_DAY - recentDay.length);
    };

    return {
        isRateLimited,
        rateLimitMessage,
        recordSubmission,
        hasReportedRecently,
        getRemainingReportsThisHour,
        getRemainingReportsToday,
    };
}
