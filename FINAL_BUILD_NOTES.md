# NUDGE Final Build

This package is the cleaned final source build.

## Important behavior
- Browser demo workspace state persists across refreshes and NEW RUN.
- Approved follow-ups remain `FOLLOW-UP SENT` on subsequent runs.
- The backend also consumes the browser-carried synthetic workspace state, so a new run does not rediscover an already handled invoice.
- `RESET DEMO` intentionally restores the original synthetic fixture.
- Human approval remains required before risky actions.

## Secrets
`backend/.env` is intentionally not included. Use `backend/.env.example` for the variable name and configure the real `GEMINI_API_KEY` only in your local environment or deployment provider.

## Frontend
From `frontend`:
- `npm install`
- `npm run dev` for local development
- `npm run build` for a production build

## Backend
From `backend` with the required Python environment and dependencies installed:
- `python app.py`
