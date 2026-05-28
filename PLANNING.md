# PLANNING.md — InterviewPrep AI · Full Specifications
# Load this file only when building new features or phases.
# For bug fixes, use only CLAUDE.md + the relevant file.
# Sections are tagged so you can load only what you need.

---

## §Schema — Supabase Database

File to create: `supabase/migrations/001_initial_schema.sql`

```sql
-- profiles: extends Supabase auth.users
create table profiles (
  id uuid references auth.users primary key,
  full_name text,
  target_role text,
  experience_years int,
  created_at timestamptz default now()
);

-- sessions: one per interview attempt
create table sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  mode text not null check (mode in ('mock', 'rapid', 'custom')),
  job_description text,
  target_company text,
  role text,
  started_at timestamptz default now(),
  completed_at timestamptz,
  overall_score int,
  weakness_tags text[]
);

-- questions: generated per session
create table questions (
  id uuid primary key default gen_random_uuid(),
  session_id uuid references sessions(id) on delete cascade,
  question_text text not null,
  question_type text check (question_type in ('technical','behavioural','situational','rapid')),
  order_index int,
  created_at timestamptz default now()
);

-- answers: user responses with STAR scores
create table answers (
  id uuid primary key default gen_random_uuid(),
  question_id uuid references questions(id) on delete cascade,
  user_id uuid references profiles(id),
  answer_text text,
  answer_audio_url text,
  star_situation_score int,  -- 0-25 each
  star_task_score int,
  star_action_score int,
  star_result_score int,
  total_score int,            -- 0-100
  feedback_text text,
  ideal_answer text,
  weakness_tags text[],
  answered_at timestamptz default now()
);

-- community_questions: crowdsourced real interview Q's
create table community_questions (
  id uuid primary key default gen_random_uuid(),
  submitted_by uuid references profiles(id),
  company text,
  role text,
  question_text text not null,
  question_type text,
  verified boolean default false,
  upvotes int default 0,
  created_at timestamptz default now()
);

-- weakness_summary: aggregated per user across all sessions
create table weakness_summary (
  user_id uuid references profiles(id) primary key,
  top_weaknesses jsonb,  -- {"missing_result": 12, "over_explains": 8}
  total_sessions int default 0,
  total_questions_answered int default 0,
  updated_at timestamptz default now()
);

-- RLS
alter table profiles enable row level security;
alter table sessions enable row level security;
alter table questions enable row level security;
alter table answers enable row level security;
alter table community_questions enable row level security;
alter table weakness_summary enable row level security;

create policy "own profile" on profiles for all using (auth.uid() = id);
create policy "own sessions" on sessions for all using (auth.uid() = user_id);
create policy "own session questions" on questions for select using (
  session_id in (select id from sessions where user_id = auth.uid())
);
create policy "own answers" on answers for all using (auth.uid() = user_id);
create policy "public verified questions" on community_questions for select using (verified = true);
create policy "submit questions" on community_questions for insert with check (auth.uid() = submitted_by);
create policy "own weakness summary" on weakness_summary for all using (auth.uid() = user_id);
```

---

## §Backend — FastAPI

### requirements.txt
```
fastapi==0.115.0
uvicorn[standard]==0.30.0
anthropic==0.40.0
pydantic==2.9.0
python-dotenv==1.0.1
supabase==2.9.0
python-multipart==0.0.12
httpx==0.27.0
```

### app/main.py
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import router
import os

