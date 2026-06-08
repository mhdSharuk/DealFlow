import os
from pathlib import Path
from dotenv import load_dotenv

path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=path, override=True)

BASE_DIR = Path(__file__).parent

DATA_DIR       = BASE_DIR / "data"
INPUT_DIR      = DATA_DIR / "input"
OUTPUT_DIR     = DATA_DIR / "output"
PROCESSING_DIR = DATA_DIR / "processing"
PROCESSED_DIR  = DATA_DIR / "processed"
DATABASE_PATH  = DATA_DIR / "tasks.db"

TICKETS_TABLE_PATH = BASE_DIR / Path('services/tickets_table_schema.sql')
JOBS_TABLE_PATH    = BASE_DIR / Path('services/jobs_table_schema.sql')

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GEMINI_MODEL   = os.getenv('GEMINI_MODEL_NAME')
API_BASE_URL   = os.getenv('API_BASE_URL', 'http://localhost:8000')

def ensure_directories():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSING_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
