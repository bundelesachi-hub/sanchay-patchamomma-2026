"""
Sanchay v3 synthetic data generator.

Distributors are per-town (3-5), carrying 2-3 divisions each.
~75% of town × division cells are sole-sourced.

Contract: Sales(town, division, month) = D × (R/D) × a × f × v holds exactly.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
import json
from pathlib import Path
from .config import DEFAULT, ScaleConfig

SEED = 20260810
rng = np.random.default_rng(SEED)

DIVISIONS = [
    "Lighting", "Wire", "Switchgear", "Fans",
    "WaterHeater", "Kitchen", "AC", "Cable"
]

DIVISION_BUNDLES = [
    ["Lighting", "Fans"],
    ["Wire", "Cable"],
    ["Switchgear", "Wire"],
    ["AC", "WaterHeater"],
    ["Kitchen", "WaterHeater", "Fans"],
    ["Lighting", "Switchgear", "Fans"],
    ["Wire", "Cable", "Switchgear"],
    ["Lighting", "Wire"],
]

TIER_MIX = {
    "Metro": 0.03,
    "Tier1": 0.09,
    "Tier2": 0.22,
    "Tier3": 0.36,
    "Tier4": 0.30
}

TIER_SCALE = {
    "Metro": 2.2,
    "Tier1": 1.5,
    "Tier2": 1.05,
    "Tier3": 0.75,
    "Tier4": 0.45
}


def build_towns(cfg: ScaleConfig = DEFAULT) -> pd.DataFrame:
    """Create the master town list."""
    n = cfg.distributor_towns
    tiers = list(TIER_MIX.keys())
    tier_probs = [TIER_MIX[t] for t in tiers]
    
    df = pd.DataFrame({
        "town_id": [f"T{i:05d}" for i in range(1, n + 1)],
        "tier": rng.choice(tiers, size=n, p=tier_probs),
    })
    
    df["lat"] = rng.uniform(8.5, 33.5, n).round(4)
    df["lon"] = rng.uniform(69.0, 92.5, n).round(4)
    df["town_name"] = [f"{row.tier[:2].upper()}-{i}" for i, row in enumerate(df.itertuples(), 1)]
    
    lo, hi = cfg.distributors_per_town
    skew = df.tier.map(TIER_SCALE).to_numpy()
    skew_norm = (skew - skew.min()) / (skew.max() - skew.min())
    n_dist = np.round(lo + (hi - lo) * skew_norm + rng.normal(0, 0.55, n))
    df["n_distributors"] = np.clip(n_dist, lo, hi).astype(int)
    
    return df


def build_distributors(towns: pd.DataFrame, cfg: ScaleConfig = DEFAULT) -> pd.DataFrame:
    """Create distributors. Each picks a division bundle."""
    lo_r, hi_r = cfg.retailers_per_distributor
    rows, did = [], 1
    
    for t in towns.itertuples(index=False):
        covered: set[str] = set()
        
        for _ in range(t.n_distributors):
            gains = [len(set(b) - covered) for b in DIVISION_BUNDLES]
            best = max(gains)
            pool = [b for b, g in zip(DIVISION_BUNDLES, gains) if g == best]
            bundle = list(pool[int(rng.integers(len(pool)))])
            covered.update(bundle)
            
            capacity = int(rng.integers(lo_r, hi_r + 1))
            rows.append({
                "distributor_id": f"D{did:06d}",
                "town_id": t.town_id,
                "divisions": "|".join(bundle),
                "capacity": capacity,
                "book_size": int(capacity * cfg.utilisation),
                "appointed_month": int(rng.integers(0, 18)),
                "service_quality": round(float(rng.beta(3.2, 1.9)), 4),
                "churned_month": None,
            })
            did += 1
    
    return pd.DataFrame(rows)


def build_retailers_and_mapping(
    towns: pd.DataFrame,
    dists: pd.DataFrame,
    cfg: ScaleConfig = DEFAULT
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build retailers and map them to distributors."""
    dist_by_town = {}
    for d in dists.itertuples(index=False):
        if d.town_id not in dist_by_town:
            dist_by_town[d.town_id] = []
        dist_by_town[d.town_id].append(d)
    
    retailers, mapping = [], []
    rid = 1
    
    for t in towns.itertuples(index=False):
        ds = dist_by_town[t.town_id]
        total_links = sum(d.book_size for d in ds)
        n_retailers = max(1, int(round(total_links / cfg.avg_links_per_retailer)))
        
        r_ids = [f"R{rid + i:07d}" for i in range(n_retailers)]
        rid += n_retailers
        quality = rng.beta(2.4, 2.2, n_retailers)
        
        for r_id, q in zip(r_ids, quality):
            retailers.append({
                "retailer_id": r_id,
                "town_id": t.town_id,
                "shop_type": rng.choice(
                    ["Counter", "Electrical", "Hardware", "Modern"],
                    p=[0.46, 0.29, 0.18, 0.07]
                ),
                "quality": round(float(q), 4),
                "onboard_month": int(rng.integers(0, 24)),
            })
        
        taken: dict[tuple[str, str], str] = {}
        for d in ds:
            divisions = d.divisions.split("|")
            order = np.argsort(-(quality + rng.normal(0, 0.18, n_retailers)))
            filled = 0
            
            for idx in order:
                if filled >= d.book_size:
                    break
                r_id = r_ids[idx]
                free = [dv for dv in divisions if (r_id, dv) not in taken]
                if not free:
                    continue
                
                for dv in free:
                    taken[(r_id, dv)] = d.distributor_id
                    mapping.append({
                        "retailer_id": r_id,
                        "division": dv,
                        "distributor_id": d.distributor_id,
                        "town_id": t.town_id,
                        "mapped_month": max(int(rng.integers(0, 24)), d.appointed_month),
                    })
                filled += 1
    
    return pd.DataFrame(retailers), pd.DataFrame(mapping)


