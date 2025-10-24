# Porte Hobe AI - Frontend

An AI-powered personalized tutoring platform built with Next.js 15, featuring autonomous AI assistance for programming and mathematics education.

## 🚀 Features

- **Autonomous AI Tutor**: Real-time chat with AI-powered tutoring
- **Personalized Learning**: Adaptive content based on user progress
- **Memory System**: Persistent learning context across sessions
- **Modern UI**: Beautiful, responsive design with dark mode support
- **Secure Authentication**: Complete Supabase authentication integration

## 🔐 Authentication

This application requires users to login/signup before accessing the platform. Features include:

- ✅ Email/Password authentication
- ✅ Protected routes with middleware
- ✅ Server-side session validation
- ✅ JWT token-based API protection
- ✅ Real-time auth state management
- ✅ Secure cookie handling

**Quick Links:**
- 📖 [Authentication Documentation](../AUTHENTICATION.md)
- 🚀 [Quick Start Guide](../QUICKSTART.md)
- 📋 [Implementation Summary](../IMPLEMENTATION_SUMMARY.md)

## 🛠️ Tech Stack

- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: Radix UI + shadcn/ui
- **Authentication**: Supabase Auth
- **Database**: Supabase (PostgreSQL)
- **Backend**: FastAPI (Python)
- **State Management**: Zustand + React Context

## 📋 Prerequisites

- Node.js 18+ 
- npm/yarn/pnpm
- Supabase account and project
- FastAPI backend running (see `/server`)

## 🚀 Getting Started

### 1. Install Dependencies

```bash
npm install
```

### 2. Environment Setup

Create a `.env.local` file:

```bash
NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
NEXT_PUBLIC_FASTAPI_URL=http://localhost:8000
```

### 3. Run Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to see the application.

### 4. Test Authentication

1. Visit the homepage
2. Click "Get Started" to create an account
3. Sign up with email and password
4. Access the dashboard and chat features

## 📁 Project Structure

```
frontend/
├── app/
│   ├── (home)/          # Public pages (home, login, signup)
│   ├── dashboard/       # Protected dashboard pages
│   ├── api/            # API routes (chat, memory)
│   └── layout.tsx      # Root layout with providers
├── components/
│   ├── auth-provider.tsx  # Auth context provider
│   ├── homepage/        # Homepage components
│   └── ui/             # shadcn/ui components
├── lib/
│   └── supabase/       # Supabase client utilities
│       ├── client.ts   # Browser client
│       └── server.ts   # Server client
└── middleware.ts       # Route protection middleware
```

## 🔒 Protected Routes

The following routes require authentication:
- `/dashboard/*` - All dashboard pages
- `/api/*` - All API endpoints

Unauthenticated users are automatically redirected to `/login`.

## 🎨 UI Components

This project uses:
- **shadcn/ui**: High-quality, accessible components
- **Radix UI**: Unstyled, accessible component primitives
- **Tailwind CSS**: Utility-first CSS framework
- **Lucide Icons**: Beautiful, consistent icons

## 📝 Available Scripts

```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
```

## 🔧 Configuration

### Supabase Setup

1. Create a project at [supabase.com](https://supabase.com)
2. Enable Email authentication
3. Configure redirect URLs
4. Copy project URL and anon key to `.env.local`

See [QUICKSTART.md](../QUICKSTART.md) for detailed setup instructions.

### Backend Integration

The frontend communicates with a FastAPI backend for:
- Chat completions (streaming)
- Memory storage and retrieval
- User session management

Ensure the backend is running and the `NEXT_PUBLIC_FASTAPI_URL` is set correctly.

## 🚢 Deployment

### Vercel (Recommended)

1. Push your code to GitHub
2. Import project in Vercel
3. Add environment variables
4. Deploy!

### Other Platforms

This is a standard Next.js app and can be deployed to:
- AWS Amplify
- Netlify
- Railway
- Your own server with Docker

## 📚 Learn More

- [Next.js Documentation](https://nextjs.org/docs)
- [Supabase Documentation](https://supabase.com/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [shadcn/ui](https://ui.shadcn.com)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is part of CSE499A-B coursework.

## 🆘 Support

For issues and questions:
- Check the [Quick Start Guide](../QUICKSTART.md)
- Review [Authentication Documentation](../AUTHENTICATION.md)
- Open an issue on GitHub
