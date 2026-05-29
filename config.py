import os
from pathlib import Path
from dotenv import load_dotenv

path = Path(os.getcwd()) / '.env'
load_dotenv(dotenv_path=path, override=True)

OUTPUT_DIR = Path('output')

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GEMINI_MODEL   = 'gemini-2.0-flash'
DATABASE_PATH   = os.getenv('DATABASE_PATH')
 