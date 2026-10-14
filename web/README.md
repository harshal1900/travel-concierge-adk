# Web client

Small Next.js chat UI (prompt-kit components). The browser calls the Next.js route `app/api/chat/route.ts`, which calls the FastAPI service; `API_BASE_URL` and `SERVICE_API_KEY` are read server-side only.

```bash
cp .env.example .env.local   # set API_BASE_URL (and SERVICE_API_KEY if the API requires it)
npm install
npm run dev                  # http://localhost:3000
npm run build
```
