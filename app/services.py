import google.generativeai as genai
import json
import os
from supabase import create_client
from app.schemas import STARScore

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
_sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])

_JSON_CONFIG = genai.types.GenerationConfig(response_mime_type="application/json")

WEAKNESS_TAGS = [
    "missing_situation","missing_task","missing_action","missing_result",
    "too_vague","over_explains","no_quantified_impact","no_technical_depth",
    "rambling","skips_conclusion","overconfident","underconfident"
]


def _model(system: str) -> genai.GenerativeModel:
    return genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=system,
        generation_config=_JSON_CONFIG,
    )


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

    r = _model("You are an expert interviewer. Return valid JSON only. No markdown, no preamble.").generate_content(prompt)
    try:
        return json.loads(r.text)
    except json.JSONDecodeError:
        raise ValueError(f"AI returned non-JSON response: {r.text[:200]}")


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

    r = _model("You are an expert interview coach. Return valid JSON only.").generate_content(prompt)
    try:
        return STARScore(**json.loads(r.text))
    except json.JSONDecodeError:
        raise ValueError(f"AI returned non-JSON response: {r.text[:200]}")


def evaluate_rapid_answer(question, answer) -> dict:
    prompt = f"""Question: {question}
Answer: {answer}

Score 0-100: keyword coverage + relevance + conciseness.
Return ONLY: {{"score": <int>, "feedback": "<one sentence>", "key_missed": "<concept or null>"}}"""

    r = _model("Fast interview evaluator. JSON only.").generate_content(prompt)
    try:
        return json.loads(r.text)
    except json.JSONDecodeError:
        raise ValueError(f"AI returned non-JSON response: {r.text[:200]}")


def detect_weakness_patterns(tags_history: list[list[str]]) -> dict:
    from collections import Counter
    all_tags = [t for session in tags_history for t in session]
    counts = Counter(all_tags)
    explanations = {
        "missing_result":        "You often skip the outcome — always end with impact",
        "missing_situation":     "You don't set context before diving in",
        "missing_action":        "You say 'we' but not what YOU specifically did",
        "over_explains":         "Answers too long — practice 90-second rule",
        "no_quantified_impact":  "Add numbers: %, ₹, time saved, users affected",
        "too_vague":             "Use specific examples, not general statements",
        "no_technical_depth":    "Go deeper on decisions and tradeoffs",
        "rambling":              "Structure before speaking: Situation → Task → Action → Result",
        "skips_conclusion":      "Always close with what you learned or the final outcome",
    }
    return {
        "top_weaknesses": [
            {"tag": t, "count": c, "explanation": explanations.get(t, t)}
            for t, c in counts.most_common(3)
        ],
        "total_answers_analysed": len(all_tags)
    }


def get_community_questions(company: str | None, role: str | None, limit: int) -> dict:
    q = _sb.table("community_questions").select("*").eq("verified", True)
    if company:
        q = q.ilike("company", f"%{company}%")
    if role:
        q = q.ilike("role", f"%{role}%")
    result = q.order("upvotes", desc=True).limit(limit).execute()
    return {"questions": result.data, "total": len(result.data)}


def submit_community_question(payload: dict) -> dict:
    from app.schemas import CommunityQuestionSubmit
    validated = CommunityQuestionSubmit(**payload)
    _sb.table("community_questions").insert({
        "submitted_by": validated.submitted_by,
        "company": validated.company,
        "role": validated.role,
        "question_text": validated.question_text,
        "question_type": validated.question_type,
        "verified": False,
        "upvotes": 0,
    }).execute()
    return {"status": "submitted", "message": "Under review — verified questions appear within 24h"}
