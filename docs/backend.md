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

