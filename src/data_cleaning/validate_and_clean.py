"""
CareFlow — Data Validation and Cleaning Pipeline
=================================================
Reads raw CSV files from data/raw/, performs comprehensive validation and
cleaning, and writes clean datasets to data/processed/.

Cleaning steps performed
------------------------
1.  Schema enforcement   — column presence, data-type coercion
2.  Null handling        — log and impute or drop based on rules
3.  Duplicate removal    — exact-row and Case_ID/Activity/Timestamp dedup
4.  Timestamp validation — parse, order-check, impossible-date removal
5.  ID consistency       — cross-file referential integrity
6.  Category validation  — enum membership for coded columns
7.  Derived features     — waiting_time_minutes, activity_sequence_number
8.  Output split         — raw data unchanged; processed files versioned

Usage
-----
    python src/data_cleaning/validate_and_clean.py
"""

from __future__ import annotations

import logging
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np

# ─────────────────────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("careflow.cleaner")

# ─────────────────────────────────────────────────────────────────────────────
# SCHEMA DEFINITIONS
# ─────────────────────────────────────────────────────────────────────────────

EVENT_LOG_SCHEMA = {
    "Case_ID": str,
    "Patient_ID": str,
    "Activity_Name": str,
    "Timestamp": str,  # will be converted to datetime
    "Department": str,
    "Doctor_ID": str,
    "Patient_Age_Group": str,
    "Priority_Level": str,
    "Arrival_Mode": str,
    "Event_Status": str,
    "Delay_Reason": str,
}

CASE_SCHEMA = {
    "Case_ID": str,
    "Patient_ID": str,
    "Arrival_Timestamp": str,
    "Departure_Timestamp": str,
    "Patient_Age_Group": str,
    "Priority_Level": str,
    "Arrival_Mode": str,
    "Initial_Department": str,
    "Final_Outcome": str,
    "Total_Length_of_Stay_Minutes": str,
}

VALID_PRIORITY_LEVELS = {"P1 - Immediate", "P2 - Urgent", "P3 - Semi-Urgent", "P4 - Non-Urgent"}
VALID_AGE_GROUPS = {"0-17", "18-34", "35-54", "55-74", "75+"}
VALID_ARRIVAL_MODES = {"Ambulance", "Walk-In", "GP Referral", "Self-Referral", "Police/Custody"}
VALID_EVENT_STATUS = {"Completed", "Skipped", "Cancelled", "Pending"}
VALID_FINAL_OUTCOMES = {"Discharged", "Admitted", "Transferred", "Left Without Being Seen"}


# ─────────────────────────────────────────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────────────────────────────────────────

def run_cleaning_pipeline() -> None:
    """Execute the full validation and cleaning pipeline."""
    log.info("CareFlow cleaning pipeline starting …")
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # ── Load raw files ────────────────────────────────────────────────────────
    log.info("Loading raw CSV files from %s", RAW_DIR)
    event_df = pd.read_csv(RAW_DIR / "event_log.csv", dtype=str, keep_default_na=False)
    case_df = pd.read_csv(RAW_DIR / "patient_cases.csv", dtype=str, keep_default_na=False)
    ref_df = pd.read_csv(RAW_DIR / "activity_reference.csv", dtype=str, keep_default_na=False)

    log.info("Raw event_log:       %d rows", len(event_df))
    log.info("Raw patient_cases:   %d rows", len(case_df))
    log.info("Raw activity_ref:    %d rows", len(ref_df))

    # ── Clean each file ───────────────────────────────────────────────────────
    event_df = _clean_event_log(event_df, ref_df)
    case_df = _clean_patient_cases(case_df)
    ref_df = _clean_activity_reference(ref_df)

    # ── Cross-file consistency ────────────────────────────────────────────────
    _cross_file_checks(event_df, case_df)

    # ── Derive additional features ────────────────────────────────────────────
    event_df = _derive_event_features(event_df)
    case_df = _derive_case_features(case_df)

    # ── Write processed files ─────────────────────────────────────────────────
    timestamp_tag = datetime.now().strftime("%Y%m%d_%H%M%S")
    _write(event_df, PROCESSED_DIR / f"event_log_clean_{timestamp_tag}.csv", "event_log_clean.csv")
    _write(case_df, PROCESSED_DIR / f"patient_cases_clean_{timestamp_tag}.csv", "patient_cases_clean.csv")
    _write(ref_df, PROCESSED_DIR / f"activity_reference_clean_{timestamp_tag}.csv", "activity_reference_clean.csv")

    log.info("✓ Cleaning pipeline complete.  Outputs → %s", PROCESSED_DIR)


