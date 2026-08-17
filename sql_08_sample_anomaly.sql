SELECT 
  town_id,
  division,
  month,
  secondary_sales,
  severity,
  confidence
FROM `project-b9c76805-d23b-435a-ab1.sanchay_core.anomaly_detection`
WHERE severity = 'TOTAL_COLLAPSE'
LIMIT 5;