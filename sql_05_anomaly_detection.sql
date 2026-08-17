CREATE OR REPLACE TABLE `project-b9c76805-d23b-435a-ab1.sanchay_core.anomaly_detection` AS
WITH monthly_stats AS (
  -- Compute median and standard deviation for each town-division
  SELECT
    town_id,
    division,
    APPROX_QUANTILES(secondary_sales, 100)[OFFSET(50)] AS median_sales,
    STDDEV_POP(secondary_sales) AS stdev_sales,
    COUNT(*) AS n_months
  FROM `project-b9c76805-d23b-435a-ab1.sanchay_core.agg_town_division_month`
  WHERE secondary_sales > 0
  GROUP BY 1, 2
),
robust_z_score AS (
  -- Robust z-score: (value - median) / (1.4826 * MAD)
  -- MAD = median absolute deviation
  SELECT
    a.town_id,
    a.division,
    a.month,
    a.secondary_sales,
    ms.median_sales,
    CASE
      WHEN a.secondary_sales = 0 AND ms.median_sales > 0 THEN 'TOTAL_COLLAPSE'
      WHEN ms.stdev_sales = 0 THEN 'INSUFFICIENT_VARIANCE'
      WHEN ABS(a.secondary_sales - ms.median_sales) / (1.4826 * GREATEST(ms.stdev_sales, 1)) < -2.5 THEN 'HIGH'
      WHEN ABS(a.secondary_sales - ms.median_sales) / (1.4826 * GREATEST(ms.stdev_sales, 1)) < -1.5 THEN 'MEDIUM'
      ELSE 'LOW'
    END AS severity,
    ROUND(
      SAFE_DIVIDE(
        a.secondary_sales - ms.median_sales,
        NULLIF(ms.median_sales, 0)
      ), 4
    ) AS pct_deviation
  FROM `project-b9c76805-d23b-435a-ab1.sanchay_core.agg_town_division_month` a
  LEFT JOIN monthly_stats ms
    ON a.town_id = ms.town_id AND a.division = ms.division
)
SELECT
  town_id,
  division,
  month,
  secondary_sales,
  median_sales,
  pct_deviation,
  severity,
  CASE
    WHEN severity = 'TOTAL_COLLAPSE' THEN 0.95
    WHEN severity = 'HIGH' THEN 0.85
    WHEN severity = 'MEDIUM' THEN 0.60
    ELSE 0.10
  END AS confidence
FROM robust_z_score
WHERE severity IN ('TOTAL_COLLAPSE', 'HIGH', 'MEDIUM')
ORDER BY town_id, division, month;