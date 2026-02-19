import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { StoryAnalytics } from "./StoryAnalytics";
import type { StoryAnalytics as StoryAnalyticsType } from "@/types";

const mockStoryAnalytics: StoryAnalyticsType = {
    story_id: "story-1",
    views: 1500,
    unique_readers: 850,
    completion_rate: 0.72,
    average_read_time: 25.5,
    engagement_score: 0.85,
    demographics: {
        age_groups: {
            "18-24": 120,
            "25-34": 280,
            "35-44": 200,
            "45-54": 150,
            "55+": 100,
        },
        locations: {
            "United States": 400,
            "United Kingdom": 180,
            "Canada": 120,
            "Australia": 80,
            "Germany": 70,
        },
    },
    traffic_sources: [
        { source: "Direct", visits: 600, percentage: 40 },
        { source: "Social Media", visits: 450, percentage: 30 },
        { source: "Search", visits: 300, percentage: 20 },
        { source: "Referral", visits: 150, percentage: 10 },
    ],
    chapter_performance: [
        { chapter_id: "ch-1", chapter_title: "Chapter 1", views: 1500, completion_rate: 95 },
        { chapter_id: "ch-2", chapter_title: "Chapter 2", views: 1200, completion_rate: 85 },
        { chapter_id: "ch-3", chapter_title: "Chapter 3", views: 900, completion_rate: 72 },
    ],
    time_series: [
        { date: "2024-01-01", value: 100 },
        { date: "2024-01-02", value: 150 },
        { date: "2024-01-03", value: 200 },
        { date: "2024-01-04", value: 180 },
        { date: "2024-01-05", value: 220 },
    ],
};

describe("StoryAnalytics", () => {
    it("renders loading state", () => {
        render(<StoryAnalytics data={mockStoryAnalytics} isLoading={true} />);

        // Should show skeleton loaders
        const skeletons = screen.getAllByRole("generic").filter((el) =>
            el.className.includes("animate-pulse")
        );
        expect(skeletons.length).toBeGreaterThan(0);
    });

    it("renders key metrics correctly", () => {
        render(<StoryAnalytics data={mockStoryAnalytics} />);

        // Check for key metrics
        expect(screen.getByText("1,500")).toBeInTheDocument(); // Total Views
        expect(screen.getByText("850")).toBeInTheDocument(); // Unique Readers
        expect(screen.getByText("72.0%")).toBeInTheDocument(); // Completion Rate
        expect(screen.getByText("26 min")).toBeInTheDocument(); // Avg Read Time (rounded)
    });

    it("renders engagement score", () => {
        render(<StoryAnalytics data={mockStoryAnalytics} />);

        expect(screen.getByText("Engagement Score")).toBeInTheDocument();
        expect(screen.getByText("85")).toBeInTheDocument(); // Engagement score as percentage
    });

    it("renders time series chart title", () => {
        render(<StoryAnalytics data={mockStoryAnalytics} />);

        expect(screen.getByText("Views Over Time")).toBeInTheDocument();
    });

    it("renders chapter performance chart title", () => {
        render(<StoryAnalytics data={mockStoryAnalytics} />);

        expect(screen.getByText("Chapter Performance")).toBeInTheDocument();
    });

    it("renders traffic sources", () => {
        render(<StoryAnalytics data={mockStoryAnalytics} />);

        expect(screen.getByText("Traffic Sources")).toBeInTheDocument();
        expect(screen.getByText("Direct")).toBeInTheDocument();
        expect(screen.getByText("Social Media")).toBeInTheDocument();
        expect(screen.getByText("Search")).toBeInTheDocument();
        expect(screen.getByText("Referral")).toBeInTheDocument();
    });

    it("renders demographics sections", () => {
        render(<StoryAnalytics data={mockStoryAnalytics} />);

        expect(screen.getByText("Reader Age Groups")).toBeInTheDocument();
        expect(screen.getByText("Top Locations")).toBeInTheDocument();
    });

    it("renders top locations correctly", () => {
        render(<StoryAnalytics data={mockStoryAnalytics} />);

        expect(screen.getByText("United States")).toBeInTheDocument();
        expect(screen.getByText("United Kingdom")).toBeInTheDocument();
        expect(screen.getByText("Canada")).toBeInTheDocument();
    });

    it("calls onExport when export button is clicked", () => {
        const onExport = vi.fn();
        render(<StoryAnalytics data={mockStoryAnalytics} onExport={onExport} />);

        const exportButton = screen.getByRole("button", { name: /export csv/i });
        exportButton.click();

        expect(onExport).toHaveBeenCalledTimes(1);
    });

    it("does not render export button when onExport is not provided", () => {
        render(<StoryAnalytics data={mockStoryAnalytics} />);

        const exportButton = screen.queryByRole("button", { name: /export csv/i });
        expect(exportButton).not.toBeInTheDocument();
    });

    it("formats large numbers with locale string", () => {
        const dataWithLargeNumbers: StoryAnalyticsType = {
            ...mockStoryAnalytics,
            views: 1234567,
            unique_readers: 987654,
        };

        render(<StoryAnalytics data={dataWithLargeNumbers} />);

        expect(screen.getByText("1,234,567")).toBeInTheDocument();
        expect(screen.getByText("987,654")).toBeInTheDocument();
    });

    it("displays completion rate as percentage with one decimal", () => {
        const dataWithDecimalRate: StoryAnalyticsType = {
            ...mockStoryAnalytics,
            completion_rate: 0.7234,
        };

        render(<StoryAnalytics data={dataWithDecimalRate} />);

        expect(screen.getByText("72.3%")).toBeInTheDocument();
    });

    it("rounds average read time to nearest minute", () => {
        const dataWithReadTime: StoryAnalyticsType = {
            ...mockStoryAnalytics,
            average_read_time: 42.7,
        };

        render(<StoryAnalytics data={dataWithReadTime} />);

        expect(screen.getByText("43 min")).toBeInTheDocument();
    });
});
