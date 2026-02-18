import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ClerkProvider, useAuth } from "@clerk/clerk-react";
import { useEffect } from "react";
import { setTokenGetter } from "@/lib/api";
import { RecaptchaProvider } from "@/contexts/RecaptchaContext";

import AppShell from "@/components/layout/AppShell";
import ProtectedRoute from "@/components/shared/ProtectedRoute";

import Index from "./pages/Index";
import Discover from "./pages/Discover";
import StoryPage from "./pages/StoryPage";
import Reader from "./pages/Reader";
import Whispers from "./pages/Whispers";
import Profile from "./pages/Profile";
import Search from "./pages/Search";
import Library from "./pages/Library";
import WriteDashboard from "./pages/WriteDashboard";
import StoryEditor from "./pages/StoryEditor";
import Notifications from "./pages/Notifications";
import ProfileSettings from "./pages/ProfileSettings";
import SignIn from "./pages/SignIn";
import SignUp from "./pages/SignUp";
import DMCARequest from "./pages/DMCARequest";
import { HelpCenter } from "./pages/HelpCenter";
import { HelpArticle } from "./pages/HelpArticle";
import { HelpSearch } from "./pages/HelpSearch";
import { HelpCategory } from "./pages/HelpCategory";
import { ContactSupport } from "./pages/ContactSupport";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 30_000 },
  },
});

const CLERK_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY ?? "";

function TokenInjector() {
  const { getToken } = useAuth();
  useEffect(() => {
    setTokenGetter(() => getToken());
  }, [getToken]);
  return null;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<AppShell><Index /></AppShell>} />
      <Route path="/discover" element={<AppShell><Discover /></AppShell>} />
      <Route path="/story/:slug" element={<AppShell><StoryPage /></AppShell>} />
      <Route path="/read/:chapterId" element={<Reader />} />
      <Route path="/whispers" element={<AppShell><Whispers /></AppShell>} />
      <Route path="/u/:handle" element={<AppShell><Profile /></AppShell>} />
      <Route path="/search" element={<AppShell><Search /></AppShell>} />
      <Route path="/library" element={<AppShell><ProtectedRoute><Library /></ProtectedRoute></AppShell>} />
      <Route path="/write" element={<AppShell><ProtectedRoute><WriteDashboard /></ProtectedRoute></AppShell>} />
      <Route path="/write/story/:id" element={<AppShell><ProtectedRoute><StoryEditor /></ProtectedRoute></AppShell>} />
      <Route path="/notifications" element={<AppShell><ProtectedRoute><Notifications /></ProtectedRoute></AppShell>} />
      <Route path="/settings/profile" element={<AppShell><ProtectedRoute><ProfileSettings /></ProtectedRoute></AppShell>} />
      <Route path="/dmca" element={<AppShell><DMCARequest /></AppShell>} />
      <Route path="/help" element={<AppShell><HelpCenter /></AppShell>} />
      <Route path="/help/search" element={<AppShell><HelpSearch /></AppShell>} />
      <Route path="/help/category/:category" element={<AppShell><HelpCategory /></AppShell>} />
      <Route path="/help/articles/:slug" element={<AppShell><HelpArticle /></AppShell>} />
      <Route path="/help/contact" element={<AppShell><ContactSupport /></AppShell>} />
      <Route path="/sign-in" element={<SignIn />} />
      <Route path="/sign-up" element={<SignUp />} />
      <Route path="*" element={<AppShell><NotFound /></AppShell>} />
    </Routes>
  );
}

const App = () => {
  // If no Clerk key, render without Clerk (dev mode)
  if (!CLERK_KEY) {
    return (
      <QueryClientProvider client={queryClient}>
        <RecaptchaProvider>
          <TooltipProvider>
            <Toaster />
            <Sonner />
            <BrowserRouter>
              <AppRoutes />
            </BrowserRouter>
          </TooltipProvider>
        </RecaptchaProvider>
      </QueryClientProvider>
    );
  }

  return (
    <ClerkProvider publishableKey={CLERK_KEY}>
      <QueryClientProvider client={queryClient}>
        <RecaptchaProvider>
          <TooltipProvider>
            <Toaster />
            <Sonner />
            <BrowserRouter>
              <TokenInjector />
              <AppRoutes />
            </BrowserRouter>
          </TooltipProvider>
        </RecaptchaProvider>
      </QueryClientProvider>
    </ClerkProvider>
  );
};

export default App;
