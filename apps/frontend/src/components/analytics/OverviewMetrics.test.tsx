import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { OverviewMetrics } from "./OverviewMetrics";
import type { AnalyticsDashboard } from "@/types";

describe("OverviewMetrics", () => {
    const mockData: AnalyticsDashboard = {
        total_views: 1500,
        total_reads: 800,
        total_followers: 250,
        engagement_rate: 0.45,
        top_stories: [],
        recent_activity: [],
    };

    it("renders loading state when isLoading is true", () => {
        render(<OverviewMetrics data={mockData} isLoading={true} />);
        const skeletons = document.querySelectorAll(".animate-pulse");
        expect(skeletons.length).toBeGreaterThan(0);
    });

    it("renders metrics correctly", () => {
        render(<OverviewMetrics data={mockData} isLoading={false} />);

        // Check if metrics are displayed
        expect(screen.getByText("1,500")).toBeInTheDocument();
        expect(screen.getByText("800")).toBeInTheDocument();
        expect(screen.getByText("250")).toBeInTheDocument();
        expect(screen.getByText("45.0%")).toBeInTheDocument();
    });

    it("displays metric titles", () => {
        render(<OverviewMetrics data={mockData} isLoading={false} />);

        expect(screen.getByText("Total Views")).toBeInTheDocument();
        expect(screen.getByText("Total Reads")).toBeInTheDocument();
        expect(screen.getByText("Followers")).toBeInTheDocument();
        expect(screen.getByText("Engagement Rate")).toBeInTheDocument();
    });

    it("displays metric descriptions", () => {
        render(<OverviewMetrics data={mockData} isLoading={false} />);

        expect(screen.getByText("Total story views")).toBeInTheDocument();
        expect(screen.getByText("Completed chapter reads")).toBeInTheDocument();
        expect(screen.getByText("Total followers")).toBeInTheDocument();
        expect(screen.getByText("Reader engagement")).toBeInTheDocument();
    });
});
