# VeriGraph Frontend

React + Vite frontend for VeriGraph automated fact-checking system.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Create environment file:
```bash
cp .env.example .env
```

3. Update `.env` with your backend API URL (default is localhost:8000)

## Running the Development Server

```bash
npm run dev
```

The app will be available at http://localhost:5173

## Building for Production

### Build with production environment variables
```bash
# Using .env.prod
npm run build

# Or specify environment file
npm run build -- --mode production
```

### Preview production build locally
```bash
npm run preview
```

## Environment Variables

Vite requires environment variables to be prefixed with `VITE_` to be exposed to the client.

- `VITE_API_URL`: Backend API URL
  - Local: `http://localhost:8000`
  - Staging: `https://verigraph-api-staging.fly.dev`
  - Production: `https://verigraph-api.fly.dev`

### Environment Files

- `.env` - Local development (not committed)
- `.env.example` - Template for environment variables
- `.env.staging` - Staging environment (not committed)
- `.env.prod` - Production environment (not committed)

To use different environment files:
```bash
# Development (uses .env)
npm run dev

# Staging
npm run build -- --mode staging

# Production  
npm run build -- --mode production
```

## Technology Stack

- React 18
- Vite
- TailwindCSS
- React Router
- Lucide Icons

