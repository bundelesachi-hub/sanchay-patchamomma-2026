from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import bigquery
import logging
from datetime import datetime
import json
from math import radians, cos, sin, asin, sqrt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize BigQuery
try:
    bq_client = bigquery.Client(project="project-b9c76805-d23b-435a-ab1")
    logger.info("✅ BigQuery client initialized")
except Exception as e:
    logger.error(f"❌ BigQuery init error: {str(e)}")
    bq_client = None

# Initialize Gemini (with graceful fallback)
gemini_enabled = False
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel
    vertexai.init(project="project-b9c76805-d23b-435a-ab1", location="asia-south1")
    model = GenerativeModel("gemini-1.5-flash")
    gemini_enabled = True
    logger.info("✅ Gemini API initialized")
except Exception as e:
    logger.warning(f"⚠️ Gemini API not available: {str(e)}")
    model = None
    gemini_enabled = False

# =========================================================================
# UTILITY FUNCTIONS
# =========================================================================

def haversine(lon1, lat1, lon2, lat2):
    """Calculate distance between two points in km"""
    try:
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Earth's radius in km
        return c * r
    except:
        return 0

# =========================================================================
# ENDPOINTS
# =========================================================================

@app.get("/health")
def health():
    """System health check"""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Sanchay v3.0 - AI-Powered",
        "bigquery": "✅" if bq_client else "❌",
        "gemini": "✅" if gemini_enabled else "⚠️ (fallback mode)"
    }

@app.get("/")
def root():
    """Serve main dashboard"""
    try:
        return FileResponse("index.html", media_type="text/html")
    except Exception as e:
        logger.error(f"Error serving index.html: {str(e)}")
        return {"error": str(e)}

@app.post("/investigate")
def investigate(town_id: str, division: str):
    """Supply chain diagnosis"""
    logger.info(f"Investigating {town_id} {division}")
    
    # Mock scenarios fallback
    SCENARIOS = {
        ('T00001', 'AC'): {'primary_cause': 'distributor_count', 'confidence': 0.95, 'severity': 'CRITICAL', 'sole_sourced': True, 'impact': '45 retailers have zero supply', 'recommended_action': 'Appoint second distributor in Delhi immediately', 'timeline': 'Critical - Action within 24 hours', 'affected_shops': 45, 'revenue_loss_pct': 38},
        ('T00001', 'Lighting'): {'primary_cause': 'activation_rate_drop', 'confidence': 0.88, 'severity': 'HIGH', 'sole_sourced': False, 'impact': '22 retailers went dormant', 'recommended_action': 'Launch retailer re-engagement campaign', 'timeline': 'High - Action within 48 hours', 'affected_shops': 22, 'revenue_loss_pct': 24},
        ('T00001', 'Fans'): {'primary_cause': 'order_frequency_decline', 'confidence': 0.92, 'severity': 'HIGH', 'sole_sourced': False, 'impact': '15 retailers reduced frequency by 55%', 'recommended_action': 'Review pricing and product mix', 'timeline': 'High - Action within 3 days', 'affected_shops': 15, 'revenue_loss_pct': 26},
        ('T00001', 'Water_Heaters'): {'primary_cause': 'pipeline_imbalance', 'confidence': 0.90, 'severity': 'HIGH', 'sole_sourced': False, 'impact': 'Inventory out of stock despite demand', 'recommended_action': 'Expedite warehouse shipment', 'timeline': 'High - Action within 2 days', 'affected_shops': 18, 'revenue_loss_pct': 30},
        ('T00001', 'Kitchen'): {'primary_cause': 'churn_rate_spike', 'confidence': 0.85, 'severity': 'MEDIUM', 'sole_sourced': False, 'impact': '6 retailers switched to competitors', 'recommended_action': 'Launch retention offer and loyalty program', 'timeline': 'Medium - Action within 5 days', 'affected_shops': 6, 'revenue_loss_pct': 12},
        ('T00002', 'AC'): {'primary_cause': 'demand_signal_loss', 'confidence': 0.87, 'severity': 'HIGH', 'sole_sourced': False, 'impact': 'Retail inquiries dropped 40%', 'recommended_action': 'Conduct product awareness training', 'timeline': 'High - Action within 4 days', 'affected_shops': 16, 'revenue_loss_pct': 20},
    }
    
    key = (town_id, division)
    scenario = SCENARIOS.get(key, {
        'primary_cause': 'data_insufficient',
        'confidence': 0.65,
        'severity': 'LOW',
        'sole_sourced': False,
        'impact': 'Insufficient data',
        'recommended_action': 'Collect more sales data',
        'timeline': 'Low - Routine monitoring',
        'affected_shops': 0,
        'revenue_loss_pct': 0,
    })
    
    return {
        "town_id": town_id,
        "division": division,
        "timestamp": datetime.utcnow().isoformat(),
        "supervisor_verdict": scenario
    }

