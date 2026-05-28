## §Deploy — Deployment Instructions

### .env.example
```
# Backend
ANTHROPIC_API_KEY=sk-ant-...
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
FRONTEND_URL=https://your-app.vercel.app

# Frontend
NEXT_PUBLIC_SUPABASE_URL=https://xxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
NEXT_PUBLIC_API_URL=https://your-backend.railway.app/api/v1
```

### Procfile (Railway backend)
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Deploy order
1. Supabase: create project → run 001_initial_schema.sql in SQL Editor → enable Google OAuth
2. Railway: connect repo → set root=. → set start command from Procfile → add env vars
3. Vercel: `cd frontend && vercel` → add env vars → set NEXT_PUBLIC_API_URL to Railway URL

---

