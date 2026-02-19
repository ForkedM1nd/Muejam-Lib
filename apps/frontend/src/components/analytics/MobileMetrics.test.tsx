import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MobileMetrics } from "./MobileMetrics";
import type { MobileMetrics as MobileMetricsType } from "@/types";

describe("MobileMetrics", () => {
    const mockData: MobileMetricsType = {
        ios_users: 1500,
        android_users: 2500,
        mobile_engagement_rate: 0.68,
        app_version_distribution: {
            "2.1.0": 1200,
            "2.0.5": 800,
            "2.0.0": 600,
            "1.9.8": 400,
            "1.9.5": 200,
            "1.9.0": 100,
        },
        device_types: {
            phone: 3000,
            tablet: 800,
            phablet: 200,
        },
    };

    it("renders loading state", () => {
        render(<MobileMetrics data={mockData} isLoading={true} />);
        const skeletons = document.querySelectorAll(".animate-pulse");
        expect(skeletons.length).toBeGreaterThan(0);
    });

    it("displays iOS user count", () => {
        render(<MobileMetrics data={mockData} isLoading={false} />);
        expect(screen.getByText("1,500")).toBeInTheDocument();
        expect(screen.getByText("iOS Users")).toBeInTheDocument();
    });

    it("displays Android user count", () => {
        render(<MobileMetrics data={mockData} isLoading={false} />);
        expect(screen.getByText("2,500")).toBeInTheDocument();
        expect(screen.getByText("Android Users")).toBeInTheDocument();
    });

    it("displays mobile engagement rate", () => {
        render(<MobileMetrics data={mockData} isLoading={false} />);
        expect(screen.getByText("68.0%")).toBeInTheDocument();
        expect(screen.getByText("Mobile Engagement")).toBeInTheDocument();
    });

    it("calculates platform percentages correctly", () => {
        render(<MobileMetrics data={mockData} isLoading={false} />);
        // iOS: 1500 / 4000 = 37.5%
        expect(screen.getByText("37.5% of mobile users")).toBeInTheDocument();
        // Android: 2500 / 4000 = 62.5%
        expect(screen.getByText("62.5% of mobile users")).toBeInTheDocument();
    });

    it("displays device types", () => {
        render(<MobileMetrics data={mockData} isLoading={false} />);
        expect(screen.getByText(/phone/i)).toBeInTheDocument();
        expect(screen.getByText(/tablet/i)).toBeInTheDocument();
        expect(screen.getByText(/phablet/i)).toBeInTheDocument();
    });

    it("displays top 5 app versions", () => {
        render(<MobileMetrics data={mockData} isLoading={false} />);
        expect(screen.getByText("Version 2.1.0")).toBeInTheDocument();
        expect(screen.getByText("Version 2.0.5")).toBeInTheDocument();
        expect(screen.getByText("Version 2.0.0")).toBeInTheDocument();
        expect(screen.getByText("Version 1.9.8")).toBeInTheDocument();
        expect(screen.getByText("Version 1.9.5")).toBeInTheDocument();
        // Version 1.9.0 should not be displayed (only top 5)
        expect(screen.queryByText("Version 1.9.0")).not.toBeInTheDocument();
    });

    it("displays platform distribution chart", () => {
        render(<MobileMetrics data={mockData} isLoading={false} />);
        expect(screen.getByText("Platform Distribution")).toBeInTheDocument();
        expect(screen.getByText("iOS vs Android breakdown")).toBeInTheDocument();
    });

    it("displays device types section", () => {
        render(<MobileMetrics data={mockData} isLoading={false} />);
        expect(screen.getByText("Device Types")).toBeInTheDocument();
        expect(screen.getByText("Distribution by device category")).toBeInTheDocument();
    });

    it("displays app version distribution section", () => {
        render(<MobileMetrics data={mockData} isLoading={false} />);
        expect(screen.getByText("App Version Distribution")).toBeInTheDocument();
        expect(screen.getByText("Top 5 app versions in use")).toBeInTheDocument();
    });

    it("handles zero users gracefully", () => {
        const emptyData: MobileMetricsType = {
            ios_users: 0,
            android_users: 0,
            mobile_engagement_rate: 0,
            app_version_distribution: {},
            device_types: {},
        };
        render(<MobileMetrics data={emptyData} isLoading={false} />);
        // Check that iOS and Android both show 0
        const zeroElements = screen.getAllByText("0");
        expect(zeroElements.length).toBeGreaterThanOrEqual(2);
        expect(screen.getByText("0.0%")).toBeInTheDocument();
    });

    it("calculates device type percentages correctly", () => {
        render(<MobileMetrics data={mockData} isLoading={false} />);
        // phone: 3000 / 4000 = 75%
        expect(screen.getByText(/3,000.*75\.0%/)).toBeInTheDocument();
        // tablet: 800 / 4000 = 20%
        expect(screen.getByText(/800.*20\.0%/)).toBeInTheDocument();
        // phablet: 200 / 4000 = 5%
        expect(screen.getByText(/200.*5\.0%/)).toBeInTheDocument();
    });

    it("calculates app version percentages correctly", () => {
        render(<MobileMetrics data={mockData} isLoading={false} />);
        // Total users: 3300
        // Version 2.1.0: 1200 / 3300 = 36.4%
        expect(screen.getByText(/1,200 users.*36\.4%/)).toBeInTheDocument();
    });
});
