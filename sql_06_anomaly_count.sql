SELECT 
  severity,
  COUNT(*) as count
FROM `project-b9c76805-d23b-435a-ab1.sanchay_core.anomaly_detection`
GROUP BY 1
ORDER BY 1;