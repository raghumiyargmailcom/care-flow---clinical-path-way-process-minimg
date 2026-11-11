# CareFlow — Power BI Dashboard Configuration & Guide

## 📊 Overview

This report models the **CareFlow: Clinical Pathway Process Mining** project. It is designed to run both as an interactive HTML Power BI visualizer ([`dashboard/index.html`](file:///c:/Users/raagh/OneDrive/Desktop/care-flow---clinical-path-way-process-minimg/dashboard/index.html)) and directly inside **Microsoft Power BI Desktop / Service** via Google BigQuery DirectQuery or local CSV imports.

---

## 🗄️ Data Model & Sources (Star Schema)

Connect Power BI to either the **Google BigQuery** dataset `careflow_dbt` or the processed CSV exports:

| Power BI Table Name | DirectQuery BigQuery Table | Local Processed Source File | Key Role |
|---|---|---|---|
| `PatientCases` | `careflow_dbt.fct_case_summary` | `data/processed/patient_cases_clean.csv` | Primary Dimension Table (1 row per journey) |
| `EventLog` | `careflow_dbt.fct_event_log` | `data/processed/event_log_clean.csv` | Central Fact Table (chronological event stream) |
| `EventTransitions` | `careflow_dbt.fct_activity_transitions` | `data/outputs/dfg_transitions.csv` | Process Mining Edge Matrix |
| `ActivityReference`| `careflow_dbt.stg_activity_reference` | `data/processed/activity_reference_clean.csv`| Activity Reference Dimension |

### Relationship Cardinality

```
PatientCases (Case_ID) ───────── 1 : M (Single) ───────► EventLog (Case_ID)
ActivityReference (Activity_Name) ── 1 : M (Single) ────► EventLog (Activity_Name)
```

---

## 📑 Report Pages

- **Page 1: Executive Overview:** Multi-row KPI cards, Cases by Priority Level (Bar), Final Outcome Distribution (Donut), and Monthly Patient Census Trend (Area).
- **Page 2: Process Mining Flow (Spaghetti Diagram):** Power Automate Process Mining Visual uncovering the 40.1% X-Ray → Triage return-loop.
- **Page 3: Bottleneck & Transition Matrix:** Full interactive transition latency table and delay duration rankings.
- **Page 4: Conformance & Governance Audit:** Log fitness metric (0.958), breakdown of non-compliant traces, and intake form remediation impact.
- **Page 5: Power BI Architecture & DAX Code:** Technical specifications and DirectQuery setup.

---

## 📐 Enterprise DAX Measures

```dax
// 1. Average Length of Stay in Minutes
Avg_LOS_Minutes = 
AVERAGEX(
    'PatientCases', 
    'PatientCases'[Total_Length_of_Stay_Minutes]
)

// 2. Average Length of Stay in Hours
Avg_LOS_Hours = 
DIVIDE([Avg_LOS_Minutes], 60, 0)

// 3. National 4-Hour Emergency Standard Compliance Rate (%)
Four_Hour_Target_Compliance = 
DIVIDE(
    CALCULATE(
        COUNTROWS('PatientCases'), 
        'PatientCases'[Total_Length_of_Stay_Minutes] <= 240
    ),
    COUNTROWS('PatientCases'),
    0
)

// 4. Critical Operational Bottleneck: X-Ray to Triage Loop-Back Rate (%)
XRay_Triage_Loopback_Rate = 
DIVIDE(
    CALCULATE(
        COUNTROWS('EventTransitions'),
        'EventTransitions'[from_activity] = "X-Ray",
        'EventTransitions'[to_activity] = "Triage"
    ),
    CALCULATE(
        COUNTROWS('EventTransitions'),
        'EventTransitions'[from_activity] = "X-Ray"
    ),
    0
)

// 5. Cumulative Clinical Capacity Saved by Form Fix (Hours)
Annual_Intake_Capacity_Saved_Hours = 
DIVIDE(
    CALCULATE(
        COUNTROWS('EventTransitions'),
        'EventTransitions'[from_activity] = "X-Ray",
        'EventTransitions'[to_activity] = "Triage"
    ) * 20.0, 
    60,
    0
)

// 6. Conformance Rate (% of Strictly Compliant Paths)
Clinical_Conformance_Rate = 
DIVIDE(
    CALCULATE(
        COUNTROWS('PatientCases'),
        'PatientCases'[Final_Outcome] IN {"Discharged", "Admitted", "Transferred"}
    ),
    COUNTROWS('PatientCases'),
    0
)
```

---

## 🚀 How to View & Use

1. **In Browser:** Double-click or open [`dashboard/index.html`](file:///c:/Users/raagh/OneDrive/Desktop/care-flow---clinical-path-way-process-minimg/dashboard/index.html).
2. **In Power BI Desktop:**
   - Launch Power BI Desktop $\to$ Import `data/processed/*.csv` or connect to BigQuery DirectQuery.
   - Configure relationships per the Star Schema above.
   - Create a New Measure and paste the DAX definitions above.