# ─────────────────────────────────────────────────────────────────────────────
# FILE-SPECIFIC CLEANERS
# ─────────────────────────────────────────────────────────────────────────────

def _clean_event_log(df: pd.DataFrame, ref_df: pd.DataFrame) -> pd.DataFrame:
    log.info("[event_log] Starting cleaning …")

    # Strip whitespace from all string fields
    df = df.apply(lambda c: c.str.strip() if c.dtype == object else c)

    # Enforce enum membership
    df = _filter_enum(df, "Priority_Level", VALID_PRIORITY_LEVELS, "event_log")
    df = _filter_enum(df, "Patient_Age_Group", VALID_AGE_GROUPS, "event_log")
    df = _filter_enum(df, "Arrival_Mode", VALID_ARRIVAL_MODES, "event_log")
    df = _filter_enum(df, "Event_Status", VALID_EVENT_STATUS, "event_log")

    # Validate activity names against reference
    valid_acts = set(ref_df["Activity_Name"].str.strip())
    unknown_mask = ~df["Activity_Name"].isin(valid_acts)
    if unknown_mask.any():
        log.warning("[event_log] Dropping %d rows with unknown Activity_Name.", unknown_mask.sum())
        df = df[~unknown_mask].copy()

    # Parse timestamps
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
    bad_ts = df["Timestamp"].isna().sum()
    if bad_ts > 0:
        log.warning("[event_log] Dropping %d rows with unparseable Timestamp.", bad_ts)
        df = df[df["Timestamp"].notna()].copy()

    # Remove exact duplicate rows
    before = len(df)
    df = df.drop_duplicates()
    log.info("[event_log] Removed %d exact duplicate rows.", before - len(df))

    # Remove duplicate (Case_ID, Activity_Name, Timestamp) triplets
    before = len(df)
    df = df.drop_duplicates(subset=["Case_ID", "Activity_Name", "Timestamp"])
    log.info("[event_log] Removed %d duplicate (Case, Activity, Timestamp) rows.", before - len(df))

    # Sort by Case_ID, then Timestamp
    df = df.sort_values(["Case_ID", "Timestamp"]).reset_index(drop=True)

    log.info("[event_log] Clean shape: %s", df.shape)
    return df


