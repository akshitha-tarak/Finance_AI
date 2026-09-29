import sys
import uvicorn
from app.config import settings

# Ensure UTF-8 output on Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

if __name__ == "__main__":
    print(f"[*] Starting {settings.PROJECT_NAME} on http://localhost:{settings.PORT}")
    print(f"[*] Interactive Swagger API Docs: http://localhost:{settings.PORT}/docs")
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=False)
