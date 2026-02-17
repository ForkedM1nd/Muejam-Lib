import { useState, useEffect } from "react";

type Theme = "light" | "dark";

export function useTheme() {
    const [theme, setThemeState] = useState<Theme>(() => {
        try {
            const stored = localStorage.getItem("muejam-theme");
            if (stored === "light" || stored === "dark") return stored;

            // Check system preference
            if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
                return "dark";
            }
            return "light";
        } catch {
            return "light";
        }
    });

    useEffect(() => {
        const root = document.documentElement;
        if (theme === "dark") {
            root.classList.add("dark");
        } else {
            root.classList.remove("dark");
        }
        localStorage.setItem("muejam-theme", theme);
    }, [theme]);

    const toggleTheme = () => {
        setThemeState((prev) => (prev === "light" ? "dark" : "light"));
    };

    return { theme, setTheme: setThemeState, toggleTheme };
}
