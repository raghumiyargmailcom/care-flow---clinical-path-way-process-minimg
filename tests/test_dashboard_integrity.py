"""
test_dashboard_integrity.py
---------------------------
Verifies data integrity and schema alignment for the CareFlow Power BI dashboard,
including DAX measures, transition matrix exports, conformance summaries, and assets.
"""

from pathlib import Path
import json
import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DASHBOARD_DIR = REPO_ROOT / "dashboard"
DATA_DIR = REPO_ROOT / "data"


def test_dashboard_files_exist():
    """Verify that all core dashboard files and images exist."""
    assert (DASHBOARD_DIR / "index.html").is_file()
    assert (DASHBOARD_DIR / "style.css").is_file()
    assert (DASHBOARD_DIR / "dashboard_config.md").is_file()
    assert (DASHBOARD_DIR / "images" / "spaghetti_diagram.png").is_file()
    assert (DASHBOARD_DIR / "images" / "dfg.png").is_file()


def test_dax_measure_schema_alignment():
    """Verify that columns referenced in DAX measures exist in processed data."""
    cases_file = DATA_DIR / "processed" / "patient_cases_clean.csv"
    assert cases_file.is_file()
    df_cases = pd.read_csv(cases_file)
    assert "Total_Length_of_Stay_Minutes" in df_cases.columns
    assert "Priority_Level" in df_cases.columns
    assert "Final_Outcome" in df_cases.columns

    transitions_file = DATA_DIR / "outputs" / "dfg_transitions.csv"
    assert transitions_file.is_file()
    df_trans = pd.read_csv(transitions_file)
    assert "source_activity" in df_trans.columns
    assert "target_activity" in df_trans.columns
    assert "transition_count" in df_trans.columns


def test_node_transition_matrix_integrity():
    """Verify that node transition matrix contains valid transitions and X-Ray loopback."""
    matrix_file = DATA_DIR / "outputs" / "node_transition_matrix.csv"
    assert matrix_file.is_file()
    df_matrix = pd.read_csv(matrix_file)
    assert len(df_matrix) >= 20

    loopbacks = df_matrix[
        (df_matrix["activity"] == "X-Ray") & (df_matrix["next_activity"] == "Triage")
    ]
    assert len(loopbacks) == 1
    assert loopbacks.iloc[0]["transition_count"] == 791


def test_conformance_summary_metrics():
    """Verify that conformance results match clinical governance targets."""
    summary_file = DATA_DIR / "outputs" / "conformance_summary.json"
    assert summary_file.is_file()
    with open(summary_file, "r", encoding="utf-8") as f:
        summary = json.load(f)

    assert summary["total_cases_analyzed"] == 5000
    assert summary["compliant_cases"] == 4158
    assert summary["compliance_rate_pct"] == 83.2
    assert summary["average_log_fitness_score"] == 0.958
    assert summary["xray_loopback_violations"] == 791
