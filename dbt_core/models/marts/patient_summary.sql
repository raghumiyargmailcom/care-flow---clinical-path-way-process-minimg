

WITH patient_summary AS (

    SELECT
        case_id,

        COUNT(*) AS total_events,

        COUNT(DISTINCT activity) AS unique_activities,

        MIN(event_timestamp) AS first_event_timestamp,

        MAX(event_timestamp) AS last_event_timestamp,

        TIMESTAMP_DIFF(
            MAX(event_timestamp),
            MIN(event_timestamp),
            MINUTE
        ) AS total_elapsed_minutes,

        SUM(waiting_time) AS total_waiting_minutes,

        AVG(waiting_time) AS avg_waiting_minutes,

        COUNTIF(next_activity IS NOT NULL) AS total_transitions,

        COUNT(DISTINCT department) AS departments_involved

    FROM {{ ref('int_patient_event') }}

    GROUP BY case_id
)

SELECT *
FROM patient_summary
