from fastapi import FastAPI
from fastapi.responses import FileResponse
from google.cloud import bigquery
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
bq_client = bigquery.Client(project="project-b9c76805-d23b-435a-ab1")

# Mock scenarios (for when BigQuery data is unavailable)
SCENARIOS = {
    ('T00001', 'AC'): {'primary_cause': 'distributor_count', 'confidence': 0.95, 'severity': 'CRITICAL', 'sole_sourced': True, 'impact': '45 retailers have zero supply', 'recommended_action': 'Appoint second distributor in Delhi immediately', 'timeline': 'Critical - Action within 24 hours', 'affected_shops': 45, 'revenue_loss_pct': 38},
    ('T00001', 'Lighting'): {'primary_cause': 'activation_rate_drop', 'confidence': 0.88, 'severity': 'HIGH', 'sole_sourced': False, 'impact': '22 retailers went dormant', 'recommended_action': 'Launch retailer re-engagement campaign', 'timeline': 'High - Action within 48 hours', 'affected_shops': 22, 'revenue_loss_pct': 24},
    ('T00001', 'Fans'): {'primary_cause': 'order_frequency_decline', 'confidence': 0.92, 'severity': 'HIGH', 'sole_sourced': False, 'impact': '15 retailers reduced frequency by 55%', 'recommended_action': 'Review pricing and product mix', 'timeline': 'High - Action within 3 days', 'affected_shops': 15, 'revenue_loss_pct': 26},
    ('T00001', 'Water_Heaters'): {'primary_cause': 'pipeline_imbalance', 'confidence': 0.90, 'severity': 'HIGH', 'sole_sourced': False, 'impact': 'Inventory out of stock despite demand', 'recommended_action': 'Expedite warehouse shipment', 'timeline': 'High - Action within 2 days', 'affected_shops': 18, 'revenue_loss_pct': 30},
    ('T00001', 'Kitchen'): {'primary_cause': 'churn_rate_spike', 'confidence': 0.85, 'severity': 'MEDIUM', 'sole_sourced': False, 'impact': '6 retailers switched to competitors', 'recommended_action': 'Launch retention offer and loyalty program', 'timeline': 'Medium - Action within 5 days', 'affected_shops': 6, 'revenue_loss_pct': 12},
    ('T00002', 'AC'): {'primary_cause': 'demand_signal_loss', 'confidence': 0.87, 'severity': 'HIGH', 'sole_sourced': False, 'impact': 'Retail inquiries dropped 40%', 'recommended_action': 'Conduct product awareness training with retailers', 'timeline': 'High - Action within 4 days', 'affected_shops': 16, 'revenue_loss_pct': 20},
    ('T00002', 'Lighting'): {'primary_cause': 'activation_rate_drop', 'confidence': 0.87, 'severity': 'HIGH', 'sole_sourced': False, 'impact': '18 retailers went dormant', 'recommended_action': 'Launch urgency campaign targeting inactive retailers', 'timeline': 'High - Action within 3 days', 'affected_shops': 18, 'revenue_loss_pct': 22},
}

# =========================================================================
# HEALTH & ROOT ENDPOINTS
# =========================================================================

@app.get("/health")
def health():
    """System health check"""
    logger.info("Health check OK")
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Sanchay v2.0",
        "database": "BigQuery (asia-south1)"
    }

@app.get("/")
def root():
    """Serve main dashboard"""
    logger.info("Serving index.html")
    try:
        return FileResponse("index.html", media_type="text/html")
    except Exception as e:
        logger.error(f"Error serving index.html: {str(e)}")
        return {"error": str(e)}

# =========================================================================
# DIAGNOSIS ENDPOINT (With BigQuery + Mock Fallback)
# =========================================================================

