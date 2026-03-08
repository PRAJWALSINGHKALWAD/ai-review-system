# Frontend (React + Vite)

Minimal UI for interacting with the backend review workflow.

## Features

- Submit review (`POST /review`)
- Generate response (`POST /generate-response/{review_id}`)
- Request revision (`POST /request-revision`)
- Approve response (`POST /approve-response`)

## Setup

1. Ensure backend is running on `http://127.0.0.1:8000` or set `VITE_API_BASE_URL`.
2. Install dependencies and run:

```bash
npm install
npm run dev
```

## Build

```bash
npm run build
```
