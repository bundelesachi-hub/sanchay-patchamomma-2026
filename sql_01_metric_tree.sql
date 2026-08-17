CREATE OR REPLACE TABLE `project-b9c76805-d23b-435a-ab1.sanchay_core.agg_town_division_month` AS
WITH distributor_count AS (
  SELECT
    s.town_id,
    s.division,
    s.month,
    COUNT(DISTINCT m.distributor_id) AS D
  FROM `project-b9c76805-d23b-435a-ab1.sanchay_raw.fact_secondary` s
  LEFT JOIN `project-b9c76805-d23b-435a-ab1.sanchay_raw.map_retailer_dist` m
    ON s.town_id = m.town_id AND s.division = m.division
  GROUP BY 1, 2, 3
),
retailer_per_dist AS (
  SELECT
    s.town_id,
    s.division,
    s.month,
    COUNT(DISTINCT m.retailer_id) AS R
  FROM `project-b9c76805-d23b-435a-ab1.sanchay_raw.fact_secondary` s
  LEFT JOIN `project-b9c76805-d23b-435a-ab1.sanchay_raw.map_retailer_dist` m
    ON s.town_id = m.town_id AND s.division = m.division
  GROUP BY 1, 2, 3
)
SELECT
  s.town_id,
  s.division,
  s.month,
  dc.D AS distributor_count,
  ROUND(SAFE_DIVIDE(rpd.R, NULLIF(dc.D, 0)), 2) AS retailers_per_dist,
  s.active_rate,
  s.frequency,
  s.avg_value,
  s.secondary_sales,
  ROUND(
    dc.D * SAFE_DIVIDE(rpd.R, NULLIF(dc.D, 0)) * s.active_rate * s.frequency * s.avg_value, 0
  ) AS reconstructed_sales
FROM `project-b9c76805-d23b-435a-ab1.sanchay_raw.fact_secondary` s
JOIN distributor_count dc
  ON s.town_id = dc.town_id AND s.division = dc.division AND s.month = dc.month
JOIN retailer_per_dist rpd
  ON s.town_id = rpd.town_id AND s.division = rpd.division AND s.month = rpd.month
ORDER BY s.town_id, s.division, s.month;