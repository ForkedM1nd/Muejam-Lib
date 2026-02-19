import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import "./index.css";
import { initMonitoring } from "./lib/monitoring";

// Initialize monitoring (Sentry, Web Vitals, Analytics)
initMonitoring();

createRoot(document.getElementById("root")!).render(<App />);
