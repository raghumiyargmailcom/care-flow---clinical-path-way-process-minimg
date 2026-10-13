"""
CareFlow — Visualisation Module (Starter)
==========================================
Chart and process-map generation for CareFlow analyses.

Planned visualisations
-----------------------
- Directly-Follows Graph heatmap
- Waiting-time distribution by activity
- Daily patient volume time-series
- Sankey diagram of patient flows
- Bottleneck dwell-time boxplots
- Length-of-stay histograms by priority

Usage (once implemented)
-------------------------
    python src/visualization/plot_charts.py
"""

from __future__ import annotations

import logging
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
REPORTS_DIR = BASE_DIR / "reports"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("careflow.visualization")


def generate_all_charts() -> None:
    """TODO: Implement full visualisation pipeline."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    log.info("Visualisation module — implementation pending.")
    log.info("Install matplotlib, seaborn, and plotly then implement chart functions.")


if __name__ == "__main__":
    generate_all_charts()
