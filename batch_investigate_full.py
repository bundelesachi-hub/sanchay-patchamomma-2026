import json
from google.cloud import bigquery
from agents.orchestrator import investigate
import time
from datetime import datetime

PROJECT_ID = "project-b9c76805-d23b-435a-ab1"
client = bigquery.Client(project=PROJECT_ID)

def get_anomalies(limit=None):
    query = """
    SELECT DISTINCT town_id, division
    FROM `{}.sanchay_core.alerts`
    WHERE severity = 'TOTAL_COLLAPSE'
    ORDER BY town_id, division
    """.format(PROJECT_ID)
    if limit:
        query += " LIMIT {}".format(limit)
    rows = list(client.query(query).result())
    return [(r.town_id, r.division) for r in rows]

def batch_investigate_full():
    anomalies = get_anomalies()
    print("\nBATCH INVESTIGATION: {} anomalies".format(len(anomalies)))
    print("Start: {}\n".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    
    results = []
    errors = []
    
    for i, (town_id, division) in enumerate(anomalies, 1):
        eta = ((len(anomalies) - i) * 2) / 60
        print("[{}/{}] {} {} ETA: {:.1f}m ".format(i, len(anomalies), town_id, division, eta), end="", flush=True)
        
        try:
            result = investigate(town_id, division)
            result["town_id"] = town_id
            result["division"] = division
            results.append(result)
            print("OK")
            time.sleep(2)
        except Exception as e:
            print("ERROR")
            errors.append({"town_id": town_id, "division": division, "error": str(e)})
            time.sleep(2)
    
    with open("investigation_results_full.json", "w") as f:
        json.dump(results, f, indent=2)
    with open("investigation_errors_full.json", "w") as f:
        json.dump(errors, f, indent=2)
    
    print("\nCOMPLETE: {} successful, {} errors".format(len(results), len(errors)))
    print("End: {}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    print("Runtime: ~{:.1f} hours\n".format(len(anomalies) * 2 / 3600))

if __name__ == "__main__":
    batch_investigate_full()