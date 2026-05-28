## §Frontend — Next.js 14

### Setup commands (run once)
```bash
mkdir frontend && cd frontend
npx create-next-app@latest . --typescript --tailwind --app --no-src-dir --import-alias "@/*"
npx shadcn@latest init --defaults
npx shadcn@latest add button card input textarea badge progress toast tabs
npm install @supabase/supabase-js recharts lucide-react react-dropzone
```

