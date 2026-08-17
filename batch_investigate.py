"""
Batch process all anomalies through the investigation framework.
"""
import json
from google.cloud import bigquery
from agents.orchestrator import investigate
import time

PROJECT_ID = "project-b9c76805-d23b-435a-ab1"
client = bigquery.Client(project=PROJECT_ID)

def get_anomalies(limit: int = None) -> list:
    """
    Fetch anomalies from alerts table.
    """
    query = f"""
    SELECT DISTINCT town_id, division
    FROM `{PROJECT_ID}.sanchay_core.alerts`
    WHERE severity = 'TOTAL_COLLAPSE'
    ORDER BY town_id, division
    """
    if limit:
        query += f" LIMIT {limit}"
    
    rows = list(client.query(query).result())
    return [(r.town_id, r.division) for r in rows]

def batch_investigate(limit: int = None):
    """
    Run investigation on all anomalies and save results.
    """
    anomalies = get_anomalies(limit)
    
    print(f"\n{'='*70}")
    print(f"BATCH INVESTIGATION: {len(anomalies)} anomalies")
    print(f"{'='*70}\n")
    
    results = []
    errors = []
    
    for i, (town_id, division) in enumerate(anomalies, 1):
        print(f"[{i}/{len(anomalies)}] Investigating {town_id} {division}...", end=" ")
        
        try:
            result = investigate(town_id, division)
            result["town_id"] = town_id
            result["division"] = division
            results.append(result)
            print("✓")
            
            # Rate limit: 1 second between calls
            time.sleep(1)
        except Exception as e:
            print(f"✗ {str(e)[:50]}")
            errors.append({"town_id": town_id, "division": division, "error": str(e)})
    
    # Save results
    with open("investigation_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    with open("investigation_errors.json", "w") as f:
        json.dump(errors, f, indent=2)
    
    print(f"\n{'='*70}")
    print(f"COMPLETE: {len(results)} successful, {len(errors)} errors")
    print(f"Results saved to investigation_results.json")
    print(f"{'='*70}\n")
    
    return results

if __name__ == "__main__":
    # Start with a small sample (10) for testing
    results = batch_investigate(limit=10)