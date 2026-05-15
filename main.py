from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(
    title="Claim Processing API",
    description="AI-powered PDF claim document processing",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {
        "message": "Claim Processing API",
        "documentation": "/docs",
        "endpoints": {
            "POST /api/process": "Process a PDF claim document",
            "GET /docs": "Interactive API documentation"
        }
    }

app.include_router(router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
