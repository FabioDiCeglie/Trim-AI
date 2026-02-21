# Trim Frontend

React frontend for Trim — cloud waste detection. Deploys to **Cloudflare Pages**.

## Setup

```bash
cd frontend
npm install
cp .env.example .env
# Optional: set VITE_API_URL to override default (http://localhost:8787)
```

## Dev

```bash
npm run dev
```

Open http://localhost:5173. Ensure the Trim worker is running (e.g. `cd ../worker && npx wrangler dev`) and `VITE_API_URL` points to it.

## Build

```bash
npm run build
```

Output is in `dist/`.

## Deploy to Cloudflare Pages

1. In Cloudflare Dashboard: **Pages** → **Create project** → **Connect to Git** (or **Direct Upload**).
2. If using Git:
   - **Build configuration**: Root directory = `frontend`
   - **Build command**: `npm run build`
   - **Build output directory**: `dist`
3. **Environment variables**: Add `VITE_API_URL` = your Trim worker URL (e.g. `https://trim-worker.<your-subdomain>.workers.dev`).

After deploy, the frontend will call the worker at `VITE_API_URL` (or default) for connect, overview, and chat.
