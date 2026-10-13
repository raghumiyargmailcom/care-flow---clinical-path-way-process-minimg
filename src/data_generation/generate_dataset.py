"""
CareFlow — Synthetic Clinical Pathway Dataset Generator
=======================================================
Generates three inter-related CSV files that form the backbone of the
CareFlow process-mining project:

  1. data/raw/event_log.csv          – one row per activity per patient visit
  2. data/raw/patient_cases.csv      – one row per patient visit (case)
  3. data/raw/activity_reference.csv – reference table of hospital activities

DISCLAIMER
----------
All data produced by this script is entirely synthetic and is generated
solely for educational and research purposes.  No real patient information
is used.  Simulated patterns, bottlenecks, and outcomes do NOT represent
any actual hospital, patient, or clinical finding.

Usage
-----
    python src/data_generation/generate_dataset.py

Fixed random seed (RANDOM_SEED) is used throughout so the dataset is
fully reproducible.  Change the constant to produce a different, but still
deterministic, dataset.
"""

from __future__ import annotations

import os
import random
import logging
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

RANDOM_SEED: int = 42
NUM_CASES: int = 5_000          # Target number of unique patient visits
START_DATE: datetime = datetime(2024, 1, 1, 0, 0, 0)
END_DATE: datetime = datetime(2024, 12, 31, 23, 59, 59)

OUTPUT_DIR: Path = Path(__file__).resolve().parents[2] / "data" / "raw"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("careflow.generator")

# ─────────────────────────────────────────────────────────────────────────────
# REFERENCE DATA  (activity_reference rows)
# ─────────────────────────────────────────────────────────────────────────────

