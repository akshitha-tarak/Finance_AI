import sys
from pathlib import Path

# Add backend directory to sys.path so app and its services are available
ROOT_DIR = Path(__file__).resolve().parent
backend_dir = ROOT_DIR / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app

if __name__ == "__main__":
    import uvicorn
    from app.config import settings
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=False)