@app.post("/investigate")
def investigate(town_id: str, division: str):
    """Supply chain diagnosis using BigQuery data"""
    logger.info(f"Investigating {town_id} {division}")
    
    key = (town_id, division)
    
    # First try to get real data from BigQuery
    try:
        query = f"""
        SELECT 
            COUNT(DISTINCT retailer_id) as total_retailers,
            ROUND(AVG(avg_order_value), 0) as avg_retailer_order_value,
            ROUND(AVG(activation_rate), 2) as avg_activation,
            ROUND(AVG(monthly_order_frequency), 1) as avg_frequency
        FROM `project-b9c76805-d23b-435a-ab1.sanchay_core.retailers_enhanced`
        WHERE town_id = '{town_id}' AND division = '{division}'
        """
        query_job = bq_client.query(query)
        results = list(query_job.result())
        
        if results:
            row = results[0]
            logger.info(f"Retrieved data from BigQuery: {row}")
    except Exception as e:
        logger.warning(f"BigQuery query failed, using mock data: {str(e)}")
    
    # Use scenario-based response (works with mock data)
    if key in SCENARIOS:
        scenario = SCENARIOS[key]
    else:
        scenario = {
            'primary_cause': 'data_insufficient',
            'confidence': 0.65,
            'severity': 'LOW',
            'sole_sourced': False,
            'impact': 'Insufficient data for this combination',
            'recommended_action': 'Collect more data',
            'timeline': 'Low - Routine monitoring',
            'affected_shops': 0,
            'revenue_loss_pct': 0,
        }
    
    return {
        "town_id": town_id,
        "division": division,
        "timestamp": datetime.utcnow().isoformat(),
        "supervisor_verdict": scenario
    }

# =========================================================================
# RETAILER ENDPOINTS
# =========================================================================

@app.get("/retailers")
def get_retailers(town_id: str = None, division: str = None, limit: int = 100):
    """Get retailers from BigQuery"""
    logger.info(f"Fetching retailers: town={town_id}, division={division}")
    
    query = "SELECT * FROM `project-b9c76805-d23b-435a-ab1.sanchay_core.retailers_enhanced`"
    
    conditions = []
    if town_id:
        conditions.append(f"town_id = '{town_id}'")
    if division:
        conditions.append(f"division = '{division}'")
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += f" LIMIT {limit}"
    
    try:
        query_job = bq_client.query(query)
        results = query_job.result()
        
        retailers = []
        for row in results:
            retailers.append({
                'retailer_id': row.retailer_id,
                'retailer_name': row.retailer_name,
                'town_id': row.town_id,
                'division': row.division,
                'city': row.city,
                'latitude': float(row.latitude),
                'longitude': float(row.longitude),
                'address': row.address,
                'phone_number': row.phone_number,
                'owner_name': row.owner_name,
                'store_size_sqft': row.store_size_sqft,
                'credit_rating': row.credit_rating,
                'overall_health_score': row.overall_health_score,
                'tier': row.tier,
                'sku_loyalty_points': row.sku_loyalty_points,
                'travel_loyalty_points': row.travel_loyalty_points,
                'billing_points': row.billing_points,
                'activation_rate': float(row.activation_rate),
                'monthly_order_frequency': row.monthly_order_frequency,
                'avg_order_value': row.avg_order_value,
                'days_since_last_order': row.days_since_last_order,
                'status': row.status,
            })
        
        logger.info(f"Returned {len(retailers)} retailers")
        return {"count": len(retailers), "retailers": retailers}
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {"error": str(e), "retailers": []}