ACTIVITY_REFERENCE: list[dict] = [
    # ── Registration ─────────────────────────────────────────────────────────
    {
        "Activity_ID": "ACT-001",
        "Activity_Name": "Registration",
        "Department": "Admissions",
        "Activity_Category": "Registration",
        "Expected_Duration_Minutes": 10,
        "Is_Required": True,
        "Description": "Patient identity verification and administrative intake at the admissions desk.",
    },
    # ── Triage ───────────────────────────────────────────────────────────────
    {
        "Activity_ID": "ACT-002",
        "Activity_Name": "Triage",
        "Department": "Emergency",
        "Activity_Category": "Assessment",
        "Expected_Duration_Minutes": 15,
        "Is_Required": True,
        "Description": "Nurse-led initial assessment to assign priority level using standardised triage protocol.",
    },
    # ── Doctor Consultation ──────────────────────────────────────────────────
    {
        "Activity_ID": "ACT-003",
        "Activity_Name": "Doctor Consultation",
        "Department": "Emergency",
        "Activity_Category": "Assessment",
        "Expected_Duration_Minutes": 20,
        "Is_Required": True,
        "Description": "Initial physician assessment of patient condition and determination of investigation plan.",
    },
    # ── Blood Test ───────────────────────────────────────────────────────────
    {
        "Activity_ID": "ACT-004",
        "Activity_Name": "Blood Test",
        "Department": "Pathology",
        "Activity_Category": "Diagnostic",
        "Expected_Duration_Minutes": 30,
        "Is_Required": False,
        "Description": "Collection and analysis of blood samples for biochemical and haematological markers.",
    },
    # ── X-Ray ────────────────────────────────────────────────────────────────
    {
        "Activity_ID": "ACT-005",
        "Activity_Name": "X-Ray",
        "Department": "Radiology",
        "Activity_Category": "Diagnostic",
        "Expected_Duration_Minutes": 20,
        "Is_Required": False,
        "Description": "Plain radiographic imaging of the requested body region.",
    },
    # ── CT Scan ───────────────────────────────────────────────────────────────
    {
        "Activity_ID": "ACT-006",
        "Activity_Name": "CT Scan",
        "Department": "Radiology",
        "Activity_Category": "Diagnostic",
        "Expected_Duration_Minutes": 45,
        "Is_Required": False,
        "Description": "Computed tomography imaging; typically used for complex or high-priority presentations.",
    },
    # ── ECG ───────────────────────────────────────────────────────────────────
    {
        "Activity_ID": "ACT-007",
        "Activity_Name": "ECG",
        "Department": "Cardiology",
        "Activity_Category": "Diagnostic",
        "Expected_Duration_Minutes": 15,
        "Is_Required": False,
        "Description": "Electrocardiogram recording to assess cardiac rhythm and electrical activity.",
    },
    # ── Ultrasound ────────────────────────────────────────────────────────────
    {
        "Activity_ID": "ACT-008",
        "Activity_Name": "Ultrasound",
        "Department": "Radiology",
        "Activity_Category": "Diagnostic",
        "Expected_Duration_Minutes": 30,
        "Is_Required": False,
        "Description": "Ultrasound imaging for soft-tissue and abdominal assessment.",
    },
    # ── Treatment ─────────────────────────────────────────────────────────────
    {
        "Activity_ID": "ACT-009",
        "Activity_Name": "Treatment",
        "Department": "Emergency",
        "Activity_Category": "Treatment",
        "Expected_Duration_Minutes": 60,
        "Is_Required": True,
        "Description": "Administration of therapeutic interventions including medication, wound care, or procedures.",
    },
    # ── Specialist Referral ───────────────────────────────────────────────────
    {
        "Activity_ID": "ACT-010",
        "Activity_Name": "Specialist Referral",
        "Department": "Emergency",
        "Activity_Category": "Assessment",
        "Expected_Duration_Minutes": 30,
        "Is_Required": False,
        "Description": "Referral and handover to an inpatient or outpatient specialist team.",
    },
    # ── Reassessment ─────────────────────────────────────────────────────────
    {
        "Activity_ID": "ACT-011",
        "Activity_Name": "Reassessment",
        "Department": "Emergency",
        "Activity_Category": "Assessment",
        "Expected_Duration_Minutes": 15,
        "Is_Required": False,
        "Description": "Follow-up clinical assessment after initial treatment or investigation results.",
    },
    # ── Medication Administration ─────────────────────────────────────────────
    {
        "Activity_ID": "ACT-012",
        "Activity_Name": "Medication Administration",
        "Department": "Nursing",
        "Activity_Category": "Treatment",
        "Expected_Duration_Minutes": 10,
        "Is_Required": False,
        "Description": "Preparation and administration of prescribed medications by nursing staff.",
    },
    # ── Admission ─────────────────────────────────────────────────────────────
    {
        "Activity_ID": "ACT-013",
        "Activity_Name": "Admission",
        "Department": "Inpatient Ward",
        "Activity_Category": "Disposition",
        "Expected_Duration_Minutes": 20,
        "Is_Required": False,
        "Description": "Formal admission to an inpatient ward following clinical decision.",
    },
    # ── Transfer ──────────────────────────────────────────────────────────────
    {
        "Activity_ID": "ACT-014",
        "Activity_Name": "Transfer",
        "Department": "Transport",
        "Activity_Category": "Disposition",
        "Expected_Duration_Minutes": 25,
        "Is_Required": False,
        "Description": "Patient transfer to another ward, unit, or external facility.",
    },
    # ── Discharge ─────────────────────────────────────────────────────────────
    {
        "Activity_ID": "ACT-015",
        "Activity_Name": "Discharge",
        "Department": "Admissions",
        "Activity_Category": "Disposition",
        "Expected_Duration_Minutes": 15,
        "Is_Required": False,
        "Description": "Completion of administrative discharge process and provision of after-care instructions.",
    },
    # ── Pain Assessment ───────────────────────────────────────────────────────
    {
        "Activity_ID": "ACT-016",
        "Activity_Name": "Pain Assessment",
        "Department": "Nursing",
        "Activity_Category": "Assessment",
        "Expected_Duration_Minutes": 5,
        "Is_Required": False,
        "Description": "Structured pain scoring using a validated scale (e.g., NRS).",
    },
    # ── IV Line Insertion ─────────────────────────────────────────────────────
    {
        "Activity_ID": "ACT-017",
        "Activity_Name": "IV Line Insertion",
        "Department": "Nursing",
        "Activity_Category": "Treatment",
        "Expected_Duration_Minutes": 10,
        "Is_Required": False,
        "Description": "Insertion of an intravenous cannula for fluid or medication delivery.",
    },
    # ── Observation ───────────────────────────────────────────────────────────
    {
        "Activity_ID": "ACT-018",
        "Activity_Name": "Observation",
        "Department": "Emergency",
        "Activity_Category": "Assessment",
        "Expected_Duration_Minutes": 60,
        "Is_Required": False,
        "Description": "Monitored waiting period for condition evolution before further decision.",
    },
    # ── Social Work Referral ──────────────────────────────────────────────────
    {
        "Activity_ID": "ACT-019",
        "Activity_Name": "Social Work Referral",
        "Department": "Social Services",
        "Activity_Category": "Assessment",
        "Expected_Duration_Minutes": 30,
        "Is_Required": False,
        "Description": "Referral to social work team for safeguarding, housing, or discharge planning needs.",
    },
    # ── Discharge Planning ────────────────────────────────────────────────────
    {
        "Activity_ID": "ACT-020",
        "Activity_Name": "Discharge Planning",
        "Department": "Nursing",
        "Activity_Category": "Disposition",
        "Expected_Duration_Minutes": 20,
        "Is_Required": False,
        "Description": "Coordination of post-discharge care, prescriptions, and follow-up appointments.",
    },
]

ACTIVITY_NAMES: list[str] = [a["Activity_Name"] for a in ACTIVITY_REFERENCE]

# ─────────────────────────────────────────────────────────────────────────────
# DOMAIN CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

PRIORITY_LEVELS: list[str] = ["P1 - Immediate", "P2 - Urgent", "P3 - Semi-Urgent", "P4 - Non-Urgent"]
PRIORITY_WEIGHTS: list[float] = [0.10, 0.25, 0.40, 0.25]

AGE_GROUPS: list[str] = ["0-17", "18-34", "35-54", "55-74", "75+"]
AGE_WEIGHTS: list[float] = [0.10, 0.20, 0.30, 0.25, 0.15]

ARRIVAL_MODES: list[str] = ["Ambulance", "Walk-In", "GP Referral", "Self-Referral", "Police/Custody"]
ARRIVAL_WEIGHTS: list[float] = [0.20, 0.45, 0.15, 0.15, 0.05]

EVENT_STATUS_OPTIONS: list[str] = ["Completed", "Skipped", "Cancelled", "Pending"]

DELAY_REASONS: list[str | None] = [
    None,
    "Awaiting Lab Results",
    "Bed Unavailability",
    "Staff Shortage",
    "Equipment Unavailability",
    "Patient Refused",
    "Missing Paperwork",
    "Awaiting Senior Review",
    "High Patient Volume",
    "Awaiting Transport",
]

FINAL_OUTCOMES: list[str] = ["Discharged", "Admitted", "Transferred", "Left Without Being Seen"]

DEPARTMENTS: dict[str, str] = {a["Activity_Name"]: a["Department"] for a in ACTIVITY_REFERENCE}

# Doctor IDs pool — prefix "DR" + zero-padded number, nullable for non-clinical activities
DOCTOR_IDS: list[str] = [f"DR{str(i).zfill(3)}" for i in range(1, 41)]

# ─────────────────────────────────────────────────────────────────────────────
# CLINICAL PATHWAY PROFILES
# Defines which activities a patient is likely to go through based on priority.
# Each profile is a weighted list of activity sequences.
# ─────────────────────────────────────────────────────────────────────────────

def build_pathway(priority: str, rng: np.random.Generator) -> list[str]:
    """
    Return a realistic ordered list of Activity_Names for a given priority level.
    Introduces deliberate variability: skips, repeats, extra steps, bottlenecks.
    """
    # Core mandatory sequence
    pathway: list[str] = ["Registration", "Triage", "Doctor Consultation"]

    # Diagnostic phase — determined by priority and randomness
    if priority in ("P1 - Immediate", "P2 - Urgent"):
        # High-acuity: many diagnostics, potential bottleneck at CT/blood
        diag_pool = ["Blood Test", "ECG", "CT Scan", "X-Ray", "IV Line Insertion", "Pain Assessment"]
        num_diags = rng.integers(2, 5)
        diagnostics = list(rng.choice(diag_pool, size=int(num_diags), replace=False))
        pathway += diagnostics

        # Possible bottleneck: Observation while awaiting results
        if rng.random() < 0.60:
            pathway.append("Observation")

        pathway.append("Treatment")

        # Possible medication administration
        if rng.random() < 0.70:
            pathway.append("Medication Administration")

        # Possible reassessment loop (deliberate bottleneck)
        if rng.random() < 0.40:
            pathway.append("Reassessment")
            if rng.random() < 0.30:
                pathway.append("Blood Test")  # Repeat blood test (bottleneck)

        # Specialist referral for high-acuity
        if rng.random() < 0.50:
            pathway.append("Specialist Referral")

    elif priority == "P3 - Semi-Urgent":
        diag_pool = ["Blood Test", "X-Ray", "Ultrasound", "Pain Assessment"]
        num_diags = rng.integers(1, 3)
        diagnostics = list(rng.choice(diag_pool, size=int(num_diags), replace=False))
        pathway += diagnostics

        pathway.append("Treatment")

        if rng.random() < 0.30:
            pathway.append("Medication Administration")

        if rng.random() < 0.20:
            pathway.append("Reassessment")

    else:  # P4 - Non-Urgent
        if rng.random() < 0.40:
            pathway.append("Blood Test")
        if rng.random() < 0.30:
            pathway.append("X-Ray")
        if rng.random() < 0.50:
            pathway.append("Treatment")
        if rng.random() < 0.15:
            pathway.append("Medication Administration")

    # Social work referral (low probability across all)
    if rng.random() < 0.05:
        pathway.append("Social Work Referral")

    # Disposition phase
    outcome_rand = rng.random()
    if priority in ("P1 - Immediate", "P2 - Urgent"):
        if outcome_rand < 0.50:
            pathway += ["Discharge Planning", "Discharge"]
        elif outcome_rand < 0.80:
            pathway += ["Admission"]
        else:
            pathway += ["Transfer"]
    elif priority == "P3 - Semi-Urgent":
        if outcome_rand < 0.70:
            pathway += ["Discharge Planning", "Discharge"]
        elif outcome_rand < 0.90:
            pathway += ["Admission"]
        else:
            pathway += ["Transfer"]
    else:
        if outcome_rand < 0.85:
            pathway += ["Discharge Planning", "Discharge"]
        elif outcome_rand < 0.92:
            pathway += ["Admission"]
        elif outcome_rand < 0.96:
            pathway += ["Transfer"]
        else:
            pass  # Left without being seen — no disposition activity

    return pathway


def determine_final_outcome(pathway: list[str]) -> str:
    """Derive the patient case final outcome from the activity pathway."""
    if "Admission" in pathway:
        return "Admitted"
    if "Transfer" in pathway:
        return "Transferred"
    if "Discharge" in pathway:
        return "Discharged"
    return "Left Without Being Seen"


# ─────────────────────────────────────────────────────────────────────────────
# HELPER — ACTIVITY DURATION & STATUS
# ─────────────────────────────────────────────────────────────────────────────

ACTIVITY_EXPECTED_DURATION: dict[str, int] = {
    a["Activity_Name"]: a["Expected_Duration_Minutes"] for a in ACTIVITY_REFERENCE
}

# Activities that require a Doctor_ID
CLINICAL_ACTIVITIES = {
    "Doctor Consultation", "Treatment", "Reassessment",
    "Specialist Referral", "CT Scan", "Discharge Planning",
}

# Bottleneck activities with inflated wait multipliers
BOTTLENECK_ACTIVITIES = {
    "CT Scan": 3.0,    # CT scanner queue
    "Blood Test": 2.0, # Lab backlog
    "Admission": 2.5,  # Bed wait
    "Observation": 2.0,
}


def sample_activity_duration(activity_name: str, priority: str, rng: np.random.Generator) -> int:
    """Return realistic duration in minutes, with bottleneck inflation and priority scaling."""
    base = ACTIVITY_EXPECTED_DURATION.get(activity_name, 20)

    # Bottleneck multiplier
    multiplier = BOTTLENECK_ACTIVITIES.get(activity_name, 1.0)

    # Priority affects wait times (higher acuity → faster service for clinical acts)
    priority_factor = {"P1 - Immediate": 0.6, "P2 - Urgent": 0.8,
                       "P3 - Semi-Urgent": 1.0, "P4 - Non-Urgent": 1.3}.get(priority, 1.0)

    # Lognormal noise for realistic variation
    noise = rng.lognormal(mean=0.0, sigma=0.4)

    duration = max(1, int(base * multiplier * priority_factor * noise))

    # Simulate high-volume bottleneck: random surge factor during peak hours
    return duration


def sample_event_status(activity_name: str, rng: np.random.Generator) -> str:
    """Assign a realistic event status with low but non-zero skip/cancel rates."""
    rand = rng.random()
    if rand < 0.88:
        return "Completed"
    elif rand < 0.93:
        return "Skipped"
    elif rand < 0.97:
        return "Cancelled"
    else:
        return "Pending"


def sample_delay_reason(event_status: str, activity_name: str, rng: np.random.Generator) -> str | None:
    """Return a delay reason only for completed events with non-trivial probability."""
    if event_status in ("Skipped", "Cancelled"):
        return None
    rand = rng.random()
    if activity_name in BOTTLENECK_ACTIVITIES and rand < 0.40:
        # Bottleneck activities have higher delay probability
        return rng.choice([r for r in DELAY_REASONS if r is not None])
    elif rand < 0.12:
        return rng.choice([r for r in DELAY_REASONS if r is not None])
    return None


def sample_doctor_id(activity_name: str, rng: np.random.Generator) -> str | None:
    """Return a doctor ID for clinical activities; None otherwise."""
    if activity_name in CLINICAL_ACTIVITIES:
        return rng.choice(DOCTOR_IDS)
    return None


# ─────────────────────────────────────────────────────────────────────────────
# CORE GENERATION
# ─────────────────────────────────────────────────────────────────────────────

