import os
from pathlib import Path
from dotenv import load_dotenv

path = Path(os.getcwd()) / '.env'
load_dotenv(dotenv_path=path, override=True)

BASE_DIR = Path(os.getcwd())
print(BASE_DIR)
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = DATA_DIR / "output"
DATABASE_PATH = DATA_DIR / "tasks.db"

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GEMINI_MODEL   = 'gemini-2.0-flash'
DATABASE_PATH   = os.getenv('DATABASE_PATH')
 
def ensure_directories():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)