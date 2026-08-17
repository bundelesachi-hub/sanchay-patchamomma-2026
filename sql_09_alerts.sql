CREATE OR REPLACE TABLE `project-b9c76805-d23b-435a-ab1.sanchay_core.alerts` AS
SELECT
  town_id,
  division,
  month,
  secondary_sales,
  severity,
  confidence,
  CURRENT_TIMESTAMP() AS alert_created_at
FROM `project-b9c76805-d23b-435a-ab1.sanchay_core.anomaly_detection`
ORDER BY severity DESC, confidence DESC, town_id, division, month;