def build_monthly_sales(
    towns: pd.DataFrame,
    mapping: pd.DataFrame,
    months: int = 30
) -> tuple[pd.DataFrame, list]:
    """Generate monthly sales with exact decomposition."""
    rows = []
    anomalies = []
    
    for town in towns.itertuples(index=False):
        for division in DIVISIONS:
            cell_map = mapping[
                (mapping.town_id == town.town_id) &
                (mapping.division == division)
            ]
            
            if len(cell_map) == 0:
                continue
            
            D = cell_map.distributor_id.nunique()
            R_over_D = len(cell_map.retailer_id.unique()) / max(D, 1)
            
            a_base = rng.uniform(0.65, 0.95)
            f_base = rng.uniform(15, 45)
            v_base = rng.uniform(1500, 3500)
            
            for month in range(months):
                season = 1.0 + 0.15 * np.sin(2 * np.pi * month / 12)
                trend = 1.0 + 0.01 * month if month > 0 else 1.0
                shock = rng.normal(1.0, 0.08)
                
                a = max(0.3, min(1.0, a_base * trend * shock))
                f = max(5, f_base * season * rng.normal(1.0, 0.1))
                v = max(500, v_base * rng.normal(1.0, 0.12))
                
                S = D * R_over_D * a * f * v
                
                rows.append({
                    "town_id": town.town_id,
                    "division": division,
                    "month": month,
                    "D": D,
                    "R_over_D": round(R_over_D, 2),
                    "active_rate": round(a, 4),
                    "frequency": round(f, 2),
                    "avg_value": round(v, 2),
                    "secondary_sales": round(S),
                })
            
            if D == 1 and months >= 3:
                anomalies.append({
                    "town_id": town.town_id,
                    "division": division,
                    "distributor_id": cell_map.iloc[0].distributor_id,
                    "n_retailers": len(cell_map.retailer_id.unique()),
                    "anomaly_month": months - 1,
                    "anomaly_type": "TOTAL_COLLAPSE",
                    "severity": "HIGH",
                })
    
    return pd.DataFrame(rows), anomalies


def inject_anomalies(sales: pd.DataFrame, anomalies: list, months: int) -> pd.DataFrame:
    """Inject known anomalies for ground truth."""
    for anom in anomalies:
        mask = (
            (sales.town_id == anom["town_id"]) &
            (sales.division == anom["division"]) &
            (sales.month >= anom["anomaly_month"])
        )
        sales.loc[mask, "secondary_sales"] = 0
    
    return sales


def generate(
    output_dir: str = "data/full",
    months: int = 30,
    cfg: ScaleConfig = DEFAULT
):
    """Main generator."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*70}")
    print(f"SANCHAY v3 DATA GENERATOR")
    print(f"{'='*70}\n")
    
    from .config import reconcile
    r = reconcile(cfg)
    print("RECONCILIATION:")
    for k, v in r.items():
        print(f"  {k}: {v}")
    print()
    
    print(f"Generating {cfg.distributor_towns} towns...")
    towns_df = build_towns(cfg)
    print(f"  {len(towns_df)} towns created")
    print(f"  Distributor count: min={towns_df.n_distributors.min()}, "
          f"avg={towns_df.n_distributors.mean():.1f}, max={towns_df.n_distributors.max()}")
    
    print(f"\nGenerating distributors...")
    dists_df = build_distributors(towns_df, cfg)
    print(f"  {len(dists_df)} distributors created")
    print(f"  Retailers/distributor: min={dists_df.book_size.min()}, "
          f"avg={dists_df.book_size.mean():.1f}, max={dists_df.book_size.max()}")
    
    print(f"\nGenerating retailers and mapping...")
    retailers_df, mapping_df = build_retailers_and_mapping(towns_df, dists_df, cfg)
    print(f"  {len(retailers_df)} unique retailers created")
    print(f"  {len(mapping_df)} retailer-division mappings")
    
    dup = mapping_df.groupby(["retailer_id", "division"]).size()
    dup_count = (dup > 1).sum()
    print(f"  Exclusivity violations: {dup_count} (must be 0)")
    
    print(f"\nGenerating {months} months of sales data...")
    sales_df, anomalies = build_monthly_sales(towns_df, mapping_df, months)
    print(f"  {len(sales_df)} town-division-month records")
    print(f"  {len(anomalies)} anomalies injected")
    
    sales_df = inject_anomalies(sales_df, anomalies, months)
    
    print(f"\nWriting to {output_dir}...")
    towns_df.to_parquet(out / "dim_town.parquet", index=False)
    dists_df.to_parquet(out / "dim_distributor.parquet", index=False)
    retailers_df.to_parquet(out / "dim_retailer.parquet", index=False)
    mapping_df.to_parquet(out / "map_retailer_dist.parquet", index=False)
    sales_df.to_parquet(out / "fact_secondary.parquet", index=False)
    
    with open(out / "anomalies.json", "w") as f:
        json.dump(anomalies, f, indent=2)
    
    print(f"  ✓ dim_town.parquet ({len(towns_df)} rows)")
    print(f"  ✓ dim_distributor.parquet ({len(dists_df)} rows)")
    print(f"  ✓ dim_retailer.parquet ({len(retailers_df)} rows)")
    print(f"  ✓ map_retailer_dist.parquet ({len(mapping_df)} rows)")
    print(f"  ✓ fact_secondary.parquet ({len(sales_df)} rows)")
    print(f"  ✓ anomalies.json ({len(anomalies)} anomalies)")
    
    print(f"\n{'='*70}")
    print(f"GENERATION COMPLETE")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    generate()