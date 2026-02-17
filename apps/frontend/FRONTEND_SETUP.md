# MueJam Library Frontend Setup

## Overview

The MueJam Library frontend is built with React 18, Vite, TypeScript, and Tailwind CSS. It uses Clerk for authentication, React Router for navigation, and shadcn/ui for UI components.

## Technology Stack

- **Framework**: React 18.3 with TypeScript
- **Build Tool**: Vite 5.4
- **Styling**: Tailwind CSS 3.4 with shadcn/ui components
- **Routing**: React Router DOM 6.30
- **Authentication**: Clerk React 5.60
- **State Management**: TanStack Query (React Query) 5.83
- **Forms**: React Hook Form 7.61 with Zod validation
- **Markdown**: React Markdown with rehype-sanitize
- **Icons**: Lucide React

## Project Structure

```
frontend/
├── public/                 # Static assets
│   ├── favicon.ico
│   └── robots.txt
├── src/
│   ├── components/        # React components
│   │   ├── layout/       # Layout components (AppShell)
│   │   ├── shared/       # Shared components (StoryCard, WhisperCard, etc.)
│   │   └── ui/           # shadcn/ui components
│   ├── hooks/            # Custom React hooks
│   │   ├── use-mobile.tsx
│   │   ├── useReaderSettings.ts
│   │   └── useSafeAuth.ts
│   ├── lib/              # Utilities and API client
│   │   ├── api.ts        # API client with Clerk token injection
│   │   ├── upload.ts     # S3 upload utilities
│   │   └── utils.ts      # Helper functions
│   ├── pages/            # Page components
│   │   ├── Discover.tsx
│   │   ├── Library.tsx
│   │   ├── Reader.tsx
│   │   ├── StoryPage.tsx
│   │   ├── Whispers.tsx
│   │   └── ...
│   ├── types/            # TypeScript type definitions
│   │   └── index.ts
│   ├── App.tsx           # Main app component with routing
│   ├── main.tsx          # Entry point
│   └── index.css         # Global styles
├── .env.example          # Environment variables template
├── package.json
├── tailwind.config.ts    # Tailwind configuration
├── tsconfig.json         # TypeScript configuration
└── vite.config.ts        # Vite configuration
```

## Getting Started

### Prerequisites

- Node.js 18+ or Bun
- Backend API running on http://localhost:8000
- Clerk account with publishable key

### Installation

1. **Install dependencies:**

```bash
cd frontend
npm install
# or
bun install
```

2. **Configure environment variables:**

```bash
cp .env.example .env
```

Edit `.env` and add your configuration:

```env
# API Configuration
VITE_API_BASE_URL=http://localhost:8000/v1

# Clerk Authentication
VITE_CLERK_PUBLISHABLE_KEY=pk_test_your_key_here

# Clerk URLs (optional)
VITE_CLERK_SIGN_IN_URL=/sign-in
VITE_CLERK_SIGN_UP_URL=/sign-up
VITE_CLERK_AFTER_SIGN_IN_URL=/discover
VITE_CLERK_AFTER_SIGN_UP_URL=/discover
```

3. **Start development server:**

```bash
npm run dev
# or
bun dev
```

The app will be available at http://localhost:8080

### Building for Production

```bash
npm run build
# or
bun run build
```

The built files will be in the `dist/` directory.

### Preview Production Build

```bash
npm run preview
# or
bun preview
```

## Key Features

### Authentication

The app uses Clerk for authentication with automatic token injection into API requests:

```typescript
// Token is automatically injected by the API client
const stories = await api.getStories();
```

Protected routes are wrapped with `<ProtectedRoute>`:

```tsx
<Route path="/library" element={
  <AppShell>
    <ProtectedRoute>
      <Library />
    </ProtectedRoute>
  </AppShell>
} />
```

### API Client

The API client (`src/lib/api.ts`) provides typed methods for all backend endpoints:

```typescript
import { api } from '@/lib/api';

// Get stories with filters
const stories = await api.getStories({ tag: 'fantasy', sort: 'trending' });

// Create a whisper
const whisper = await api.createWhisper({
  body: 'Great story!',
  scope: 'STORY',
  story_id: storyId
});

// Upload media
const presign = await api.presign({
  type: 'avatar',
  content_type: 'image/jpeg',
  size_bytes: 1024000
});
```

### State Management

TanStack Query (React Query) is used for server state management:

```typescript
const { data: stories, isLoading } = useQuery({
  queryKey: ['stories', { tag, sort }],
  queryFn: () => api.getStories({ tag, sort }),
  staleTime: 30_000, // 30 seconds
});
```

### Routing

React Router DOM handles navigation:

```typescript
// Navigate programmatically
const navigate = useNavigate();
navigate('/story/my-story-slug');

// Link component
<Link to="/discover">Discover</Link>

// Get current location
const location = useLocation();
```

### Styling

Tailwind CSS with custom theme configuration:

