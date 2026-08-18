from fastapi import FastAPI
from fastapi.responses import JSONResponse
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
    return {"service": "Sanchay", "version": "1.0"}

@app.post("/investigate")
def api_investigate(town_id: str, division: str):
    try:
        logger.info(f"Investigating {town_id} {division}")
        from agents.orchestrator import investigate
        result = investigate(town_id, division)
        return {"town_id": town_id, "division": division, "result": result}
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {"error": str(e)[:200]}, 500

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)