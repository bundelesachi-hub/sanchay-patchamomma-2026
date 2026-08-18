from fastapi import FastAPI
from fastapi.responses import FileResponse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return FileResponse("index.html", media_type="text/html")

@app.post("/investigate")
def investigate(town_id: str, division: str):
    return {
        "town_id": town_id,
        "division": division,
        "supervisor_verdict": {
            "primary_cause": "distributor_count",
            "confidence": 0.95,
            "severity": "CRITICAL",
            "sole_sourced": True,
            "recommended_action": "Appoint second distributor immediately",
            "impact": "100+ retailers have zero supply",
            "timeline": "Immediate action required"
        },
        "agent_findings": {
            "distributor_agent": {
                "name": "🏭 Distributor Agent",
                "finding": "Distributor count dropped to 0",
                "moved": True,
                "confidence": 0.95,
                "reasoning": "Sole-sourced distributor went dark"
            },
            "activation_agent": {
                "name": "📊 Activation Agent",
                "finding": "Activation rate stable",
                "moved": False,
                "confidence": 0.88,
                "reasoning": "Demand signal intact"
            },
            "frequency_agent": {
                "name": "📈 Frequency Agent",
                "finding": "Order frequency unchanged",
                "moved": False,
                "confidence": 0.90,
                "reasoning": "No change in ordering"
            },
            "value_agent": {
                "name": "💰 Value Agent",
                "finding": "Average order value baseline",
                "moved": False,
                "confidence": 0.87,
                "reasoning": "Product mix stable"
            },
            "pipeline_agent": {
                "name": "🔗 Pipeline Agent",
                "finding": "Supply-demand mismatch",
                "moved": True,
                "confidence": 0.92,
                "reasoning": "Structural supply gap"
            }
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")