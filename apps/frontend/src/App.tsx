import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ClerkProvider, useAuth } from "@clerk/clerk-react";
import { useEffect, lazy, Suspense } from "react";
import { setTokenGetter, setRefreshTokenFn } from "@/lib/api";
import { queryClient } from "@/lib/queryClient";
import { RecaptchaProvider } from "@/contexts/RecaptchaContext";
import { AuthProvider } from "@/contexts/AuthContext";
import { OnboardingCompletionPrompt } from "@/components/onboarding/OnboardingCompletionPrompt";
import { TermsAcceptancePrompt } from "@/components/legal/TermsAcceptancePrompt";
import { FloatingConnectionStatus } from "@/components/shared/ConnectionStatus";
import { useOnlineStatus } from "@/hooks/useOnlineStatus";
import { useOfflineSync } from "@/hooks/useOfflineSync";
import { Skeleton } from "@/components/ui/skeleton";
import { registerServiceWorker } from "@/lib/serviceWorker";

import AppShell from "@/components/layout/AppShell";
import ProtectedRoute from "@/components/shared/ProtectedRoute";

// Eager load critical pages
import Index from "./pages/Index";
import SignIn from "./pages/SignIn";
import SignUp from "./pages/SignUp";

// Lazy load all other pages
const Discover = lazy(() => import("./pages/Discover"));
const RisingAuthors = lazy(() => import("./pages/RisingAuthors"));
const GenreDiscovery = lazy(() => import("./pages/GenreDiscovery"));
const TrendingStories = lazy(() => import("./pages/TrendingStories"));
const NewAndNoteworthy = lazy(() => import("./pages/NewAndNoteworthy"));
const RecommendedStories = lazy(() => import("./pages/RecommendedStories"));
const StaffPicks = lazy(() => import("./pages/StaffPicks"));
const Activity = lazy(() => import("./pages/Activity"));
const StoryPage = lazy(() => import("./pages/StoryPage"));
const Reader = lazy(() => import("./pages/Reader"));
const Whispers = lazy(() => import("./pages/Whispers"));
const Profile = lazy(() => import("./pages/Profile"));
const Followers = lazy(() => import("./pages/Followers"));
const Following = lazy(() => import("./pages/Following"));
const Search = lazy(() => import("./pages/Search"));
const Library = lazy(() => import("./pages/Library"));
const Highlights = lazy(() => import("./pages/Highlights"));
const MyReports = lazy(() => import("./pages/MyReports"));
const WriteDashboard = lazy(() => import("./pages/WriteDashboard"));
const StoryEditor = lazy(() => import("./pages/StoryEditor"));
const Notifications = lazy(() => import("./pages/Notifications"));
const ProfileSettings = lazy(() => import("./pages/ProfileSettings"));
const PrivacySettings = lazy(() => import("./pages/PrivacySettings"));
const SecuritySettings = lazy(() => import("./pages/SecuritySettings"));
const NotificationSettings = lazy(() => import("./pages/NotificationSettings"));
const DeviceManagement = lazy(() => import("./pages/DeviceManagement"));
const ForgotPassword = lazy(() => import("./pages/ForgotPassword"));
const ResetPassword = lazy(() => import("./pages/ResetPassword"));
const EmailVerification = lazy(() => import("./pages/EmailVerification"));
const Verify2FA = lazy(() => import("./pages/Verify2FA"));
const DMCARequest = lazy(() => import("./pages/DMCARequest"));
const HelpCenter = lazy(() => import("./pages/HelpCenter").then(m => ({ default: m.HelpCenter })));
const HelpArticle = lazy(() => import("./pages/HelpArticle").then(m => ({ default: m.HelpArticle })));
const HelpSearch = lazy(() => import("./pages/HelpSearch").then(m => ({ default: m.HelpSearch })));
const HelpCategory = lazy(() => import("./pages/HelpCategory").then(m => ({ default: m.HelpCategory })));
const ContactSupport = lazy(() => import("./pages/ContactSupport").then(m => ({ default: m.ContactSupport })));
const TermsOfService = lazy(() => import("./pages/TermsOfService").then(m => ({ default: m.TermsOfService })));
const PrivacyPolicy = lazy(() => import("./pages/PrivacyPolicy").then(m => ({ default: m.PrivacyPolicy })));
const CookiePolicy = lazy(() => import("./pages/CookiePolicy").then(m => ({ default: m.CookiePolicy })));
const CommunityGuidelines = lazy(() => import("./pages/CommunityGuidelines").then(m => ({ default: m.CommunityGuidelines })));
const CopyrightPolicy = lazy(() => import("./pages/CopyrightPolicy").then(m => ({ default: m.CopyrightPolicy })));
const Onboarding = lazy(() => import("./pages/Onboarding"));
const AdminDashboard = lazy(() => import("./pages/AdminDashboard"));
const AnalyticsDashboard = lazy(() => import("./pages/AnalyticsDashboard"));
const ModerationQueue = lazy(() => import("./pages/ModerationQueue"));
const ModerationReview = lazy(() => import("./pages/ModerationReview"));
const NotFound = lazy(() => import("./pages/NotFound"));

