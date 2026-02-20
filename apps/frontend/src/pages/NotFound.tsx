import { Link, useLocation } from "react-router-dom";
import { useEffect } from "react";
import SurfacePanel from "@/components/shared/SurfacePanel";

const NotFound = () => {
  const location = useLocation();

  useEffect(() => {
    console.error("404 Error: User attempted to access non-existent route:", location.pathname);
  }, [location.pathname]);

  return (
    <div className="mx-auto max-w-2xl py-10">
      <SurfacePanel className="p-8 text-center sm:p-10">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-primary/80">404</p>
        <h1 className="mt-3 text-4xl font-semibold" style={{ fontFamily: "var(--font-display)" }}>
          This page does not exist
        </h1>
        <p className="mt-3 text-sm text-muted-foreground sm:text-base">
          The link may be outdated or the page has moved.
        </p>
        <div className="mt-6 flex justify-center gap-3">
          <Link to="/" className="text-sm font-medium text-primary hover:underline">
            Return home
          </Link>
          <Link to="/discover" className="text-sm font-medium text-primary hover:underline">
            Explore stories
          </Link>
        </div>
      </SurfacePanel>
    </div>
  );
};

export default NotFound;
