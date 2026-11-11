"""
CareFlow — Process Conformance Checking Engine
==============================================
Compares actual patient journeys against the hospital's mandated clinical pathway,
computes trace and log fitness metrics, and flags non-compliant paths (especially
the unauthorized X-Ray -> Triage loop-back).
"""

from __future__ import annotations

import logging
import json
from pathlib import Path
import pandas as pd
import numpy as np
import pm4py

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parents[2]
PROCESSED_DIR = BASE_DIR / "data" / "processed"
OUTPUTS_DIR = BASE_DIR / "data" / "outputs"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("careflow.conformance")


# ── Hospital Mandated Pathway Definition ─────────────────────────────────────
# Standard mandated clinical order:
# 1. Registration -> 2. Triage -> 3. Doctor Consultation -> 4. Treatment/Diagnostics -> 5. Disposition
MANDATED_INITIAL_STEPS = ["Registration", "Triage", "Doctor Consultation"]
PERMITTED_TERMINAL_STEPS = {"Discharge", "Admission", "Transfer", "Patient Discharged"}


def check_trace_compliance(trace_activities: list[str]) -> dict:
    """
    Evaluates an individual patient trace against clinical governance rules:
      - Rule 1: Starts with Registration & Triage
      - Rule 2: No backward loop from X-Ray to Triage (intake paperwork fault)
      - Rule 3: Doctor Consultation before Treatment/Disposition
      - Rule 4: Valid terminal disposition
    """
    deviations: list[str] = []
    is_compliant = True

    # Rule 1 Check
    if not trace_activities or trace_activities[0] not in ("Registration", "Patient Registration"):
        deviations.append("MISSING_REGISTRATION_START")
        is_compliant = False

    if len(trace_activities) < 2 or trace_activities[1] not in ("Triage", "Initial Triage"):
        deviations.append("MISSING_INITIAL_TRIAGE")
        is_compliant = False

    # Rule 2 Check: Loop-back from X-Ray to Triage
    for i in range(len(trace_activities) - 1):
        if trace_activities[i] == "X-Ray" and trace_activities[i + 1] in ("Triage", "Initial Triage"):
            deviations.append("UNAUTHORIZED_XRAY_TO_TRIAGE_LOOPBACK")
            is_compliant = False
            break

    # Rule 3 Check: Doctor Consultation must exist
    consult_names = {"Doctor Consultation", "Initial Consultation"}
    if not any(act in consult_names for act in trace_activities):
        deviations.append("MISSING_DOCTOR_CONSULTATION")
        is_compliant = False

    # Rule 4 Check: Terminal step
    last_act = trace_activities[-1] if trace_activities else ""
    if not any(term in last_act for term in PERMITTED_TERMINAL_STEPS):
        deviations.append("INCOMPLETE_OR_IRREGULAR_DISPOSITION")
        is_compliant = False

    # Calculate trace fitness (percentage of rule criteria satisfied)
    max_rules = 4.0
    violations_count = len(deviations)
    trace_fitness = max(0.0, round((max_rules - violations_count) / max_rules, 3))

    return {
        "is_compliant": is_compliant,
        "trace_fitness": trace_fitness,
        "deviations": "; ".join(deviations) if deviations else "NONE",
        "primary_deviation": deviations[0] if deviations else "NONE",
    }


def run_conformance_checking() -> tuple[pd.DataFrame, dict]:
    """
    Executes conformance checking over all patient cases in the event log.
    """
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    event_path = PROCESSED_DIR / "event_log_clean.csv"
    if not event_path.exists():
        event_path = PROCESSED_DIR / "cleaned_data.csv"

    log.info("Loading event log for conformance checking from %s", event_path)
    df = pd.read_csv(event_path)
    
    col_map = {"Case_ID": "case_id", "Activity_Name": "activity", "Timestamp": "timestamp"}
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(["case_id", "timestamp"])

    log.info("Evaluating trace compliance for %d cases …", df["case_id"].nunique())

    case_traces = df.groupby("case_id")["activity"].agg(list)
    results = []

    for case_id, acts in case_traces.items():
        comp = check_trace_compliance(acts)
        results.append({
            "case_id": case_id,
            "pathway_length": len(acts),
            "trace_signature": " -> ".join(acts),
            "is_compliant": comp["is_compliant"],
            "trace_fitness": comp["trace_fitness"],
            "deviations": comp["deviations"],
            "primary_deviation": comp["primary_deviation"],
        })

    conformance_df = pd.DataFrame(results)

    # Calculate overall log fitness
    total_cases = len(conformance_df)
    compliant_cases = int(conformance_df["is_compliant"].sum())
    non_compliant_cases = total_cases - compliant_cases
    average_log_fitness = round(conformance_df["trace_fitness"].mean(), 3)
    compliance_rate_pct = round(100.0 * compliant_cases / total_cases, 1)

    # Deviation breakdown
    dev_counts = (
        conformance_df[conformance_df["primary_deviation"] != "NONE"]["primary_deviation"]
        .value_counts()
        .to_dict()
    )

    summary = {
        "total_cases_analyzed": total_cases,
        "compliant_cases": compliant_cases,
        "non_compliant_cases": non_compliant_cases,
        "compliance_rate_pct": compliance_rate_pct,
        "average_log_fitness_score": average_log_fitness,
        "deviation_breakdown": dev_counts,
        "xray_loopback_violations": dev_counts.get("UNAUTHORIZED_XRAY_TO_TRIAGE_LOOPBACK", 0),
    }

    # Save to disk
    conformance_df.to_csv(OUTPUTS_DIR / "conformance_results.csv", index=False)
    with open(OUTPUTS_DIR / "conformance_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    log.info("✓ Conformance results written to %s", OUTPUTS_DIR / "conformance_results.csv")
    log.info("✓ Conformance summary written to %s", OUTPUTS_DIR / "conformance_summary.json")

    return conformance_df, summary


def main():
    conformance_df, summary = run_conformance_checking()
    print("\n========================================================")
    print("          CAREFLOW PROCESS CONFORMANCE AUDIT            ")
    print("========================================================")
    print(f"Total Cases Analyzed:       {summary['total_cases_analyzed']}")
    print(f"Fully Compliant Cases:      {summary['compliant_cases']} ({summary['compliance_rate_pct']}%)")
    print(f"Non-Compliant Cases:        {summary['non_compliant_cases']}")
    print(f"Overall Log Fitness Score:  {summary['average_log_fitness_score']}")
    print("\nDeviation Breakdown:")
    for dev, count in summary["deviation_breakdown"].items():
        print(f"  - {dev}: {count} cases")


if __name__ == "__main__":
    main()