app = FastAPI(title="InterviewPrep AI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        os.getenv("FRONTEND_URL", "https://your-app.vercel.app")
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")

@app.get("/health")
def health():
    return {"status": "ok"}
```

### app/schemas.py
```python
from pydantic import BaseModel
from typing import Optional, List
from enum import Enum

class InterviewMode(str, Enum):
    mock = "mock"
    rapid = "rapid"
    custom = "custom"

class GenerateQuestionsRequest(BaseModel):
    job_description: str
    resume_text: Optional[str] = None
    target_role: str
    target_company: Optional[str] = None
    mode: InterviewMode = InterviewMode.mock
    num_questions: int = 10

class EvaluateAnswerRequest(BaseModel):
    question: str
    answer: str
    question_type: str
    user_id: str

class STARScore(BaseModel):
    situation: int
    task: int
    action: int
    result: int
    total: int
    feedback: str
    ideal_answer: str
    weakness_tags: List[str]

class CommunityQuestionSubmit(BaseModel):
    company: str
    role: str
    question_text: str
    question_type: str
    submitted_by: str
```

### app/services.py
# ALL Claude API calls live here. Do not put AI logic anywhere else.
```python
import anthropic, json, os
from app.schemas import STARScore

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
MODEL = "claude-sonnet-4-20250514"

WEAKNESS_TAGS = [
    "missing_situation","missing_task","missing_action","missing_result",
    "too_vague","over_explains","no_quantified_impact","no_technical_depth",
    "rambling","skips_conclusion","overconfident","underconfident"
]

def generate_questions(jd, resume, role, company, num, mode) -> dict:
    prompt = f"""Generate {num} interview questions for this candidate.

Job Description: {jd}
Resume/Background: {resume or 'Not provided'}
Role: {role} | Company: {company or 'Unknown'} | Mode: {mode}

Return ONLY valid JSON, no markdown:
{{
  "questions": [
    {{
      "id": 1,
      "text": "...",
      "type": "technical|behavioural|situational",
      "difficulty": "easy|medium|hard",
      "hint": "What the interviewer is really testing",
      "time_estimate_seconds": 120
    }}
  ],
  "session_context": "One sentence about interview focus"
}}

Mix: 40% behavioural (STAR format), 40% technical (role-specific), 20% situational.
Rapid mode: all questions answerable in <15 seconds."""

    r = client.messages.create(
        model=MODEL, max_tokens=3000,
        system="You are an expert interviewer. Return valid JSON only. No markdown, no preamble.",
        messages=[{"role": "user", "content": prompt}]
    )
    return json.loads(r.content[0].text.strip())


def evaluate_answer_star(question, answer, q_type) -> STARScore:
    prompt = f"""Evaluate this answer against the STAR framework.

Question: {question}
Type: {q_type}
Answer: {answer}

Score each STAR component (25 pts each, total 100):
- Situation: Did they set clear context?
- Task: Did they explain their specific responsibility?
- Action: Did they describe what THEY did (not "we")?
- Result: Did they share measurable outcome?

Return ONLY valid JSON:
{{
  "situation": <0-25>,
  "task": <0-25>,
  "action": <0-25>,
  "result": <0-25>,
  "total": <0-100>,
  "feedback": "2-3 specific sentences on what was strong and what was missing",
  "ideal_answer": "A complete STAR-structured model answer in 4-5 sentences",
  "weakness_tags": ["tag1"]
}}

Available tags: {', '.join(WEAKNESS_TAGS)}
Max 3 tags. Only include tags that genuinely apply."""

    r = client.messages.create(
        model=MODEL, max_tokens=1000,
        system="You are an expert interview coach. Return valid JSON only.",
        messages=[{"role": "user", "content": prompt}]
    )
    return STARScore(**json.loads(r.content[0].text.strip()))


def evaluate_rapid_answer(question, answer) -> dict:
    prompt = f"""Question: {question}
Answer: {answer}

Score 0-100: keyword coverage + relevance + conciseness.
Return ONLY: {{"score": <int>, "feedback": "<one sentence>", "key_missed": "<concept or null>"}}"""

    r = client.messages.create(
        model=MODEL, max_tokens=150,
        system="Fast interview evaluator. JSON only.",
        messages=[{"role": "user", "content": prompt}]
    )
    return json.loads(r.content[0].text.strip())


def detect_weakness_patterns(tags_history: list[list[str]]) -> dict:
    from collections import Counter
    all_tags = [t for session in tags_history for t in session]
    counts = Counter(all_tags)
    explanations = {
        "missing_result": "You often skip the outcome — always end with impact",
        "missing_situation": "You don't set context before diving in",
        "missing_action": "You say 'we' but not what YOU specifically did",
        "over_explains": "Answers too long — practice 90-second rule",
        "no_quantified_impact": "Add numbers: %, ₹, time saved, users affected",
        "too_vague": "Use specific examples, not general statements",
        "no_technical_depth": "Go deeper on decisions and tradeoffs",
        "rambling": "Structure before speaking: Situation → Task → Action → Result",
        "skips_conclusion": "Always close with what you learned or the final outcome",
    }
    return {
        "top_weaknesses": [
            {"tag": t, "count": c, "explanation": explanations.get(t, t)}
            for t, c in counts.most_common(3)
        ],
        "total_answers_analysed": len(all_tags)
    }
```

### app/api.py
```python
from fastapi import APIRouter, HTTPException
from app.schemas import GenerateQuestionsRequest, EvaluateAnswerRequest, STARScore
from app import services

router = APIRouter()

@router.post("/questions/generate")
async def generate_questions(req: GenerateQuestionsRequest):
    try:
        return services.generate_questions(
            req.job_description, req.resume_text,
            req.target_role, req.target_company,
            req.num_questions, req.mode.value
        )
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/answers/evaluate", response_model=STARScore)
async def evaluate_answer(req: EvaluateAnswerRequest):
    try:
        return services.evaluate_answer_star(req.question, req.answer, req.question_type)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/answers/evaluate-rapid")
async def evaluate_rapid(req: EvaluateAnswerRequest):
    try:
        return services.evaluate_rapid_answer(req.question, req.answer)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/weakness/analyse")
async def analyse_weakness(payload: dict):
    try:
        return services.detect_weakness_patterns(payload["weakness_tags_history"])
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/community/questions")
async def get_community_questions(company: str = None, role: str = None, limit: int = 20):
    # TODO Phase 2: query Supabase community_questions table
    return {"questions": [], "total": 0}

@router.post("/community/submit")
async def submit_question(payload: dict):
    # TODO Phase 2: insert to community_questions, validate with Claude
    return {"status": "submitted", "message": "Under review"}
```

---

## §Frontend — Next.js 14

### Setup commands (run once)
```bash
mkdir frontend && cd frontend
npx create-next-app@latest . --typescript --tailwind --app --no-src-dir --import-alias "@/*"
npx shadcn@latest init --defaults
npx shadcn@latest add button card input textarea badge progress toast tabs
npm install @supabase/supabase-js recharts lucide-react react-dropzone
```

### frontend/lib/types.ts
```typescript
export type QuestionType = 'technical' | 'behavioural' | 'situational' | 'rapid'
export type InterviewMode = 'mock' | 'rapid' | 'custom'

export interface Question {
  id: number
  text: string
  type: QuestionType
  difficulty: 'easy' | 'medium' | 'hard'
  hint: string
  time_estimate_seconds: number
}

export interface STARScore {
  situation: number  // 0-25
  task: number
  action: number
  result: number
  total: number      // 0-100
  feedback: string
  ideal_answer: string
  weakness_tags: string[]
}

export interface WeaknessSummary {
  top_weaknesses: Array<{ tag: string; count: number; explanation: string }>
  total_answers_analysed: number
}
```

### frontend/lib/claude.ts
# All frontend→backend API calls live here only.
```typescript
const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1'

async function post(path: string, body: unknown) {
  const res = await fetch(`${API}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`API error ${res.status}: ${await res.text()}`)
  return res.json()
}

export const generateQuestions = (params: {
  job_description: string
  resume_text?: string
  target_role: string
  target_company?: string
  mode?: string
  num_questions?: number
}) => post('/questions/generate', { num_questions: 10, mode: 'mock', ...params })

export const evaluateAnswer = (params: {
  question: string; answer: string
  question_type: string; user_id: string
}) => post('/answers/evaluate', params)

export const evaluateRapidAnswer = (question: string, answer: string) =>
  post('/answers/evaluate-rapid', { question, answer, question_type: 'rapid', user_id: 'anon' })

export const analyseWeakness = (tags_history: string[][]) =>
  post('/weakness/analyse', { weakness_tags_history: tags_history })
```

### frontend/lib/supabase.ts
```typescript
import { createClient } from '@supabase/supabase-js'

export const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)
```

### frontend/components/VoiceRecorder.tsx
```typescript
'use client'
import { useState, useRef, useCallback } from 'react'
import { Mic, Square } from 'lucide-react'
import { Button } from '@/components/ui/button'

export default function VoiceRecorder({
  onTranscript, disabled
}: { onTranscript: (t: string) => void; disabled?: boolean }) {
  const [recording, setRecording] = useState(false)
  const [liveText, setLiveText] = useState('')
  const ref = useRef<SpeechRecognition | null>(null)

  const start = useCallback(() => {
    const SR = window.SpeechRecognition ?? window.webkitSpeechRecognition
    if (!SR) { alert('Voice not supported. Please type your answer.'); return }
    const r = new SR()
    r.continuous = true; r.interimResults = true; r.lang = 'en-IN'
    r.onresult = (e) => {
      let t = ''
      for (let i = 0; i < e.results.length; i++) t += e.results[i][0].transcript
      setLiveText(t)
    }
    r.start(); ref.current = r; setRecording(true)
  }, [])

  const stop = useCallback(() => {
    ref.current?.stop(); ref.current = null
    setRecording(false); onTranscript(liveText)
  }, [liveText, onTranscript])

  return (
    <div className="space-y-2">
      {!recording
        ? <Button onClick={start} disabled={disabled} className="gap-2 bg-red-500 hover:bg-red-600">
            <Mic className="w-4 h-4" /> Speak Answer
          </Button>
        : <Button onClick={stop} variant="outline" className="gap-2 animate-pulse">
            <Square className="w-4 h-4 fill-current" /> Stop & Score
          </Button>
      }
      {recording && liveText && (
        <p className="text-sm italic text-muted-foreground bg-muted p-2 rounded">"{liveText}"</p>
      )}
    </div>
  )
}
```

### frontend/components/STARScoreCard.tsx
```typescript
import { STARScore } from '@/lib/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'

const WEAKNESS_LABELS: Record<string, string> = {
  missing_result: '⚠ No Result', missing_situation: '⚠ No Context',
  over_explains: '⚠ Too Wordy', no_quantified_impact: '⚠ No Numbers',
  too_vague: '⚠ Too Vague', rambling: '⚠ Unfocused',
  no_technical_depth: '⚠ Needs Depth', missing_action: '⚠ No Action',
}

export default function STARScoreCard({ score }: { score: STARScore }) {
  const color = score.total >= 75 ? 'text-green-600' : score.total >= 50 ? 'text-yellow-600' : 'text-red-600'
  return (
    <Card className="mt-4">
      <CardHeader>
        <div className="flex justify-between items-center">
          <CardTitle>STAR Score</CardTitle>
          <span className={`text-3xl font-bold ${color}`}>{score.total}/100</span>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          {(['situation','task','action','result'] as const).map(k => (
            <div key={k} className="space-y-1">
              <div className="flex justify-between text-sm">
                <span className="capitalize font-medium">{k}</span>
                <span className="text-muted-foreground">{score[k]}/25</span>
              </div>
              <Progress value={(score[k] / 25) * 100} className="h-1.5" />
            </div>
          ))}
        </div>
        {score.weakness_tags.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {score.weakness_tags.map(t => (
              <Badge key={t} variant="destructive" className="text-xs">
                {WEAKNESS_LABELS[t] ?? t}
              </Badge>
            ))}
          </div>
        )}
        <div className="bg-muted rounded-lg p-3 text-sm space-y-1">
          <p className="font-medium">📝 Feedback</p>
          <p className="text-muted-foreground">{score.feedback}</p>
        </div>
        <details>
          <summary className="text-sm font-medium text-primary cursor-pointer hover:underline">
            ✨ See ideal answer
          </summary>
          <div className="mt-2 bg-green-50 dark:bg-green-950 rounded p-3 text-sm">
            {score.ideal_answer}
          </div>
        </details>
      </CardContent>
    </Card>
  )
}
```

### frontend/components/RapidFireTimer.tsx
```typescript
'use client'
import { useEffect, useState } from 'react'

export default function RapidFireTimer({
  totalSeconds, onTimeUp, isRunning
}: { totalSeconds: number; onTimeUp: () => void; isRunning: boolean }) {
  const [left, setLeft] = useState(totalSeconds)
  useEffect(() => { setLeft(totalSeconds) }, [totalSeconds])
  useEffect(() => {
    if (!isRunning || left <= 0) { if (left <= 0) onTimeUp(); return }
    const t = setTimeout(() => setLeft(l => l - 1), 1000)
    return () => clearTimeout(t)
  }, [left, isRunning, onTimeUp])
  const pct = (left / totalSeconds) * 100
  const c = pct > 50 ? '#22c55e' : pct > 25 ? '#f59e0b' : '#ef4444'
  return (
    <div className="flex items-center gap-2">
      <div className="relative w-14 h-14 rounded-full flex items-center justify-center"
        style={{ background: `conic-gradient(${c} ${pct*3.6}deg, #e5e7eb ${pct*3.6}deg)` }}>
        <div className="w-10 h-10 bg-background rounded-full flex items-center justify-center">
          <span className="text-base font-bold tabular-nums">{left}</span>
        </div>
      </div>
      <span className="text-xs text-muted-foreground">sec left</span>
    </div>
  )
}
```

### frontend/app/layout.tsx
```typescript
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import Link from 'next/link'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'InterviewPrep AI',
  description: 'AI-powered mock interviews with STAR scoring',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <nav className="border-b px-4 py-3 flex items-center justify-between">
          <Link href="/" className="font-bold text-lg">InterviewPrep AI</Link>
          <div className="flex gap-4 text-sm">
            <Link href="/mock" className="hover:underline">Mock Interview</Link>
            <Link href="/rapid" className="hover:underline">⚡ Rapid Fire</Link>
            <Link href="/questions" className="hover:underline">Question Bank</Link>
            <Link href="/dashboard" className="hover:underline">Dashboard</Link>
          </div>
        </nav>
        {children}
      </body>
    </html>
  )
}
```

### frontend/app/page.tsx (Landing)
```typescript
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Mic, Zap, TrendingUp, Users, FileText, ArrowRight } from 'lucide-react'

