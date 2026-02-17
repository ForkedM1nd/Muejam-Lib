# MueJam Library - Frontend

A modern, feature-rich frontend for the MueJam Library serial fiction platform.

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Set up environment variables
cp .env.example .env
# Edit .env and add your Clerk publishable key

# Start development server
npm run dev
```

Visit http://localhost:5173

## 📚 Documentation

### Authentication
- **[Quick Start Guide](AUTH_QUICK_START.md)** - Get auth working in 5 minutes
- **[Complete Guide](AUTHENTICATION.md)** - Full authentication documentation
- **[Implementation Summary](AUTH_IMPLEMENTATION_SUMMARY.md)** - Technical details
- **[Test Checklist](AUTH_TEST_CHECKLIST.md)** - 150+ test cases
- **[Status](AUTH_COMPLETE.md)** - Implementation status

### Other Documentation
- **[API Client](API_CLIENT.md)** - API integration guide
- **[Frontend Setup](FRONTEND_SETUP.md)** - Detailed setup instructions
- **[Components](components.json)** - UI component configuration

## ✨ Features

### Authentication
- ✅ Email/password sign-in and sign-up
- ✅ Social login support (Google, GitHub, etc.)
- ✅ Protected routes with automatic redirect
- ✅ Session persistence
- ✅ Token-based API authentication
- ✅ User profile management

### Core Features
- 📖 Story reading with customizable reader
- ✍️ Story writing and editing
- 🔍 Advanced search with suggestions
- 📚 Personal library management
- 💬 Whispers (social features)
- 🔔 Notifications
- 🌓 Dark/light theme
- 📱 Fully responsive design

## 🛠️ Tech Stack

- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Routing**: React Router v6
- **State Management**: TanStack Query (React Query)
- **Authentication**: Clerk
- **UI Components**: Radix UI + shadcn/ui
- **Styling**: Tailwind CSS
- **Forms**: React Hook Form + Zod
- **Testing**: Vitest + Testing Library

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── layout/        # Layout components (AppShell, etc.)
│   │   ├── shared/        # Shared components (ProtectedRoute, etc.)
│   │   └── ui/            # UI components (shadcn/ui)
│   ├── contexts/          # React contexts (AuthContext, etc.)
│   ├── hooks/             # Custom hooks (useSafeAuth, etc.)
│   ├── lib/               # Utilities (API client, utils)
│   ├── pages/             # Page components
│   ├── types/             # TypeScript types
│   └── App.tsx            # Main app component
├── public/                # Static assets
└── docs/                  # Documentation
```

## 🔐 Authentication Setup

### 1. Create Clerk Account

1. Go to [clerk.com](https://clerk.com/) and sign up
2. Create a new application
3. Copy your Publishable Key

### 2. Configure Environment

```bash
# .env
VITE_CLERK_PUBLISHABLE_KEY=pk_test_your_key_here
VITE_API_BASE_URL=http://localhost:8000/v1
```

### 3. Test Authentication

```bash
npm run dev
```

Visit http://localhost:5173 and click "Sign Up"

**For detailed instructions, see [AUTH_QUICK_START.md](AUTH_QUICK_START.md)**

## 🧪 Testing

```bash
# Run tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage
```

## 🏗️ Building

```bash
# Build for production
npm run build

# Preview production build
npm run preview

# Build for development (with source maps)
npm run build:dev
```

## 📝 Scripts

| Script | Description |
|--------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run build:dev` | Build for development |
| `npm run preview` | Preview production build |
| `npm test` | Run tests |
| `npm run test:watch` | Run tests in watch mode |
| `npm run lint` | Lint code |

## 🌍 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_CLERK_PUBLISHABLE_KEY` | Yes* | Clerk authentication key |
| `VITE_API_BASE_URL` | No | Backend API URL (default: production API) |
| `VITE_CLERK_SIGN_IN_URL` | No | Sign-in page URL (default: `/sign-in`) |
| `VITE_CLERK_SIGN_UP_URL` | No | Sign-up page URL (default: `/sign-up`) |
| `VITE_CLERK_AFTER_SIGN_IN_URL` | No | Redirect after sign-in (default: `/discover`) |
| `VITE_CLERK_AFTER_SIGN_UP_URL` | No | Redirect after sign-up (default: `/discover`) |

*Required for authentication to work. App runs in dev mode without it.

## 🎨 Customization

### Theme

The app supports dark and light themes. Theme preference is saved to localStorage.

### Components

UI components are built with Radix UI and styled with Tailwind CSS. Customize in:
- `src/components/ui/` - Component implementations
- `tailwind.config.ts` - Theme configuration
- `src/index.css` - Global styles

### Authentication UI

Customize Clerk components in:
- `src/pages/SignIn.tsx` - Sign-in page
- `src/pages/SignUp.tsx` - Sign-up page

## 🐛 Troubleshooting

### Authentication Issues

See [AUTHENTICATION.md](AUTHENTICATION.md) → Troubleshooting section

### Common Issues

**Port already in use**
```bash
# Kill process on port 5173
npx kill-port 5173
```

**Module not found**
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

**Build errors**
```bash
# Clear Vite cache
rm -rf node_modules/.vite
npm run dev
```

## 📦 Dependencies

### Core
- `react` - UI library
- `react-dom` - React DOM renderer
- `react-router-dom` - Routing
- `@tanstack/react-query` - Data fetching

### Authentication
- `@clerk/clerk-react` - Authentication

### UI
- `@radix-ui/*` - Headless UI components
- `tailwindcss` - Utility-first CSS
- `lucide-react` - Icons
- `sonner` - Toast notifications

### Forms
- `react-hook-form` - Form management
- `zod` - Schema validation

### Utilities
- `date-fns` - Date utilities
- `clsx` - Class name utilities
- `tailwind-merge` - Tailwind class merging

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## 📄 License

See LICENSE file for details.

## 🔗 Links

- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/v1/docs
- **Clerk Dashboard**: https://dashboard.clerk.com

## 💬 Support

- **Documentation**: See docs in this directory
- **Issues**: Create a GitHub issue
- **Questions**: Ask in team chat

---

**Built with ❤️ by the MueJam team**
