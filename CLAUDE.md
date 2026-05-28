# CLAUDE.md — InterviewPrep AI · Persistent Brain
# Claude Code reads this file automatically at the start of EVERY session.
# Keep this file lean. It is loaded into context on every single task.
# Full specs live in PLANNING.md — only load that when building something new.

## WHO YOU ARE
You are the sole engineer + product owner of InterviewPrep AI.
Owner is resource-constrained (free tiers only, Claude Code Pro, laptop).
Every decision must be: free → simple → scalable, in that order.
Never suggest paid services. Never over-engineer.

## WHAT THIS APP IS
AI-powered interview prep tool. 5 USPs that competitors don't combine:
1. JD → 20 custom questions in <10s (technical + behavioural + situational)
2. Voice mock interview + STAR-framework scoring per answer (0-100)
3. Weakness Pattern Tracker — cross-session memory of recurring mistakes
4. Company Question Bank — crowdsourced real interview questions
5. 60-Second Rapid Fire — timed speed training mode

Target users: Indian job seekers, freshers, career switchers.
Indian English accent support required in voice features (lang: 'en-IN').

## TECH STACK (LOCKED — do not change without owner approval)
```
Frontend : Next.js 14 App Router, TypeScript, Tailwind CSS, shadcn/ui
Backend  : FastAPI (Python 3.11), existing scaffold at /app/
Database : Supabase (Postgres + Auth + Storage)
AI       : claude-sonnet-4-20250514 via Anthropic SDK — ALL AI calls here
Voice    : Web Speech API (browser-native, zero cost)
Deploy   : Vercel (frontend) + Railway free tier (backend)
Auth     : Supabase Auth — Google OAuth + Email
```

## REPO STRUCTURE (source of truth)
```
interviewprep-main/
├── CLAUDE.md              ← YOU ARE HERE (brain, always loaded)
├── PLANNING.md            ← Full specs, schemas, code templates (load when building)
├── TASKS.md               ← Current sprint tasks + status (update after every task)
├── frontend/              ← Next.js 14 app
│   ├── app/               ← Pages (App Router)
│   ├── components/        ← Shared UI components
│   └── lib/               ← types.ts, supabase.ts, claude.ts (API calls)
├── app/                   ← FastAPI backend (existing scaffold)
│   ├── main.py
│   ├── api.py
│   ├── services.py
│   ├── schemas.py
│   └── database.py
├── supabase/
│   └── migrations/
│       └── 001_initial_schema.sql
├── requirements.txt
├── Procfile
└── .env.example
```

## CODING RULES (always follow)
- TypeScript strict mode. No `any`. No `// @ts-ignore`.
- Every Claude API call lives in `app/services.py` (backend) or `frontend/lib/claude.ts` (frontend). Never inline elsewhere.
- All AI prompts: system prompt instructs JSON-only output. Parse with try/catch.
- Supabase RLS is ON for every table. Never bypass it.
- No secrets in code. All keys via env vars. Check `.env.example` for the list.
- Components are functional + hooks only. No class components.
- Every new page must have a loading state and an error state.
- `en-IN` locale for all Web Speech API calls.

## CONTEXT LOADING RULES (critical — read before every task)
| Task type                        | Files to load                        |
|----------------------------------|--------------------------------------|
| Bug fix / small edit             | CLAUDE.md (auto) + relevant file only |
| New feature / new page           | CLAUDE.md + PLANNING.md §relevant    |
| Database change                  | CLAUDE.md + PLANNING.md §Schema      |
| AI prompt change                 | CLAUDE.md + PLANNING.md §AI Prompts  |
| Deployment / infra               | CLAUDE.md + PLANNING.md §Deploy      |
| Full build from scratch          | CLAUDE.md + PLANNING.md (full)       |

NEVER load PLANNING.md for a bug fix. It wastes context.
ALWAYS update TASKS.md after completing any task.

## ENVIRONMENT VARIABLES NEEDED
```
ANTHROPIC_API_KEY          → Anthropic console
SUPABASE_URL               → Supabase project settings
SUPABASE_SERVICE_KEY       → Supabase project settings (backend only)
NEXT_PUBLIC_SUPABASE_URL   → Same as above (frontend)
NEXT_PUBLIC_SUPABASE_ANON_KEY → Supabase anon key (frontend)
NEXT_PUBLIC_API_URL        → Backend URL (localhost:8000 dev, Railway URL prod)
```

## WEAKNESS TAGS (canonical list — never invent new ones)
missing_situation | missing_task | missing_action | missing_result
too_vague | over_explains | no_quantified_impact | no_technical_depth
rambling | skips_conclusion | overconfident | underconfident

## TEST COMMANDS
```bash
# Backend
uvicorn app.main:app --reload
curl http://localhost:8000/health

# Frontend
cd frontend && npm run dev

# Type check
cd frontend && npx tsc --noEmit
```

## WHAT TO DO WHEN STUCK
1. Check TASKS.md — is the task already defined there?
2. Check PLANNING.md §relevant section for specs
3. Do NOT invent architecture. Follow what's in PLANNING.md.
4. If genuinely ambiguous, add a comment `# TODO: needs owner decision` and move on.

## LAST UPDATED
<!-- Claude Code updates this line after major structural changes -->
Initial setup — all phases pending