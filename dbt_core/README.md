# CareFlow dbt Core — Clinical Pathway Process Mining Data Models

This dbt project transforms raw clinical event logs into high-fidelity, analytics-ready models optimized for **Process Mining (DFG / Petri Nets / Conformance)**, **Clinical Pathway Optimization**, and **Operational Hospital Dashboards**.

---

## 🏗️ Architecture & Medallion Pipeline

```
Raw Sources & Seeds (seeds/)
  ├── raw_hospital_events.csv (953 clinical events, 100 patient cases)
  └── activity_reference.csv (Standard activity definitions, departments, and SLA targets)
         │
         ▼
Staging Layer (models/staging/ - Views)
  ├── stg_hospital_events.sql (Surrogate keys, cleaned typos: 'DoctorL' -> 'Doctor', temporal features)
  └── stg_activity_reference.sql (Typed reference metadata, milestone flags, SLA minutes)
         │
         ▼
Intermediate Layer (models/intermediate/ - Views)
  ├── int_event_transitions.sql (Step sequencing, LAG/LEAD event transition edges, wait & dwell times, rework flags)
  ├── int_case_journeys.sql (Case-level aggregations: total LoS, clinical milestones: Reg->Triage->Doctor, 4hr SLA compliance)
  └── int_pathway_variants.sql (String-aggregated pathway signatures, variant ranking, frequency & % distribution)
         │
         ▼
Marts / Analytics Layer (models/marts/ - Tables)
  ├── fct_case_summary.sql (Gold dimensional table: 1 row per patient journey with KPIs, outcome, and variant)
  ├── fct_event_log.sql (Enriched event log ready for PM4Py, Celonis, Disco, and BI tools)
  ├── fct_activity_transitions.sql (Directed edge matrix for Directly Follows Graphs (DFG) and Sankey flow)
  ├── fct_activity_performance.sql (Activity-level volume, wait times, dwell times, and rework rates)
  ├── fct_daily_hospital_metrics.sql (Daily patient census, LoS trends, and 4-hour target compliance rates)
  └── fct_bottleneck_analysis.sql (Ranked delay bottleneck stages weighted by cumulative delay hours)
```

---

## 🧼 Automatic Data Cleaning & Standardization

1. **Typo Correction**: Automatically corrects staff role typos (e.g. `DoctorL` standardized to `Doctor`).
2. **Surrogate Key Generation**: Generates deterministic MD5 primary keys (`event_id`) using `{{ surrogate_key(...) }}`.
3. **Temporal Feature Extraction**: Generates `activity_date`, `activity_hour`, `day_of_week`, and `is_weekend` flags.
4. **Data Hygiene**: Trims whitespace on all text columns, enforces strict NOT NULL constraints, and ensures uppercase case identifiers.

---

## 📊 Process Mining & Clinical KPIs Modeled

- **Length of Stay (LoS)**: Case duration in minutes and hours from initial registration to discharge.
- **National 4-Hour Standard Compliance**: Flags cases where `total_los_minutes <= 240`.
- **Milestone Gaps**:
  - `reg_to_triage_minutes`: Wait time from registration to triage nurse.
  - `triage_to_doctor_minutes`: Critical clinical consultation waiting time.
  - `reg_to_doctor_minutes`: Front-door operational turnaround time.
- **Rework & Quality Indicators**: Flags repeat consultations (`Repeat Doctor Consultation`), test repeats, and loop-backs.
- **Directly Follows Graph (DFG)**: Powers process discovery graphs with source-to-target transitions, edge counts, and average duration.
- **Pathway Variant Classification**: Categorizes patient journeys into distinct variants (e.g., standard outpatient vs inpatient admission vs diagnostic testing).

---

## 🚀 Usage Guide

### 1. Prerequisites
Ensure `dbt-core` and `dbt-bigquery` are installed:
```bash
pip install -r ../requirements4.txt
```

### 2. Configure Profile
Set your GCP credentials or environment variables:
```bash
export GCP_PROJECT_ID="your-project-id"
export DBT_DATASET="careflow_dbt"
```
Or edit `profiles.yml` located in this folder.

### 3. Parse and Compile Models
```bash
# Validate and compile all models without executing queries
dbt compile --profiles-dir .
```

### 4. Load Seeds (Initial Load)
```bash
dbt seed --profiles-dir .
```

### 5. Execute Pipeline & Run Tests
```bash
dbt run --profiles-dir .
dbt test --profiles-dir .
```
