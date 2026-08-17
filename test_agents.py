"""
Test the investigation against T00001.
"""
import json
from agents.orchestrator import investigate

print("Investigating T00001 AC collapse...")
print("="*70)

result = investigate(town_id="T00001", division="AC")

print(json.dumps(result, indent=2))
print("="*70)