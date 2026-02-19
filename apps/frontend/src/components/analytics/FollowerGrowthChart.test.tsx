import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { FollowerGrowthChart } from "./FollowerGrowthChart";
import type { FollowerGrowthData } from "@/types";

describe("FollowerGrowthChart", () => {
    const mockData: FollowerGrowthData = {
        data_points: [
            {
                date: "2024-01-01",
                followers: 100,
                new_followers: 10,
                unfollows: 2,
            },
            {
                date: "2024-01-02",
                followers: 108,
                new_followers: 12,
                unfollows: 4,
            },
            {
                date: "2024-01-03",
                followers: 116,
                new_followers: 15,
                unfollows: 7,
            },
        ],
        total_growth: 16,
        growth_rate: 0.16,
    };

    it("renders loading state when isLoading is true", () => {
        render(<FollowerGrowthChart data={mockData} isLoading={true} />);
        const skeletons = document.querySelectorAll(".animate-pulse");
        expect(skeletons.length).toBeGreaterThan(0);
    });

    it("renders chart title and description", () => {
        render(<FollowerGrowthChart data={mockData} isLoading={false} />);

        expect(screen.getByText("Follower Growth")).toBeInTheDocument();
        expect(screen.getByText("Track your audience growth over time")).toBeInTheDocument();
    });

    it("displays total growth metric", () => {
        render(<FollowerGrowthChart data={mockData} isLoading={false} />);

        expect(screen.getByText("Total Growth")).toBeInTheDocument();
        expect(screen.getByText("+16")).toBeInTheDocument();
    });

    it("displays growth rate metric", () => {
        render(<FollowerGrowthChart data={mockData} isLoading={false} />);

        expect(screen.getByText("Growth Rate")).toBeInTheDocument();
        expect(screen.getByText("+16.0%")).toBeInTheDocument();
    });

    it("handles negative growth correctly", () => {
        const negativeGrowthData: FollowerGrowthData = {
            ...mockData,
            total_growth: -5,
            growth_rate: -0.05,
        };

        render(<FollowerGrowthChart data={negativeGrowthData} isLoading={false} />);

        expect(screen.getByText("-5")).toBeInTheDocument();
        expect(screen.getByText("-5.0%")).toBeInTheDocument();
    });
});
