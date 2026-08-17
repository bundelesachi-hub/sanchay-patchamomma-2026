from dataclasses import dataclass

@dataclass(frozen=True)
class ScaleConfig:
    """Scale parameters for synthetic data generation."""
    distributors_per_town: tuple[int, int] = (3, 5)
    retailers_per_distributor: tuple[int, int] = (150, 200)
    divisions_per_distributor: tuple[int, int] = (2, 3)
    n_divisions: int = 8
    distributor_towns: int = 700
    reach_towns: int = 5000
    avg_links_per_retailer: float = 1.5
    utilisation: float = 1.0
    target_retailers: int = 300_000

DEFAULT = ScaleConfig()

def reconcile(cfg: ScaleConfig = DEFAULT) -> dict:
    d_per_town = sum(cfg.distributors_per_town) / 2
    r_per_dist = sum(cfg.retailers_per_distributor) / 2 * cfg.utilisation
    links_per_town = d_per_town * r_per_dist
    retailers_per_town = links_per_town / cfg.avg_links_per_retailer
    total_retailers = retailers_per_town * cfg.distributor_towns
    dist_per_division = d_per_town * sum(cfg.divisions_per_distributor) / 2 / cfg.n_divisions
    
    return {
        "distributors_per_town": round(d_per_town, 1),
        "retailers_per_distributor": round(r_per_dist),
        "unique_retailers_per_town": round(retailers_per_town),
        "distributor_towns": cfg.distributor_towns,
        "total_retailers": round(total_retailers),
        "target_retailers": cfg.target_retailers,
        "variance_pct": round(100 * (total_retailers - cfg.target_retailers) / cfg.target_retailers, 1),
        "pct_cells_sole_sourced": round(100 * max(0.0, min(1.0, 2 - dist_per_division)), 1),
    }

if __name__ == "__main__":
    import json
    r = reconcile()
    print(json.dumps(r, indent=2))