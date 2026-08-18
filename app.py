from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Sanchay API", version="1.0")

@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "ok", "service": "sanchay"}

@app.get("/")
def root():
    """Root endpoint"""
    return {
        "service": "Sanchay",
        "version": "1.0",
        "endpoints": {
            "health": "/health",
            "investigate": "/investigate?town_id=T00001&division=AC"
        }
    }

@app.post("/investigate")
def api_investigate(town_id: str, division: str):
    """Investigate anomaly"""
    try:
        logger.info(f"Investigating {town_id} {division}")
        from agents.orchestrator import investigate
        result = investigate(town_id, division)
        result["town_id"] = town_id
        result["division"] = division
        return JSONResponse(content=result)
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