import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

BASE_DIR  = Path(__file__).parent.parent
INPUT_DIR = BASE_DIR / "data" / "input"

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL_NAME")
API_BASE_URL   = os.getenv("API_BASE_URL", "http://localhost:8000")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")


def get_supabase_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def ensure_directories():
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
