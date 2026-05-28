import os
import sys
from dotenv import load_dotenv

load_dotenv()  # must run before any app imports that read os.environ

_REQUIRED_VARS = [
    ("GEMINI_API_KEY",      "Google AI Studio → https://aistudio.google.com/app/apikey"),
    ("SUPABASE_URL",        "Supabase Dashboard → Project → Settings → API → Project URL"),
    ("SUPABASE_SERVICE_KEY","Supabase Dashboard → Project → Settings → API → service_role key"),
]

def _validate_env() -> None:
    missing = [
        f"  {var}\n    → {source}"
        for var, source in _REQUIRED_VARS
        if not os.environ.get(var)
    ]
    if missing:
        sys.exit(
            "\n[InterviewPrep] Startup failed — missing required environment variables:\n"
            + "\n".join(missing)
            + "\n\nSee .env.example for the full list and where to get each value.\n"
        )

_validate_env()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import router

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
