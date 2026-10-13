"""
CareFlow — EDA Summary Script
==============================
Generates a statistical overview of the cleaned CareFlow datasets.
Outputs summary tables to data/outputs/ and prints key metrics.

Usage
-----
    python src/eda/eda_summary.py
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
log = logging.getLogger("careflow.eda")


def run_eda() -> None:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    log.info("Loading processed datasets …")
    event_df = pd.read_csv(PROCESSED_DIR / "event_log_clean.csv", parse_dates=["Timestamp"])
    case_df = pd.read_csv(PROCESSED_DIR / "patient_cases_clean.csv",
                          parse_dates=["Arrival_Timestamp", "Departure_Timestamp"])

    # ── Case-level summaries ──────────────────────────────────────────────────
    log.info("=== PATIENT CASE SUMMARY ===")
    log.info("Total cases: %d", len(case_df))
    log.info("Date range: %s → %s",
             case_df["Arrival_Timestamp"].min(), case_df["Arrival_Timestamp"].max())

    priority_dist = case_df["Priority_Level"].value_counts(normalize=True).mul(100).round(1)
    log.info("Priority distribution:\n%s", priority_dist.to_string())

    outcome_dist = case_df["Final_Outcome"].value_counts()
    log.info("Final outcome distribution:\n%s", outcome_dist.to_string())

    los_stats = case_df["Total_Length_of_Stay_Minutes"].astype(float).describe()
    log.info("Length of Stay (minutes) stats:\n%s", los_stats.to_string())

    # ── Event-level summaries ─────────────────────────────────────────────────
    log.info("=== EVENT LOG SUMMARY ===")
    log.info("Total events: %d", len(event_df))
    log.info("Mean events per case: %.1f", len(event_df) / len(case_df))

    activity_counts = event_df["Activity_Name"].value_counts()
    log.info("Activity frequency:\n%s", activity_counts.to_string())

    status_dist = event_df["Event_Status"].value_counts(normalize=True).mul(100).round(1)
    log.info("Event status distribution:\n%s", status_dist.to_string())

    delay_reasons = event_df[event_df["Delay_Reason"] != ""]["Delay_Reason"].value_counts()
    log.info("Top delay reasons:\n%s", delay_reasons.head(10).to_string())

    # ── Save summary tables ───────────────────────────────────────────────────
    priority_dist.to_csv(OUTPUTS_DIR / "priority_distribution.csv", header=["Percentage"])
    outcome_dist.to_csv(OUTPUTS_DIR / "outcome_distribution.csv", header=["Count"])
    activity_counts.to_csv(OUTPUTS_DIR / "activity_frequency.csv", header=["Count"])
    los_stats.to_csv(OUTPUTS_DIR / "los_statistics.csv", header=["Value"])

    log.info("✓ EDA outputs written to %s", OUTPUTS_DIR)


if __name__ == "__main__":
    run_eda()
