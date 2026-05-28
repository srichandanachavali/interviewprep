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

