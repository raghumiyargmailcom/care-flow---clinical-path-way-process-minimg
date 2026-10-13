-- ============================================================
-- CareFlow — Core SQL Analytical Queries
-- ============================================================
-- Compatible with: DuckDB, SQLite, PostgreSQL
-- Raw CSV files are treated as virtual tables.
-- In DuckDB, replace <table_name> with read_csv_auto('path/to/file.csv')
-- ============================================================

-- ─────────────────────────────────────────────────────────────
-- Q1: Average Length of Stay by Priority Level
-- ─────────────────────────────────────────────────────────────
SELECT
    Priority_Level,
    COUNT(*)                                        AS Total_Cases,
    ROUND(AVG(Total_Length_of_Stay_Minutes), 1)     AS Avg_LOS_Minutes,
    ROUND(MEDIAN(Total_Length_of_Stay_Minutes), 1)  AS Median_LOS_Minutes,
    ROUND(MAX(Total_Length_of_Stay_Minutes), 0)     AS Max_LOS_Minutes
FROM patient_cases
WHERE Total_Length_of_Stay_Minutes IS NOT NULL
GROUP BY Priority_Level
ORDER BY Priority_Level;


-- ─────────────────────────────────────────────────────────────
-- Q2: Final Outcome Distribution
-- ─────────────────────────────────────────────────────────────
SELECT
    Final_Outcome,
    COUNT(*)                                    AS Case_Count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS Percentage
FROM patient_cases
GROUP BY Final_Outcome
ORDER BY Case_Count DESC;


-- ─────────────────────────────────────────────────────────────
-- Q3: Activity Frequency and Average Dwell Time
-- ─────────────────────────────────────────────────────────────
SELECT
    el.Activity_Name,
    el.Department,
    COUNT(*)                                                AS Event_Count,
    ROUND(AVG(el.Time_Since_Previous_Event_Minutes), 1)    AS Avg_Wait_Before_Minutes,
    ROUND(SUM(CASE WHEN el.Event_Status = 'Completed' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS Completion_Rate_Pct
FROM event_log el
GROUP BY el.Activity_Name, el.Department
ORDER BY Event_Count DESC;


-- ─────────────────────────────────────────────────────────────
-- Q4: Top Delay Reasons
-- ─────────────────────────────────────────────────────────────
SELECT
    Delay_Reason,
    COUNT(*) AS Occurrences,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS Percentage
FROM event_log
WHERE Delay_Reason IS NOT NULL AND Delay_Reason != ''
GROUP BY Delay_Reason
ORDER BY Occurrences DESC;


-- ─────────────────────────────────────────────────────────────
-- Q5: Daily Patient Volume
-- ─────────────────────────────────────────────────────────────
SELECT
    CAST(Arrival_Timestamp AS DATE) AS Arrival_Date,
    COUNT(*)                        AS Daily_Case_Count,
    COUNT(DISTINCT Patient_ID)      AS Unique_Patients
FROM patient_cases
GROUP BY Arrival_Date
ORDER BY Arrival_Date;


-- ─────────────────────────────────────────────────────────────
-- Q6: Cases with Repeated Activities (Bottleneck Indicator)
-- ─────────────────────────────────────────────────────────────
SELECT
    Case_ID,
    Activity_Name,
    COUNT(*) AS Repetitions
FROM event_log
GROUP BY Case_ID, Activity_Name
HAVING COUNT(*) > 1
ORDER BY Repetitions DESC
LIMIT 50;


-- ─────────────────────────────────────────────────────────────
-- Q7: Triage-to-Doctor Consultation Time by Priority
-- ─────────────────────────────────────────────────────────────
WITH triage_times AS (
    SELECT Case_ID, Timestamp AS Triage_TS
    FROM event_log
    WHERE Activity_Name = 'Triage'
),
consult_times AS (
    SELECT Case_ID, MIN(Timestamp) AS Consult_TS
    FROM event_log
    WHERE Activity_Name = 'Doctor Consultation'
    GROUP BY Case_ID
)
SELECT
    pc.Priority_Level,
    COUNT(*)                                        AS Cases,
    ROUND(AVG(DATEDIFF('minute', t.Triage_TS, c.Consult_TS)), 1) AS Avg_Triage_To_Doctor_Min,
    ROUND(MEDIAN(DATEDIFF('minute', t.Triage_TS, c.Consult_TS)), 1) AS Median_Triage_To_Doctor_Min
FROM triage_times t
JOIN consult_times c USING (Case_ID)
JOIN patient_cases pc USING (Case_ID)
GROUP BY pc.Priority_Level
ORDER BY pc.Priority_Level;


-- ─────────────────────────────────────────────────────────────
-- Q8: Event Status Breakdown per Activity
-- ─────────────────────────────────────────────────────────────
SELECT
    Activity_Name,
    Event_Status,
    COUNT(*) AS Count
FROM event_log
GROUP BY Activity_Name, Event_Status
ORDER BY Activity_Name, Event_Status;
