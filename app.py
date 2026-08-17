"""
Cloud Run FastAPI service for Sanchay investigations.
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import json
import os

from agents.orchestrator import investigate

app = FastAPI(title="Sanchay Investigation API", version="1.0")

@app.get("/health")
def health():
    """Health check."""
    return {"status": "ok"}

@app.post("/investigate")
def api_investigate(town_id: str, division: str):
    """
    Investigate an anomaly.
    
    Example:
    POST /investigate?town_id=T00001&division=AC
    """
    try:
        result = investigate(town_id, division)
        result["town_id"] = town_id
        result["division"] = division
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/summary")
def api_summary():
    """
    Get investigation summary report.
    """
    try:
        with open("investigation_results.json", "r") as f:
            results = json.load(f)
        
        # Quick summary
        causes = {}
        for r in results:
            cause = r.get("primary_cause", "unknown")
            causes[cause] = causes.get(cause, 0) + 1
        
        return {
            "total_investigated": len(results),
            "causes": causes,
            "avg_confidence": sum([r.get("confidence", 0) for r in results]) / len(results) if results else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)