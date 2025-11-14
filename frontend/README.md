# SchoolFlow — Frontend

Path: `C:\coding_projects\dev\schoolflow\frontend`

## Quick start (Windows PowerShell)

1. Ensure you are in the frontend folder:
```powershell
Set-Location "C:\coding_projects\dev\schoolflow\frontend"


Install dependencies (pnpm required):

pnpm install


Development:

pnpm dev


Build:

pnpm build
pnpm preview

Environment

Create a .env.local (or platform-specific env) with:

VITE_API_BASE=http://localhost:8000
VITE_RAZORPAY_KEY_ID=


If VITE_RAZORPAY_KEY_ID is empty, the UI shows Simulate Payment which calls the backend webhook.

DO NOT change backend .env from here.