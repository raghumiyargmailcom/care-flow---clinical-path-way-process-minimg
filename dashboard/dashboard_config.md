# CareFlow — Power BI Dashboard Documentation

## Overview

This document describes the Power BI dashboard configuration for the CareFlow project.

## Data Sources

Connect Power BI to the following processed CSV files:

| Table Name (PBI) | Source File |
|---|---|
| `EventLog` | `data/processed/event_log_clean.csv` |
| `PatientCases` | `data/processed/patient_cases_clean.csv` |
| `ActivityReference` | `data/processed/activity_reference_clean.csv` |
| `KPISummary` | `data/outputs/los_by_priority.csv` |

## Relationships (Star Schema)

```
PatientCases (Case_ID) ──1:M──► EventLog (Case_ID)
ActivityReference (Activity_Name) ──1:M──► EventLog (Activity_Name)
```

## Planned Report Pages

### Page 1: Executive Summary
- KPI cards: Total Cases, Avg LoS, Discharge Rate, 4-Hour Compliance
- Bar chart: Cases by Priority Level
- Donut: Final Outcome Distribution

### Page 2: Patient Flow
- Sankey diagram: Arrival Mode → Priority → Outcome
- Area chart: Daily patient volume trend
- Table: Top 10 longest cases

### Page 3: Bottleneck Analysis
- Heatmap: Activity wait times by hour of day
- Bar chart: Average dwell time per activity (vs reference)
- Table: Delay reason frequency

### Page 4: Process Conformance
- Gauge: Overall fitness score
- Table: Cases with conformance deviations
- Matrix: Activity × Event Status

## DAX Measures

```dax
Avg_LOS_Minutes =
    AVERAGEX(PatientCases, PatientCases[Total_Length_of_Stay_Minutes])

Discharge_Rate =
    DIVIDE(
        COUNTROWS(FILTER(PatientCases, PatientCases[Final_Outcome] = "Discharged")),
        COUNTROWS(PatientCases)
    )

Four_Hour_Target_Compliance =
    DIVIDE(
        COUNTROWS(FILTER(PatientCases, PatientCases[Total_Length_of_Stay_Minutes] <= 240)),
        COUNTROWS(PatientCases)
    )
```

## Theme

Use the `careflow_theme.json` file (to be created) for consistent brand colours.

Recommended palette:
- Primary: `#1A56DB` (Deep Blue)
- Secondary: `#7E3AF2` (Purple)
- Accent: `#0E9F6E` (Teal Green)
- Warning: `#FF5A1F` (Orange Red)
- Background: `#F9FAFB` (Near White)