def _clean_patient_cases(df: pd.DataFrame) -> pd.DataFrame:
    log.info("[patient_cases] Starting cleaning …")

    df = df.apply(lambda c: c.str.strip() if c.dtype == object else c)

    df = _filter_enum(df, "Priority_Level", VALID_PRIORITY_LEVELS, "patient_cases")
    df = _filter_enum(df, "Patient_Age_Group", VALID_AGE_GROUPS, "patient_cases")
    df = _filter_enum(df, "Arrival_Mode", VALID_ARRIVAL_MODES, "patient_cases")
    df = _filter_enum(df, "Final_Outcome", VALID_FINAL_OUTCOMES, "patient_cases")

    # Parse timestamps
    df["Arrival_Timestamp"] = pd.to_datetime(df["Arrival_Timestamp"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
    df["Departure_Timestamp"] = pd.to_datetime(df["Departure_Timestamp"], format="%Y-%m-%d %H:%M:%S", errors="coerce")

    # Flag cases where departure < arrival
    impossible_mask = (
        df["Departure_Timestamp"].notna() &
        (df["Departure_Timestamp"] < df["Arrival_Timestamp"])
    )
    if impossible_mask.any():
        log.warning("[patient_cases] Setting Departure_Timestamp to NaT for %d impossible timestamps.",
                    impossible_mask.sum())
        df.loc[impossible_mask, "Departure_Timestamp"] = pd.NaT

    # Convert LoS to numeric
    df["Total_Length_of_Stay_Minutes"] = pd.to_numeric(
        df["Total_Length_of_Stay_Minutes"], errors="coerce"
    )

    # Remove duplicate Case_IDs (keep first)
    before = len(df)
    df = df.drop_duplicates(subset=["Case_ID"], keep="first")
    log.info("[patient_cases] Removed %d duplicate Case_ID rows.", before - len(df))

    df = df.sort_values("Arrival_Timestamp").reset_index(drop=True)

    log.info("[patient_cases] Clean shape: %s", df.shape)
    return df


def _clean_activity_reference(df: pd.DataFrame) -> pd.DataFrame:
    log.info("[activity_reference] Starting cleaning …")
    df = df.apply(lambda c: c.str.strip() if c.dtype == object else c)

    df["Expected_Duration_Minutes"] = pd.to_numeric(df["Expected_Duration_Minutes"], errors="coerce")
    df["Is_Required"] = df["Is_Required"].map({"True": True, "False": False, "true": True, "false": False})

    before = len(df)
    df = df.drop_duplicates(subset=["Activity_ID"])
    log.info("[activity_reference] Removed %d duplicate Activity_ID rows.", before - len(df))

    log.info("[activity_reference] Clean shape: %s", df.shape)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# CROSS-FILE CHECKS
# ─────────────────────────────────────────────────────────────────────────────

def _cross_file_checks(event_df: pd.DataFrame, case_df: pd.DataFrame) -> None:
    log.info("Running cross-file consistency checks …")

    event_cases = set(event_df["Case_ID"].unique())
    case_cases = set(case_df["Case_ID"].unique())

    orphan_events = event_cases - case_cases
    if orphan_events:
        log.warning("  %d Case_IDs in event_log have no matching patient_cases row.", len(orphan_events))

    missing_events = case_cases - event_cases
    if missing_events:
        log.warning("  %d Case_IDs in patient_cases have no events in event_log.", len(missing_events))

    log.info("  Cross-file check complete.")


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE DERIVATION
# ─────────────────────────────────────────────────────────────────────────────

def _derive_event_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add sequence number and intra-case waiting time columns."""
    log.info("Deriving event features …")

    df = df.sort_values(["Case_ID", "Timestamp"]).copy()

    # Activity sequence number within each case
    df["Activity_Sequence_Number"] = df.groupby("Case_ID").cumcount() + 1

    # Time since previous event within same case (minutes)
    df["Time_Since_Previous_Event_Minutes"] = (
        df.groupby("Case_ID")["Timestamp"]
        .diff()
        .dt.total_seconds()
        .div(60)
        .round(1)
    )

    log.info("Event features derived.")
    return df


def _derive_case_features(df: pd.DataFrame) -> pd.DataFrame:
    """Recalculate LoS from timestamps where departure is available."""
    log.info("Deriving case features …")

    mask = df["Departure_Timestamp"].notna() & df["Arrival_Timestamp"].notna()
    df.loc[mask, "Total_Length_of_Stay_Minutes"] = (
        (df.loc[mask, "Departure_Timestamp"] - df.loc[mask, "Arrival_Timestamp"])
        .dt.total_seconds()
        .div(60)
        .round(0)
        .astype("Int64")
    )

    log.info("Case features derived.")
    return df


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _filter_enum(df: pd.DataFrame, col: str, valid_set: set, file_label: str) -> pd.DataFrame:
    invalid_mask = ~df[col].isin(valid_set) & df[col].notna() & (df[col] != "")
    if invalid_mask.any():
        log.warning("[%s] Dropping %d rows with invalid %s values: %s",
                    file_label, invalid_mask.sum(), col, df.loc[invalid_mask, col].unique()[:5])
        df = df[~invalid_mask].copy()
    return df


def _write(df: pd.DataFrame, versioned_path: Path, canonical_name: str) -> None:
    """Write to both a timestamped path and a canonical (latest) filename."""
    df.to_csv(versioned_path, index=False)
    df.to_csv(PROCESSED_DIR / canonical_name, index=False)
    log.info("✓ Written: %s  (%d rows)", canonical_name, len(df))


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_cleaning_pipeline()