// Lazy load React Query Devtools only in development
const ReactQueryDevtools = import.meta.env.DEV
  ? lazy(() =>
    import("@tanstack/react-query-devtools").then((module) => ({
      default: module.ReactQueryDevtools,
    }))
  )
  : null;

// Loading fallback component
const PageLoader = () => (
  <div className="flex flex-col gap-4 p-6">
    <Skeleton className="h-8 w-64" />
    <Skeleton className="h-4 w-full" />
    <Skeleton className="h-4 w-full" />
    <Skeleton className="h-4 w-3/4" />
  </div>
);

const CLERK_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY ?? "";

function TokenInjector() {
  const { getToken, signOut } = useAuth();

  useEffect(() => {
    // Set the token getter function
    setTokenGetter(() => getToken());

    // Set the refresh token function
    // This will be called automatically by the API client on 401 errors
    setRefreshTokenFn(async () => {
      try {
        // Clerk's getToken() with skipCache forces a fresh token
        const token = await getToken({ skipCache: true });

        if (!token) {
          // Token refresh failed - refresh token likely expired
          // Sign out and redirect to sign-in page
          await signOut();
          window.location.href = '/sign-in';
          return null;
        }

        return token;
      } catch (error) {
        // Token refresh failed - redirect to sign-in
        console.error('Token refresh failed:', error);
        await signOut();
        window.location.href = '/sign-in';
        return null;
      }
    });
  }, [getToken, signOut]);

  return null;
}