@app.get("/retailers")
def get_retailers(town_id: str = None, limit: int = 100):
    """Get retailers"""
    if not bq_client:
        return {"error": "Database unavailable", "retailers": []}
    
    query = "SELECT * FROM `project-b9c76805-d23b-435a-ab1.sanchay_core.retailers_enhanced`"
    
    if town_id:
        query += f" WHERE town_id = '{town_id}'"
    
    query += f" LIMIT {limit}"
    
    try:
        query_job = bq_client.query(query)
        results = query_job.result()
        
        retailers = []
        for row in results:
            retailers.append({
                'retailer_id': row.retailer_id,
                'retailer_name': row.retailer_name,
                'latitude': float(row.latitude),
                'longitude': float(row.longitude),
                'town_id': row.town_id,
                'division': row.division,
                'avg_order_value': row.avg_order_value,
            })
        
        return {"count": len(retailers), "retailers": retailers}
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {"error": str(e), "retailers": []}

@app.get("/distributors")
def get_distributors(town_id: str = None):
    """Get distributors"""
    if not bq_client:
        return {"error": "Database unavailable", "distributors": []}
    
    query = """
    SELECT 
        distributor_id, distributor_name, town_id, city, division,
        latitude, longitude, address, phone_number,
        retailers_count_active, retailers_count_dormant, status,
        on_time_delivery_pct, order_accuracy_pct, distributor_health_score
    FROM `project-b9c76805-d23b-435a-ab1.sanchay_core.distributors_enhanced`
    """
    
    if town_id:
        query += f" WHERE town_id = '{town_id}'"
    
    try:
        query_job = bq_client.query(query)
        results = query_job.result()
        
        distributors = []
        for row in results:
            distributors.append({
                'distributor_id': row.distributor_id,
                'distributor_name': row.distributor_name,
                'town_id': row.town_id,
                'city': row.city,
                'division': row.division,
                'latitude': float(row.latitude),
                'longitude': float(row.longitude),
                'address': row.address,
                'phone_number': row.phone_number,
                'retailers_active': row.retailers_count_active,
                'retailers_dormant': row.retailers_count_dormant,
                'status': row.status,
                'on_time_delivery_pct': float(row.on_time_delivery_pct),
                'order_accuracy_pct': float(row.order_accuracy_pct),
                'health_score': row.distributor_health_score,
            })
        
        return {"count": len(distributors), "distributors": distributors}
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {"error": str(e), "distributors": []}

