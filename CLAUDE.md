# CLAUDE.md — InterviewPrep AI · Master Index
# Auto-loaded every session. Stays under 100 lines. Never bloat this file.
# All specs live in docs/. Read this index first, then fetch only what you need.

## IDENTITY
Sole engineer on InterviewPrep AI. Constraints: free tiers only, Claude Code Pro.
Every decision: free → simple → scalable. No paid services. No over-engineering.

## APP IN ONE PARAGRAPH
AI interview prep for Indian job seekers. 5 USPs: (1) JD → 20 custom questions <10s,
(2) voice mock interview + STAR scoring 0-100, (3) cross-session weakness tracker,
(4) crowdsourced company question bank, (5) 60-second rapid fire mode.
Voice: Web Speech API, lang='en-IN'. Target: freshers, career switchers.

## TECH STACK (locked — owner approval to change)
Frontend : Next.js 14, TypeScript strict, Tailwind, shadcn/ui → Vercel
Backend  : FastAPI Python 3.11, app/ scaffold → Railway free tier
Database : Supabase (Postgres + RLS + Auth)
AI       : gemini-2.5-flash via google-generativeai — ALL AI calls in app/services.py
Voice    : Web Speech API (browser-native, zero cost)
Auth     : Supabase Auth, Google OAuth + Email (Phase 6)

## CODING RULES (non-negotiable)
- TypeScript: strict mode, no `any`, no `@ts-ignore`
- AI calls: backend only in app/services.py · frontend only in frontend/lib/claude.ts
- Every json.loads() wrapped in try/except json.JSONDecodeError
- Supabase RLS ON for every table, never bypass
- No secrets in code — all via env vars (see docs/deploy.md)
- Components: functional + hooks only, no class components
- Every page: must have loading state + error state
- Voice: always lang='en-IN'

## WEAKNESS TAGS (canonical — never add new ones)
missing_situation | missing_task | missing_action | missing_result
too_vague | over_explains | no_quantified_impact | no_technical_depth
rambling | skips_conclusion | overconfident | underconfident

## TEST COMMANDS
```bash
python -m py_compile app/services.py app/api.py app/main.py  # backend syntax
cd frontend && npx tsc --noEmit                               # frontend types
uvicorn app.main:app --reload                                 # run backend
cd frontend && npm run dev                                    # run frontend
```

## ALWAYS DO
- Read this file first (auto-loaded)
- Lookup the INDEX below → fetch only the doc(s) for your task
- Update TASKS.md after every task (mark [x] with one-line note)

## NEVER DO
- Load docs/ files not listed for your task type — wasted context
- Invent architecture not in docs/ — add `# TODO: owner decision` and move on
- Load docs/frontend-pages.md for a backend bug fix
- Load docs/backend.md for a frontend component tweak

---

## 📋 CONTEXT INDEX — look up your task type, load only those files

| Task Type | Load These Files |
|-----------|-----------------|
| Bug fix / small edit | CLAUDE.md (auto) + the broken file only |
| New backend endpoint | docs/backend-api.md + docs/backend-schemas.md |
| New backend service (AI call) | docs/backend-services.md + docs/ai-prompts.md |
| New frontend page | docs/frontend-pages.md + docs/frontend-lib.md |
| New frontend component | docs/frontend-components.md |
| Database change | docs/schema.md |
| Auth / Supabase wiring | docs/schema.md + docs/backend-api.md |
| Deployment / infra / env vars | docs/deploy.md |
| Phase 2+ roadmap feature | docs/roadmap.md → then lookup specific doc above |
| Full rebuild from scratch | ALL docs/ files (last resort only) |
| AI prompt tuning | docs/ai-prompts.md + docs/backend-services.md |
| Frontend lib (types/api wrapper) | docs/frontend-lib.md |
| Requirements / dependencies | docs/backend-requirements.md |

## 📁 DOCS DIRECTORY (what lives where)
```
docs/
├── schema.md               — 6 Supabase tables + RLS policies (99 lines)
├── backend.md              — full backend spec (260 lines) [fallback only]
├── backend-api.md          — api.py routes only (53 lines)
├── backend-schemas.md      — schemas.py Pydantic models (43 lines)
├── backend-services.md     — services.py AI functions (123 lines)
├── backend-requirements.md — requirements.txt pinned versions (11 lines)
├── frontend.md             — full frontend spec (592 lines) [fallback only]
├── frontend-setup.md       — Next.js scaffold commands (11 lines)
├── frontend-lib.md         — types.ts + claude.ts + supabase.ts (77 lines)
├── frontend-components.md  — VoiceRecorder, STARScoreCard, RapidFireTimer (144 lines)
├── frontend-pages.md       — all 6 page specs (360 lines)
├── deploy.md               — env vars, Procfile, Railway + Vercel steps (28 lines)
├── ai-prompts.md           — prompt rules, JSON contract, token limits (13 lines)
└── roadmap.md              — Phase 2+ features in priority order (8 lines)
```

## LAST UPDATED
2026-05-28: CLAUDE.md redesigned as pointer index. PLANNING.md sliced into docs/.
            AI stack updated to Gemini 2.5 Flash. database.py reference removed.
