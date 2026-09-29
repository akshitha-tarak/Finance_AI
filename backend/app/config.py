import os
from pathlib import Path
from dotenv import load_dotenv

# Base backend directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
load_dotenv(BASE_DIR / ".env")

class Settings:
    PROJECT_NAME: str = "AI-Powered Financial Insights Assistant"
    VERSION: str = "1.0.0"
    
    # Paths
    DATA_PATH: Path = BASE_DIR / "data" / "transactions.csv"
    KNOWLEDGE_DOCS_DIR: Path = BASE_DIR / "data" / "knowledge_docs"
    
    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # API Keys (Optional - Free Groq or Gemini API keys)
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "").strip()
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
    
    # Model configs
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

settings = Settings()