@app.get("/distributor-coverage/{distributor_id}")
def get_distributor_coverage(distributor_id: str):
    """Get geographic coverage area"""
    if not bq_client:
        return {"error": "Database unavailable"}
    
    logger.info(f"Fetching coverage for: {distributor_id}")
    
    try:
        query = f"""
        SELECT 
            d.distributor_id, d.distributor_name, d.latitude, d.longitude,
            r.retailer_id, r.retailer_name, r.latitude as r_lat, r.longitude as r_lng,
            r.address, r.avg_order_value
        FROM `project-b9c76805-d23b-435a-ab1.sanchay_core.distributors_enhanced` d
        LEFT JOIN `project-b9c76805-d23b-435a-ab1.sanchay_core.retailers_enhanced` r 
            ON d.distributor_id = r.primary_distributor_id
        WHERE d.distributor_id = '{distributor_id}'
        ORDER BY r.retailer_id
        """
        
        query_job = bq_client.query(query)
        results = list(query_job.result())
        
        if not results:
            return {"error": "Distributor not found"}
        
        distributor_data = results[0]
        retailers = []
        
        for row in results:
            if row.retailer_id:
                retailers.append({
                    'retailer_id': row.retailer_id,
                    'retailer_name': row.retailer_name,
                    'latitude': float(row.r_lat),
                    'longitude': float(row.r_lng),
                    'address': row.address,
                    'avg_order_value': row.avg_order_value,
                })
        
        if retailers:
            lats = [r['latitude'] for r in retailers]
            lngs = [r['longitude'] for r in retailers]
            
            coverage = {
                'distributor_id': distributor_data.distributor_id,
                'distributor_name': distributor_data.distributor_name,
                'latitude': float(distributor_data.latitude),
                'longitude': float(distributor_data.longitude),
                'total_retailers': len(retailers),
                'total_revenue_monthly': sum([r['avg_order_value'] for r in retailers]),
                'service_area': {
                    'north': max(lats),
                    'south': min(lats),
                    'east': max(lngs),
                    'west': min(lngs),
                    'center_lat': sum(lats) / len(lats),
                    'center_lng': sum(lngs) / len(lngs),
                },
                'retailers': retailers,
                'density': len(retailers) / ((max(lats) - min(lats)) * (max(lngs) - min(lngs)) + 0.0001)
            }
            
            return coverage
        
        return {"distributor_id": distributor_id, "retailers": []}
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {"error": str(e)}

@app.post("/analyze")
def analyze(town_id: str, division: str):
    """Run AI analysis (with graceful Gemini fallback)"""
    logger.info(f"Analyzing {town_id} {division}")
    
    if not gemini_enabled:
        logger.info("Gemini not available, using mock data")
        return {
            "town_id": town_id,
            "division": division,
            "timestamp": datetime.utcnow().isoformat(),
            "agents": {
                "distributor": {"agent": "🏭 Distributor Agent", "analysis": {"risk_level": "MEDIUM", "confidence": 0.8, "prediction": "Network needs monitoring", "recommended_action": "Review distributor performance", "timeline": "Within 30 days"}},
                "activation": {"agent": "📊 Activation Agent", "analysis": {"engagement_risk": "MEDIUM", "confidence": 0.75, "prediction": "Retailer engagement declining", "recommended_action": "Launch re-engagement program", "timeline": "Within 2 weeks"}},
                "frequency": {"agent": "📈 Frequency Agent", "analysis": {"demand_risk": "LOW", "confidence": 0.82, "prediction": "Order frequency stable", "recommended_action": "Maintain current strategy", "timeline": "Ongoing"}},
                "value": {"agent": "💰 Value Agent", "analysis": {"pricing_trend": "Stable", "confidence": 0.78, "prediction": "Transaction values stable", "recommended_action": "Introduce premium offerings", "timeline": "Within 60 days"}},
                "pipeline": {"agent": "🔗 Pipeline Agent", "analysis": {"stockout_risk": "LOW", "confidence": 0.85, "prediction": "Supply-demand balanced", "recommended_action": "Monitor inventory levels", "timeline": "Ongoing"}},
            }
        }
    
    # If Gemini is available, use it (implement your Gemini logic here)
    return {
        "town_id": town_id,
        "division": division,
        "timestamp": datetime.utcnow().isoformat(),
        "agents": {}
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting Sanchay v3.0 API")
    logger.info(f"✅ BigQuery: {bq_client is not None}")
    logger.info(f"✅ Gemini: {gemini_enabled}")
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")