function AppRoutes() {
  // Initialize online status detection
  useOnlineStatus();

  // Initialize offline sync
  useOfflineSync();

  return (
    <>
      <OnboardingCompletionPrompt />
      <TermsAcceptancePrompt />
      <FloatingConnectionStatus />
      <Suspense fallback={<PageLoader />}>
        <Routes>
          <Route path="/" element={<AppShell><Index /></AppShell>} />
          <Route path="/discover" element={<AppShell><Discover /></AppShell>} />
          <Route path="/discover/trending" element={<AppShell><TrendingStories /></AppShell>} />
          <Route path="/discover/new" element={<AppShell><NewAndNoteworthy /></AppShell>} />
          <Route path="/discover/recommended" element={<AppShell><RecommendedStories /></AppShell>} />
          <Route path="/discover/staff-picks" element={<AppShell><StaffPicks /></AppShell>} />
          <Route path="/discover/rising-authors" element={<AppShell><RisingAuthors /></AppShell>} />
          <Route path="/discover/genre" element={<AppShell><GenreDiscovery /></AppShell>} />
          <Route path="/discover/genre/:genre" element={<AppShell><GenreDiscovery /></AppShell>} />
          <Route path="/activity" element={<AppShell><ProtectedRoute><Activity /></ProtectedRoute></AppShell>} />
          <Route path="/story/:slug" element={<AppShell><StoryPage /></AppShell>} />
          <Route path="/stories/:slug" element={<AppShell><StoryPage /></AppShell>} />
          <Route path="/read/:chapterId" element={<Reader />} />
          <Route path="/chapter/:chapterId" element={<Reader />} />
          <Route path="/whispers" element={<AppShell><Whispers /></AppShell>} />
          <Route path="/u/:handle" element={<AppShell><Profile /></AppShell>} />
          <Route path="/profile/:handle" element={<AppShell><Profile /></AppShell>} />
          <Route path="/users/:handle/followers" element={<AppShell><Followers /></AppShell>} />
          <Route path="/users/:handle/following" element={<AppShell><Following /></AppShell>} />
          <Route path="/search" element={<AppShell><Search /></AppShell>} />
          <Route path="/library" element={<AppShell><ProtectedRoute><Library /></ProtectedRoute></AppShell>} />
          <Route path="/highlights" element={<AppShell><ProtectedRoute><Highlights /></ProtectedRoute></AppShell>} />
          <Route path="/reports" element={<AppShell><ProtectedRoute><MyReports /></ProtectedRoute></AppShell>} />
          <Route path="/write" element={<AppShell><ProtectedRoute><WriteDashboard /></ProtectedRoute></AppShell>} />
          <Route path="/write/story/:id" element={<AppShell><ProtectedRoute><StoryEditor /></ProtectedRoute></AppShell>} />
          <Route path="/notifications" element={<AppShell><ProtectedRoute><Notifications /></ProtectedRoute></AppShell>} />
          <Route path="/settings/profile" element={<AppShell><ProtectedRoute><ProfileSettings /></ProtectedRoute></AppShell>} />
          <Route path="/settings/privacy" element={<AppShell><ProtectedRoute><PrivacySettings /></ProtectedRoute></AppShell>} />
          <Route path="/settings/security" element={<AppShell><ProtectedRoute><SecuritySettings /></ProtectedRoute></AppShell>} />
          <Route path="/settings/notifications" element={<AppShell><ProtectedRoute><NotificationSettings /></ProtectedRoute></AppShell>} />
          <Route path="/settings/devices" element={<AppShell><ProtectedRoute><DeviceManagement /></ProtectedRoute></AppShell>} />
          <Route path="/dmca" element={<AppShell><DMCARequest /></AppShell>} />
          <Route path="/help" element={<AppShell><HelpCenter /></AppShell>} />
          <Route path="/help/search" element={<AppShell><HelpSearch /></AppShell>} />
          <Route path="/help/category/:category" element={<AppShell><HelpCategory /></AppShell>} />
          <Route path="/help/articles/:slug" element={<AppShell><HelpArticle /></AppShell>} />
          <Route path="/help/contact" element={<AppShell><ContactSupport /></AppShell>} />
          <Route path="/legal/terms" element={<AppShell><TermsOfService /></AppShell>} />
          <Route path="/legal/privacy" element={<AppShell><PrivacyPolicy /></AppShell>} />
          <Route path="/legal/cookies" element={<AppShell><CookiePolicy /></AppShell>} />
          <Route path="/legal/guidelines" element={<AppShell><CommunityGuidelines /></AppShell>} />
          <Route path="/legal/copyright" element={<AppShell><CopyrightPolicy /></AppShell>} />
          <Route path="/admin" element={<AdminDashboard />} />
          <Route path="/analytics" element={<AnalyticsDashboard />} />
          <Route path="/moderation" element={<ModerationQueue />} />
          <Route path="/moderation/review/:itemId" element={<ModerationReview />} />
          <Route path="/sign-in" element={<SignIn />} />
          <Route path="/sign-up" element={<SignUp />} />
          <Route path="/verify-2fa" element={<Verify2FA />} />
          <Route path="/onboarding" element={<Onboarding />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route path="/verify-email" element={<EmailVerification />} />
          <Route path="*" element={<AppShell><NotFound /></AppShell>} />
        </Routes>
      </Suspense>
    </>
  );
}

const App = () => {
  // Register service worker
  useEffect(() => {
    registerServiceWorker({
      onUpdate: (registration) => {
        console.log('New version available! Please refresh.');
        // Could show a toast notification here
      },
      onSuccess: (registration) => {
        console.log('Service worker registered successfully');
      },
      onError: (error) => {
        console.error('Service worker registration failed:', error);
      },
    });
  }, []);

  // If no Clerk key, render without Clerk (dev mode)
  if (!CLERK_KEY) {
    return (
      <QueryClientProvider client={queryClient}>
        <RecaptchaProvider>
          <TooltipProvider>
            <Toaster />
            <Sonner />
            <BrowserRouter>
              <AuthProvider>
                <AppRoutes />
              </AuthProvider>
            </BrowserRouter>
          </TooltipProvider>
        </RecaptchaProvider>
        {ReactQueryDevtools && (
          <Suspense fallback={null}>
            <ReactQueryDevtools initialIsOpen={false} />
          </Suspense>
        )}
      </QueryClientProvider>
    );
  }

  return (
    <QueryClientProvider client={queryClient}>
      <RecaptchaProvider>
        <TooltipProvider>
          <Toaster />
          <Sonner />
          <BrowserRouter>
            <ClerkProvider publishableKey={CLERK_KEY}>
              <AuthProvider>
                <TokenInjector />
                <AppRoutes />
              </AuthProvider>
            </ClerkProvider>
          </BrowserRouter>
        </TooltipProvider>
      </RecaptchaProvider>
      {ReactQueryDevtools && (
        <Suspense fallback={null}>
          <ReactQueryDevtools initialIsOpen={false} />
        </Suspense>
      )}
    </QueryClientProvider>
  );
};

export default App;
