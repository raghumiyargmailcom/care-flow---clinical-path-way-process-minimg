
from google.cloud import bigquery

import pandas as pd

# Connect to your Google Cloud project
PROJECT_ID = "dbt-bigquery-512805"

client = bigquery.Client(project=PROJECT_ID)

# Read patient summary from dbt
patient_query = """
SELECT *
FROM `dbt-bigquery-512805.process_mining.patient_summary`
"""

patient_summary = client.query(patient_query).to_dataframe()

# Read transition analysis from dbt
transition_query = """
SELECT *
FROM `dbt-bigquery-512805.process_mining.mart_transition`
"""

mart_transition = client.query(transition_query).to_dataframe()

# Save the results for Power BI
patient_summary.to_csv("patient_summary.csv", index=False)
mart_transition.to_csv("mart_transition.csv", index=False)

print("BigQuery connection successful!")
print("Patient summary shape:", patient_summary.shape)
print("Transition table shape:", mart_transition.shape)

print(patient_summary.head())
print(mart_transition.head())
