"""
CareFlow — Test Suite
=====================
Automated unit and integration tests for data generation and cleaning.

Run with:
    pytest tests/ -v
    pytest tests/ -v --cov=src
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import numpy as np
import pytest

# Ensure src is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from data_generation.generate_dataset import (
    build_pathway,
    determine_final_outcome,
    PRIORITY_LEVELS,
    AGE_GROUPS,
    ARRIVAL_MODES,
    ACTIVITY_REFERENCE,
)


# ─────────────────────────────────────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def rng():
    return np.random.default_rng(42)


@pytest.fixture(scope="module")
def activity_names():
    return [a["Activity_Name"] for a in ACTIVITY_REFERENCE]


# ─────────────────────────────────────────────────────────────────────────────
# PATHWAY TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestBuildPathway:
    def test_mandatory_activities_present_high_priority(self, rng):
        pathway = build_pathway("P1 - Immediate", rng)
        assert "Registration" in pathway
        assert "Triage" in pathway
        assert "Doctor Consultation" in pathway

    def test_pathway_is_list_of_strings(self, rng):
        for p in PRIORITY_LEVELS:
            pathway = build_pathway(p, rng)
            assert isinstance(pathway, list)
            assert all(isinstance(act, str) for act in pathway)

    def test_pathway_minimum_length(self, rng):
        for p in PRIORITY_LEVELS:
            pathway = build_pathway(p, rng)
            # At minimum: Registration, Triage, Doctor Consultation
            assert len(pathway) >= 3

    def test_pathway_all_activities_known(self, rng, activity_names):
        for p in PRIORITY_LEVELS:
            pathway = build_pathway(p, rng)
            for act in pathway:
                assert act in activity_names, f"Unknown activity: {act}"

    def test_outcome_derivation(self, rng):
        pathway_discharged = ["Registration", "Triage", "Treatment", "Discharge Planning", "Discharge"]
        assert determine_final_outcome(pathway_discharged) == "Discharged"

        pathway_admitted = ["Registration", "Triage", "Treatment", "Admission"]
        assert determine_final_outcome(pathway_admitted) == "Admitted"

        pathway_transferred = ["Registration", "Triage", "Transfer"]
        assert determine_final_outcome(pathway_transferred) == "Transferred"

        pathway_lwbs = ["Registration", "Triage"]
        assert determine_final_outcome(pathway_lwbs) == "Left Without Being Seen"


# ─────────────────────────────────────────────────────────────────────────────
# REFERENCE DATA TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestActivityReference:
    def test_unique_activity_ids(self):
        ids = [a["Activity_ID"] for a in ACTIVITY_REFERENCE]
        assert len(ids) == len(set(ids)), "Duplicate Activity_IDs found"

    def test_unique_activity_names(self):
        names = [a["Activity_Name"] for a in ACTIVITY_REFERENCE]
        assert len(names) == len(set(names)), "Duplicate Activity_Names found"

    def test_required_keys_present(self):
        required_keys = {
            "Activity_ID", "Activity_Name", "Department",
            "Activity_Category", "Expected_Duration_Minutes",
            "Is_Required", "Description",
        }
        for act in ACTIVITY_REFERENCE:
            assert required_keys.issubset(act.keys()), f"Missing keys in {act['Activity_ID']}"

    def test_expected_duration_positive(self):
        for act in ACTIVITY_REFERENCE:
            assert act["Expected_Duration_Minutes"] > 0, \
                f"{act['Activity_ID']} has non-positive duration"

    def test_is_required_is_bool(self):
        for act in ACTIVITY_REFERENCE:
            assert isinstance(act["Is_Required"], bool), \
                f"{act['Activity_ID']} Is_Required is not bool"


# ─────────────────────────────────────────────────────────────────────────────
# DOMAIN CONSTANTS TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestDomainConstants:
    def test_priority_levels_count(self):
        assert len(PRIORITY_LEVELS) == 4

    def test_age_groups_count(self):
        assert len(AGE_GROUPS) == 5

    def test_arrival_modes_count(self):
        assert len(ARRIVAL_MODES) == 5


# ─────────────────────────────────────────────────────────────────────────────
# INTEGRATION TEST — Full generation smoke test (small scale)
# ─────────────────────────────────────────────────────────────────────────────

class TestGenerateDatasets:
    def test_smoke_generate_10_cases(self, tmp_path, monkeypatch):
        """Generate 10 cases and verify file structure and row counts."""
        import data_generation.generate_dataset as gen
        monkeypatch.setattr(gen, "OUTPUT_DIR", tmp_path)
        gen.generate_datasets(num_cases=10, seed=42)

        event_df = pd.read_csv(tmp_path / "event_log.csv")
        case_df = pd.read_csv(tmp_path / "patient_cases.csv")
        ref_df = pd.read_csv(tmp_path / "activity_reference.csv")

        assert len(case_df) == 10
        assert len(event_df) > 10   # Multiple events per case
        assert len(ref_df) == len(ACTIVITY_REFERENCE)

    def test_all_case_ids_in_event_log(self, tmp_path, monkeypatch):
        import data_generation.generate_dataset as gen
        monkeypatch.setattr(gen, "OUTPUT_DIR", tmp_path)
        gen.generate_datasets(num_cases=20, seed=99)

        event_df = pd.read_csv(tmp_path / "event_log.csv")
        case_df = pd.read_csv(tmp_path / "patient_cases.csv")

        assert set(case_df["Case_ID"]).issubset(set(event_df["Case_ID"]))

    def test_timestamps_monotonic_within_cases(self, tmp_path, monkeypatch):
        import data_generation.generate_dataset as gen
        monkeypatch.setattr(gen, "OUTPUT_DIR", tmp_path)
        gen.generate_datasets(num_cases=50, seed=7)

        event_df = pd.read_csv(tmp_path / "event_log.csv", parse_dates=["Timestamp"])
        event_df = event_df.sort_values(["Case_ID", "Timestamp"])

        bad_cases = []
        for case_id, grp in event_df.groupby("Case_ID"):
            if not grp["Timestamp"].is_monotonic_increasing:
                bad_cases.append(case_id)

        assert len(bad_cases) == 0, f"Non-monotonic timestamps in cases: {bad_cases[:5]}"