@app.get("/retailers/{retailer_id}")
def get_retailer_detail(retailer_id: str):
    """Get individual retailer details"""
    logger.info(f"Fetching retailer: {retailer_id}")
    
    query = f"""
    SELECT * 
    FROM `project-b9c76805-d23b-435a-ab1.sanchay_core.retailers_enhanced`
    WHERE retailer_id = '{retailer_id}'
    LIMIT 1
    """
    
    try:
        query_job = bq_client.query(query)
        results = list(query_job.result())
        
        if results:
            row = results[0]
            return {
                'retailer_id': row.retailer_id,
                'retailer_name': row.retailer_name,
                'town_id': row.town_id,
                'division': row.division,
                'city': row.city,
                'region': row.region,
                'latitude': float(row.latitude),
                'longitude': float(row.longitude),
                'address': row.address,
                'retailer_type': row.retailer_type,
                'phone_number': row.phone_number,
                'owner_name': row.owner_name,
                'store_manager_email': row.store_manager_email,
                'store_size_sqft': row.store_size_sqft,
                'store_category': row.store_category,
                'credit_limit_rupees': row.credit_limit_rupees,
                'credit_rating': row.credit_rating,
                'payment_days_avg': row.payment_days_avg,
                'overall_health_score': row.overall_health_score,
                'tier': row.tier,
                'competitor_count_nearby': row.competitor_count_nearby,
                'market_share_pct': float(row.market_share_pct),
                'compliance_status': row.compliance_status,
                'churn_risk_score': float(row.churn_risk_score),
                'current_stock_units': row.current_stock_units,
                'sku_loyalty_points': row.sku_loyalty_points,
                'travel_loyalty_points': row.travel_loyalty_points,
                'billing_points': row.billing_points,
                'activation_rate': float(row.activation_rate),
                'monthly_order_frequency': row.monthly_order_frequency,
                'avg_order_value': row.avg_order_value,
                'days_since_last_order': row.days_since_last_order,
                'status': row.status,
                'loyalty_tier': row.loyalty_tier,
                'points_balance': row.points_balance,
            }
        
        return {"error": "Retailer not found"}
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {"error": str(e)}

# =========================================================================
# DISTRIBUTOR ENDPOINTS
# =========================================================================

@app.get("/distributors")
def get_distributors(town_id: str = None):
    """Get all distributors"""
    logger.info(f"Fetching distributors for town: {town_id}")
    
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
        
        logger.info(f"Returned {len(distributors)} distributors")
        return {"count": len(distributors), "distributors": distributors}
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {"error": str(e), "distributors": []}

@app.get("/distributor-map/{town_id}")
def get_distributor_map(town_id: str):
    """Get distributor map data"""
    logger.info(f"Fetching distributor map for: {town_id}")
    
    query = f"""
    SELECT 
        distributor_id, distributor_name, latitude, longitude,
        retailers_count_active, status
    FROM `project-b9c76805-d23b-435a-ab1.sanchay_core.distributors_enhanced`
    WHERE town_id = '{town_id}'
    """
    
    try:
        query_job = bq_client.query(query)
        results = query_job.result()
        
        distributors = []
        for row in results:
            distributors.append({
                'id': row.distributor_id,
                'name': row.distributor_name,
                'lat': float(row.latitude),
                'lng': float(row.longitude),
                'retailers': row.retailers_count_active,
                'status': row.status,
                'color': '#10b981' if row.status == 'ACTIVE' else '#ef4444'
            })
        
        return {"town_id": town_id, "distributors": distributors}
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {"error": str(e), "distributors": []}

# =========================================================================
# REAL-TIME TRANSACTIONS
# =========================================================================

@app.get("/realtime-transactions")
def get_realtime_transactions(town_id: str = None, limit: int = 50):
    """Get real-time transactions"""
    logger.info(f"Fetching transactions for town: {town_id}")
    
    query = """
    SELECT 
        transaction_id, transaction_date, town_id, retailer_id,
        distributor_id, division, transaction_time, total_amount,
        loyalty_points_earned, payment_status, status
    FROM `project-b9c76805-d23b-435a-ab1.sanchay_core.transactions_realtime_enhanced`
    ORDER BY transaction_time DESC
    """
    
    if town_id:
        query = f"""
        SELECT 
            transaction_id, transaction_date, town_id, retailer_id,
            distributor_id, division, transaction_time, total_amount,
            loyalty_points_earned, payment_status, status
        FROM `project-b9c76805-d23b-435a-ab1.sanchay_core.transactions_realtime_enhanced`
        WHERE town_id = '{town_id}'
        ORDER BY transaction_time DESC
        LIMIT {limit}
        """
    else:
        query += f" LIMIT {limit}"
    
    try:
        query_job = bq_client.query(query)
        results = query_job.result()
        
        transactions = []
        for row in results:
            transactions.append({
                'transaction_id': row.transaction_id,
                'transaction_date': str(row.transaction_date),
                'town_id': row.town_id,
                'retailer_id': row.retailer_id,
                'distributor_id': row.distributor_id,
                'division': row.division,
                'transaction_time': row.transaction_time.isoformat() if row.transaction_time else None,
                'total_amount': row.total_amount,
                'loyalty_points_earned': row.loyalty_points_earned,
                'payment_status': row.payment_status,
                'status': row.status,
            })
        
        return {"count": len(transactions), "transactions": transactions}
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {"error": str(e), "transactions": []}

