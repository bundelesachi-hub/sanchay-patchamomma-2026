CREATE OR REPLACE TABLE `project-b9c76805-d23b-435a-ab1.sanchay_core.distributor_drill` AS
SELECT
  m.town_id,
  m.division,
  COUNT(DISTINCT m.distributor_id) AS n_distributors,
  COUNT(DISTINCT m.retailer_id) AS n_retailers,
  ARRAY_AGG(DISTINCT m.distributor_id) AS distributor_ids
FROM `project-b9c76805-d23b-435a-ab1.sanchay_raw.map_retailer_dist` m
GROUP BY 1, 2
ORDER BY 1, 2;