```tsx
// Use Tailwind classes
<div className="flex items-center gap-4 p-6 rounded-lg bg-card">
  <h2 className="text-2xl font-semibold">Title</h2>
</div>

// Use cn() utility for conditional classes
<button className={cn(
  "px-4 py-2 rounded-md",
  isActive && "bg-primary text-primary-foreground"
)}>
  Button
</button>
```

### Forms

React Hook Form with Zod validation:

```typescript
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const schema = z.object({
  title: z.string().min(1, 'Title is required'),
  blurb: z.string().optional(),
});

const form = useForm({
  resolver: zodResolver(schema),
  defaultValues: { title: '', blurb: '' },
});

const onSubmit = form.handleSubmit(async (data) => {
  await api.createStory(data);
});
```

## Component Library

The app uses shadcn/ui components which are:
- Fully customizable
- Accessible by default
- Built with Radix UI primitives
- Styled with Tailwind CSS

Available components include:
- Button, Input, Textarea, Select
- Dialog, Sheet, Popover, Dropdown Menu
- Card, Badge, Avatar, Separator
- Tabs, Accordion, Collapsible
- Toast, Alert, Progress
- And many more...

## Custom Hooks

### useSafeAuth

Safely access Clerk auth state:

```typescript
const { isSignedIn, userId, isLoaded } = useSafeAuth();
```

### useReaderSettings

Manage reader customization settings:

```typescript
const { fontSize, theme, lineWidth, updateSettings } = useReaderSettings();
```

### use-mobile

Detect mobile viewport:

```typescript
const isMobile = useMobile();
```

## Development Guidelines

### Code Style

- Use TypeScript for type safety
- Follow React best practices (hooks, functional components)
- Use Tailwind CSS for styling (avoid custom CSS when possible)
- Keep components small and focused
- Extract reusable logic into custom hooks

### File Naming

- Components: PascalCase (e.g., `StoryCard.tsx`)
- Hooks: camelCase with `use` prefix (e.g., `useReaderSettings.ts`)
- Utilities: camelCase (e.g., `api.ts`, `utils.ts`)
- Types: PascalCase (e.g., `Story`, `UserProfile`)

### Import Aliases

Use the `@/` alias for imports:

```typescript
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { StoryCard } from '@/components/shared/StoryCard';
```

### Error Handling

API errors are typed and can be caught:

```typescript
try {
  await api.createStory(data);
} catch (error) {
  const apiError = error as ApiError;
  console.error(apiError.error.message);
  toast.error(apiError.error.message);
}
```

## Testing

### Running Tests

```bash
npm test          # Run tests once
npm run test:watch # Run tests in watch mode
```

### Writing Tests

Tests use Vitest and React Testing Library:

```typescript
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { StoryCard } from './StoryCard';

describe('StoryCard', () => {
  it('renders story title', () => {
    render(<StoryCard story={mockStory} />);
    expect(screen.getByText('Story Title')).toBeInTheDocument();
  });
});
```

## Performance Optimization

### Code Splitting

React Router automatically code-splits routes. For additional splitting:

```typescript
import { lazy, Suspense } from 'react';

const HeavyComponent = lazy(() => import('./HeavyComponent'));

<Suspense fallback={<Loading />}>
  <HeavyComponent />
</Suspense>
```

### Image Optimization

Use responsive images and lazy loading:

```tsx
<img
  src={coverUrl}
  alt={title}
  loading="lazy"
  className="w-full h-auto"
/>
```

### Query Caching

Configure appropriate stale times for queries:

```typescript
useQuery({
  queryKey: ['stories'],
  queryFn: api.getStories,
  staleTime: 5 * 60 * 1000, // 5 minutes
});
```

## Deployment

### Environment Variables

Set these in your deployment platform:

- `VITE_API_BASE_URL` - Backend API URL
- `VITE_CLERK_PUBLISHABLE_KEY` - Clerk publishable key

### Build Command

```bash
npm run build
```

### Output Directory

```
dist/
```

### Deployment Platforms

The app can be deployed to:
- Vercel
- Netlify
- AWS S3 + CloudFront
- Any static hosting service

## Troubleshooting

### Clerk Authentication Not Working

1. Check that `VITE_CLERK_PUBLISHABLE_KEY` is set correctly
2. Verify the key starts with `pk_test_` or `pk_live_`
3. Check browser console for Clerk errors

### API Requests Failing

1. Verify backend is running on the correct URL
2. Check `VITE_API_BASE_URL` in `.env`
3. Check browser network tab for CORS errors
4. Verify Clerk token is being sent in Authorization header

### Build Errors

1. Clear node_modules and reinstall: `rm -rf node_modules && npm install`
2. Clear Vite cache: `rm -rf node_modules/.vite`
3. Check TypeScript errors: `npm run build`

## Resources

- [React Documentation](https://react.dev/)
- [Vite Documentation](https://vitejs.dev/)
- [Tailwind CSS Documentation](https://tailwindcss.com/)
- [shadcn/ui Documentation](https://ui.shadcn.com/)
- [Clerk Documentation](https://clerk.com/docs)
- [TanStack Query Documentation](https://tanstack.com/query/latest)
- [React Router Documentation](https://reactrouter.com/)

## Support

For questions or issues, contact: support@muejam.com
