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
