import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "lost-kingdom-secret-key-2026-agents")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'lost_kingdom.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # LLM Settings (Optional API keys, fallback procedural engine activates if not provided)
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    USE_MOCK_LLM_FALLBACK = True