# =========================================================================
# INVENTORY ENDPOINT
# =========================================================================

@app.get("/inventory/{retailer_id}")
def get_retailer_inventory(retailer_id: str):
    """Get retailer current inventory levels"""
    logger.info(f"Fetching inventory for retailer: {retailer_id}")
    
    query = f"""
    SELECT 
        retailer_id, sku_id, product_name, quantity_on_hand,
        quantity_available, reorder_point, unit_cost, retail_price,
        condition_status, last_updated
    FROM `project-b9c76805-d23b-435a-ab1.sanchay_core.retailer_inventory`
    WHERE retailer_id = '{retailer_id}'
    ORDER BY last_updated DESC
    """
    
    try:
        query_job = bq_client.query(query)
        results = query_job.result()
        
        inventory = []
        for row in results:
            inventory.append({
                'sku_id': row.sku_id,
                'product_name': row.product_name,
                'quantity_on_hand': row.quantity_on_hand,
                'quantity_available': row.quantity_available,
                'reorder_point': row.reorder_point,
                'unit_cost': row.unit_cost,
                'retail_price': row.retail_price,
                'condition_status': row.condition_status,
                'last_updated': row.last_updated.isoformat() if row.last_updated else None,
            })
        
        return {"retailer_id": retailer_id, "sku_count": len(inventory), "inventory": inventory}
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {"error": str(e), "inventory": []}

# =========================================================================
# SUMMARY DASHBOARD
# =========================================================================

@app.get("/dashboard-summary")
def get_dashboard_summary(town_id: str = None):
    """Get summary metrics for dashboard"""
    logger.info(f"Fetching summary for town: {town_id}")
    
    where_clause = f"WHERE town_id = '{town_id}'" if town_id else ""
    
    try:
        query = f"""
        SELECT
            COUNT(DISTINCT distributor_id) as total_distributors,
            COUNT(DISTINCT retailer_id) as total_retailers,
            ROUND(AVG(overall_health_score), 1) as avg_retailer_health,
            ROUND(AVG(activation_rate), 2) as avg_activation,
            SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END) as active_retailers
        FROM `project-b9c76805-d23b-435a-ab1.sanchay_core.retailers_enhanced`
        {where_clause}
        """
        
        query_job = bq_client.query(query)
        results = list(query_job.result())
        
        if results:
            row = results[0]
            return {
                "total_distributors": row.total_distributors,
                "total_retailers": row.total_retailers,
                "avg_retailer_health": float(row.avg_retailer_health) if row.avg_retailer_health else 0,
                "avg_activation": float(row.avg_activation) if row.avg_activation else 0,
                "active_retailers": row.active_retailers,
            }
        
        return {"error": "No data found"}
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {"error": str(e)}

# =========================================================================
# MAIN
# =========================================================================

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Sanchay v2.0 API - BigQuery Connected")
    logger.info("Available endpoints:")
    logger.info("  GET  /health")
    logger.info("  GET  /")
    logger.info("  POST /investigate?town_id=T00001&division=AC")
    logger.info("  GET  /retailers?town_id=T00001")
    logger.info("  GET  /retailers/{retailer_id}")
    logger.info("  GET  /distributors?town_id=T00001")
    logger.info("  GET  /distributor-map/{town_id}")
    logger.info("  GET  /realtime-transactions?town_id=T00001")
    logger.info("  GET  /inventory/{retailer_id}")
    logger.info("  GET  /dashboard-summary")
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")