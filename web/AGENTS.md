# PROJECT KNOWLEDGE BASE

**Generated:** 2026-03-15
**Commit:** a02750b
**Branch:** main

## OVERVIEW

Next.js 16 frontend with React 19 and TanStack Query. Provides UI for Claude Assistant with real-time SSE streaming, project/workspace management, and AI resource browsing.

## STRUCTURE

```
./
├── app/                # Next.js App Router pages
│   ├── layout.tsx      # Root layout with providers
│   ├── page.tsx        # Home page
│   └── ai-resources/   # AI resources browser page
├── components/         # React components
│   ├── layout/         # Layout components (Sidebar, Header)
│   └── ui/             # UI primitives (shadcn-based)
├── hooks/              # Custom React hooks (TanStack Query)
├── lib/                # Core libraries
│   ├── api/            # API client + types
│   ├── stores/         # Zustand stores
│   └── queryClient.tsx # React Query provider
└── public/             # Static assets
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add page | `app/*/page.tsx` | Next.js App Router convention |
| Add component | `components/` | layout/ or ui/ subdirs |
| Add API call | `lib/api/*.ts` | client.ts has base fetcher |
| Add React hook | `hooks/use*.ts` | TanStack Query pattern |
| Add state store | `lib/stores/*.ts` | Zustand stores |
| API types | `lib/api/types.ts` | Shared TypeScript types |
| SSE streaming | `lib/api/sse.ts` | EventSource wrapper |

## CONVENTIONS

- **Framework**: Next.js 16 App Router (`app/` directory)
- **React**: v19.2.3 with React DOM
- **Styling**: Tailwind CSS v4 + shadcn/ui components
- **State**: TanStack Query v5 for server state, Zustand v5 for client state
- **Path alias**: `@/*` maps to `web/` root
- **Package manager**: bun (bun.lock present)

## ANTI-PATTERNS (THIS PROJECT)

- **Never** use `any` type - define proper TypeScript types
- **Never** fetch directly in components - use hooks
- **Never** commit `node_modules/`
- **Never** bypass TanStack Query for server state

## UNIQUE STYLES

- **shadcn/ui**: Component library with Tailwind CSS
- **Base UI**: @base-ui/react for primitives
- **UUID v7**: uuidv7 package for time-sortable IDs
- **EventSource**: SSE client for real-time streaming
- **class-variance-authority**: CVA for component variants

## COMMANDS

```bash
# Setup
npm install

# Development
npm run dev          # Start dev server (port 3000)

# Build
npm run build        # Production build
npm run start        # Production server

# Quality
npm run lint         # ESLint
npm test             # Vitest
```

## NOTES

- Backend API expected at `http://localhost:8000`
- CORS configured on backend for `localhost:3000`
- Uses Next.js 16.1.6 with App Router
- React 19.2.3 (latest)
- TypeScript strict mode enabled
- Tailwind CSS v4 with @tailwindcss/postcss
