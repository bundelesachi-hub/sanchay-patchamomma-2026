CREATE OR REPLACE TABLE `project-b9c76805-d23b-435a-ab1.sanchay_core.agg_town_division_month` AS
SELECT
  s.town_id,
  s.division,
  s.month,
  s.D AS distributor_count,
  s.R_over_D AS retailers_per_dist,
  s.active_rate,
  s.frequency,
  s.avg_value,
  s.secondary_sales,
  ROUND(
    s.D * s.R_over_D * s.active_rate * s.frequency * s.avg_value, 0
  ) AS reconstructed_sales
FROM `project-b9c76805-d23b-435a-ab1.sanchay_raw.fact_secondary` s
ORDER BY s.town_id, s.division, s.month;