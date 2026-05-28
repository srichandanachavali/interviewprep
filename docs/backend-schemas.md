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

