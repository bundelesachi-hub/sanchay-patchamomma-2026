from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Scenario database
SCENARIOS = {
    ('T00001', 'AC'): {
        'primary_cause': 'distributor_count',
        'confidence': 0.95,
        'severity': 'CRITICAL',
        'sole_sourced': True,
        'impact': '45 retailers have zero supply',
        'recommended_action': 'Appoint second distributor in Delhi immediately',
        'timeline': 'Critical - Action within 24 hours',
        'affected_shops': 45,
        'revenue_loss_pct': 38,
    },
    ('T00002', 'Lighting'): {
        'primary_cause': 'activation_rate_drop',
        'confidence': 0.87,
        'severity': 'HIGH',
        'sole_sourced': False,
        'impact': '18 retailers went dormant',
        'recommended_action': 'Launch urgency campaign targeting inactive retailers',
        'timeline': 'High - Action within 3 days',
        'affected_shops': 18,
        'revenue_loss_pct': 22,
    },
    ('T00003', 'Fans'): {
        'primary_cause': 'order_frequency_decline',
        'confidence': 0.91,
        'severity': 'HIGH',
        'sole_sourced': False,
        'impact': '12 retailers reduced order frequency by 60%',
        'recommended_action': 'Investigate pricing or product issues; consider promotional offers',
        'timeline': 'High - Action within 2 days',
        'affected_shops': 12,
        'revenue_loss_pct': 28,
    },
    ('T00004', 'Water_Heaters'): {
        'primary_cause': 'avg_order_value_collapse',
        'confidence': 0.89,
        'severity': 'MEDIUM',
        'sole_sourced': True,
        'impact': 'Average transaction value dropped 45%',
        'recommended_action': 'Bundle products or adjust pricing strategy',
        'timeline': 'Medium - Action within 5 days',
        'affected_shops': 8,
        'revenue_loss_pct': 18,
    },
    ('T00005', 'Kitchen'): {
        'primary_cause': 'pipeline_imbalance',
        'confidence': 0.93,
        'severity': 'CRITICAL',
        'sole_sourced': False,
        'impact': 'Inventory stockout; demand signal intact',
        'recommended_action': 'Expedite inventory replenishment from central warehouse',
        'timeline': 'Critical - Action within 12 hours',
        'affected_shops': 28,
        'revenue_loss_pct': 35,
    },
    ('T00006', 'AC'): {
        'primary_cause': 'churn_rate_spike',
        'confidence': 0.88,
        'severity': 'HIGH',
        'sole_sourced': True,
        'impact': '8 retailers switched to competitors',
        'recommended_action': 'Retention campaign + loyalty incentives',
        'timeline': 'High - Action within 48 hours',
        'affected_shops': 8,
        'revenue_loss_pct': 15,
    },
    ('T00007', 'Lighting'): {
        'primary_cause': 'distributor_count',
        'confidence': 0.94,
        'severity': 'CRITICAL',
        'sole_sourced': True,
        'impact': '32 retailers have zero supply access',
        'recommended_action': 'Emergency: Activate backup distributor network',
        'timeline': 'Critical - Immediate action required',
        'affected_shops': 32,
        'revenue_loss_pct': 42,
    },
    ('T00008', 'Fans'): {
        'primary_cause': 'demand_signal_loss',
        'confidence': 0.86,
        'severity': 'MEDIUM',
        'sole_sourced': False,
        'impact': 'Retail interest dropped; few shops inquiring',
        'recommended_action': 'Product awareness campaign; retail training program',
        'timeline': 'Medium - Action within 7 days',
        'affected_shops': 5,
        'revenue_loss_pct': 12,
    },
    ('T00009', 'Water_Heaters'): {
        'primary_cause': 'payment_delay_friction',
        'confidence': 0.82,
        'severity': 'MEDIUM',
        'sole_sourced': False,
        'impact': 'Payment terms causing order hesitation',
        'recommended_action': 'Introduce flexible payment terms or credit line',
        'timeline': 'Medium - Action within 5 days',
        'affected_shops': 6,
        'revenue_loss_pct': 9,
    },
    ('T00010', 'Kitchen'): {
        'primary_cause': 'distributor_count',
        'confidence': 0.96,
        'severity': 'CRITICAL',
        'sole_sourced': True,
        'impact': '24 retailers unable to order',
        'recommended_action': 'Urgent: Secure second distributor or direct supply channel',
        'timeline': 'Critical - Action within 24 hours',
        'affected_shops': 24,
        'revenue_loss_pct': 40,
    },
}

@app.get("/health")
def health():
    logger.info("Health check OK")
    return {"status": "ok"}

@app.get("/")
def root():
    logger.info("Serving index.html")
    try:
        return FileResponse("index.html", media_type="text/html")
    except Exception as e:
        logger.error(f"Error serving index.html: {str(e)}")
        return {"error": str(e)}

@app.post("/investigate")
def investigate(town_id: str, division: str):
    """Return unique response based on town_id and division"""
    logger.info(f"Investigating {town_id} {division}")
    
    # Look up scenario
    key = (town_id, division)
    
    if key in SCENARIOS:
        scenario = SCENARIOS[key]
    else:
        # Default scenario for unknown combinations
        scenario = {
            'primary_cause': 'data_insufficient',
            'confidence': 0.65,
            'severity': 'LOW',
            'sole_sourced': False,
            'impact': 'Insufficient data for this location-division combination',
            'recommended_action': 'Collect more sales data or contact regional manager',
            'timeline': 'Low - Routine monitoring',
            'affected_shops': 0,
            'revenue_loss_pct': 0,
        }
    
    return {
        "town_id": town_id,
        "division": division,
        "supervisor_verdict": {
            "primary_cause": scenario['primary_cause'],
            "confidence": scenario['confidence'],
            "severity": scenario['severity'],
            "sole_sourced": scenario['sole_sourced'],
            "impact": scenario['impact'],
            "recommended_action": scenario['recommended_action'],
            "timeline": scenario['timeline'],
            "affected_shops": scenario['affected_shops'],
            "revenue_loss_pct": scenario['revenue_loss_pct'],
        }
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Sanchay API on port 8080")
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")