# TASKS.md — InterviewPrep AI · Sprint Board
# Claude Code: update this file after completing EVERY task.
# Format: move task from [ ] to [x] and add a one-line note.
# Owner reviews this to know what's done and what's next.

## HOW TO USE
- Before starting: read this file to find your next task
- After finishing: mark [x] and note what you built/changed
- If blocked: mark [~] and write why, then skip to next task
- Never delete completed tasks — they are the build history

---

## PHASE 1 — Foundation (Do these first, in order)

- [x] P1-1: Create `supabase/migrations/001_initial_schema.sql` from PLANNING.md §Schema
        Done: full schema with all 6 tables + RLS policies
- [x] P1-2: Rewrite `app/main.py` — add CORS, health endpoint
        Done: FastAPI app with CORS middleware, /health endpoint, router mounted at /api/v1
- [x] P1-3: Rewrite `app/schemas.py` — all Pydantic models
        Done: InterviewMode enum, GenerateQuestionsRequest, EvaluateAnswerRequest, STARScore, CommunityQuestionSubmit
- [x] P1-4: Rewrite `app/services.py` — all Claude API functions
        Done: generate_questions, evaluate_answer_star, evaluate_rapid_answer, detect_weakness_patterns using claude-sonnet-4-20250514
- [x] P1-5: Rewrite `app/api.py` — all FastAPI routes
        Done: /questions/generate, /answers/evaluate, /answers/evaluate-rapid, /weakness/analyse, /community/* stubs
- [x] P1-6: Update `requirements.txt`
        Done: pinned versions for fastapi, uvicorn, anthropic, pydantic, supabase, etc.
- [x] P1-7: Create `.env.example`
        Done: all 7 env vars documented with placeholder values
- [x] P1-8: Create `Procfile`
        Done: uvicorn Railway deploy command

## PHASE 2 — Frontend Setup

- [x] P2-1: Scaffold Next.js 14 in `/frontend` (commands in PLANNING.md §Frontend)
        Done: Next.js 16.2.6 + shadcn/ui (base-ui variant) + all components + extra packages installed
- [x] P2-2: Create `frontend/lib/types.ts`
        Done: Question, STARScore, WeaknessSummary, QuestionType, InterviewMode
- [x] P2-3: Create `frontend/lib/claude.ts` (API wrapper functions)
        Done: generateQuestions, evaluateAnswer, evaluateRapidAnswer, analyseWeakness
- [x] P2-4: Create `frontend/lib/supabase.ts`
        Done: Supabase client using NEXT_PUBLIC_ env vars
- [x] P2-5: Create `frontend/app/layout.tsx` (nav + root layout)
        Done: Inter font, nav with 4 links (Mock, Rapid, Questions, Dashboard)

## PHASE 3 — Core Components

- [x] P3-1: Create `frontend/components/VoiceRecorder.tsx`
        Done: Web Speech API, lang: en-IN, continuous interim results, typed without `any`
- [x] P3-2: Create `frontend/components/STARScoreCard.tsx`
        Done: 4 progress bars (S/T/A/R), weakness badges, feedback panel, ideal answer collapsible
- [x] P3-3: Create `frontend/components/RapidFireTimer.tsx`
        Done: conic-gradient countdown, green→amber→red colour shift, onTimeUp callback

## PHASE 4 — Pages

- [x] P4-1: Create `frontend/app/page.tsx` (landing — 5 USP cards)
        Done: dark gradient hero, 5 USP cards, CTA links to /mock and /rapid
- [x] P4-2: Create `frontend/app/mock/page.tsx` (JD upload form)
        Done: role/company/JD/resume form, generates questions, stores in sessionStorage
- [x] P4-3: Create `frontend/app/mock/session/page.tsx` (active interview)
        Done: progress bar, question card, voice+text input, STAR scoring, next/finish flow
- [x] P4-4: Create `frontend/app/rapid/page.tsx` (rapid fire mode)
        Done: intro/playing/done phases, 6s timer, 10 questions, auto-advance, colour-coded results
- [x] P4-5: Create `frontend/app/questions/page.tsx` (community bank — stub OK)
        Done: stub with "Coming Soon / Phase 2" card
- [x] P4-6: Create `frontend/app/dashboard/page.tsx` (stub — reads ip_scores from sessionStorage)
        Done: reads sessionStorage, shows avg score, weakness tag counts, answer history

## PHASE 5 — Integration & Deploy

- [~] P5-1: End-to-end test: JD upload → question gen → voice answer → STAR score
        E2E test pending deployment. Backend + frontend must both be running.
- [~] P5-2: Deploy backend to Railway
        Owner action: Railway → New Project → connect GitHub → root=. → add 7 env vars from .env.example → deploy
- [~] P5-3: Deploy frontend to Vercel
        Owner action: cd frontend && vercel → add 3 NEXT_PUBLIC_ env vars → deploy
- [~] P5-4: Update `NEXT_PUBLIC_API_URL` in Vercel env vars to Railway URL
        Owner action: Vercel dashboard → set NEXT_PUBLIC_API_URL to Railway backend URL
- [~] P5-5: Smoke test on live URLs
        Owner action: visit live URLs → run a mock session → confirm STAR score returns

## PHASE 6 — Auth & Persistence (Post-MVP)

- [ ] P6-1: Enable Supabase Google OAuth
- [ ] P6-2: Add auth to frontend (login page, session guard)
- [ ] P6-3: Save sessions + answers to Supabase on completion
- [ ] P6-4: Build dashboard with real data from Supabase
- [ ] P6-5: Wire up weakness/analyse endpoint with DB data

---

## ENV SECURITY (completed 2026-05-23)

- [x] ENV-1: Audit all source files for hardcoded secrets
        Done: no hardcoded keys found; all vars already read from env
- [x] ENV-2: Update `.env.example` with comments explaining where to get each value
        Done: all 8 vars documented with exact source (Anthropic console / Supabase Dashboard paths)
- [x] ENV-3: Add startup env validator to `app/main.py`
        Done: _validate_env() runs before app init; sys.exit with readable message listing missing vars + sources
- [x] ENV-4: Create `frontend/lib/env.ts` — frontend startup validator
        Done: throws on module load if any NEXT_PUBLIC_* var missing; explicit references for Next.js static inlining
- [x] ENV-5: Update `frontend/lib/supabase.ts` and `frontend/lib/claude.ts` to use env.ts
        Done: removed ! assertions and ?? fallbacks; both modules now import from validated env object

## COMPLETED
- [x] SYS-1: Migrate to indexed context system
      Done: PLANNING.md sliced into 14 docs/ files. CLAUDE.md redesigned as
      pointer index (~98 lines). Cold-start context reduced from ~1100 to ~130
      lines for bug fixes. PLANNING.md archived in place with header note.

- [x] FIX-1: Wrap all json.loads() calls in try/except json.JSONDecodeError in app/services.py
        Done: all 4 functions (generate_questions, evaluate_answer_star, evaluate_rapid_answer, detect_weakness_patterns) now raise ValueError with truncated AI response on parse failure
- [x] FIX-2: Reconcile CLAUDE.md AI stack reference — was "Claude Sonnet", now correctly says "gemini-2.5-flash via google-generativeai"
        Done: LAST UPDATED line updated; AI line in TECH STACK reflects Gemini
- [x] FIX-3: Recreate .env.example with all 7 required vars and source comments
        Done: GEMINI_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY, FRONTEND_URL, NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY, NEXT_PUBLIC_API_URL — all with instructions
- [x] FIX-4: Wire community endpoints to real Supabase queries instead of hardcoded stubs
        Done: get_community_questions + submit_community_question in services.py; api.py routes call them; frontend/lib/claude.ts has getCommunityQuestions + submitCommunityQuestion; questions/page.tsx is a full real page
- [x] FIX-5: Dashboard — real session data + Recharts chart + weakness analysis API call
        Done: BarChart with colour-coded cells, analyseWeakness() integration, ip_context display, empty state CTA
- [x] FIX-6: Backend env validator already checks GEMINI_API_KEY — confirmed correct, no change needed
        Done: _validate_env() in app/main.py covers all 3 required backend vars
- [x] FIX-7: Frontend env validator already uses explicit process.env.NEXT_PUBLIC_* references — confirmed correct, no change needed
        Done: env.ts reads each var explicitly for Next.js static inlining; no dynamic access
- [x] FIX-8: Mark Phase 5 tasks as [~] with owner deployment instructions
        Done: P5-1 through P5-5 all marked [~] with exact steps for Railway + Vercel deploy

- 2026-05-23: All Phase 1–4 tasks completed. Backend scaffold + full frontend built. TypeScript: zero errors.
- 2026-05-23: Env security hardening done. Startup validators on both backend and frontend. No secrets ever logged.
- 2026-05-23: Switched AI backend from Anthropic SDK to Google Gemini 1.5 Flash (free tier). Updated services.py, requirements.txt, env validator, .env.example. Same JSON output contract preserved.
- 2026-05-28: Audit fixes FIX-1 through FIX-8 completed. All json.loads() crash-safe. Community endpoints wired to Supabase. Dashboard has real charts + AI weakness analysis. TypeScript: zero errors.

---

## BLOCKED / NEEDS OWNER DECISION
<!-- Claude Code adds items here when stuck -->
