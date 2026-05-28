# Reef — Frontend

React + TypeScript dashboard for the [Pirates of the Coral-bean](../README.md) incident intelligence agent.  
Backend API: `backend/README.md` · Architecture: `docs/architecture_diagram.txt`

---

## Prerequisites

| Tool | Version |
|------|---------|
| Node.js | >= 20 |
| pnpm | >= 9 |

---

## Quick start

```bash
cd frontend
pnpm install
pnpm dev
```

Runs at `http://localhost:5173`.

| Command | Description |
|---------|-------------|
| `pnpm dev` | Start dev server with HMR |
| `pnpm build` | Production build to `dist/` |
| `pnpm preview` | Preview production build locally |
| `pnpm lint` | Run ESLint |

---

## Environment variables

Create a `.env` file in this directory:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

If omitted, API calls are made relative to the current origin (suitable when the frontend is served behind a reverse proxy alongside the backend).

---

## Project structure

```text
frontend/
├── index.html
├── vite.config.ts
└── src/
    ├── api/              # Typed fetch wrappers (investigations, triggers)
    ├── components/       # Shared UI components
    ├── contexts/         # InvestigationContext, ThemeContext
    ├── hooks/            # useInvestigation, useTheme, useFontSize
    ├── layout/           # Header, page shell
    ├── pages/            # Route-level page components
    ├── types/            # Shared TypeScript types
    ├── routes.tsx         # React Router v7 route definitions
    ├── App.tsx
    └── index.css         # Global styles and design tokens
```

---

## Routes

| Path | Page |
|------|------|
| `/` | Home — investigation form and history |
| `/report/:reportId` | Report view (direct URL access) |
| `/:orgId` | Org dashboard |
| `/:orgId/report/:reportId` | Report view scoped to org |
| `/login` | Sign in |
| `/signup` | Create account |
