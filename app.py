from fastapi import FastAPI
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Sanchay API", version="1.0")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    """Serve HTML dashboard"""
    return FileResponse("index.html", media_type="text/html")

@app.post("/investigate")
def api_investigate(town_id: str, division: str):
    """Investigate anomaly"""
    try:
        logger.info(f"Investigating {town_id} {division}")
        from agents.orchestrator import investigate
        result = investigate(town_id, division)
        return {"town_id": town_id, "division": division, "result": result}
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)[:200]}
        )

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Sanchay API...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )