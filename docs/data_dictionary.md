# CareFlow — Data Dictionary

> **Version:** 1.0  
> **Last Updated:** 2024  
> **Status:** Active

---

## Overview

This document defines every column in the three core CareFlow CSV datasets.  
All data is entirely synthetic — no real patient information is used.

---

## 1. `event_log.csv` — Patient Activity Event Log

**Location:** `data/raw/event_log.csv`  
**Grain:** One row per activity performed during a patient hospital visit.  
**Primary Key:** Composite (`Case_ID`, `Activity_Name`, `Timestamp`)  
**Foreign Keys:** `Case_ID` → `patient_cases.Case_ID` | `Activity_Name` → `activity_reference.Activity_Name`

| Column | Data Type | Nullable | Example Value | Description |
|---|---|---|---|---|
| `Case_ID` | `string` | No | `CASE00001` | Unique identifier for a single hospital visit. Format: `CASE` + 5-digit zero-padded number. |
| `Patient_ID` | `string` | No | `PT00001` | Pseudonymous patient identifier. Format: `PT` + 5-digit zero-padded number. One patient may have multiple cases. |
| `Activity_Name` | `string` | No | `Blood Test` | Name of the hospital activity performed. Must match a value in `activity_reference.Activity_Name`. |
| `Timestamp` | `datetime` | No | `2024-03-15 09:42:00` | Date and time when the activity started. Format: `YYYY-MM-DD HH:MM:SS`. Chronologically ordered within each `Case_ID`. |
| `Department` | `string` | No | `Pathology` | Hospital department responsible for performing the activity. Derived from `activity_reference.Department`. |
| `Doctor_ID` | `string` | Yes | `DR007` | Pseudonymous doctor identifier. Format: `DR` + 3-digit number. Empty string when no doctor is directly involved (e.g., nursing activities). |
| `Patient_Age_Group` | `string` | No | `55-74` | Broad age category of the patient. Possible values: `0-17`, `18-34`, `35-54`, `55-74`, `75+`. |
| `Priority_Level` | `string` | No | `P2 - Urgent` | Emergency triage priority. Possible values: `P1 - Immediate`, `P2 - Urgent`, `P3 - Semi-Urgent`, `P4 - Non-Urgent`. |
| `Arrival_Mode` | `string` | No | `Ambulance` | How the patient arrived at the hospital. Possible values: `Ambulance`, `Walk-In`, `GP Referral`, `Self-Referral`, `Police/Custody`. |
| `Event_Status` | `string` | No | `Completed` | Outcome of the activity event. Possible values: `Completed`, `Skipped`, `Cancelled`, `Pending`. |
| `Delay_Reason` | `string` | Yes | `Awaiting Lab Results` | Reason for a process delay, if applicable. Empty string when no delay occurred. |

**Derived Columns (in `data/processed/event_log_clean.csv`):**

| Column | Data Type | Description |
|---|---|---|
| `Activity_Sequence_Number` | `integer` | 1-based rank of this activity within the case (sorted by `Timestamp`). |
| `Time_Since_Previous_Event_Minutes` | `float` | Minutes elapsed since the previous event in the same case. `NaN` for the first event. |

---

## 2. `patient_cases.csv` — Patient Visit Information

**Location:** `data/raw/patient_cases.csv`  
**Grain:** One row per hospital visit (case).  
**Primary Key:** `Case_ID`  
**Relationship:** One-to-many with `event_log.csv` (one case → many events)

| Column | Data Type | Nullable | Example Value | Description |
|---|---|---|---|---|
| `Case_ID` | `string` | No | `CASE00001` | Unique hospital visit identifier. Matches `event_log.Case_ID`. |
| `Patient_ID` | `string` | No | `PT00001` | Pseudonymous patient identifier. |
| `Arrival_Timestamp` | `datetime` | No | `2024-03-15 08:30:00` | Date and time of patient arrival at the hospital. |
| `Departure_Timestamp` | `datetime` | Yes | `2024-03-15 14:15:00` | Date and time of final departure. Empty for `Left Without Being Seen` cases. |
| `Patient_Age_Group` | `string` | No | `55-74` | Broad age category. See `event_log` for valid values. |
| `Priority_Level` | `string` | No | `P2 - Urgent` | Triage priority assigned at arrival. |
| `Arrival_Mode` | `string` | No | `Ambulance` | Mode of patient arrival. |
| `Initial_Department` | `string` | No | `Emergency` | First department the patient presented to. |
| `Final_Outcome` | `string` | No | `Discharged` | Overall case outcome. Possible values: `Discharged`, `Admitted`, `Transferred`, `Left Without Being Seen`. |
| `Total_Length_of_Stay_Minutes` | `integer` | Yes | `345` | Total visit duration in whole minutes. Calculated as `Departure_Timestamp − Arrival_Timestamp`. Empty when departure is unavailable. |

---

## 3. `activity_reference.csv` — Activity Reference Table

**Location:** `data/raw/activity_reference.csv`  
**Grain:** One row per standard hospital activity type.  
**Primary Key:** `Activity_ID`  
**Referenced by:** `event_log.Activity_Name`

| Column | Data Type | Nullable | Example Value | Description |
|---|---|---|---|---|
| `Activity_ID` | `string` | No | `ACT-001` | Unique activity identifier. Format: `ACT-` + 3-digit zero-padded number. |
| `Activity_Name` | `string` | No | `Blood Test` | Standard activity name. Must be unique. Used as a foreign key in `event_log`. |
| `Department` | `string` | No | `Pathology` | Hospital department responsible for this activity type. |
| `Activity_Category` | `string` | No | `Diagnostic` | High-level classification. Possible values: `Registration`, `Assessment`, `Diagnostic`, `Treatment`, `Disposition`. |
| `Expected_Duration_Minutes` | `integer` | No | `30` | Reference (ideal) duration in minutes for this activity. Used in conformance checking and bottleneck detection. |
| `Is_Required` | `boolean` | No | `False` | Whether this activity is required in the documented ideal process pathway. |
| `Description` | `string` | No | `Collection and analysis of blood samples …` | Plain-language description of the activity's clinical purpose. |

---

## File Relationships

```
activity_reference.csv
        │
        │ Activity_Name
        ▼
   event_log.csv ──── Case_ID ────► patient_cases.csv
   (many events)                     (one case per row)
```

---

## Categorical Value Reference

### Priority Levels (approximate real-world mappings)
| Value | Clinical Analogue | Target Response Time |
|---|---|---|
| `P1 - Immediate` | Resuscitation (MTS Level 1) | Immediate |
| `P2 - Urgent` | Very Urgent (MTS Level 2) | < 10 minutes |
| `P3 - Semi-Urgent` | Urgent (MTS Level 3) | < 60 minutes |
| `P4 - Non-Urgent` | Standard (MTS Level 4–5) | < 120–240 minutes |

### Activity Categories
| Category | Description |
|---|---|
| `Registration` | Administrative check-in and identity verification |
| `Assessment` | Clinical evaluation by medical or nursing staff |
| `Diagnostic` | Investigation to inform diagnosis (lab, imaging) |
| `Treatment` | Therapeutic intervention |
| `Disposition` | End-of-visit routing decision and execution |

---

> ⚠️ **Disclaimer:** All values in this project are entirely synthetic. No real patient, doctor, or hospital data is referenced.