const USPS = [
  { icon: FileText, title: 'JD → Questions in 10s', badge: '#1',
    desc: 'Paste any JD. Get 20 custom questions covering technical, behavioural, and situational angles instantly.' },
  { icon: Mic, title: 'Voice + STAR Scoring', badge: '#2',
    desc: 'Answer by voice. AI scores every answer against the STAR framework and shows exactly what you missed.' },
  { icon: TrendingUp, title: 'Weakness Tracker', badge: '#3',
    desc: 'Detect your recurring mistakes across sessions. See your top 3 patterns and fix them with targeted drills.' },
  { icon: Users, title: 'Real Interview Questions', badge: '#4',
    desc: 'Crowdsourced Q\'s from Google, Flipkart, Zomato, Infosys. Practice what actually gets asked.' },
  { icon: Zap, title: '60-Second Rapid Fire', badge: '#5',
    desc: '10 questions, 6 seconds each. Build the speed and clarity most candidates never train.' },
]

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 text-white">
      <div className="container mx-auto px-4 py-24 text-center space-y-6">
        <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30">
          Free AI Interview Prep
        </Badge>
        <h1 className="text-5xl md:text-7xl font-bold tracking-tight">
          Stop practising.<br />
          <span className="text-emerald-400">Start performing.</span>
        </h1>
        <p className="text-xl text-slate-400 max-w-2xl mx-auto">
          Upload a JD. Get custom questions. Answer by voice. Get STAR scores. Track your weaknesses. Land the job.
        </p>
        <div className="flex gap-4 justify-center flex-wrap pt-2">
          <Button asChild size="lg" className="bg-emerald-500 hover:bg-emerald-600 text-black font-bold">
            <Link href="/mock">Start Mock Interview <ArrowRight className="ml-2 w-4 h-4" /></Link>
          </Button>
          <Button asChild size="lg" variant="outline" className="border-slate-700 text-white">
            <Link href="/rapid">⚡ Rapid Fire Mode</Link>
          </Button>
        </div>
      </div>
      <div className="container mx-auto px-4 pb-24">
        <h2 className="text-3xl font-bold text-center mb-10">Why we're different</h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
          {USPS.map(({ icon: Icon, title, badge, desc }) => (
            <Card key={title} className="bg-slate-800/50 border-slate-700 hover:border-emerald-500/50 transition-colors">
              <CardContent className="p-6 space-y-3">
                <div className="flex items-start justify-between">
                  <div className="p-2 bg-emerald-500/10 rounded-lg text-emerald-400"><Icon className="w-5 h-5" /></div>
                  <Badge variant="outline" className="text-xs text-slate-500 border-slate-700">USP {badge}</Badge>
                </div>
                <h3 className="font-bold">{title}</h3>
                <p className="text-slate-400 text-sm leading-relaxed">{desc}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </main>
  )
}
```

### frontend/app/mock/page.tsx (JD Upload → Generate)
```typescript
'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { generateQuestions } from '@/lib/claude'
import { Loader2 } from 'lucide-react'

export default function MockSetupPage() {
  const router = useRouter()
  const [jd, setJd] = useState('')
  const [resume, setResume] = useState('')
  const [role, setRole] = useState('')
  const [company, setCompany] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const start = async () => {
    if (!jd.trim() || !role.trim()) { setError('JD and role are required'); return }
    setLoading(true); setError('')
    try {
      const data = await generateQuestions({ job_description: jd, resume_text: resume, target_role: role, target_company: company })
      sessionStorage.setItem('ip_questions', JSON.stringify(data.questions))
      sessionStorage.setItem('ip_context', data.session_context ?? '')
      router.push('/mock/session')
    } catch { setError('Failed to generate questions. Check backend is running.') }
    finally { setLoading(false) }
  }

  return (
    <div className="container max-w-2xl mx-auto px-4 py-12 space-y-6">
      <h1 className="text-3xl font-bold">Start Mock Interview</h1>
      <Card>
        <CardHeader><CardTitle>Tell us about the role</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <Input placeholder="Target Role *  (e.g. Software Engineer)" value={role} onChange={e => setRole(e.target.value)} />
          <Input placeholder="Company (optional)" value={company} onChange={e => setCompany(e.target.value)} />
          <Textarea placeholder="Paste full Job Description here *" value={jd} onChange={e => setJd(e.target.value)} rows={7} className="resize-none" />
          <Textarea placeholder="Your resume / key skills (optional — improves personalisation)" value={resume} onChange={e => setResume(e.target.value)} rows={4} className="resize-none" />
          {error && <p className="text-sm text-destructive">{error}</p>}
          <Button onClick={start} disabled={loading} className="w-full bg-emerald-500 hover:bg-emerald-600 text-black font-bold">
            {loading ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Generating your interview...</> : 'Generate My Interview →'}
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
```

### frontend/app/mock/session/page.tsx (Active Interview)
```typescript
'use client'
import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import VoiceRecorder from '@/components/VoiceRecorder'
import STARScoreCard from '@/components/STARScoreCard'
import { evaluateAnswer } from '@/lib/claude'
import type { Question, STARScore } from '@/lib/types'
import { Loader2 } from 'lucide-react'

const TYPE_COLOR: Record<string, string> = {
  technical: 'bg-blue-100 text-blue-800',
  behavioural: 'bg-purple-100 text-purple-800',
  situational: 'bg-orange-100 text-orange-800',
}

export default function MockSessionPage() {
  const router = useRouter()
  const [questions, setQuestions] = useState<Question[]>([])
  const [idx, setIdx] = useState(0)
  const [answer, setAnswer] = useState('')
  const [score, setScore] = useState<STARScore | null>(null)
  const [loading, setLoading] = useState(false)
  const [allScores, setAllScores] = useState<STARScore[]>([])

  useEffect(() => {
    const stored = sessionStorage.getItem('ip_questions')
    if (!stored) { router.push('/mock'); return }
    setQuestions(JSON.parse(stored))
  }, [router])

  const q = questions[idx]

  const submitAnswer = async () => {
    if (!answer.trim()) return
    setLoading(true)
    try {
      const s = await evaluateAnswer({ question: q.text, answer, question_type: q.type, user_id: 'anon' })
      setScore(s); setAllScores(prev => [...prev, s])
    } catch { alert('Evaluation failed. Check backend.') }
    finally { setLoading(false) }
  }

  const next = () => {
    if (idx + 1 >= questions.length) {
      sessionStorage.setItem('ip_scores', JSON.stringify(allScores))
      router.push('/dashboard')
      return
    }
    setIdx(i => i + 1); setAnswer(''); setScore(null)
  }

  if (!q) return <div className="p-12 text-center text-muted-foreground">Loading your interview...</div>

  return (
    <div className="container max-w-3xl mx-auto px-4 py-8 space-y-6">
      <div className="flex items-center justify-between">
        <span className="text-sm text-muted-foreground">Q{idx + 1} / {questions.length}</span>
        <div className="flex gap-1">
          {questions.map((_, i) => (
            <div key={i} className={`h-1.5 w-7 rounded-full ${i < idx ? 'bg-emerald-500' : i === idx ? 'bg-emerald-300' : 'bg-muted'}`} />
          ))}
        </div>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-start justify-between gap-3">
            <CardTitle className="text-xl leading-relaxed">{q.text}</CardTitle>
            <Badge className={TYPE_COLOR[q.type] ?? ''}>{q.type}</Badge>
          </div>
          <p className="text-xs text-muted-foreground italic mt-1">💡 {q.hint}</p>
        </CardHeader>
        <CardContent className="space-y-4">
          <Textarea placeholder="Type your answer, or use voice below..." value={answer}
            onChange={e => setAnswer(e.target.value)} rows={5} disabled={!!score} className="resize-none" />
          <VoiceRecorder onTranscript={setAnswer} disabled={!!score} />
          {!score
            ? <Button onClick={submitAnswer} disabled={loading || !answer.trim()} className="w-full">
                {loading ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Scoring...</> : 'Submit & Get STAR Score'}
              </Button>
            : <Button onClick={next} className="w-full bg-emerald-500 hover:bg-emerald-600 text-black font-bold">
                {idx + 1 >= questions.length ? 'Finish → View Analysis' : 'Next Question →'}
              </Button>
          }
        </CardContent>
      </Card>

      {score && <STARScoreCard score={score} />}
    </div>
  )
}
```

### frontend/app/rapid/page.tsx (Rapid Fire Mode)
```typescript
'use client'
import { useState, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import RapidFireTimer from '@/components/RapidFireTimer'
import { evaluateRapidAnswer } from '@/lib/claude'
import { Zap, Trophy } from 'lucide-react'

const QUESTIONS = [
  "What's your greatest professional achievement?",
  "Explain recursion in one sentence.",
  "Tell me one weakness you're actively fixing.",
  "Difference between SQL and NoSQL?",
  "Why do you want this role?",
  "Describe REST in under 30 words.",
  "What does 'fail fast' mean to you?",
  "Disagreed with your manager — what happened?",
  "Explain Big O notation simply.",
  "Where do you see yourself in 3 years?"
]

interface Result { question: string; answer: string; score: number; feedback: string }

export default function RapidPage() {
  const [phase, setPhase] = useState<'intro'|'playing'|'done'>('intro')
  const [idx, setIdx] = useState(0)
  const [answer, setAnswer] = useState('')
  const [results, setResults] = useState<Result[]>([])
  const [timerKey, setTimerKey] = useState(0)

  const handleTimeUp = useCallback(async () => {
    const q = QUESTIONS[idx]; const a = answer || '(no answer)'
    const res = await evaluateRapidAnswer(q, a).catch(() => ({ score: 0, feedback: 'Could not evaluate' }))
    const r: Result = { question: q, answer: a, score: res.score ?? 0, feedback: res.feedback ?? '' }
    setResults(prev => {
      const next = [...prev, r]
      if (next.length >= QUESTIONS.length) setPhase('done')
      return next
    })
    if (idx < QUESTIONS.length - 1) {
      setIdx(i => i + 1); setAnswer(''); setTimerKey(k => k + 1)
    }
  }, [idx, answer])

  const avg = results.length ? Math.round(results.reduce((s, r) => s + r.score, 0) / results.length) : 0

  if (phase === 'intro') return (
    <div className="container max-w-lg mx-auto px-4 py-24 text-center space-y-5">
      <div className="text-5xl">⚡</div>
      <h1 className="text-4xl font-bold">Rapid Fire Mode</h1>
      <p className="text-muted-foreground">10 questions · 6 seconds each · Build speed under pressure</p>
      <Button onClick={() => setPhase('playing')} size="lg" className="bg-yellow-500 hover:bg-yellow-600 text-black font-bold">
        <Zap className="w-4 h-4 mr-2" /> Start Now
      </Button>
    </div>
  )

  if (phase === 'done') return (
    <div className="container max-w-2xl mx-auto px-4 py-12 space-y-5">
      <div className="text-center space-y-2">
        <Trophy className="w-10 h-10 mx-auto text-yellow-500" />
        <h1 className="text-3xl font-bold">Done!</h1>
        <p className="text-5xl font-bold text-emerald-500">{avg}<span className="text-lg text-muted-foreground">/100</span></p>
      </div>
      {results.map((r, i) => (
        <Card key={i} className="border-l-4" style={{ borderLeftColor: r.score>=70?'#22c55e':r.score>=40?'#f59e0b':'#ef4444' }}>
          <CardContent className="p-4 space-y-1">
            <p className="text-sm font-medium">{r.question}</p>
            <p className="text-xs text-muted-foreground">You: {r.answer}</p>
            <p className="text-xs text-emerald-600">{r.feedback}</p>
            <p className="text-sm font-bold">{r.score}/100</p>
          </CardContent>
        </Card>
      ))}
      <Button onClick={() => { setPhase('intro'); setIdx(0); setResults([]); setAnswer(''); setTimerKey(0) }} className="w-full">
        Try Again
      </Button>
    </div>
  )

  return (
    <div className="container max-w-xl mx-auto px-4 py-12 space-y-5">
      <div className="flex items-center justify-between">
        <span className="font-medium">Q{idx + 1} / {QUESTIONS.length}</span>
        <RapidFireTimer key={timerKey} totalSeconds={6} onTimeUp={handleTimeUp} isRunning />
      </div>
      <Card className="border-yellow-400/40">
        <CardContent className="p-6 space-y-4">
          <p className="text-xl font-semibold">{QUESTIONS[idx]}</p>
          <Input placeholder="Type fast — press Enter to submit"
            value={answer} onChange={e => setAnswer(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleTimeUp()} className="text-base" autoFocus />
          <Button onClick={handleTimeUp} className="w-full bg-yellow-500 hover:bg-yellow-600 text-black font-bold">
            Submit → Next
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
```

---

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

## §AI Prompts — Canonical Prompt Templates

All prompts are in `app/services.py`. Key rules:
- System prompt always says "Return valid JSON only. No markdown. No preamble."
- Wrap every `json.loads()` in try/except
- STAR scores: situation+task+action+result each 0-25, total must equal sum
- Weakness tags: only from the canonical list in CLAUDE.md
- Rapid evaluation: max_tokens=150 (keep it cheap)
- Question generation: max_tokens=3000
- STAR evaluation: max_tokens=1000

---

## §Roadmap — Post-MVP Features (Phase 2+)

Priority order:
1. Supabase Auth (Google OAuth) — save sessions to DB, enable dashboard
2. Dashboard page — WeaknessChart (Recharts), session history, score over time
3. Community Question Bank — /questions page, company/role filter, upvotes
4. Resume PDF upload — PyMuPDF, extract text → send to Claude for personalisation
5. Email reminders — Resend API, weekly weakness digest
6. WhatsApp bot — Twilio free tier, 1 question/day (high-impact for Indian users)