def generate_datasets(num_cases: int = NUM_CASES, seed: int = RANDOM_SEED) -> None:
    """
    Main entry point.  Generates all three CSV files and writes them to OUTPUT_DIR.
    """
    log.info("CareFlow dataset generator starting.  seed=%d  cases=%d", seed, num_cases)
    rng = np.random.default_rng(seed)
    random.seed(seed)

    # Unique ID counters
    patient_ids = [f"PT{str(i).zfill(5)}" for i in range(1, num_cases + 1)]
    case_ids = [f"CASE{str(i).zfill(5)}" for i in range(1, num_cases + 1)]

    # Pre-sample case-level attributes
    priorities = rng.choice(PRIORITY_LEVELS, size=num_cases, p=PRIORITY_WEIGHTS)
    age_groups = rng.choice(AGE_GROUPS, size=num_cases, p=AGE_WEIGHTS)
    arrival_modes = rng.choice(ARRIVAL_MODES, size=num_cases, p=ARRIVAL_WEIGHTS)
    initial_departments = ["Emergency"] * num_cases  # All cases enter via Emergency

    # Random arrival timestamps spread uniformly across the year
    total_seconds = int((END_DATE - START_DATE).total_seconds())
    arrival_offsets = rng.integers(0, total_seconds, size=num_cases)
    arrival_timestamps = [START_DATE + timedelta(seconds=int(s)) for s in arrival_offsets]

    event_rows: list[dict] = []
    case_rows: list[dict] = []

    log.info("Building event log for %d patient cases …", num_cases)

    for idx in range(num_cases):
        case_id = case_ids[idx]
        patient_id = patient_ids[idx]
        priority = priorities[idx]
        age_group = age_groups[idx]
        arrival_mode = arrival_modes[idx]
        arrival_ts = arrival_timestamps[idx]

        # Build pathway
        pathway = build_pathway(priority, rng)
        final_outcome = determine_final_outcome(pathway)

        # Generate events along the pathway
        current_ts = arrival_ts
        case_events: list[dict] = []

        for act_name in pathway:
            duration_minutes = sample_activity_duration(act_name, priority, rng)
            event_status = sample_event_status(act_name, rng)
            delay_reason = sample_delay_reason(event_status, act_name, rng)
            doctor_id = sample_doctor_id(act_name, rng)
            department = DEPARTMENTS.get(act_name, "Emergency")

            # Add inter-activity waiting time (simulating queue wait)
            wait_minutes = max(0, int(rng.exponential(scale=15)))  # avg 15 min wait
            current_ts += timedelta(minutes=wait_minutes)
            event_ts = current_ts
            current_ts += timedelta(minutes=duration_minutes)

            case_events.append({
                "Case_ID": case_id,
                "Patient_ID": patient_id,
                "Activity_Name": act_name,
                "Timestamp": event_ts.strftime("%Y-%m-%d %H:%M:%S"),
                "Department": department,
                "Doctor_ID": doctor_id if doctor_id else "",
                "Patient_Age_Group": age_group,
                "Priority_Level": priority,
                "Arrival_Mode": arrival_mode,
                "Event_Status": event_status,
                "Delay_Reason": delay_reason if delay_reason else "",
            })

        event_rows.extend(case_events)
        departure_ts = current_ts if pathway else arrival_ts
        total_los = int((departure_ts - arrival_ts).total_seconds() / 60)

        case_rows.append({
            "Case_ID": case_id,
            "Patient_ID": patient_id,
            "Arrival_Timestamp": arrival_ts.strftime("%Y-%m-%d %H:%M:%S"),
            "Departure_Timestamp": departure_ts.strftime("%Y-%m-%d %H:%M:%S") if final_outcome != "Left Without Being Seen" else "",
            "Patient_Age_Group": age_group,
            "Priority_Level": priority,
            "Arrival_Mode": arrival_mode,
            "Initial_Department": initial_departments[idx],
            "Final_Outcome": final_outcome,
            "Total_Length_of_Stay_Minutes": total_los if final_outcome != "Left Without Being Seen" else "",
        })

        if (idx + 1) % 1000 == 0:
            log.info("  Generated %d / %d cases …", idx + 1, num_cases)

    # ── Build DataFrames ──────────────────────────────────────────────────────
    event_df = pd.DataFrame(event_rows)
    case_df = pd.DataFrame(case_rows)
    activity_ref_df = pd.DataFrame(ACTIVITY_REFERENCE)

    log.info("Event log shape: %s", event_df.shape)
    log.info("Patient cases shape: %s", case_df.shape)
    log.info("Activity reference shape: %s", activity_ref_df.shape)

    # ── Validate ──────────────────────────────────────────────────────────────
    _validate(event_df, case_df, activity_ref_df)

    # ── Write to disk ─────────────────────────────────────────────────────────
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    event_path = OUTPUT_DIR / "event_log.csv"
    case_path = OUTPUT_DIR / "patient_cases.csv"
    ref_path = OUTPUT_DIR / "activity_reference.csv"

    event_df.to_csv(event_path, index=False)
    case_df.to_csv(case_path, index=False)
    activity_ref_df.to_csv(ref_path, index=False)

    log.info("✓ event_log.csv       → %s  (%d rows)", event_path, len(event_df))
    log.info("✓ patient_cases.csv   → %s  (%d rows)", case_path, len(case_df))
    log.info("✓ activity_reference.csv → %s  (%d rows)", ref_path, len(activity_ref_df))
    log.info("Dataset generation complete.")


