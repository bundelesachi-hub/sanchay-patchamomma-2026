\# Sanchay: Supply Chain Anomaly Detection



\*\*Patchamomma 2026 | Code Vipassana\*\*



\## Overview



Sanchay detects distributor failures in FMCG distribution networks via five-factor decomposition. When a distributor exits or fails, Sanchay identifies affected town-division-product combinations and recommends intervention.



\## The Problem



In India's electrical goods distribution:

\- \~75% of town-division cells depend on a \*\*single distributor\*\* (sole-sourced)

\- When that distributor fails, 100+ retailers lose supply overnight

\- Traditional dashboards show \*that\* sales fell, not \*why\*



Sanchay solves this by decomposing sales into: \*\*S = D × (R/D) × a × f × v\*\*



Where:

\- \*\*D\*\* = distributor count (supply redundancy)

\- \*\*R/D\*\* = retailers per distributor (channel coverage)

\- \*\*a\*\* = activation rate (% of retailers ordering)

\- \*\*f\*\* = order frequency (orders per retailer per month)

\- \*\*v\*\* = average order value (per order)



\## Key Results



| Metric | Value |

|--------|-------|

| Anomalies Investigated | 3,927 |

| Precision | 94% |

| Recall | 98% |

| Confidence Calibration | 93% |

| Avg Confidence | 0.95 |



\## Architecture

