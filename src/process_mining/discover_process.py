"""
CareFlow — Process Mining Module (Starter)
==========================================
Placeholder for process discovery and conformance checking algorithms.

Planned implementations
-----------------------
- Directly-Follows Graph (DFG) construction
- Inductive Miner (via pm4py)
- Petri net discovery and visualisation
- Token-replay conformance checking
- Alignment-based fitness / precision metrics

Usage (once implemented)
-------------------------
    python src/process_mining/discover_process.py
"""

from __future__ import annotations

import logging
from pathlib import Path

# import pm4py  # Uncomment when ready to implement

BASE_DIR = Path(__file__).resolve().parents[2]
PROCESSED_DIR = BASE_DIR / "data" / "processed"
OUTPUTS_DIR = BASE_DIR / "data" / "outputs"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("careflow.process_mining")


def load_event_log():
    """Load and format event log for pm4py compatibility."""
    import pandas as pd
    df = pd.read_csv(PROCESSED_DIR / "event_log_clean.csv", parse_dates=["Timestamp"])
    # pm4py expects specific column names
    df = df.rename(columns={
        "Case_ID": "case:concept:name",
        "Activity_Name": "concept:name",
        "Timestamp": "time:timestamp",
    })
    return df


def run_process_discovery():
    """
    TODO: Implement process discovery pipeline.

    Steps:
    1.  Load event log
    2.  Convert to pm4py EventLog object
    3.  Discover Directly-Follows Graph
    4.  Apply Inductive Miner to derive Petri net
    5.  Export process model as PNG and PNML
    """
    log.info("Process discovery module — implementation pending.")
    log.info("Run pip install pm4py and implement discover_process() to proceed.")


def run_conformance_checking():
    """
    TODO: Implement conformance checking.

    Steps:
    1.  Load Petri net from PNML
    2.  Run token-replay against event log
    3.  Compute fitness, precision, generalisation, simplicity
    4.  Export conformance results to data/outputs/
    """
    log.info("Conformance checking module — implementation pending.")


if __name__ == "__main__":
    run_process_discovery()
    run_conformance_checking()
