"""
CareFlow — Analytics Module (Starter)
======================================
Waiting-time, bottleneck, throughput, and KPI calculations.

Planned KPIs
------------
- Average triage-to-doctor time by priority
- Average length of stay by outcome and priority
- 4-hour target compliance rate
- Re-assessment rate (proxy for re-admission)
- Bottleneck activity dwell times
- Hourly / daily throughput

Usage (once implemented)
-------------------------
    python src/analytics/kpi_calculator.py
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parents[2]
PROCESSED_DIR = BASE_DIR / "data" / "processed"
OUTPUTS_DIR = BASE_DIR / "data" / "outputs"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("careflow.analytics")


def calculate_kpis() -> None:
    """
    TODO: Implement KPI calculation pipeline.

    Interim stub — loads data and logs shape only.
    """
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    log.info("Loading processed event log …")
    event_df = pd.read_csv(PROCESSED_DIR / "event_log_clean.csv", parse_dates=["Timestamp"])
    case_df = pd.read_csv(PROCESSED_DIR / "patient_cases_clean.csv",
                          parse_dates=["Arrival_Timestamp", "Departure_Timestamp"])

    log.info("Event log: %d rows | Cases: %d rows", len(event_df), len(case_df))
    log.info("KPI calculation pipeline — implementation pending.")

    # ── Stub: average LoS by priority ─────────────────────────────────────────
    los_by_priority = (
        case_df.groupby("Priority_Level")["Total_Length_of_Stay_Minutes"]
        .agg(["mean", "median", "std", "count"])
        .round(1)
    )
    log.info("LoS by priority:\n%s", los_by_priority.to_string())
    los_by_priority.to_csv(OUTPUTS_DIR / "los_by_priority.csv")
    log.info("✓ los_by_priority.csv written.")


if __name__ == "__main__":
    calculate_kpis()
