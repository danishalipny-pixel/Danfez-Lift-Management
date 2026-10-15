import uvicorn
from backend.app.config import settings

if __name__ == "__main__":
    print("==================================================")
    print("  DANFEZ TECH HOUSE - Smart Lift Management System")
    print("  Product: Danfez Lift Control v2.0")
    print(f"  Host: http://localhost:{settings.PORT}")
    print(f"  API Docs: http://localhost:{settings.PORT}/api/docs")
    print("==================================================")
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=settings.PORT, reload=False)
