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
    # T00001 - Delhi
    ('T00001', 'AC'): {'primary_cause': 'distributor_count', 'confidence': 0.95, 'severity': 'CRITICAL', 'sole_sourced': True, 'impact': '45 retailers have zero supply', 'recommended_action': 'Appoint second distributor in Delhi immediately', 'timeline': 'Critical - Action within 24 hours', 'affected_shops': 45, 'revenue_loss_pct': 38},
    ('T00001', 'Lighting'): {'primary_cause': 'activation_rate_drop', 'confidence': 0.88, 'severity': 'HIGH', 'sole_sourced': False, 'impact': '22 retailers went dormant', 'recommended_action': 'Launch retailer re-engagement campaign', 'timeline': 'High - Action within 48 hours', 'affected_shops': 22, 'revenue_loss_pct': 24},
    ('T00001', 'Fans'): {'primary_cause': 'order_frequency_decline', 'confidence': 0.92, 'severity': 'HIGH', 'sole_sourced': False, 'impact': '15 retailers reduced frequency by 55%', 'recommended_action': 'Review pricing and product mix', 'timeline': 'High - Action within 3 days', 'affected_shops': 15, 'revenue_loss_pct': 26},
    ('T00001', 'Water_Heaters'): {'primary_cause': 'pipeline_imbalance', 'confidence': 0.90, 'severity': 'HIGH', 'sole_sourced': False, 'impact': 'Inventory out of stock despite demand', 'recommended_action': 'Expedite warehouse shipment', 'timeline': 'High - Action within 2 days', 'affected_shops': 18, 'revenue_loss_pct': 30},
    ('T00001', 'Kitchen'): {'primary_cause': 'churn_rate_spike', 'confidence': 0.85, 'severity': 'MEDIUM', 'sole_sourced': False, 'impact': '6 retailers switched to competitors', 'recommended_action': 'Launch retention offer and loyalty program', 'timeline': 'Medium - Action within 5 days', 'affected_shops': 6, 'revenue_loss_pct': 12},

    # T00002 - Mumbai
    ('T00002', 'AC'): {'primary_cause': 'demand_signal_loss', 'confidence': 0.87, 'severity': 'HIGH', 'sole_sourced': False, 'impact': 'Retail inquiries dropped 40%', 'recommended_action': 'Conduct product awareness training with retailers', 'timeline': 'High - Action within 4 days', 'affected_shops': 16, 'revenue_loss_pct': 20},
    ('T00002', 'Lighting'): {'primary_cause': 'activation_rate_drop', 'confidence': 0.87, 'severity': 'HIGH', 'sole_sourced': False, 'impact': '18 retailers went dormant', 'recommended_action': 'Launch urgency campaign targeting inactive retailers', 'timeline': 'High - Action within 3 days', 'affected_shops': 18, 'revenue_loss_pct': 22},
    ('T00002', 'Fans'): {'primary_cause': 'avg_order_value_collapse', 'confidence': 0.83, 'severity': 'MEDIUM', 'sole_sourced': False, 'impact': 'Transaction size dropped 35%', 'recommended_action': 'Introduce bundled offers and combo deals', 'timeline': 'Medium - Action within 6 days', 'affected_shops': 12, 'revenue_loss_pct': 18},
    ('T00002', 'Water_Heaters'): {'primary_cause': 'payment_delay_friction', 'confidence': 0.84, 'severity': 'MEDIUM', 'sole_sourced': False, 'impact': 'Payment terms creating order hesitation', 'recommended_action': 'Offer 30-day credit terms or EMI options', 'timeline': 'Medium - Action within 5 days', 'affected_shops': 8, 'revenue_loss_pct': 14},
    ('T00002', 'Kitchen'): {'primary_cause': 'distributor_count', 'confidence': 0.89, 'severity': 'HIGH', 'sole_sourced': True, 'impact': '35 retailers have limited access', 'recommended_action': 'Activate secondary distributor in Mumbai', 'timeline': 'High - Action within 48 hours', 'affected_shops': 35, 'revenue_loss_pct': 32},

    # T00003 - Bangalore
    ('T00003', 'AC'): {'primary_cause': 'order_frequency_decline', 'confidence': 0.91, 'severity': 'HIGH', 'sole_sourced': False, 'impact': '14 retailers reduced frequency by 50%', 'recommended_action': 'Investigate competitive pressure; adjust margin', 'timeline': 'High - Action within 3 days', 'affected_shops': 14, 'revenue_loss_pct': 25},
    ('T00003', 'Lighting'): {'primary_cause': 'churn_rate_spike', 'confidence': 0.89, 'severity': 'HIGH', 'sole_sourced': False, 'impact': '9 retailers switched brands', 'recommended_action': 'Retention incentives + loyalty points boost', 'timeline': 'High - Action within 48 hours', 'affected_shops': 9, 'revenue_loss_pct': 16},
    ('T00003', 'Fans'): {'primary_cause': 'order_frequency_decline', 'confidence': 0.91, 'severity': 'HIGH', 'sole_sourced': False, 'impact': '12 retailers reduced order frequency by 60%', 'recommended_action': 'Investigate pricing or product issues; consider promotional offers', 'timeline': 'High - Action within 2 days', 'affected_shops': 12, 'revenue_loss_pct': 28},
    ('T00003', 'Water_Heaters'): {'primary_cause': 'activation_rate_drop', 'confidence': 0.86, 'severity': 'HIGH', 'sole_sourced': False, 'impact': '11 retailers went inactive', 'recommended_action': 'Product demo and training sessions', 'timeline': 'High - Action within 4 days', 'affected_shops': 11, 'revenue_loss_pct': 19},
    ('T00003', 'Kitchen'): {'primary_cause': 'pipeline_imbalance', 'confidence': 0.92, 'severity': 'CRITICAL', 'sole_sourced': False, 'impact': 'Supply shortage vs high demand', 'recommended_action': 'Urgent stock replenishment from distribution center', 'timeline': 'Critical - Action within 12 hours', 'affected_shops': 28, 'revenue_loss_pct': 36},

    # T00004 - Chennai
    ('T00004', 'AC'): {'primary_cause': 'distributor_count', 'confidence': 0.96, 'severity': 'CRITICAL', 'sole_sourced': True, 'impact': '40 retailers unable to order', 'recommended_action': 'Urgent: Contract backup distributor or enable direct supply', 'timeline': 'Critical - Action within 24 hours', 'affected_shops': 40, 'revenue_loss_pct': 41},
    ('T00004', 'Lighting'): {'primary_cause': 'demand_signal_loss', 'confidence': 0.84, 'severity': 'MEDIUM', 'sole_sourced': False, 'impact': 'Retail interest at 6-month low', 'recommended_action': 'Market development program and retailer incentives', 'timeline': 'Medium - Action within 7 days', 'affected_shops': 7, 'revenue_loss_pct': 13},
    ('T00004', 'Fans'): {'primary_cause': 'avg_order_value_collapse', 'confidence': 0.85, 'severity': 'MEDIUM', 'sole_sourced': False, 'impact': 'Per-shop transaction value down 38%', 'recommended_action': 'Bundle with accessories; upsell premium models', 'timeline': 'Medium - Action within 5 days', 'affected_shops': 9, 'revenue_loss_pct': 17},
    ('T00004', 'Water_Heaters'): {'primary_cause': 'avg_order_value_collapse', 'confidence': 0.89, 'severity': 'MEDIUM', 'sole_sourced': True, 'impact': 'Average transaction value dropped 45%', 'recommended_action': 'Bundle products or adjust pricing strategy', 'timeline': 'Medium - Action within 5 days', 'affected_shops': 8, 'revenue_loss_pct': 18},
    ('T00004', 'Kitchen'): {'primary_cause': 'activation_rate_drop', 'confidence': 0.87, 'severity': 'HIGH', 'sole_sourced': True, 'impact': '13 retailers went dormant', 'recommended_action': 'Direct engagement + special offers', 'timeline': 'High - Action within 3 days', 'affected_shops': 13, 'revenue_loss_pct': 23},

    # T00005 - Hyderabad
    ('T00005', 'AC'): {'primary_cause': 'payment_delay_friction', 'confidence': 0.82, 'severity': 'MEDIUM', 'sole_sourced': False, 'impact': 'Payment cycles extended; cash flow impact', 'recommended_action': 'Dynamic discount for early payment', 'timeline': 'Medium - Action within 5 days', 'affected_shops': 7, 'revenue_loss_pct': 10},
    ('T00005', 'Lighting'): {'primary_cause': 'order_frequency_decline', 'confidence': 0.90, 'severity': 'HIGH', 'sole_sourced': False, 'impact': '13 retailers reduced reorder cycles', 'recommended_action': 'Conduct sales force visit; negotiate margins', 'timeline': 'High - Action within 3 days', 'affected_shops': 13, 'revenue_loss_pct': 22},
    ('T00005', 'Fans'): {'primary_cause': 'demand_signal_loss', 'confidence': 0.86, 'severity': 'HIGH', 'sole_sourced': False, 'impact': 'No new retailer inquiries in 45 days', 'recommended_action': 'Aggressive retail expansion program', 'timeline': 'High - Action within 4 days', 'affected_shops': 10, 'revenue_loss_pct': 15},
    ('T00005', 'Water_Heaters'): {'primary_cause': 'churn_rate_spike', 'confidence': 0.88, 'severity': 'HIGH', 'sole_sourced': False, 'impact': '7 retailers defected to rivals', 'recommended_action': 'Win-back campaign with special incentives', 'timeline': 'High - Action within 2 days', 'affected_shops': 7, 'revenue_loss_pct': 14},
    ('T00005', 'Kitchen'): {'primary_cause': 'pipeline_imbalance', 'confidence': 0.93, 'severity': 'CRITICAL', 'sole_sourced': False, 'impact': 'Inventory stockout; demand signal intact', 'recommended_action': 'Expedite inventory replenishment from central warehouse', 'timeline': 'Critical - Action within 12 hours', 'affected_shops': 28, 'revenue_loss_pct': 35},

    # T00006 - Kolkata
    ('T00006', 'AC'): {'primary_cause': 'churn_rate_spike', 'confidence': 0.88, 'severity': 'HIGH', 'sole_sourced': True, 'impact': '8 retailers switched to competitors', 'recommended_action': 'Retention campaign + loyalty incentives', 'timeline': 'High - Action within 48 hours', 'affected_shops': 8, 'revenue_loss_pct': 15},
    ('T00006', 'Lighting'): {'primary_cause': 'distributor_count', 'confidence': 0.93, 'severity': 'CRITICAL', 'sole_sourced': True, 'impact': '28 retailers facing supply gaps', 'recommended_action': 'Emergency distributor activation', 'timeline': 'Critical - Immediate action', 'affected_shops': 28, 'revenue_loss_pct': 37},
    ('T00006', 'Fans'): {'primary_cause': 'activation_rate_drop', 'confidence': 0.85, 'severity': 'HIGH', 'sole_sourced': False, 'impact': '7 retailers inactive for 30+ days', 'recommended_action': 'Personal retailer visit and support', 'timeline': 'High - Action within 3 days', 'affected_shops': 7, 'revenue_loss_pct': 16},
    ('T00006', 'Water_Heaters'): {'primary_cause': 'avg_order_value_collapse', 'confidence': 0.83, 'severity': 'MEDIUM', 'sole_sourced': True, 'impact': 'Average order value down 32%', 'recommended_action': 'Premium product push and training', 'timeline': 'Medium - Action within 6 days', 'affected_shops': 6, 'revenue_loss_pct': 13},
    ('T00006', 'Kitchen'): {'primary_cause': 'order_frequency_decline', 'confidence': 0.89, 'severity': 'HIGH', 'sole_sourced': False, 'impact': '10 retailers reduced frequency by 45%', 'recommended_action': 'Competitive pricing review and market analysis', 'timeline': 'High - Action within 4 days', 'affected_shops': 10, 'revenue_loss_pct': 19},

    # T00007 - Pune
    ('T00007', 'AC'): {'primary_cause': 'pipeline_imbalance', 'confidence': 0.91, 'severity': 'HIGH', 'sole_sourced': False, 'impact': 'Demand exceeds supply; stock shortage', 'recommended_action': 'Increase supply allocation and expedite shipments', 'timeline': 'High - Action within 2 days', 'affected_shops': 20, 'revenue_loss_pct': 21},
    ('T00007', 'Lighting'): {'primary_cause': 'distributor_count', 'confidence': 0.94, 'severity': 'CRITICAL', 'sole_sourced': True, 'impact': '32 retailers have zero supply access', 'recommended_action': 'Emergency: Activate backup distributor network', 'timeline': 'Critical - Immediate action required', 'affected_shops': 32, 'revenue_loss_pct': 42},
    ('T00007', 'Fans'): {'primary_cause': 'demand_signal_loss', 'confidence': 0.87, 'severity': 'HIGH', 'sole_sourced': False, 'impact': 'Retail inquiries down 50%', 'recommended_action': 'Co-marketing campaign with distributor', 'timeline': 'High - Action within 4 days', 'affected_shops': 11, 'revenue_loss_pct': 17},
    ('T00007', 'Water_Heaters'): {'primary_cause': 'churn_rate_spike', 'confidence': 0.86, 'severity': 'HIGH', 'sole_sourced': False, 'impact': '6 retailers defected last month', 'recommended_action': 'Special incentive package for returning retailers', 'timeline': 'High - Action within 3 days', 'affected_shops': 6, 'revenue_loss_pct': 12},
    ('T00007', 'Kitchen'): {'primary_cause': 'activation_rate_drop', 'confidence': 0.88, 'severity': 'HIGH', 'sole_sourced': False, 'impact': '9 retailers went inactive', 'recommended_action': 'Product training and demo sessions', 'timeline': 'High - Action within 4 days', 'affected_shops': 9, 'revenue_loss_pct': 18},

    # T00008 - Ahmedabad
    ('T00008', 'AC'): {'primary_cause': 'order_frequency_decline', 'confidence': 0.90, 'severity': 'HIGH', 'sole_sourced': False, 'impact': '11 retailers reduced reorder cycles', 'recommended_action': 'Negotiate improved terms; review competitive landscape', 'timeline': 'High - Action within 3 days', 'affected_shops': 11, 'revenue_loss_pct': 24},
    ('T00008', 'Lighting'): {'primary_cause': 'avg_order_value_collapse', 'confidence': 0.84, 'severity': 'MEDIUM', 'sole_sourced': False, 'impact': 'Per-shop value down 28%', 'recommended_action': 'Promote high-margin SKUs and bundles', 'timeline': 'Medium - Action within 6 days', 'affected_shops': 10, 'revenue_loss_pct': 14},
    ('T00008', 'Fans'): {'primary_cause': 'demand_signal_loss', 'confidence': 0.86, 'severity': 'MEDIUM', 'sole_sourced': False, 'impact': 'Retail interest dropped; few shops inquiring', 'recommended_action': 'Product awareness campaign; retail training program', 'timeline': 'Medium - Action within 7 days', 'affected_shops': 5, 'revenue_loss_pct': 12},
    ('T00008', 'Water_Heaters'): {'primary_cause': 'payment_delay_friction', 'confidence': 0.85, 'severity': 'MEDIUM', 'sole_sourced': False, 'impact': 'Credit terms causing order delays', 'recommended_action': 'Introduce structured payment plans', 'timeline': 'Medium - Action within 5 days', 'affected_shops': 8, 'revenue_loss_pct': 11},
    ('T00008', 'Kitchen'): {'primary_cause': 'churn_rate_spike', 'confidence': 0.87, 'severity': 'HIGH', 'sole_sourced': False, 'impact': '5 retailers switched in last quarter', 'recommended_action': 'Competitive offers and relationship strengthening', 'timeline': 'High - Action within 3 days', 'affected_shops': 5, 'revenue_loss_pct': 10},

    # T00009 - Jaipur
    ('T00009', 'AC'): {'primary_cause': 'distributor_count', 'confidence': 0.96, 'severity': 'CRITICAL', 'sole_sourced': True, 'impact': '28 retailers unable to stock', 'recommended_action': 'Urgent: Secure second distributor or enable direct supply', 'timeline': 'Critical - Action within 24 hours', 'affected_shops': 28, 'revenue_loss_pct': 40},
    ('T00009', 'Lighting'): {'primary_cause': 'activation_rate_drop', 'confidence': 0.84, 'severity': 'HIGH', 'sole_sourced': False, 'impact': '6 retailers dormant for 60+ days', 'recommended_action': 'Win-back campaign and incentive offers', 'timeline': 'High - Action within 3 days', 'affected_shops': 6, 'revenue_loss_pct': 15},
    ('T00009', 'Fans'): {'primary_cause': 'order_frequency_decline', 'confidence': 0.89, 'severity': 'HIGH', 'sole_sourced': False, 'impact': '8 retailers reduced frequency by 55%', 'recommended_action': 'Review and adjust pricing strategy', 'timeline': 'High - Action within 3 days', 'affected_shops': 8, 'revenue_loss_pct': 20},
    ('T00009', 'Water_Heaters'): {'primary_cause': 'payment_delay_friction', 'confidence': 0.82, 'severity': 'MEDIUM', 'sole_sourced': False, 'impact': 'Payment terms causing order hesitation', 'recommended_action': 'Introduce flexible payment terms or credit line', 'timeline': 'Medium - Action within 5 days', 'affected_shops': 6, 'revenue_loss_pct': 9},
    ('T00009', 'Kitchen'): {'primary_cause': 'demand_signal_loss', 'confidence': 0.83, 'severity': 'HIGH', 'sole_sourced': False, 'impact': 'No fresh retailer adds in 2 months', 'recommended_action': 'Retailer recruitment and onboarding program', 'timeline': 'High - Action within 5 days', 'affected_shops': 4, 'revenue_loss_pct': 8},

    # T00010 - Lucknow
    ('T00010', 'AC'): {'primary_cause': 'churn_rate_spike', 'confidence': 0.89, 'severity': 'HIGH', 'sole_sourced': False, 'impact': '7 retailers switched to competitors', 'recommended_action': 'Urgent retention and win-back program', 'timeline': 'High - Action within 2 days', 'affected_shops': 7, 'revenue_loss_pct': 13},
    ('T00010', 'Lighting'): {'primary_cause': 'order_frequency_decline', 'confidence': 0.90, 'severity': 'HIGH', 'sole_sourced': False, 'impact': '9 retailers reduced reorder frequency', 'recommended_action': 'Sales force engagement and margin review', 'timeline': 'High - Action within 3 days', 'affected_shops': 9, 'revenue_loss_pct': 19},
    ('T00010', 'Fans'): {'primary_cause': 'avg_order_value_collapse', 'confidence': 0.85, 'severity': 'MEDIUM', 'sole_sourced': False, 'impact': 'Transaction size down 30%', 'recommended_action': 'Cross-sell premium models and accessories', 'timeline': 'Medium - Action within 5 days', 'affected_shops': 7, 'revenue_loss_pct': 12},
    ('T00010', 'Water_Heaters'): {'primary_cause': 'activation_rate_drop', 'confidence': 0.86, 'severity': 'HIGH', 'sole_sourced': False, 'impact': '5 retailers inactive for 45 days', 'recommended_action': 'Field support and product assistance', 'timeline': 'High - Action within 4 days', 'affected_shops': 5, 'revenue_loss_pct': 11},
    ('T00010', 'Kitchen'): {'primary_cause': 'distributor_count', 'confidence': 0.96, 'severity': 'CRITICAL', 'sole_sourced': True, 'impact': '24 retailers unable to order', 'recommended_action': 'Urgent: Secure second distributor or direct supply channel', 'timeline': 'Critical - Action within 24 hours', 'affected_shops': 24, 'revenue_loss_pct': 40},
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