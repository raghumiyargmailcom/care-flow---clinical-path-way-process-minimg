# CareFlow — Clinical Pathway Process Mining

> **Disclaimer:** All data in this project is fully synthetic and generated for educational/research purposes only. No real patient information is used. Simulated findings do not represent actual hospital operations.

---

## 📋 Project Overview

CareFlow is a clinical pathway process mining project that analyses patient journeys through a simulated hospital environment. It applies process-mining algorithms (process discovery, conformance checking, and performance analysis) to uncover bottlenecks, deviations, and optimisation opportunities in clinical workflows.

---

## 🗂️ Folder Structure

```
careflow-process-mining/
├── data/
│   ├── raw/                  ← Generated source CSV files (event log, patient cases, activity reference)
│   ├── processed/            ← Cleaned, validated, and feature-engineered datasets
│   └── outputs/              ← Aggregated KPI tables, bottleneck summaries, conformance results
├── src/
│   ├── data_generation/      ← Synthetic dataset generation scripts
│   ├── data_cleaning/        ← Validation, deduplication, and cleaning scripts
│   ├── eda/                  ← Exploratory data analysis scripts
│   ├── process_mining/       ← Process discovery and conformance checking
│   ├── analytics/            ← Waiting-time, throughput, and KPI calculations
│   └── visualization/        ← Chart and process-map generation
├── notebooks/                ← Jupyter analysis notebooks
├── sql/                      ← SQL queries and analytical models
├── dashboard/                ← Power BI dashboard documentation and config
├── reports/                  ← Final reports and exported visualisations
├── tests/                    ← Automated unit and integration tests
├── docs/                     ← Data dictionary, methodology, project documentation
├── README.md
├── requirements.txt
└── .gitignore
```

---

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone <repository-url>
cd careflow-process-mining
```

### 2. Create and Activate a Virtual Environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Generate the Synthetic Dataset
```bash
python src/data_generation/generate_dataset.py
```
This writes three CSV files to `data/raw/`:
- `event_log.csv`
- `patient_cases.csv`
- `activity_reference.csv`

### 5. Run Data Cleaning & Validation
```bash
python src/data_cleaning/validate_and_clean.py
```
Cleaned data is written to `data/processed/`.

### 6. Exploratory Data Analysis
Open `notebooks/01_eda_overview.ipynb` or run:
```bash
python src/eda/eda_summary.py
```

---

## 📊 Dataset Summary

| File | Description | Rows (approx.) |
|---|---|---|
| `event_log.csv` | One row per activity per patient visit | ~55,000+ |
| `patient_cases.csv` | One row per patient visit | 5,000 |
| `activity_reference.csv` | Reference table of hospital activities | ~20 |

---

## 🔬 Key Analyses

1. **Process Discovery** — Inductive miner and directly-follows graph construction
2. **Conformance Checking** — Token-replay and alignment-based fitness metrics
3. **Bottleneck Detection** — Waiting-time heatmaps and throughput analysis
4. **KPI Dashboard** — Average length of stay, re-admission rate, triage-to-doctor time

---

## 📦 Dependencies

See `requirements.txt` for the full list. Key libraries:
- `pandas`, `numpy` — Data manipulation
- `pm4py` — Process mining (discovery, conformance, performance)
- `matplotlib`, `seaborn`, `plotly` — Visualisation
- `scipy`, `scikit-learn` — Statistical analysis

---

## 🧪 Running Tests
```bash
pytest tests/ -v
```

---

## 📄 Documentation

- `docs/data_dictionary.md` — Column definitions, data types, and relationships
- `docs/methodology.md` — Process mining approach and algorithm selection
- `docs/project_charter.md` — Project scope, objectives, and success criteria

---

## ⚠️ Ethical Notice

This project uses **entirely synthetic data** generated with a fixed random seed for reproducibility. It is intended solely for academic study of process-mining techniques in healthcare settings. The simulated patient journeys, delay patterns, and outcomes **do not represent any real hospital, patient, or clinical outcome**.
