"""
CareFlow — Process Mining & Conformance Test Suite
==================================================
Tests PM4Py discovery, DFG generation, and conformance checking algorithms.
"""

from __future__ import annotations

import sys
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Ensure src is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from process_mining.discover_process import (
    load_and_format_event_log,
    discover_process_models,
)
from process_mining.conformance import (
    check_trace_compliance,
    run_conformance_checking,
)
from analytics.kpi_calculator import (
    compute_node_transition_matrix,
    analyze_xray_triage_loopback,
    compute_executive_kpis,
)


@pytest.fixture(scope="module")
def sample_event_log():
    data = [
        {"case_id": "C1", "activity": "Registration", "timestamp": "2026-01-01 08:00:00", "department": "Admissions", "resource": "Clerk"},
        {"case_id": "C1", "activity": "Triage", "timestamp": "2026-01-01 08:15:00", "department": "Emergency", "resource": "Nurse"},
        {"case_id": "C1", "activity": "Doctor Consultation", "timestamp": "2026-01-01 08:45:00", "department": "Emergency", "resource": "Doctor"},
        {"case_id": "C1", "activity": "X-Ray", "timestamp": "2026-01-01 09:15:00", "department": "Radiology", "resource": "Tech"},
        {"case_id": "C1", "activity": "Triage", "timestamp": "2026-01-01 09:45:00", "department": "Emergency", "resource": "Nurse"},  # Loop-back!
        {"case_id": "C1", "activity": "Treatment", "timestamp": "2026-01-01 10:15:00", "department": "Emergency", "resource": "Doctor"},
        {"case_id": "C1", "activity": "Discharge", "timestamp": "2026-01-01 11:00:00", "department": "Emergency", "resource": "Nurse"},
        # Compliant trace
        {"case_id": "C2", "activity": "Registration", "timestamp": "2026-01-01 09:00:00", "department": "Admissions", "resource": "Clerk"},
        {"case_id": "C2", "activity": "Triage", "timestamp": "2026-01-01 09:10:00", "department": "Emergency", "resource": "Nurse"},
        {"case_id": "C2", "activity": "Doctor Consultation", "timestamp": "2026-01-01 09:30:00", "department": "Emergency", "resource": "Doctor"},
        {"case_id": "C2", "activity": "Treatment", "timestamp": "2026-01-01 10:00:00", "department": "Emergency", "resource": "Doctor"},
        {"case_id": "C2", "activity": "Discharge", "timestamp": "2026-01-01 10:30:00", "department": "Emergency", "resource": "Nurse"},
    ]
    df = pd.DataFrame(data)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def test_conformance_detection_of_xray_loopback():
    """Verify that returning to Triage after X-Ray is correctly flagged as unauthorized."""
    trace_with_loopback = ["Registration", "Triage", "Doctor Consultation", "X-Ray", "Triage", "Treatment", "Discharge"]
    res = check_trace_compliance(trace_with_loopback)
    assert not res["is_compliant"]
    assert "UNAUTHORIZED_XRAY_TO_TRIAGE_LOOPBACK" in res["deviations"]


def test_conformance_of_compliant_trace():
    """Verify that standard clinical flow achieves high fitness and compliance."""
    compliant_trace = ["Registration", "Triage", "Doctor Consultation", "Treatment", "Discharge"]
    res = check_trace_compliance(compliant_trace)
    assert res["is_compliant"]
    assert res["trace_fitness"] == 1.0


def test_node_transition_matrix(sample_event_log):
    """Verify transition matrix correctly counts edges and durations."""
    trans = compute_node_transition_matrix(sample_event_log)
    assert not trans.empty
    xray_triage = trans[(trans["activity"] == "X-Ray") & (trans["next_activity"] == "Triage")]
    assert len(xray_triage) == 1
    assert xray_triage.iloc[0]["transition_count"] == 1
    assert xray_triage.iloc[0]["avg_duration_minutes"] == 30.0


def test_xray_loopback_analytics(sample_event_log):
    """Verify loopback percentage calculation on sample data."""
    metrics = analyze_xray_triage_loopback(sample_event_log)
    assert metrics["total_xray_patients"] == 1
    assert metrics["xray_to_triage_loopback_cases"] == 1
    assert metrics["xray_to_triage_loopback_pct"] == 100.0