# ─────────────────────────────────────────────────────────────────────────────
# VALIDATION
# ─────────────────────────────────────────────────────────────────────────────

def _validate(event_df: pd.DataFrame, case_df: pd.DataFrame, ref_df: pd.DataFrame) -> None:
    """
    Run lightweight pre-write validation checks.
    Raises ValueError if critical consistency rules are violated.
    Logs warnings for soft rules.
    """
    log.info("Running validation checks …")
    errors: list[str] = []
    warnings: list[str] = []

    # ── Null checks ───────────────────────────────────────────────────────────
    required_event_cols = ["Case_ID", "Patient_ID", "Activity_Name", "Timestamp",
                           "Department", "Patient_Age_Group", "Priority_Level",
                           "Arrival_Mode", "Event_Status"]
    for col in required_event_cols:
        nulls = event_df[col].isna().sum()
        if nulls > 0:
            errors.append(f"event_log.{col} has {nulls} null values.")

    required_case_cols = ["Case_ID", "Patient_ID", "Arrival_Timestamp",
                          "Patient_Age_Group", "Priority_Level", "Arrival_Mode",
                          "Initial_Department", "Final_Outcome"]
    for col in required_case_cols:
        nulls = case_df[col].isna().sum()
        if nulls > 0:
            errors.append(f"patient_cases.{col} has {nulls} null values.")

    # ── Duplicate Case_IDs ────────────────────────────────────────────────────
    dup_cases = case_df["Case_ID"].duplicated().sum()
    if dup_cases > 0:
        errors.append(f"patient_cases has {dup_cases} duplicate Case_IDs.")

    # ── ID consistency: every event Case_ID must exist in patient_cases ───────
    orphan_events = set(event_df["Case_ID"].unique()) - set(case_df["Case_ID"].unique())
    if orphan_events:
        errors.append(f"event_log has {len(orphan_events)} Case_IDs not in patient_cases.")

    # ── Timestamp ordering within cases ───────────────────────────────────────
    event_df["_ts"] = pd.to_datetime(event_df["Timestamp"])
    bad_order_count = 0
    for case_id, grp in event_df.groupby("Case_ID"):
        if not grp["_ts"].is_monotonic_increasing:
            bad_order_count += 1
    if bad_order_count > 0:
        warnings.append(f"{bad_order_count} cases have non-monotonic timestamps.")
    event_df.drop(columns=["_ts"], inplace=True)

    # ── Activity names in event log must exist in reference ──────────────────
    ref_acts = set(ref_df["Activity_Name"])
    unknown_acts = set(event_df["Activity_Name"].unique()) - ref_acts
    if unknown_acts:
        warnings.append(f"event_log contains activity names not in reference: {unknown_acts}")

    # ── Priority level cardinality ────────────────────────────────────────────
    invalid_priorities = set(event_df["Priority_Level"]) - set(PRIORITY_LEVELS)
    if invalid_priorities:
        errors.append(f"Invalid priority levels in event_log: {invalid_priorities}")

    # ── Report ────────────────────────────────────────────────────────────────
    for w in warnings:
        log.warning("  ⚠  %s", w)

    if errors:
        for e in errors:
            log.error("  ✗  %s", e)
        raise ValueError(f"Validation failed with {len(errors)} error(s). See log above.")

    log.info("  ✓ All validation checks passed (%d warning(s)).", len(warnings))


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    generate_datasets()
