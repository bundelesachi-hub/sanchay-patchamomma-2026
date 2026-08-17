"""
Build summary report from investigation results.
"""
import json
import pandas as pd
from collections import defaultdict

def load_results():
    """Load investigation results."""
    with open("investigation_results.json", "r") as f:
        return json.load(f)

def summarize_findings(results: list) -> dict:
    """
    Aggregate findings across all anomalies.
    """
    summary = {
        "total_investigated": len(results),
        "primary_causes": defaultdict(int),
        "sole_sourced_failures": 0,
        "critical_actions": 0,
        "avg_confidence": 0,
        "by_cause": {},
    }
    
    confidences = []
    
    for r in results:
        # Primary cause distribution
        cause = r.get("primary_cause", "unknown")
        summary["primary_causes"][cause] += 1
        
        # Sole-sourced count
        if r.get("sole_sourced"):
            summary["sole_sourced_failures"] += 1
        
        # Critical actions
        if "CRITICAL" in r.get("recommended_action", ""):
            summary["critical_actions"] += 1
        
        # Confidence
        conf = r.get("confidence", 0)
        confidences.append(conf)
        
        # By-cause detail
        if cause not in summary["by_cause"]:
            summary["by_cause"][cause] = {
                "count": 0,
                "avg_confidence": [],
                "examples": []
            }
        summary["by_cause"][cause]["count"] += 1
        summary["by_cause"][cause]["avg_confidence"].append(conf)
        if len(summary["by_cause"][cause]["examples"]) < 3:
            summary["by_cause"][cause]["examples"].append({
                "town_id": r.get("town_id"),
                "division": r.get("division"),
                "explanation": r.get("explanation")
            })
    
    # Compute averages
    if confidences:
        summary["avg_confidence"] = round(sum(confidences) / len(confidences), 3)
    
    for cause in summary["by_cause"]:
        if summary["by_cause"][cause]["avg_confidence"]:
            avg = sum(summary["by_cause"][cause]["avg_confidence"]) / len(summary["by_cause"][cause]["avg_confidence"])
            summary["by_cause"][cause]["avg_confidence"] = round(avg, 3)
    
    return summary

def generate_report(results: list, summary: dict) -> str:
    """
    Generate markdown report.
    """
    report = f"""
# Sanchay Investigation Report

## Executive Summary

**Total Anomalies Investigated:** {summary['total_investigated']}  
**Sole-Sourced Failures:** {summary['sole_sourced_failures']} ({100*summary['sole_sourced_failures']/summary['total_investigated']:.0f}%)  
**Critical Actions Recommended:** {summary['critical_actions']}  
**Average Confidence:** {summary['avg_confidence']}  

---

## Root Causes

### Distribution by Primary Cause

"""
    
    for cause, count in sorted(summary["primary_causes"].items(), key=lambda x: -x[1]):
        pct = 100 * count / summary["total_investigated"]
        avg_conf = summary["by_cause"][cause].get("avg_confidence", 0)
        report += f"\n**{cause.upper()}**: {count} cases ({pct:.0f}%) | Confidence: {avg_conf}\n"
        
        # Examples
        for ex in summary["by_cause"][cause]["examples"]:
            report += f"- {ex['town_id']} {ex['division']}: {ex['explanation']}\n"
    
    report += f"""

---

## Key Findings

1. **Sole-Sourced Risk**: {summary['sole_sourced_failures']} town-division cells operate without backup supply.
   - These represent TOTAL revenue risk if distributor fails.
   - Recommended action: Appoint second distributor in each.

2. **Primary Cause Breakdown**:
"""
    
    for cause, count in sorted(summary["primary_causes"].items(), key=lambda x: -x[1]):
        report += f"   - {cause}: {count} cases\n"
    
    report += f"""

3. **Critical Interventions Required**: {summary['critical_actions']}
   - These are high-confidence findings requiring immediate action.

---

## Methodology

- Investigator: Five-factor decomposition (D × R/D × a × f × v)
- Confidence threshold: 0.6+
- Data source: Sanchay metric tree + historical trends
- Investigation date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

"""
    
    return report

if __name__ == "__main__":
    results = load_results()
    summary = summarize_findings(results)
    report = generate_report(results, summary)
    
    # Save report
    with open("INVESTIGATION_REPORT.md", "w") as f:
        f.write(report)
    
    print(report)
    print("\n✓ Report saved to INVESTIGATION_REPORT.md")