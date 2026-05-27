import os
from pathlib import Path
from dotenv import load_dotenv

path = Path(os.getcwd()) / '.env'
load_dotenv(dotenv_path=path, override=True)

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')