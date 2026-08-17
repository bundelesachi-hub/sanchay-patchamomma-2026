"""
BigQuery tools for agents to query the metric tree and anomaly data.
"""
from google.cloud import bigquery

PROJECT_ID = "project-b9c76805-d23b-435a-ab1"

def get_metric_tree(town_id: str, division: str, month: int) -> dict:
    """
    Fetch the metric tree (S = D × R/D × a × f × v) for a specific anomaly.
    """
    client = bigquery.Client(project=PROJECT_ID)
    query = f"""
    SELECT
      town_id, division, month,
      distributor_count AS D,
      retailers_per_dist AS R_over_D,
      active_rate AS a,
      frequency AS f,
      avg_value AS v,
      secondary_sales AS S
    FROM `{PROJECT_ID}.sanchay_core.agg_town_division_month`
    WHERE town_id = '{town_id}' AND division = '{division}' AND month = {month}
    """
    try:
        job = client.query(query)
        rows = job.result()
        row_list = [dict(row) for row in rows]
        
        if len(row_list) == 0:
            return {"error": "No data found"}
        
        row = row_list[0]
        return {
            "town_id": row['town_id'],
            "division": row['division'],
            "month": row['month'],
            "D": float(row['D']) if row['D'] else 0,
            "R_over_D": float(row['R_over_D']) if row['R_over_D'] else 0,
            "a": float(row['a']) if row['a'] else 0,
            "f": float(row['f']) if row['f'] else 0,
            "v": float(row['v']) if row['v'] else 0,
            "S": float(row['S']) if row['S'] else 0,
        }
    except Exception as e:
        return {"error": str(e)}

def get_distributor_info(town_id: str, division: str) -> dict:
    """
    Get distributor(s) serving this town-division cell.
    """
    client = bigquery.Client(project=PROJECT_ID)
    query = f"""
    SELECT
      distributor_id,
      COUNT(DISTINCT retailer_id) AS retailer_count
    FROM `{PROJECT_ID}.sanchay_raw.map_retailer_dist`
    WHERE town_id = '{town_id}' AND division = '{division}'
    GROUP BY 1
    """
    try:
        job = client.query(query)
        rows = [dict(row) for row in job.result()]
        return {
            "town_id": town_id,
            "division": division,
            "n_distributors": len(rows),
            "distributors": [
                {"id": r['distributor_id'], "retailers": int(r['retailer_count'])}
                for r in rows
            ]
        }
    except Exception as e:
        return {"error": str(e)}

def get_alert_details(town_id: str, division: str) -> dict:
    """
    Get the alert that triggered this investigation.
    """
    client = bigquery.Client(project=PROJECT_ID)
    query = f"""
    SELECT
      town_id, division, month,
      secondary_sales, severity, confidence
    FROM `{PROJECT_ID}.sanchay_core.alerts`
    WHERE town_id = '{town_id}' AND division = '{division}'
    ORDER BY month DESC LIMIT 1
    """
    try:
        job = client.query(query)
        rows = [dict(row) for row in job.result()]
        
        if len(rows) == 0:
            return {"error": "No alert found"}
        
        r = rows[0]
        return {
            "town_id": r['town_id'],
            "division": r['division'],
            "month": int(r['month']),
            "secondary_sales": float(r['secondary_sales']) if r['secondary_sales'] else 0,
            "severity": r['severity'],
            "confidence": float(r['confidence']) if r['confidence'] else 0,
        }
    except Exception as e:
        return {"error": str(e)}

def get_historical_trend(town_id: str, division: str, months_back: int = 6) -> dict:
    """
    Get historical trend for comparison.
    """
    client = bigquery.Client(project=PROJECT_ID)
    query = f"""
    SELECT
      month,
      secondary_sales,
      distributor_count,
      active_rate,
      frequency,
      avg_value
    FROM `{PROJECT_ID}.sanchay_core.agg_town_division_month`
    WHERE town_id = '{town_id}' AND division = '{division}'
    ORDER BY month DESC LIMIT {months_back}
    """
    try:
        job = client.query(query)
        rows = [dict(row) for row in job.result()]
        
        return {
            "town_id": town_id,
            "division": division,
            "history": [
                {
                    "month": int(r['month']),
                    "sales": float(r['secondary_sales']) if r['secondary_sales'] else 0,
                    "D": int(r['distributor_count']) if r['distributor_count'] else 0,
                    "a": float(r['active_rate']) if r['active_rate'] else 0,
                    "f": float(r['frequency']) if r['frequency'] else 0,
                    "v": float(r['avg_value']) if r['avg_value'] else 0,
                }
                for r in rows
            ]
        }
    except Exception as e:
        return {"error": str(e)}