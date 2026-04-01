# canvas-chat-2

Canvas Chat v2 live-coded

Made with ❤️ by Eric Ma (@ericmjl).

## Get started for development

To get started:

```bash
git clone git@github.com:ericmjl/canvas-chat-2
cd canvas-chat-2
pixi install
```

## Canvas Chat MVP (FastAPI + SvelteKit)

This repository now includes:

- Backend API: `canvas_chat_2/api` (FastAPI + SQLite + LiteLLM)
- Frontend UI: `frontend` (SvelteKit + Svelte Flow)

### 1) Configure environment

```bash
cp .env.example .env
```

Set at least one provider API key in `.env` (for example `OPENAI_API_KEY`) and keep:

- `CANVAS_CHAT_DEFAULT_PROVIDER_ID`
- `CANVAS_CHAT_DEFAULT_LITELLM_MODEL`

aligned with a provider/model you want to use.

### 2) Run backend

```bash
pixi run python -m uvicorn canvas_chat_2.api.main:app --reload --host 127.0.0.1 --port 8000
```

### 3) Run frontend

```bash
cd frontend
npm run dev
```

Open the URL from the SvelteKit dev server (usually `http://localhost:5173`).

Or run both backend + frontend from repo root:

```bash
pixi run dev-canvas
```

### 4) Run tests/checks

Backend:

```bash
pixi run ruff check canvas_chat_2 tests
pixi run test
```

Frontend:

```bash
cd frontend
npm run check
```
