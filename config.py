import os
from pathlib import Path
from dotenv import load_dotenv

path = Path(os.getcwd()) / '.env'
load_dotenv(dotenv_path=path, override=True)

BASE_DIR = Path(os.getcwd())

DATA_DIR = BASE_DIR / "data"
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"
DATABASE_PATH = DATA_DIR / "tasks.db"
TICKETS_TABLE_PATH = BASE_DIR / Path('services/tickets_table_schema.sql')

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GEMINI_MODEL   = 'gemini-2.0-flash'

 
def ensure_directories():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)